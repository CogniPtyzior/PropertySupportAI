"""
PropertySupport AI - app/config.py

Centralized configuration loaded from environment variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PropertySupport AI"
    app_env: str = "local"
    app_debug: bool = True
    app_version: str = "0.1.0"

    api_host: str = "127.0.0.1"
    api_port: int = 8001
    api_max_message_length: int = 4000
    include_debug_metadata: bool = False

    database_url: str = "sqlite:///./property_support.db"
    database_echo: bool = False
    database_timeout_seconds: int = 10

    safe_mode: bool = True
    write_ticket_events: bool = True
    dry_run: bool = False

    llm_provider: str = "ollama"
    llm_base_url: str | None = "http://localhost:11434"
    llm_api_key: str | None = None
    llm_model: str = "mistral-nemo:12b"
    llm_timeout_seconds: int = 90
    llm_max_retries: int = 1
    llm_temperature_classification: float = 0.0
    llm_temperature_extraction: float = 0.0
    llm_temperature_reasoning: float = 0.1
    llm_temperature_writing: float = 0.3

    request_timeout_seconds: int = 120
    min_classification_confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    duplicate_ticket_window_hours: int = 72
    max_recent_tickets: int = 20
    include_graph_path: bool = True

    langfuse_base_url: str | None = None
    langfuse_enabled: bool = True
    langfuse_host: str | None = "http://localhost:3001"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_environment: str = "local"
    langfuse_release: str = "0.1.0"

    log_level: str = "INFO"
    log_format: str = "human"
    log_workflow_state: bool = False

    test_database_url: str = "sqlite:///./property_support_test.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


settings = get_settings()
