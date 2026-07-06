"""Centralized application settings, loaded once from environment/.env."""
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Populate process env from .env for any third-party client that reads env
# vars directly (e.g. TavilySearch, QdrantClient) rather than via Settings.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    log_level: str = "INFO"
    environment: str = "development"

    # --- API security ---
    api_keys: Optional[str] = None  # comma-separated list of accepted API keys
    cors_allow_origins: str = "http://localhost:5173"  # comma-separated list
    rate_limit_per_minute: int = 30

    # --- LLM providers ---
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    ollama_host: str = "localhost:11434"

    # --- Memory / checkpointing ---
    redis_url: Optional[str] = None

    # --- Vector store ---
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

    # --- Tools ---
    tavily_api_key: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None

    @property
    def api_key_list(self) -> List[str]:
        if not self.api_keys:
            return []
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
