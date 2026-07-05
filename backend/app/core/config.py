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
    openrouter_gemini_model: str = ""

    gemini_api_key: str = ""
    gemini_model: str = ""

    tavily_api_key: str = ""

    judge_provider: str = ""
    judge_model: str = ""

    frontend_origin: str = "http://localhost:3000"

    provider_timeout_seconds: float = 45.0
    provider_max_retries: int = 2
    answer_max_tokens: int = 1000
    tavily_max_results_per_query: int = 5
    embedding_batch_size: int = 64
    chunk_max_chars: int = 1200

    # Demo / presentation: fewer LLM rounds, lighter web search, parallel Tavily.
    pipeline_fast_mode: bool = False
    fast_mode_max_claims: int = 8
    fast_mode_max_web_claims: int = 4
    fast_mode_tavily_max_queries: int = 4
    fast_mode_hybrid_top_k: int = 3

    # Trust Score component weights (must sum to 1.0)
    trust_weight_evidence: float = 0.28
    trust_weight_source: float = 0.12
    trust_weight_consensus: float = 0.28
    trust_weight_logic: float = 0.22
    trust_weight_freshness: float = 0.10

    # Presentation: AI 합의·논리 중심, 근거 부족·경미 Risk에 덜 엄격
    trust_score_generous_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
