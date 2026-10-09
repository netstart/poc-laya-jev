from __future__ import annotations

import time
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from laya_ultrafast.config.settings import LAYAConfig, get_config
from laya_ultrafast.core.action_executor import (
    Action,
    ActionExecutor,
    ActionType,
    find_element,
)
from laya_ultrafast.core.context_manager import ContextManager, SessionContext
from laya_ultrafast.core.exceptions import (
    ActionValidationError,
    AgentBlockedError,
    AgentError,
    AgentMaxStepsExceededError,
    BrowserSnapshotError,
)
from laya_ultrafast.utils.dom import ElementSnapshot
from laya_ultrafast.utils.metrics import get_metrics, timing
from laya_ultrafast.questions import (
    build_prompt,
    model_response_to_action,
    validate_action_response,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = structlog.get_logger(__name__)

#: Re-prompts máximos para JSON inválido (§4.4: 1 tentativa + 2 re-prompts).
MAX_JSON_RETRIES = 2

#: Tolerância (px) aceita na comparação de bounding box do teste de frescura.
FRESHNESS_TOLERANCE_PX = 2.0


@dataclass(frozen=True, slots=True)
class RunResult:
    """Resultado final de uma execução do agente."""

    success: bool
    session_id: str
    goal: str
    steps_taken: int
    final_message: str
    error: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    session_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "session_id": self.session_id,
            "goal": self.goal,
            "steps_taken": self.steps_taken,
            "final_message": self.final_message,
            "error": self.error,
            "metrics": self.metrics,
            "session_summary": self.session_summary,
        }


