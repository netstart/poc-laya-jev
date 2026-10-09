"""Configuração do LAYA UltraFast.

Este módulo define apenas os tipos de domínio (literais) usados pela
configuração. A implementação concreta fica em
:mod:`laya_ultrafast.config.settings`.
"""

from __future__ import annotations

from typing import Literal

#: Provedores de modelo local suportados (ADR-003).
ModelProvider = Literal["ollama", "openai", "local"]

#: Formatos de log estruturado.
LogFormat = Literal["text", "json"]

__all__ = ["LogFormat", "ModelProvider"]
