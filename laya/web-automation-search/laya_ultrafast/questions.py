from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from laya_ultrafast.core.action_executor import Action, ActionType
from laya_ultrafast.core.exceptions import ActionValidationError
from laya_ultrafast.utils.dom import ElementSnapshot, build_element_summary

if TYPE_CHECKING:
    from laya_ultrafast.model import ModelResponse


MAX_ELEMENTS = 50
MAX_HISTORY = 10

ACTION_CHOICES = [
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

ACTION_DESCRIPTIONS = {
    "CLICK": "Clica em botão, link ou elemento clicável (requer target_id/selector)",
    "TYPE_TEXT": "Digita texto em campo input/textarea (requer target_id/selector + value)",
    "SELECT": "Seleciona opção em dropdown <select> (requer target_id/selector + value)",
    "SCROLL_UP": "Rola página para cima (direction=up, amount=pixels)",
    "SCROLL_DOWN": "Rola página para baixo (direction=down, amount=pixels)",
    "WAIT": "Aguarda carregamento/estabilização (wait_ms em ms)",
    "NAVIGATE": "Navega para URL (requer url)",
    "GO_BACK": "Volta página anterior no histórico",
    "DONE": "Meta alcançada - finaliza execução",
    "BLOCKED": "Não é possível prosseguir - impasse ou erro",
}


def build_prompt(
    snapshot: list[ElementSnapshot],
    goal: str,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Constrói o estado estruturado para o modelo de decisão LAYA.
    
    Em vez de um prompt de texto para LLM, retorna um dicionário estruturado
    com state (elementos do DOM) e questions (ações possíveis).
    
    Args:
        snapshot: Lista de ElementSnapshot do DOM atual
        goal: Meta do usuário em linguagem natural
        history: Histórico de ações anteriores
        
    Returns:
        Dict com state (elementos) e questions (esquema de decisão)
    """
    elements = snapshot[:MAX_ELEMENTS]
    
    state = {
        "goal": goal,
        "elements": [
            {
                "id": e.id,
                "index": e.index,
                "tag": e.tag,
                "role": e.role,
                "label": e.label,
                "selector": e.selector,
                "bbox": e.bbox,
                "attrs": e.attrs,
                "is_visible": e.is_visible,
                "is_obstructed": e.is_obstructed,
                "is_interactive": e.is_interactive,
                "is_editable": e.is_editable,
            }
            for e in elements
        ],
        "history": history or [],
    }

    questions = {
        "choices": ACTION_CHOICES,
        "descriptions": ACTION_DESCRIPTIONS,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {"type": "string", "enum": ACTION_CHOICES},
                "score": {"type": "number", "minimum": 0, "maximum": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "probabilities": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "reasoning": {"type": "string"},
            },
            "required": ["choice", "score", "confidence", "probabilities"],
        },
    }

    return {
        "state": state,
        "questions": questions,
    }


def model_response_to_action(response: "ModelResponse") -> Action:
    """
    Converte a resposta estruturada do modelo LAYA em Action executável.
    
    Args:
        response: ModelResponse com choice, score, confidence, probabilities
        
    Returns:
        Action para ser executada pelo ActionExecutor
    """
    from laya_ultrafast.model import ModelResponse
    choice = response.choice
    
    # Mapeia escolha para Action baseada na probabilidade
    if choice == "CLICK":
        # O executor precisa do target_id - será resolvido no laya_engine
        return Action(type=ActionType.CLICK, target_id="auto", selector=None)
    elif choice == "TYPE_TEXT":
        return Action(type=ActionType.TYPE_TEXT, target_id="auto", selector=None, value="")
    elif choice == "SELECT":
        return Action(type=ActionType.SELECT, target_id="auto", selector=None, value="")
    elif choice == "SCROLL_UP":
        return Action(type=ActionType.SCROLL_UP, direction="up", amount=300)
    elif choice == "SCROLL_DOWN":
        return Action(type=ActionType.SCROLL_DOWN, direction="down", amount=300)
    elif choice == "WAIT":
        return Action(type=ActionType.WAIT, wait_ms=1000)
    elif choice == "NAVIGATE":
        return Action(type=ActionType.NAVIGATE, url="")
    elif choice == "GO_BACK":
        return Action(type=ActionType.GO_BACK)
    elif choice == "DONE":
        return Action(type=ActionType.DONE)
    elif choice == "BLOCKED":
        return Action(type=ActionType.BLOCKED, value="Modelo indicou bloqueio")
    
    # Fallback
    return Action(type=ActionType.WAIT)


def parse_response(response: "ModelResponse | dict | str") -> Action:
    """
    Parseia a resposta do modelo LAYA para Action.
    
    Aceita ModelResponse, dict, ou string JSON.
    """
    from laya_ultrafast.model import ModelResponse
    from pydantic import ValidationError
    
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError as e:
            raise ActionValidationError(f"Resposta não é JSON válido: {e}")
    
    if isinstance(response, dict):
        try:
            response = ModelResponse.model_validate(response)
        except ValidationError as e:
            raise ActionValidationError(f"Resposta não corresponde ao schema: {e}")
    
    if not isinstance(response, ModelResponse):
        raise ActionValidationError(f"Tipo de resposta inválido: {type(response)}")
    
    return model_response_to_action(response)


def validate_action_response(response: "ModelResponse") -> tuple[bool, str | None]:
    """
    Valida se a resposta do modelo LAYA é válida.
    
    Returns:
        (is_valid, error_message)
    """
    from laya_ultrafast.model import ModelResponse
    
    if not isinstance(response, ModelResponse):
        return False, "Resposta não é ModelResponse"
    
    if response.choice not in ACTION_CHOICES:
        return False, f"Ação inválida: {response.choice}"
    
    if not (0.0 <= response.score <= 1.0):
        return False, "Score fora do intervalo [0, 1]"
    
    if not (0.0 <= response.confidence <= 1.0):
        return False, "Confidence fora do intervalo [0, 1]"
    
    # Verifica se probabilidades somam aproximadamente 1
    prob_sum = sum(response.probabilities.values())
    if prob_sum > 0 and abs(prob_sum - 1.0) > 0.2:
        return False, f"Probabilidades não somam 1: {prob_sum}"
    
    return True, None