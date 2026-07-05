from app.core.config import get_settings
from app.services.llm.base import LLMClient, ProviderError
from app.services.llm.claude_client import ClaudeClient
from app.services.llm.gemini_client import GeminiClient
from app.services.llm.gpt_client import GPTClient
from app.services.llm.openrouter_client import OpenRouterClient

_BUILDERS = {
    "gpt": GPTClient,
    "claude": ClaudeClient,
    "gemini": GeminiClient,
    "openrouter": OpenRouterClient,
}


def get_client(provider: str) -> LLMClient:
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise ProviderError(provider, f"알 수 없는 Provider입니다: {provider}")
    return builder()


def get_judge_client() -> tuple[LLMClient, str]:
    """Resolve the Judge client from JUDGE_PROVIDER/JUDGE_MODEL, falling back
    to the first provider with a usable key (gpt -> claude -> gemini).

    JUDGE_MODEL, when set, overrides the resolved client's model_name so the
    Judge can run a stronger/different model than a provider's own
    independent-answer model (e.g. JUDGE_PROVIDER=openrouter,
    JUDGE_MODEL=anthropic/claude-opus-4-8 while OPENROUTER_CLAUDE_MODEL is
    used for Claude's own answer).
    """
    settings = get_settings()
    candidates = [settings.judge_provider] if settings.judge_provider else []
    candidates += ["gpt", "claude", "gemini"]

    last_error: Exception | None = None
    seen = set()
    for provider in candidates:
        if not provider or provider in seen:
            continue
        seen.add(provider)
        try:
            client = get_client(provider)
            if settings.judge_model:
                client.model_name = settings.judge_model
            return client, "configured" if provider == settings.judge_provider else "fallback"
        except ProviderError as exc:
            last_error = exc
            continue
    raise ProviderError("judge", f"사용 가능한 Judge Provider가 없습니다: {last_error}")
