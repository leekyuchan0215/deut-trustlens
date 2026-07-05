from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    use_mock: bool = True

    database_url: str = "postgresql+psycopg://trustlens:trustlens@localhost:5432/trustlens"

    openai_api_key: str = ""
    openai_chat_model: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    anthropic_api_key: str = ""
    claude_model: str = ""

    openrouter_api_key: str = ""
    openrouter_claude_model: str = ""

    gemini_api_key: str = ""
    gemini_model: str = ""

    tavily_api_key: str = ""

    judge_provider: str = ""
    judge_model: str = ""

    frontend_origin: str = "http://localhost:3000"

    provider_timeout_seconds: float = 45.0
    provider_max_retries: int = 2
    tavily_max_results_per_query: int = 5
    embedding_batch_size: int = 64
    chunk_max_chars: int = 1200


@lru_cache
def get_settings() -> Settings:
    return Settings()
