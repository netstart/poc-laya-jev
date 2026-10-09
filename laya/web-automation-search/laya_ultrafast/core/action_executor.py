from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog

from laya_ultrafast.core.exceptions import (
    BrowserExecutionError,
    ElementNotFoundError,
    ElementNotInteractableError,
    ElementStaleError,
)
from laya_ultrafast.utils.geometry import BoundingBox, Viewport, compute_element_visibility

if TYPE_CHECKING:
    from laya_ultrafast.utils.dom import ElementSnapshot

logger = structlog.get_logger(__name__)


class ActionType(StrEnum):
    """Operações suportadas pelo agente (§1 do plano)."""

    CLICK = "CLICK"
    TYPE_TEXT = "TYPE_TEXT"
    SELECT = "SELECT"
    SCROLL_UP = "SCROLL_UP"
    SCROLL_DOWN = "SCROLL_DOWN"
    WAIT = "WAIT"
    NAVIGATE = "NAVIGATE"
    GO_BACK = "GO_BACK"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class Action:
    """Ação a ser executada pelo agente."""

    type: ActionType
    target_id: str | None = None
    selector: str | None = None
    value: str | None = None  # texto para TYPE_TEXT, valor para SELECT
    direction: str | None = None  # para SCROLL
    amount: int | None = None  # pixels para SCROLL
    url: str | None = None  # para NAVIGATE
    wait_ms: int | None = None  # para WAIT

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "target_id": self.target_id,
            "selector": self.selector,
            "value": self.value,
            "direction": self.direction,
            "amount": self.amount,
            "url": self.url,
            "wait_ms": self.wait_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Action:
        return cls(
            type=ActionType(data["type"]),
            target_id=data.get("target_id"),
            selector=data.get("selector"),
            value=data.get("value"),
            direction=data.get("direction"),
            amount=data.get("amount"),
            url=data.get("url"),
            wait_ms=data.get("wait_ms"),
        )

    @classmethod
    def click(cls, target_id: str, selector: str) -> Action:
        return cls(type=ActionType.CLICK, target_id=target_id, selector=selector)

    @classmethod
    def type_text(cls, target_id: str, selector: str, text: str) -> Action:
        return cls(type=ActionType.TYPE_TEXT, target_id=target_id, selector=selector, value=text)

    @classmethod
    def select(cls, target_id: str, selector: str, value: str) -> Action:
        return cls(type=ActionType.SELECT, target_id=target_id, selector=selector, value=value)

    @classmethod
    def scroll(cls, direction: str, amount: int = 300) -> Action:
        return cls(
            type=ActionType.SCROLL_UP if direction == "up" else ActionType.SCROLL_DOWN,
            direction=direction,
            amount=amount,
        )

    @classmethod
    def wait(cls, ms: int = 1000) -> Action:
        return cls(type=ActionType.WAIT, wait_ms=ms)

    @classmethod
    def navigate(cls, url: str) -> Action:
        return cls(type=ActionType.NAVIGATE, url=url)

    @classmethod
    def go_back(cls) -> Action:
        return cls(type=ActionType.GO_BACK)

    @classmethod
    def done(cls) -> Action:
        return cls(type=ActionType.DONE)

    @classmethod
    def blocked(cls, reason: str = "") -> Action:
        return cls(type=ActionType.BLOCKED, value=reason)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Resultado da execução de uma ação."""

    success: bool
    action: Action
    message: str = ""
    error: str | None = None
    new_snapshot_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action.to_dict(),
            "message": self.message,
            "error": self.error,
            "new_snapshot_id": self.new_snapshot_id,
            "metadata": self.metadata,
        }


def find_element(
    action: Action,
    snapshot: list[ElementSnapshot],
) -> ElementSnapshot | None:
    """Localiza o alvo no snapshot.

    Ordem de resolução:
    1. ``target_id`` igual ao ``id`` estável gerado pelo ``snapshot.js``;
    2. ``target_id`` numérico → posição no resumo do prompt (``[0]``, ``[1]``…)
       ou ``index`` original do elemento;
    3. ``selector`` CSS.
    """
    target = action.target_id
    if target:
        for elem in snapshot:
            if elem.id == target:
                return elem
        if target.isdigit():
            idx = int(target)
            if 0 <= idx < len(snapshot):
                return snapshot[idx]
            for elem in snapshot:
                if elem.index == idx:
                    return elem
    if action.selector:
        for elem in snapshot:
            if elem.selector == action.selector:
                return elem
    return None


class ActionExecutor:
    """
    Executor robusto de ações no navegador.

    Responsabilidades:
    - Validar elemento antes de interagir
    - Verificar visibilidade, obstrução, estabilidade
    - Executar ação via CDP/Playwright
    - Verificar resultado (sucesso/falha)
    """

    def __init__(
        self,
        browser_session: Any,  # BrowserSession - import tardio para evitar circular
        viewport: Viewport,
        action_timeout_ms: int = 10000,
        verify_after_action: bool = True,
        stability_threshold_px: float = 2.0,
    ):
        self.browser = browser_session
        self.viewport = viewport
        self.action_timeout_ms = action_timeout_ms
        self.verify_after_action = verify_after_action
        self.stability_threshold = stability_threshold_px
        self._previous_boxes: list[BoundingBox] = []
        self._scroll_y: float = 0.0

    async def execute(self, action: Action, snapshot: list[ElementSnapshot]) -> ExecutionResult:
        """
        Executa uma ação baseada no snapshot atual.

        Args:
            action: Ação a executar
            snapshot: Lista de ElementSnapshot atuais

        Returns:
            ExecutionResult com sucesso/falha e metadados
        """
        logger.debug("Executing action", action=action.to_dict())

        try:
            if action.type == ActionType.CLICK:
                return await self._execute_click(action, snapshot)
            elif action.type == ActionType.TYPE_TEXT:
                return await self._execute_type_text(action, snapshot)
            elif action.type == ActionType.SELECT:
                return await self._execute_select(action, snapshot)
            elif action.type in (ActionType.SCROLL_UP, ActionType.SCROLL_DOWN):
                return await self._execute_scroll(action, snapshot)
            elif action.type == ActionType.WAIT:
                return await self._execute_wait(action)
            elif action.type == ActionType.NAVIGATE:
                return await self._execute_navigate(action)
            elif action.type == ActionType.GO_BACK:
                return await self._execute_go_back()
            elif action.type == ActionType.DONE:
                return ExecutionResult(success=True, action=action, message="Goal achieved")
            elif action.type == ActionType.BLOCKED:
                return ExecutionResult(
                    success=False,
                    action=action,
                    message=f"Blocked: {action.value}",
                    error="AGENT_BLOCKED",
                )
            else:
                return ExecutionResult(
                    success=False,
                    action=action,
                    error=f"Unknown action type: {action.type}",
                )
        except Exception as e:
            logger.error("Action execution failed", action=action.to_dict(), error=str(e))
            return ExecutionResult(
                success=False,
                action=action,
                error=str(e),
            )

    async def _execute_click(
        self, action: Action, snapshot: list[ElementSnapshot]
    ) -> ExecutionResult:
        element = self._find_element(action, snapshot)
        if not element:
            raise ElementNotFoundError(f"Element {action.target_id} not found in snapshot")

        # Validações pré-clique
        self._validate_element_for_click(element)

        # Verifica estabilidade de posição
        box = BoundingBox.from_dict(element.bbox)
        if not self._is_position_stable(box):
            raise ElementStaleError(f"Element {action.target_id} position unstable")

        # Executa clique via CDP
        center_x = box.center_x
        center_y = box.center_y

        await self.browser.click_at(center_x, center_y)

        # Verificação pós-ação
        if self.verify_after_action:
            await self._wait_for_stability()

        return ExecutionResult(
            success=True,
            action=action,
            message=f"Clicked element {action.target_id} ({element.label})",
            metadata={"click_x": center_x, "click_y": center_y},
        )

    async def _execute_type_text(
        self, action: Action, snapshot: list[ElementSnapshot]
    ) -> ExecutionResult:
        if not action.value:
            raise BrowserExecutionError("TYPE_TEXT requires value (text to type)")

        element = self._find_element(action, snapshot)
        if not element:
            raise ElementNotFoundError(f"Element {action.target_id} not found in snapshot")

        # Validações
        if not element.is_editable:
            raise ElementNotInteractableError(f"Element {action.target_id} is not editable")

        if element.state.get("disabled") or element.state.get("readonly"):
            raise ElementNotInteractableError(f"Element {action.target_id} is disabled or readonly")

        # Foca no elemento primeiro
        selector = action.selector or element.selector
        await self.browser.focus_element(selector)

        # Digita o texto
        await self.browser.type_text(selector, action.value)

        # Verificação
        if self.verify_after_action:
            actual_value = await self.browser.get_element_value(selector)
            if actual_value != action.value:
                logger.warning(
                    "Type verification failed", expected=action.value, actual=actual_value
                )

        return ExecutionResult(
            success=True,
            action=action,
            message=f"Typed text into {action.target_id} ({element.label})",
            metadata={"text_length": len(action.value)},
        )

    async def _execute_select(
        self, action: Action, snapshot: list[ElementSnapshot]
    ) -> ExecutionResult:
        if not action.value:
            raise BrowserExecutionError("SELECT requires value (option to select)")

        element = self._find_element(action, snapshot)
        if not element:
            raise ElementNotFoundError(f"Element {action.target_id} not found in snapshot")

        if element.tag != "select":
            raise ElementNotInteractableError(f"Element {action.target_id} is not a SELECT")

        await self.browser.select_option(action.selector or element.selector, action.value)

        return ExecutionResult(
            success=True,
            action=action,
            message=f"Selected '{action.value}' in {action.target_id} ({element.label})",
        )

    async def _execute_scroll(
        self,
        action: Action,
        snapshot: list[ElementSnapshot],
    ) -> ExecutionResult:
        direction = action.direction or "down"
        amount = action.amount or 300

        # Prefere scrollIntoView do alvo (§4.6); quantitativo como fallback
        element = self._find_element(action, snapshot) if action.target_id else None
        if element is not None and element.selector:
            try:
                await self.browser.scroll_to_element(element.selector)
            except Exception as exc:
                logger.debug("scrollIntoView failed, using quantitative scroll", error=str(exc))
                await self.browser.scroll(direction, amount)
        else:
            await self.browser.scroll(direction, amount)

        # Acompanha o offset de rolagem (informativo: bbox é relativo ao viewport)
        self._scroll_y = max(0.0, self._scroll_y + (amount if direction == "down" else -amount))

        await self._wait_for_stability()

        return ExecutionResult(
            success=True,
            action=action,
            message=f"Scrolled {direction} by {amount}px",
            metadata={"scroll_y": self._scroll_y},
        )

    async def _execute_wait(self, action: Action) -> ExecutionResult:
        wait_ms = action.wait_ms or 1000
        await self.browser.wait(wait_ms)
        return ExecutionResult(
            success=True,
            action=action,
            message=f"Waited {wait_ms}ms",
        )

    async def _execute_navigate(self, action: Action) -> ExecutionResult:
        if not action.url:
            raise BrowserExecutionError("NAVIGATE requires url")

        await self.browser.navigate(action.url)
        await self._wait_for_stability()

        return ExecutionResult(
            success=True,
            action=action,
            message=f"Navigated to {action.url}",
        )

    async def _execute_go_back(self) -> ExecutionResult:
        await self.browser.go_back()
        await self._wait_for_stability()
        return ExecutionResult(
            success=True,
            action=Action.go_back(),
            message="Navigated back",
        )

    def _find_element(
        self, action: Action, snapshot: list[ElementSnapshot]
    ) -> ElementSnapshot | None:
        """Atalho de instância para :func:`find_element`."""
        return find_element(action, snapshot)

    def _validate_element_for_click(self, element: ElementSnapshot):
        """Validações obrigatórias antes de clicar."""
        if not element.is_visible:
            raise ElementNotInteractableError(f"Element {element.id} is not visible")

        if element.is_obstructed:
            raise ElementNotInteractableError(f"Element {element.id} is obstructed")

        if element.state.get("disabled"):
            raise ElementNotInteractableError(f"Element {element.id} is disabled")

        # Verifica se está no viewport
        box = BoundingBox.from_dict(element.bbox)
        visible, ratio = compute_element_visibility(box, self.viewport)
        if not visible:
            raise ElementNotInteractableError(
                f"Element {element.id} not in viewport (visible ratio: {ratio:.2f})"
            )

        # Verifica tamanho mínimo
        if box.width < 1 or box.height < 1:
            raise ElementNotInteractableError(f"Element {element.id} has zero size")

    def _is_position_stable(self, box: BoundingBox) -> bool:
        """Verifica se posição não mudou significativamente."""
        if not self._previous_boxes:
            self._previous_boxes.append(box)
            return True

        last_box = self._previous_boxes[0]
        distance = box.distance_to(last_box)

        self._previous_boxes.insert(0, box)
        if len(self._previous_boxes) > 10:
            self._previous_boxes.pop()

        return distance <= self.stability_threshold

    async def _wait_for_stability(self, max_wait_ms: int = 2000):
        """Aguarda estabilidade da página (network idle, sem mutações DOM)."""
        try:
            await self.browser.wait_for_stability(max_wait_ms)
        except Exception as e:
            logger.debug("Stability wait failed", error=str(e))

    def update_viewport(self, viewport: Viewport):
        self.viewport = viewport

    def clear_history(self):
        self._previous_boxes.clear()
