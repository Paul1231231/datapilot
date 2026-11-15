from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DataPilot"
    app_env: str = "development"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    database_url: str
    database_readonly_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",    
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()