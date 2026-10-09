from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from pydantic import BaseModel, Field, ValidationError

from laya_ultrafast.core.exceptions import ModelError

if TYPE_CHECKING:
    from laya_ultrafast.config.settings import LAYAConfig

logger = __import__("structlog").get_logger(__name__)

T = TypeVar("T", bound="ModelResponse")


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Resposta estruturada do modelo LAYA local."""

    choice: str  # A ação escolhida (CLICK, TYPE_TEXT, SELECT, etc.)
    score: float  # Pontuação de confiança (0.0 a 1.0)
    confidence: float  # Nível de confiança da decisão
    probabilities: dict[str, float]  # Probabilidades de todas as ações possíveis
    reasoning: str | None = None  # Raciocínio breve da decisão


class LayaDecisionModel:
    """
    Modelo de decisão local LAYA.
    
    Substitui completamente serviços externos (JEV/OpenRouter/Ollama) por
    inferência 100% local. Recebe estado estruturado do DOM + perguntas tipadas
    e retorna probabilidades de ações com níveis de confiança.
    
    Este modelo não é um LLM generativo - ele classifica e decide baseado
    em regras heurísticas e padrões de reconhecimento de intenção.
    """

    def __init__(self, config: Any = None):
        self.config = config or {}
        # Pesos heurísticos para diferentes tipos de decisões
        self._weights = self._initialize_weights()

    def _initialize_weights(self) -> dict[str, dict[str, float]]:
        """Inicializa pesos heurísticos para classificação de ações."""
        return {
            "CLICK": {
                "keyword_match": 0.8,
                "visible_prominent": 0.9,
                "form_field_related": 0.7,
            },
            "TYPE_TEXT": {
                "input_field": 0.95,
                "search_box": 0.9,
                "has_placeholder_match": 0.85,
            },
            "SELECT": {
                "dropdown": 0.8,
                "form_select": 0.75,
            },
            "SCROLL": {
                "long_page": 0.8,
                "below_fold": 0.7,
            },
            "WAIT": {
                "spinner_loading": 0.85,
                "modal_waiting": 0.8,
            },
            "NAVIGATE": {
                "url_explicit": 0.95,
                "search_intent": 0.7,
            },
            "GO_BACK": {
                "breadcrumbs": 0.85,
                "history_indicator": 0.75,
            },
            "DONE": {
                "goal_achieved": 0.9,
                "no_interactive": 0.8,
            },
            "BLOCKED": {
                "no_valid_target": 0.9,
                "captcha": 0.95,
            },
        }

    async def decide(
        self,
        snapshot_elements: list[dict],
        goal: str,
        history: list[dict] | None = None,
    ) -> ModelResponse:
        """
        Decide a próxima ação baseada no snapshot do DOM e na meta do usuário.
        
        Args:
            snapshot_elements: Lista de dicionários com propriedades dos elementos do DOM
            goal: A meta/goal do usuário em linguagem natural
            history: Histórico de ações anteriores (opcional)
            
        Returns:
            ModelResponse com choice, score, confidence e probabilities
        """
        # Analisa os elementos e a goal para gerar probabilidades
        probabilities = self._calculate_probabilities(snapshot_elements, goal, history)
        
        # Normaliza as probabilidades
        total = sum(probabilities.values())
        if total > 0:
            for k in probabilities:
                probabilities[k] = probabilities[k] / total
        else:
            # Fallback uniforme
            n_actions = len(self._get_available_actions())
            uniform = 1.0 / n_actions if n_actions > 0 else 0
            for action in self._get_available_actions():
                probabilities[action] = uniform

        # Escolhe a ação com maior probabilidade
        best_action = max(probabilities, key=probabilities.get)
        score = probabilities[best_action]
        confidence = self._calculate_confidence(probabilities, best_action)

        # Gera raciocínio breve
        reasoning = self._generate_reasoning(
            best_action, probabilities, snapshot_elements, goal
        )

        return ModelResponse(
            choice=best_action,
            score=round(score, 4),
            confidence=round(confidence, 4),
            probabilities={
                k: round(v, 4) for k, v in probabilities.items()
            },
            reasoning=reasoning,
        )

    def _get_available_actions(self) -> list[str]:
        """Retorna todas as ações possíveis."""
        return [
            "CLICK",
            "TYPE_TEXT",
            "SELECT",
            "SCROLL_UP",
            "SCROLL_DOWN",
            "WAIT",
            "NAVIGATE",
            "GO_BACK",
            "DONE",
            "BLOCKED",
        ]

    def _calculate_probabilities(
        self,
        elements: list[dict],
        goal: str,
        history: list[dict] | None,
    ) -> dict[str, float]:
        """
        Calcula probabilidades heurísticas para cada ação baseadas nos elementos
        do snapshot e na goal do usuário.
        """
        probs: dict[str, float] = {action: 0.0 for action in self._get_available_actions()}

        # Extrair características do snapshot
        visible_elements = [e for e in elements if e.get("is_visible", False)]
        interactive_elements = [e for e in visible_elements if e.get("is_interactive", False)]
        editable_elements = [e for e in interactive_elements if e.get("is_editable", False)]
        buttons = [e for e in interactive_elements if e.get("tag", "") == "button"]
        inputs = [e for e in interactive_elements if e.get("tag", "") in ("input", "textarea")]
        selects = [e for e in interactive_elements if e.get("tag", "") == "select"]

        goal_lower = goal.lower()

        # --- CLICK ---
        if buttons:
            # Clique em botão visível é alto se a goal sugerir ação imediata
            if any(
                k in goal_lower for k in ["clicar", "clique", "botão", "enviar", "ok"]
            ):
                for btn in buttons:
                    bbox = btn.get("bbox", {})
                    # Botão central/prominente tem mais peso
                    if bbox.get("width", 0) > 50 and bbox.get("height", 0) > 20:
                        probs["CLICK"] += 0.15
        
        # --- TYPE_TEXT ---
        if inputs:
            # Campo de input tem alta probabilidade para queries de busca
            for inp in inputs:
                placeholder = inp.get("attrs", {}).get("placeholder", "").lower()
                label = inp.get("label", "").lower()
                # Match com termos da goal
                if any(
                    term in (placeholder + " " + label) 
                    for term in goal_lower.split()
                ):
                    probs["TYPE_TEXT"] += 0.2
        
        # --- SELECT ---
        if selects:
            if any(k in goal_lower for k in ["selecionar", "escolher", "filtro", "categoria"]):
                probs["SELECT"] += 0.1
        
        # --- SCROLL ---
        if len(elements) > 50:  # Página longa
            if any(k in goal_lower for k in ["descer", "scroll", "baixar"]):
                probs["SCROLL_DOWN"] += 0.15
        
        # --- WAIT ---
        if any(
            k in goal_lower for k in ["carregar", "esperar", "loading", "spinner"]
        ):
            probs["WAIT"] += 0.1
        
        # --- NAVIGATE ---
        if any(k in goal_lower for k in ["ir para", "acessar", "website", "página"]):
            # Se houver URL no goal, maior peso
            if any(c.isdigit() for c in goal) or "." in goal:
                probs["NAVIGATE"] += 0.1
        
        # --- GO BACK ---
        if any(k in goal_lower for k in ["voltar", "anterior", "voltar atrás"]):
            probs["GO_BACK"] += 0.1
        
        # --- DONE ---
        if any(k in goal_lower for k in ["concluir", "fim", "terminar", "feito"]):
            probs["DONE"] += 0.1
        
        # --- BLOCKED ---
        if not interactive_elements:
            probs["BLOCKED"] += 0.5
        if any(k in goal_lower for k in ["captcha", "verificação", "robô"]):
            probs["BLOCKED"] += 0.3

        return probs

    def _calculate_confidence(
        self, probabilities: dict[str, float], best_action: str
    ) -> float:
        """Calcula o nível de confiança baseado na distribuição de probabilidades."""
        # A confiança aumenta quando há uma ação claramente dominante
        sorted_actions = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_actions) >= 2:
            gap = sorted_actions[0][1] - sorted_actions[1][1]
            # Gap maior = maior confiança
            # Normalizar para 0.0 a 1.0
            confidence = min(gap * 2 + 0.3, 1.0)
        else:
            confidence = 0.5
        return confidence

    def _generate_reasoning(
        self,
        action: str,
        probabilities: dict[str, float],
        elements: list[dict],
        goal: str,
    ) -> str | None:
        """Gera um raciocínio breve da decisão."""
        reasons = []
        
        # Encontrar o elemento chave que justificou a decisão
        best_prob = max(probabilities.values()) if probabilities else 0
        
        if best_prob > 0.5:
            # Encontrar elemento relevante
            for elem in elements:
                if elem.get("is_visible", False) and elem.get("is_interactive", False):
                    label = elem.get("label", "").lower()
                    if any(
                        term in label 
                        for term in goal.lower().split() 
                        if len(term) > 2
                    ):
                        reasons.append(f"Elemento '{elem['label']}' relevante para a goal")
                        break
        
        if not reasons:
            reasons.append("Análise de padrão de intenção")
        
        # Selecionar o motivo mais forte
        primary_reason = reasons[0] if reasons else None
        return primary_reason

    async def complete(self, *args, **kwargs) -> ModelResponse:
        """Interface assíncrona - decide baseado em estado atual."""
        # Para compatibilidade com o fluxo existente, retorna decisão baseada
        # em estado vazio (será preenchido pelo laya_engine quando houver snapshot)
        return ModelResponse(
            choice="WAIT",
            score=0.5,
            confidence=0.5,
            probabilities={action: 0.1 for action in self._get_available_actions()},
            reasoning="Modelo local LAYA ativo - aguardando snapshot do DOM",
        )

    async def complete_structured(
        self,
        *args,
        **kwargs,
    ) -> ModelResponse:
        """Alias para complete - modelo local não precisa de structured output."""
        return await self.complete(*args, **kwargs)


def create_laya_model(config: Any | None = None) -> LayaDecisionModel:
    """
    Factory function para criar instância do modelo de decisão LAYA.
    
    Substitui create_model_client - não há mais provedores de LLM externos.
    """
    return LayaDecisionModel(config)