class LayaEngine:
    """
    Orquestrador principal do agente LAYA.

    Fluxo:
    1. Captura snapshot do DOM
    2. Constrói estado estruturado para o modelo
    3. Chama modelo para decidir ação
    4. Valida e executa ação
    5. Verifica resultado
    6. Repete até DONE/BLOCKED/max_steps
    """

    def __init__(
        self,
        config: LAYAConfig | None = None,
        browser_session: Any = None,
        model_client: Any = None,
        prompt_builder: Callable[
            [list[ElementSnapshot], str, list[dict]], dict[str, Any]
        ] | None = None,
        response_parser: Callable[[ModelResponse | dict | str], Action] | None = None,
        context_manager: ContextManager | None = None,
    ):
        self.config = config or get_config()
        self.browser = browser_session
        self.model = model_client
        self.prompt_builder = prompt_builder
        self.response_parser = response_parser
        self.context_manager = context_manager or ContextManager(
            checkpoint_interval_steps=self.config.checkpoint_interval_steps,
            default_ttl_seconds=3600,
        )
        self.metrics = get_metrics()
        self._action_executor: ActionExecutor | None = None
        # Circuit breaker do modelo (§4.3); criado de forma preguiçosa para
        # evitar import circular com laya_ultrafast.utils.retry.
        self._model_circuit_breaker: Any = None

    def set_browser(self, browser_session: Any):
        self.browser = browser_session
        self._action_executor = None  # Reset executor

    def set_model(self, model_client: Any):
        self.model = model_client

    def _get_executor(self) -> ActionExecutor:
        if self._action_executor is None:
            if not self.browser:
                raise AgentError("Browser session not set")
            viewport = self.browser.get_viewport()
            self._action_executor = ActionExecutor(
                browser_session=self.browser,
                viewport=viewport,
                action_timeout_ms=self.config.action_timeout_ms,
                verify_after_action=True,
            )
        return self._action_executor

    async def run(
        self,
        goal: str,
        max_steps: int | None = None,
        session_id: str | None = None,
        initial_url: str | None = None,
    ) -> RunResult:
        """
        Executa o agente para alcançar a meta.

        Args:
            goal: Objetivo em linguagem natural
            max_steps: Override do máximo de passos
            session_id: ID de sessão existente para resume
            initial_url: URL inicial para navegar antes de começar

        Returns:
            RunResult com resultado da execução
        """
        max_steps = max_steps or self.config.max_steps
        session = self._get_or_create_session(goal, max_steps, session_id)

        if initial_url and session.current_step == 0:
            await self.browser.navigate(initial_url)
            await self._wait_for_stability()

        logger.info(
            "Session created",
            goal=goal,
            session_id=session.id,
            max_steps=max_steps,
        )
        logger.info(
            "Starting agent run",
            goal=goal,
            max_steps=max_steps,
            session_id=session.id,
        )

        # Loop principal do agente
        while session.current_step < max_steps:
            step_start = time.time()

            # 1. Captura snapshot do DOM
            snapshot_id = None
            snapshot = []
            with timing("snapshot.capture"):
                try:
                    snapshot, snapshot_id = await self._capture_snapshot()
                    logger.debug(
                        "Snapshot captured",
                        elements=len(snapshot),
                        snapshot_id=snapshot_id,
                    )
                except BrowserSnapshotError as exc:
                    logger.error(
                        "Failed to capture snapshot", error=str(exc)
                    )
                    return RunResult(
                        success=False,
                        session_id=session.id,
                        goal=goal,
                        steps_taken=session.current_step,
                        final_message="Falha ao capturar estado da página",
                        error=f"BrowserSnapshotError: {exc}",
                    )

            # 2. Constrói estado estruturado para o modelo
            with timing("prompt.build"):
                try:
                    prompt_data = (
                        self.prompt_builder or build_prompt
                    )(snapshot, goal, session.history)
                except Exception as exc:
                    logger.error(
                        "Failed to build prompt", error=str(exc)
                    )
                    return RunResult(
                        success=False,
                        session_id=session.id,
                        goal=goal,
                        steps_taken=session.current_step,
                        final_message="Falha ao preparar entrada para o modelo",
                        error=f"PromptBuildError: {exc}",
                    )

            # 3. Chama modelo para decidir ação
            raw_response = None
            with timing("model.inference"):
                try:
                    raw_response = await self._call_model(prompt_data)
                    logger.debug(
                        "Model decision",
                        action=raw_response.type.value,
                        target_id=raw_response.target_id,
                    )
                except Exception as exc:
                    logger.error(
                        "Model inference failed", error=str(exc)
                    )
                    # Continua o loop para permitir retry via session
                    raw_response = None

            # 4. Converte resposta do modelo para Action (se ainda não for Action)
            action = raw_response
            if not isinstance(action, Action):
                # Se for ModelResponse ou dict, converte
                try:
                    action = (
                        self.response_parser or model_response_to_action
                    )(raw_response)
                except (ActionValidationError, ValidationError) as exc:
                    logger.warning(
                        "Invalid model response",
                        error=str(exc),
                        raw_response=str(raw_response)[:200] if raw_response else None,
                    )
                    # Usa ação de bloqueio como fallback
                    action = Action.blocked(
                        f"Resposta do modelo inválida: {exc}"
                    )

            # 5. Valida frescura da página (anti-TOCTOU)
            fresh = await self._is_action_fresh(action, snapshot)
            if not fresh:
                logger.warning(
                    "Stale target detected, restarting cycle",
                    action=action.to_dict(),
                    snapshot_id=snapshot_id,
                )
                # Pula a execução e tenta novamente com novo snapshot
                continue

            # 6. Executa ação
            result = None
            with timing("action.execution"):
                try:
                    executor = self._get_executor()
                    result = await executor.execute(action, snapshot)
                    logger.info(
                        "laya.cycle",
                        action=action.type.value,
                        latencia_execucao_ms=result.latencia_execucao_ms,
                        latencia_inferencia_ms=result.latencia_inferencia_ms,
                        latencia_snapshot_ms=result.latencia_snapshot_ms,
                        session_id=session.id,
                        snapshot_id=snapshot_id,
                        step=session.current_step + 1,
                        target_id=action.target_id,
                        tokens_completion=result.tokens_completion,
                        tokens_prompt=result.tokens_prompt,
                    )
                except Exception as exc:
                    logger.error(
                        "Action execution failed",
                        action=action.to_dict(),
                        error=str(exc),
                    )
                    result = ExecutionResult(
                        success=False,
                        action=action,
                        error=str(exc),
                    )

            # 7. Atualiza métricas e histórico
            step_duration_ms = (time.time() - step_start) * 1000
            session.add_step(
                action=action,
                result=result,
                snapshot_id=snapshot_id,
                duration_ms=step_duration_ms,
            )

            # 8. Verifica se deve continuar
            if result.success:
                if action.type in (ActionType.DONE, ActionType.BLOCKED):
                    logger.info(
                        "Agent finished",
                        success=action.type == ActionType.DONE,
                        reason=result.message,
                        session_id=session.id,
                        steps_taken=session.current_step,
                    )
                    return RunResult(
                        success=(action.type == ActionType.DONE),
                        session_id=session.id,
                        goal=goal,
                        steps_taken=session.current_step,
                        final_message=result.message
                        or (
                            "Meta alcançada"
                            if action.type == ActionType.DONE
                            else "Agente bloqueado"
                        ),
                        error=None
                        if action.type == ActionType.DONE
                        else result.error,
                        metrics=self._collect_metrics(session),
                        session_summary=session.to_dict(),
                    )

            # Se chegou aqui, continua o loop
            # (a sessão já foi atualizada em session.add_step)

        # Limite de passos atingido
        logger.warning(
            "Max steps exceeded",
            goal=goal,
            session_id=session.id,
            max_steps=max_steps,
        )
        return RunResult(
            success=False,
            session_id=session.id,
            goal=goal,
            steps_taken=max_steps,
            final_message=f"Limite de {max_steps} passos excedido",
            error="AgentMaxStepsExceededError",
            metrics=self._collect_metrics(session),
            session_summary=session.to_dict(),
        )

    # Métodos auxiliares (mantidos do original)
    async def _capture_snapshot(self) -> tuple[list[ElementSnapshot], str]:
        """Captura snapshot do DOM via browser session."""
        if not self.browser:
            raise AgentError("Browser session not set")
        elements = await self.browser.get_snapshot()
        snapshot_id = str(uuid.uuid4())
        return elements, snapshot_id

    async def _wait_for_stability(self, ms: int = 100):
        """Espera estabilidade básica da página."""
        if self.browser:
            await self.browser.wait(ms)

    async def _is_action_fresh(
        self,
        action: Action,
        previous: list[ElementSnapshot],
    ) -> bool:
        """Verifica a frescura da página antes de executar (anti-TOCTOU, §4.5).

        Refaz um snapshot barato e compara o bounding box do alvo. Retorna
        False se o elemento sumiu, ficou obstruído/invisível ou moveu mais
        que :data:`FRESHNESS_TOLERANCE_PX` desde a decisão do modelo.
        """
        if action.type not in (ActionType.CLICK, ActionType.TYPE_TEXT, ActionType.SELECT):
            return True

        old = find_element(action, previous)
        if old is None:
            # Sem alvo conhecido: o executor fará fail-fast com contexto
            return True

        try:
            current, _ = await self._capture_snapshot()
        except BrowserSnapshotError:
            # Sem snapshot novo, deixa o executor validar (melhor esforço)
            return True

        new = find_element(action, current)
        if new is None or not new.is_visible or new.is_obstructed:
            return False
        if new.state.get("disabled") or new.state.get("readonly"):
            return False

        for key in ("x", "y", "width", "height"):
            if abs(new.bbox.get(key, 0.0) - old.bbox.get(key, 0.0)) > FRESHNESS_TOLERANCE_PX:
                return False

        return True

    def _collect_metrics(self, session: SessionContext) -> dict[str, Any]:
        """Coleta métricas da sessão para resultado final."""
        return {
            "duration_ms": sum(s.duration_ms for s in session.steps),
            "steps": len(session.steps),
            "success_rate": (
                sum(1 for s in session.steps if s.result.success)
                / max(len(session.steps), 1)
            ),
            "counters": {
                "total_steps": len(session.steps),
                "successful_steps": sum(1 for s in session.steps if s.result.success),
                "failed_steps": sum(1 for s in session.steps if not s.result.success),
            },
            "gauges": {
                "avg_step_duration_ms": (
                    sum(s.duration_ms for s in session.steps)
                    / max(len(session.steps), 1)
                ),
            },
            "histograms": {
                "step_duration_ms": {
                    "count": len(session.steps),
                    "min": min((s.duration_ms for s in session.steps), default=0),
                    "max": max((s.duration_ms for s in session.steps), default=0),
                    "mean": (
                        sum(s.duration_ms for s in session.steps)
                        / max(len(session.steps), 1)
                    ),
                }
            },
        }

    def _get_or_create_session(
        self,
        goal: str,
        max_steps: int,
        session_id: str | None,
    ) -> SessionContext:
        """Recupera sessão existente ou cria nova."""
        if session_id:
            session = self.context_manager.get(session_id)
            if session is None:
                raise AgentError(f"Session {session_id} not found")
            return session
        return self.context_manager.create(goal, max_steps)