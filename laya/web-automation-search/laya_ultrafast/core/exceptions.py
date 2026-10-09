from __future__ import annotations


class LAYAError(Exception):
    """Base exception for all LAYA errors."""

    def __init__(self, message: str, *, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        ctx = f" | context: {self.context}" if self.context else ""
        return f"{self.__class__.__name__}: {self.message}{ctx}"


class ConfigurationError(LAYAError):
    """Erro de configuração inválida."""

    pass


class BrowserError(LAYAError):
    """Erro na camada do navegador."""

    pass


class BrowserConnectionError(BrowserError):
    """Falha ao conectar ao navegador via CDP."""

    pass


class BrowserTimeoutError(BrowserError):
    """Timeout em operação do navegador."""

    pass


class BrowserNavigationError(BrowserError):
    """Erro de navegação."""

    pass


class BrowserSnapshotError(BrowserError):
    """Erro ao capturar snapshot do DOM."""

    pass


class BrowserExecutionError(BrowserError):
    """Erro ao executar ação no navegador."""

    pass


class ModelError(LAYAError):
    """Erro no modelo de inferência."""

    pass


class ModelConnectionError(ModelError):
    """Falha ao conectar ao endpoint do modelo."""

    pass


class ModelTimeoutError(ModelError):
    """Timeout na inferência do modelo."""

    pass


class ModelResponseError(ModelError):
    """Resposta inválida do modelo."""

    pass


class ModelRateLimitError(ModelError):
    """Rate limit do modelo excedido."""

    pass


class ModelContextOverflowError(ModelError):
    """Contexto do modelo excedido (tokens)."""

    pass


class ValidationError(LAYAError):
    """Erro de validação de dados."""

    pass


class ActionValidationError(ValidationError):
    """Ação inválida retornada pelo modelo."""

    pass


class ElementNotFoundError(LAYAError):
    """Elemento não encontrado no snapshot."""

    pass


class ElementNotInteractableError(LAYAError):
    """Elemento encontrado mas não interagível (obstruído, invisível, etc.)."""

    pass


class ElementStaleError(LAYAError):
    """Elemento ficou stale (página mudou) antes da ação."""

    pass


class SessionError(LAYAError):
    """Erro de gerenciamento de sessão."""

    pass


class CheckpointError(SessionError):
    """Erro ao salvar/restaurar checkpoint."""

    pass


class SessionExpiredError(SessionError):
    """Sessão expirou ou não pode ser restaurada."""

    pass


class AgentError(LAYAError):
    """Erro no loop principal do agente."""

    pass


class AgentMaxStepsExceededError(AgentError):
    """Número máximo de passos excedido."""

    pass


class AgentBlockedError(AgentError):
    """Agente travado (BLOCKED retornado pelo modelo)."""

    pass


class AgentGoalNotAchievedError(AgentError):
    """Meta não alcançada dentro do limite de passos."""

    pass


class CircuitBreakerOpenError(LAYAError):
    """Circuit breaker está aberto."""

    pass


class SnapshotExtractionError(LAYAError):
    """Erro ao extrair/processar snapshot.js."""

    pass


class IncrementalSnapshotError(LAYAError):
    """Erro no diff de snapshots incrementais."""

    pass


# Mapeamento para retry logic
RETRYABLE_EXCEPTIONS = (
    BrowserConnectionError,
    BrowserTimeoutError,
    BrowserSnapshotError,
    ModelConnectionError,
    ModelTimeoutError,
    ModelRateLimitError,
    TimeoutError,
    ConnectionError,
    IOError,
)

NON_RETRYABLE_EXCEPTIONS = (
    ConfigurationError,
    ValidationError,
    ActionValidationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    ElementStaleError,
    CircuitBreakerOpenError,
    AgentMaxStepsExceededError,
    AgentBlockedError,
)


def is_retryable(error: Exception) -> bool:
    """Verifica se erro é retryable."""
    return isinstance(error, RETRYABLE_EXCEPTIONS)


def is_non_retryable(error: Exception) -> bool:
    """Verifica se erro NÃO é retryable."""
    return isinstance(error, NON_RETRYABLE_EXCEPTIONS)
