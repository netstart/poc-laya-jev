"""Configuração do LAYA UltraFast baseada em ``pydantic-settings``.

Todos os campos são lidos do ambiente com o prefixo ``LAYA_`` (e, quando
existente, do arquivo ``.env`` na raiz do projeto). Consulte o
``.env.example`` para a lista completa de variáveis.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from laya_ultrafast.config import LogFormat, ModelProvider

#: Teto de contexto de LLM aceito (§5 do plano).
MAX_NUM_CTX = 131072


class LAYAConfig(BaseSettings):
    """Configuração do agente LAYA.

    A validação acontece na instanciamento (fail-fast, §3.1 do plano):
    qualquer valor fora dos limites levanta ``pydantic.ValidationError``.
    """

    model_config = SettingsConfigDict(
        env_prefix="laya_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        # Os campos do LAYA usam o prefixo ``model_`` por convenção do plano;
        # sem isso o Pydantic emite avisos de conflito com o namespace padrão.
        protected_namespaces=(),
    )

    # --- Modelo Local ---
    model_provider: ModelProvider = Field(
        default="ollama", description="Provedor do modelo local para inferência"
    )
    model_name: str = Field(
        default="llama3.1:8b-instruct-q4_K_M",
        description="Nome do modelo ou caminho para o modelo GGUF",
    )
    model_endpoint: str = Field(
        default="http://localhost:11434/v1",
        description="URL do endpoint do provedor do modelo (OpenAI-compatível)",
    )
    model_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperatura para inferência (0.0 = determinístico)",
    )
    model_max_tokens: int = Field(
        default=512, gt=0, le=16384, description="Máximo de tokens de saída permitidos"
    )
    model_num_ctx: int = Field(
        default=4096,
        gt=0,
        le=131072,
        description="Contexto máximo (window) para modelos compatíveis com sliding window",
    )
    model_seed: int = Field(
        default=42,
        ge=0,
        le=2**31 - 1,
        description="Seed fixa para decisões reprodutíveis (§3.1 do plano)",
    )
    model_timeout_ms: int = Field(
        default=60000, ge=1000, le=300000, description="Timeout para chamadas do modelo em ms"
    )
    model_retry_max_attempts: int = Field(
        default=3, ge=1, le=5, description="Máximo de tentativas de retry para chamadas de modelo"
    )

    # --- Navegador ---
    browser_cdp_url: str = Field(
        default="http://localhost:9222", description="URL do Chrome DevTools Protocol"
    )
    browser_headless: bool = Field(
        default=True, description="Executar o navegador em modo headless"
    )
    browser_viewport_width: int = Field(
        default=1280, gt=0, description="Largura da viewport para screenshots e extração"
    )
    browser_viewport_height: int = Field(
        default=720, gt=0, description="Altura da viewport para screenshots e extração"
    )
    browser_timeout_ms: int = Field(
        default=30000, ge=5000, le=120000, description="Timeout para operações do navegador em ms"
    )
    browser_user_agent: str = Field(
        default="LAYA-Bot/0.1.0 (+https://github.com/your-org/laya-ultrafast)",
        description="User-Agent identificável do agente (§3.1 do plano)",
    )

    # --- Engine ---
    max_steps: int = Field(
        default=25, ge=1, le=100, description="Máximo de etapas por execução de agente"
    )
    global_timeout_s: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Aborta run() e emite RunResult parcial ao exceder (§4.5)",
    )
    history_max_steps: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Passos de histórico mantidos no prompt (§4.5)",
    )
    snapshot_interval_ms: int = Field(
        default=100, ge=10, le=1000, description="Intervalo entre snapshots em ms"
    )
    action_timeout_ms: int = Field(
        default=10000,
        ge=1000,
        le=60000,
        description="Timeout individual para ações (click, type, etc.)",
    )
    enable_incremental_snapshot: bool = Field(
        default=True, description="Usar snapshots incrementais (diff) em vez de full snapshots"
    )
    checkpoint_interval_steps: int = Field(
        default=5, ge=1, le=50, description="Salvar checkpoint a cada N passos"
    )
    enable_resume: bool = Field(
        default=True, description="Permitir retomar execuções interrompidas"
    )

    # --- Performance ---
    inference_pool_size: int = Field(
        default=2, ge=1, le=8, description="Número de workers paralelos para inferência"
    )
    geometry_batch_size: int = Field(
        default=50, ge=1, le=200, description="Batch para validações geométricas"
    )
    metrics_enabled: bool = Field(default=True, description="Coletar métricas de performance")
    enable_tracing: bool = Field(default=False, description="Habilitar OpenTelemetry tracing")

    # --- Logging ---
    log_level: str = Field(
        default="INFO", description="Nível de log (DEBUG, INFO, WARN, ERROR, CRITICAL)"
    )
    log_format: LogFormat = Field(default="json", description="Formato de log (text ou json)")
    debug: bool = Field(
        default=False, description="Modo debug (maiores logs, snapshots adicionais)"
    )

    # --- Retry / Resiliência ---
    retry_max_attempts: int = Field(
        default=3, ge=1, le=5, description="Tentativas de retry para operações falhadas"
    )
    retry_backoff_base_ms: int = Field(
        default=1000, ge=100, le=10000, description="Backoff base para retry exponencial em ms"
    )
    retry_backoff_max_ms: int = Field(
        default=10000, ge=1000, le=60000, description="Backoff máximo para retry exponencial em ms"
    )
    circuit_breaker_threshold: int = Field(
        default=5, ge=3, le=10, description="Número de falhas para acionar circuit breaker"
    )
    circuit_breaker_timeout_ms: int = Field(
        default=30000,
        ge=10000,
        le=300000,
        description="Timeout para tentar acionar novamente após circuit breaker em ms",
    )

    # --- Segurança ---
    enable_sandbox: bool = Field(
        default=False, description="Usar sandbox restrito do navegador (flags adicionais)"
    )
    blocked_domains: str = Field(
        default="", description="Lista de domínios separados por vírgula para bloquear o agente"
    )

    @model_validator(mode="after")
    def validate_config(self) -> LAYAConfig:
        if not self.model_endpoint:
            raise ValueError(
                "model_endpoint deve ser configurado para provedores OpenAI-compatíveis"
            )

        if self.enable_sandbox and self.browser_headless:
            raise ValueError("sandbox no navegador não é compatível com headless")

        if self.model_num_ctx > MAX_NUM_CTX:
            raise ValueError(f"model_num_ctx não pode exceder {MAX_NUM_CTX}")

        if self.retry_backoff_max_ms < self.retry_backoff_base_ms:
            raise ValueError("retry_backoff_max_ms deve ser >= retry_backoff_base_ms")

        if not self.model_name:
            raise ValueError("model_name não pode ser vazio")

        return self

    @classmethod
    def get_model_endpoint(cls, provider: ModelProvider | None = None) -> str:
        """Retornar endpoint base para um provedor (com fallback)"""
        if provider is None:
            provider = cls().model_provider

        defaults = {
            "ollama": "http://localhost:11434/v1",
            "openai": "http://localhost:8000/v1",
            "local": "http://localhost:8080",
        }
        return cls().model_endpoint or defaults.get(provider, defaults["ollama"])


@lru_cache(maxsize=1)
def get_config() -> LAYAConfig:
    """Retorna a instância única (cacheada) da configuração LAYA.

    Em testes, chame ``get_config.cache_clear()`` após alterar variáveis de
    ambiente para forçar a recarga.
    """
    return LAYAConfig()


__all__ = ["MAX_NUM_CTX", "LAYAConfig", "get_config"]
