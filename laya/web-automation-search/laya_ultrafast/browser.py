from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import structlog
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import CDPSession, Page, async_playwright
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from laya_ultrafast.config.settings import LAYAConfig, get_config
from laya_ultrafast.core.exceptions import (
    BrowserConnectionError,
    BrowserExecutionError,
    BrowserNavigationError,
    BrowserSnapshotError,
    BrowserTimeoutError,
    CircuitBreakerOpenError,
)
from laya_ultrafast.utils.dom import ElementSnapshot
from laya_ultrafast.utils.geometry import Viewport
from laya_ultrafast.utils.retry import CircuitBreaker, retry_with_circuit_breaker

logger = structlog.get_logger(__name__)


class BrowserSession:
    """
    Camada de conexão do navegador via Playwright + CDP.

    Responsabilidades:
    - Conexão persistente via CDP
    - Captura de snapshots do DOM
    - Execução atômica de ações
    - Reconexão automática com backoff
    """

    def __init__(
        self,
        config: LAYAConfig,
        snapshot_script_path: Path | str | None = None,
        cdp_url: str | None = None,
    ):
        self.config = config
        self._cdp_url = cdp_url or config.browser_cdp_url
        self._playwright = None
        self._browser: PlaywrightBrowser | None = None
        self._page: Page | None = None
        self._cdp_session: CDPSession | None = None
        self._snapshot_script: str | None = None
        self._viewport: Viewport | None = None
        self._circuit_breaker: CircuitBreaker | None = None

        if snapshot_script_path is None:
            snapshot_script_path = Path(__file__).parent / "snapshot.js"

        self._load_snapshot_script(snapshot_script_path)

        self._circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout_ms=config.circuit_breaker_timeout_ms,
            expected_exception=(BrowserConnectionError, BrowserTimeoutError),
        )

    def _load_snapshot_script(self, script_path: Path | str):
        """Carrega script de snapshot do arquivo."""
        path = Path(script_path)
        if path.exists():
            self._snapshot_script = path.read_text(encoding="utf-8")
        else:
            logger.warning("Snapshot script not found, using inline", path=str(path))
            self._snapshot_script = self._get_default_snapshot_script()

    def _get_default_snapshot_script(self) -> str:
        """Script de fallback inline."""
        return """
        (() => {
            const elements = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role]'));
            return elements.map((el, i) => {
                const rect = el.getBoundingClientRect();
                return {
                    id: 'el-' + i,
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    label: el.getAttribute('aria-label') || el.textContent?.trim() || '',
                    selector: '#' + (el.id || 'el-' + i),
                    bbox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height, top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left },
                    attrs: {},
                    state: {},
                    is_visible: rect.width > 1 && rect.height > 1,
                    is_obstructed: false,
                    is_interactive: ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName),
                    is_editable: ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName),
                };
            });
        })();
        """

    async def connect(self, url: str | None = None) -> None:
        """
        Conecta ao navegador via CDP.

        Args:
            url: URL opcional para navegar após conexão
        """

        async def _connect():
            if self._playwright is None:
                self._playwright = await async_playwright().start()

            if self._browser is None:
                if self._cdp_url.startswith("http://") or self._cdp_url.startswith("ws://"):
                    # Conexão via CDP
                    cdp_url = self._cdp_url.replace("http://", "ws://").replace(
                        "https://", "wss://"
                    )
                    self._browser = await self._playwright.chromium.connect_over_cdp(cdp_url)
                else:
                    # Lança navegador local
                    self._browser = await self._playwright.chromium.launch(
                        headless=self.config.browser_headless,
                        args=[
                            f"--window-size={self.config.browser_viewport_width},{self.config.browser_viewport_height}",
                            *(
                                []
                                if self.config.enable_sandbox
                                else ["--no-sandbox", "--disable-setuid-sandbox"]
                            ),
                        ],
                    )

                self._page = await self._browser.new_page(
                    viewport={
                        "width": self.config.browser_viewport_width,
                        "height": self.config.browser_viewport_height,
                    }
                )

                self._viewport = Viewport(
                    width=self.config.browser_viewport_width,
                    height=self.config.browser_viewport_height,
                    scroll_x=0,
                    scroll_y=0,
                )

            if url:
                await self.navigate(url)

            logger.info("Browser connected", url=url or "about:blank")

        try:
            await retry_with_circuit_breaker(
                _connect,
                policy=self._get_retry_policy(),
                circuit_breaker=self._circuit_breaker,
            )
        except Exception as e:
            if isinstance(e, CircuitBreakerOpenError):
                raise BrowserConnectionError(f"Circuit breaker open for browser: {e}") from e
            raise BrowserConnectionError(f"Failed to connect to browser: {e}") from e

    def _get_retry_policy(self):
        """Política de retry padrão para operações de navegador."""
        from laya_ultrafast.utils.retry import BROWSER_RETRY

        return BROWSER_RETRY

    @property
    def page(self) -> Page:
        if self._page is None:
            raise BrowserConnectionError("Browser not connected. Call connect() first.")
        return self._page

    @property
    def is_connected(self) -> bool:
        return self._page is not None and self._browser is not None

    async def disconnect(self) -> None:
        """Desconecta do navegador."""
        try:
            if self._page:
                await self._page.close()
                self._page = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            self._viewport = None
            logger.info("Browser disconnected")
        except Exception as e:
            logger.warning("Error disconnecting browser", error=str(e))

    def _blocked_domains(self) -> tuple[str, ...]:
        """Lista normalizada de domínios bloqueados (``LAYA_BLOCKED_DOMAINS``)."""
        raw = self.config.blocked_domains or ""
        return tuple(d.strip().lower() for d in raw.split(",") if d.strip())

    def _assert_url_allowed(self, url: str) -> None:
        """Aplica ``LAYA_BLOCKED_DOMAINS`` antes de navegar (fail-fast, §5)."""
        blocked = self._blocked_domains()
        if not blocked:
            return
        host = (urlparse(url).hostname or "").lower()
        for domain in blocked:
            if host == domain or host.endswith("." + domain):
                raise BrowserNavigationError(
                    f"Navegação bloqueada: '{host}' está em LAYA_BLOCKED_DOMAINS"
                )

    async def navigate(self, url: str, timeout_ms: int | None = None) -> None:
        """Navega para URL especificada."""
        self._assert_url_allowed(url)
        timeout = timeout_ms or self.config.browser_timeout_ms

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=10),
            retry=retry_if_exception_type((BrowserTimeoutError, BrowserNavigationError)),
            reraise=True,
        )
        async def _navigate():
            try:
                await self.page.goto(url, timeout=timeout, wait_until="networkidle")
                await self.wait_for_stability(5000)
                logger.info("Navigation complete", url=url)
            except Exception as e:
                if "Timeout" in str(e):
                    raise BrowserTimeoutError(f"Navigation timeout for {url}: {e}") from e
                raise BrowserNavigationError(f"Navigation failed to {url}: {e}") from e

        await _navigate()

    async def go_back(self) -> None:
        """Navega para a página anterior."""
        try:
            await self.page.go_back()
            await self.wait_for_stability(3000)
            logger.info("Navigation: went back")
        except Exception as e:
            raise BrowserNavigationError(f"Failed to go back: {e}") from e

    async def get_snapshot(self, use_incremental: bool = True) -> list[dict[str, Any]]:
        """
        Captura snapshot do DOM.

        Args:
            use_incremental: Se True, tenta usar diff incremental
        """
        snapshot_id = f"snap-{id(self.page)}"

        if self._snapshot_script is None:
            raise BrowserSnapshotError("Snapshot script not loaded")

        try:
            result = await self.page.evaluate(self._snapshot_script)
            if result is None:
                result = []
            if not isinstance(result, list):
                result = [result]

            logger.debug("Snapshot captured", elements=len(result), snapshot_id=snapshot_id)
            return result
        except Exception as e:
            raise BrowserSnapshotError(f"Failed to capture snapshot: {e}") from e

    async def click_at(self, x: float, y: float) -> None:
        """Clica em coordenadas específicas."""
        try:
            await self.page.mouse.click(x, y)
            logger.debug("Clicked at", x=x, y=y)
        except Exception as e:
            raise BrowserExecutionError(f"Failed to click at ({x}, {y}): {e}") from e

    async def click_element(self, selector: str) -> None:
        """Clica em elemento pelo seletor."""
        try:
            element = await self.page.wait_for_selector(
                selector, state="visible", timeout=self.config.action_timeout_ms
            )
            if element is None:
                raise BrowserExecutionError(f"Element not found or not visible: {selector}")
            await element.click()
            logger.debug("Clicked element", selector=selector)
        except Exception as e:
            raise BrowserExecutionError(f"Failed to click element {selector}: {e}") from e

    async def type_text(self, selector: str, text: str) -> None:
        """Digita texto em elemento."""
        try:
            element = await self.page.wait_for_selector(
                selector, state="visible", timeout=self.config.action_timeout_ms
            )
            if element is None:
                raise BrowserExecutionError(f"Element not found or not visible: {selector}")
            await element.fill(text)
            logger.debug("Typed text", selector=selector, length=len(text))
        except Exception as e:
            raise BrowserExecutionError(f"Failed to type in {selector}: {e}") from e

    async def focus_element(self, selector: str) -> None:
        """Foca elemento."""
        try:
            element = await self.page.wait_for_selector(
                selector, state="attached", timeout=self.config.action_timeout_ms
            )
            if element is None:
                raise BrowserExecutionError(f"Element not found: {selector}")
            await element.focus()
            logger.debug("Focused element", selector=selector)
        except Exception as e:
            raise BrowserExecutionError(f"Failed to focus {selector}: {e}") from e

    async def select_option(self, selector: str, value: str) -> None:
        """Seleciona opção em select."""
        try:
            element = await self.page.wait_for_selector(
                selector, state="visible", timeout=self.config.action_timeout_ms
            )
            if element is None:
                raise BrowserExecutionError(f"Element not found: {selector}")
            await element.select_option(value=value)
            logger.debug("Selected option", selector=selector, value=value)
        except Exception as e:
            raise BrowserExecutionError(f"Failed to select option in {selector}: {e}") from e

    async def scroll(self, direction: str, amount: int) -> None:
        """Faz scroll na página."""
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            else:
                raise BrowserExecutionError(f"Invalid scroll direction: {direction}")

            if self._viewport:
                if direction == "down":
                    self._viewport.scroll_y += amount
                else:
                    self._viewport.scroll_y = max(0, self._viewport.scroll_y - amount)

            logger.debug("Scrolled", direction=direction, amount=amount)
        except Exception as e:
            raise BrowserExecutionError(f"Failed to scroll {direction} by {amount}: {e}") from e

    async def scroll_to_element(self, selector: str) -> None:
        """Faz scroll até elemento."""
        try:
            await self.page.wait_for_selector(
                selector, state="attached", timeout=self.config.action_timeout_ms
            )
            await self.page.evaluate(f"""() => {{
                const el = document.querySelector('{selector}');
                if (el) el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
            }}""")
        except Exception as e:
            raise BrowserExecutionError(f"Failed to scroll to {selector}: {e}") from e

    async def wait(self, ms: int) -> None:
        """Aguarda ms milissegundos."""
        await self.page.wait_for_timeout(ms)
        logger.debug("Waited", ms=ms)

    async def wait_for_stability(self, max_wait_ms: int = 5000) -> None:
        """Aguarda estabilidade da página (network idle, sem mutações)."""
        # Best effort: nem toda página atinge "networkidle"
        with suppress(Exception):
            await self.page.wait_for_load_state("networkidle", timeout=max_wait_ms)

    async def get_element_value(self, selector: str) -> str | None:
        """Obtém valor de elemento."""
        try:
            return await self.page.get_attribute(selector, "value")
        except Exception:
            return None

    async def evaluate(self, expression: str, arg: Any | None = None) -> Any:
        """Avalia expressão JavaScript na página."""
        try:
            return await self.page.evaluate(expression, arg)
        except Exception as e:
            raise BrowserExecutionError(f"Evaluate failed: {expression}: {e}") from e

    def get_viewport(self) -> Viewport:
        """Retorna viewport atual."""
        if self._viewport is None:
            self._viewport = Viewport(
                width=self.config.browser_viewport_width,
                height=self.config.browser_viewport_height,
            )
        return self._viewport

    async def screenshot(
        self, output_path: str | Path | None = None, full_page: bool = False
    ) -> bytes:
        """Tira screenshot da página ou viewport."""
        try:
            return await self.page.screenshot(
                path=str(output_path) if output_path else None,
                full_page=full_page,
            )
        except Exception as e:
            raise BrowserExecutionError(f"Failed to take screenshot: {e}") from e

    async def reload(self) -> None:
        """Recarrega a página."""
        await self.page.reload()
        await self.wait_for_stability(3000)

    async def get_current_url(self) -> str:
        """Retorna URL atual."""
        return self.page.url

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False

    async def snapshot(self) -> list[ElementSnapshot]:
        """Captura o snapshot do DOM como objetos tipados (§4.2 do plano)."""
        raw = await self.get_snapshot()
        return [ElementSnapshot.from_dict(item) for item in raw]

    async def close(self) -> None:
        """Encerra a sessão (alias de :meth:`disconnect`, contrato da §4.2)."""
        await self.disconnect()


async def connect(
    cdp_url: str | None = None,
    config: LAYAConfig | None = None,
) -> BrowserSession:
    """Cria e conecta uma :class:`BrowserSession` (``connect(cdp_url?)``, §4.2).

    Args:
        cdp_url: URL do DevTools Protocol (usa ``LAYA_BROWSER_CDP_URL`` se None).
        config: Configuração LAYA (usa a singleton se None).

    Returns:
        Sessão já conectada e pronta para uso.
    """
    cfg = config if config is not None else get_config()
    session = BrowserSession(config=cfg, cdp_url=cdp_url)
    await session.connect()
    return session
