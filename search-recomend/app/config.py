import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    APP_NAME: str = "busca-que-entende"
    PORT: int = 4111
    HOST: str = "127.0.0.1"
    CATALOGO_PATH: str = os.path.join(os.path.dirname(__file__), "..", "data", "catalogo.json")
    MODEL_CHECKPOINT: str = "convaiinnovations/laya-multilingual"
    CACHE_DIR: str = os.path.join(os.path.dirname(__file__), "..", "data-runtime", "cache")
    CACHE_TTL_SECONDS: int = 30 * 60
    CACHE_MAX_ITEMS: int = 500
    DEBOUNCE_MS: int = 550
    MODEL_DEVICE: str = "cpu"
    BATCH_SIZE: int = 24
    LOGS_DIR: str = os.path.join(os.path.dirname(__file__), "..", "data-runtime", "logs")


settings = Settings()
