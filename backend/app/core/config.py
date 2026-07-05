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


@lru_cache
def get_settings() -> Settings:
    return Settings()
