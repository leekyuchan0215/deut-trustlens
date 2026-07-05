"""OpenAI text-embedding-3-small, 1536-dim (docs/DB_SCHEMA.md #13,
docs/FEATURES.md F-12). Always real (is_mock=False) when called from Real
Mode; Mock Mode continues to use app/services/mock_data_generator instead."""
import time

from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.llm.base import ProviderError

EMBEDDING_DIMENSION = 1536
_RETRYABLE = (RateLimitError, APITimeoutError, APIError)


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderError("openai_embedding", "OPENAI_API_KEY가 설정되지 않았습니다.")
        self._client = OpenAI(api_key=settings.openai_api_key, timeout=settings.provider_timeout_seconds)
        self.model_name = settings.openai_embedding_model or "text-embedding-3-small"
        self._batch_size = settings.embedding_batch_size
        self._max_retries = settings.provider_max_retries

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        @retry(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(_RETRYABLE),
            reraise=True,
        )
        def _call(batch: list[str]):
            return self._client.embeddings.create(model=self.model_name, input=batch, dimensions=EMBEDDING_DIMENSION)

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            try:
                response = _call(batch)
            except _RETRYABLE as exc:
                raise ProviderError("openai_embedding", f"Embedding 생성 실패: {exc}") from exc
            except Exception as exc:  # pragma: no cover - defensive
                raise ProviderError("openai_embedding", f"Embedding 생성 중 알 수 없는 오류: {exc}") from exc
            vectors.extend(item.embedding for item in response.data)
        return vectors
