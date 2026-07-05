import time

import anthropic
from openai import APIError as OpenAIAPIError
from openai import APITimeoutError as OpenAIAPITimeoutError
from openai import OpenAI, RateLimitError as OpenAIRateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.llm.base import LLMCallResult, ProviderError

_ANTHROPIC_RETRYABLE = (
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)
_OPENROUTER_RETRYABLE = (OpenAIRateLimitError, OpenAIAPITimeoutError, OpenAIAPIError)


class ClaudeClient:
    """Direct Anthropic API if ANTHROPIC_API_KEY is set, else OpenRouter fallback."""

    provider = "claude"

    def __init__(self):
        settings = get_settings()
        self._max_retries = settings.provider_max_retries
        if settings.anthropic_api_key:
            self._mode = "anthropic"
            self._client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key, timeout=settings.provider_timeout_seconds
            )
            self.model_name = settings.claude_model or "claude-sonnet-4-5"
        elif settings.openrouter_api_key:
            self._mode = "openrouter"
            self._client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=settings.provider_timeout_seconds,
            )
            self.model_name = settings.openrouter_claude_model or "anthropic/claude-sonnet-4.5"
        else:
            raise ProviderError(
                "claude", "ANTHROPIC_API_KEY 또는 OPENROUTER_API_KEY가 설정되지 않았습니다."
            )

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> LLMCallResult:
        if self._mode == "anthropic":
            return self._chat_anthropic(system_prompt, user_prompt, max_tokens)
        return self._chat_openrouter(system_prompt, user_prompt, max_tokens)

    def _chat_anthropic(self, system_prompt: str, user_prompt: str, max_tokens: int) -> LLMCallResult:
        @retry(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(_ANTHROPIC_RETRYABLE),
            reraise=True,
        )
        def _call():
            return self._client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.2,
            )

        started = time.monotonic()
        try:
            response = _call()
        except _ANTHROPIC_RETRYABLE as exc:
            raise ProviderError("claude", f"Anthropic 호출 실패: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise ProviderError("claude", f"Anthropic 호출 중 알 수 없는 오류: {exc}") from exc
        latency_ms = round((time.monotonic() - started) * 1000)

        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMCallResult(
            text=text,
            input_tokens=response.usage.input_tokens if response.usage else None,
            output_tokens=response.usage.output_tokens if response.usage else None,
            latency_ms=latency_ms,
            model_name=self.model_name,
        )

    def _chat_openrouter(self, system_prompt: str, user_prompt: str, max_tokens: int) -> LLMCallResult:
        @retry(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(_OPENROUTER_RETRYABLE),
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
        except _OPENROUTER_RETRYABLE as exc:
            raise ProviderError("claude", f"OpenRouter(Claude) 호출 실패: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise ProviderError("claude", f"OpenRouter(Claude) 호출 중 알 수 없는 오류: {exc}") from exc
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
