import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.llm.base import LLMCallResult, ProviderError

_RETRYABLE = (genai_errors.ServerError, genai_errors.ClientError)


class GeminiClient:
    provider = "gemini"

    def __init__(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ProviderError("gemini", "GEMINI_API_KEY가 설정되지 않았습니다.")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model or "gemini-2.0-flash"
        self._max_retries = settings.provider_max_retries
        self._timeout_seconds = settings.provider_timeout_seconds

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> LLMCallResult:
        @retry(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(_RETRYABLE),
            reraise=True,
        )
        def _call():
            return self._client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=0.2,
                    http_options=genai_types.HttpOptions(
                        timeout=int(self._timeout_seconds * 1000)
                    ),
                ),
            )

        started = time.monotonic()
        try:
            response = _call()
        except _RETRYABLE as exc:
            raise ProviderError("gemini", f"Gemini 호출 실패: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise ProviderError("gemini", f"Gemini 호출 중 알 수 없는 오류: {exc}") from exc
        latency_ms = round((time.monotonic() - started) * 1000)

        usage = response.usage_metadata
        return LLMCallResult(
            text=response.text or "",
            input_tokens=usage.prompt_token_count if usage else None,
            output_tokens=usage.candidates_token_count if usage else None,
            latency_ms=latency_ms,
            model_name=self.model_name,
        )
