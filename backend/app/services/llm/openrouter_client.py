"""Generic OpenRouter chat client. Used directly when JUDGE_PROVIDER=openrouter
(so the Judge can run a different/stronger model than any single provider's
own independent-answer model), and internally by ClaudeClient as a fallback
when ANTHROPIC_API_KEY is not set."""
import time

from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.llm.base import LLMCallResult, ProviderError

_RETRYABLE = (RateLimitError, APITimeoutError, APIError)


class OpenRouterClient:
    provider = "openrouter"

    def __init__(self, model_name: str | None = None):
        settings = get_settings()
        if not settings.openrouter_api_key:
            raise ProviderError("openrouter", "OPENROUTER_API_KEY가 설정되지 않았습니다.")
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=settings.provider_timeout_seconds,
        )
        self.model_name = model_name or settings.judge_model or settings.openrouter_claude_model or "openai/gpt-4o-mini"
        self._max_retries = settings.provider_max_retries

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> LLMCallResult:
        @retry(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(_RETRYABLE),
            reraise=True,
        )
        def _call():
            return self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.2,
            )

        started = time.monotonic()
        try:
            response = _call()
        except _RETRYABLE as exc:
            raise ProviderError("openrouter", f"OpenRouter 호출 실패: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise ProviderError("openrouter", f"OpenRouter 호출 중 알 수 없는 오류: {exc}") from exc
        latency_ms = round((time.monotonic() - started) * 1000)

        choice = response.choices[0]
        usage = response.usage
        return LLMCallResult(
            text=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            latency_ms=latency_ms,
            model_name=self.model_name,
        )
