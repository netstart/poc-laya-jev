"""LAYA UltraFast — agente local de automação web baseado em DOM estruturado.

O pacote expõe uma API pública enxuta; importe os submódulos diretamente
quando precisar de controle fino::

    from laya_ultrafast.agent import LayaAgent
    from laya_ultrafast.browser import BrowserSession, connect
    from laya_ultrafast.config.settings import LAYAConfig, get_config
    from laya_ultrafast.core import LayaEngine, RunResult
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - apenas para o type checker
    from laya_ultrafast.agent import LayaAgent
    from laya_ultrafast.browser import BrowserSession
    from laya_ultrafast.config.settings import LAYAConfig
    from laya_ultrafast.core.laya_engine import LayaEngine, RunResult

__version__ = "0.1.0"

#: Reexports lazy para evitar imports circulares e custo de import inicial.
_LAZY_EXPORTS: dict[str, str] = {
    "LayaAgent": "laya_ultrafast.agent",
    "BrowserSession": "laya_ultrafast.browser",
    "LAYAConfig": "laya_ultrafast.config.settings",
    "LayaEngine": "laya_ultrafast.core.laya_engine",
    "RunResult": "laya_ultrafast.core.laya_engine",
}

__all__ = [
    "BrowserSession",
    "LAYAConfig",
    "LayaAgent",
    "LayaEngine",
    "RunResult",
    "__version__",
]


def __getattr__(name: str) -> Any:
    """Resolve reexports de forma preguiçosa (PEP 562)."""
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value
