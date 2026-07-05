"""Tavily web search (docs/FEATURES.md F-11). Results are returned as plain
dicts; the caller decides source_type classification and persists them as
SearchDocument rows. Injected instructions inside returned content are never
executed — they are treated purely as data by downstream agents."""
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone

from tavily import TavilyClient
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.llm.base import ProviderError

logger = logging.getLogger("trustlens.tavily")

_OFFICIAL_DOMAIN_HINTS = (".gov", ".go.kr", "who.int", "un.org", ".int")
_ACADEMIC_DOMAIN_HINTS = (".edu", "arxiv.org", "ncbi.nlm.nih.gov", "scholar.google")
_DOCUMENTATION_DOMAIN_HINTS = ("docs.", "readthedocs.io", "developer.", "github.io")
_NEWS_DOMAIN_HINTS = ("news.", "reuters.com", "bbc.", "nytimes.com", "yna.co.kr", "chosun.com", "hani.co.kr")


@dataclass
class TavilyResult:
    title: str
    url: str
    domain: str
    content: str
    source_type: str
    published_at: datetime | None
    search_query: str
    content_hash: str


def classify_source_type(domain: str) -> str:
    domain = (domain or "").lower()
    if any(hint in domain for hint in _OFFICIAL_DOMAIN_HINTS):
        return "government"
    if any(hint in domain for hint in _ACADEMIC_DOMAIN_HINTS):
        return "academic"
    if any(hint in domain for hint in _DOCUMENTATION_DOMAIN_HINTS):
        return "documentation"
    if any(hint in domain for hint in _NEWS_DOMAIN_HINTS):
        return "news"
    if "blog" in domain or "medium.com" in domain or "tistory.com" in domain or "velog.io" in domain:
        return "blog"
    if "wikipedia.org" in domain:
        return "documentation"
    if "reddit.com" in domain or "stackoverflow.com" in domain or "stackexchange.com" in domain:
        return "community"
    return "unknown"


def _sanitize_text(text: str) -> str:
    """Postgres TEXT columns reject NUL (0x00) bytes outright; PDF-extracted
    content from Tavily occasionally contains them alongside other control
    characters."""
    if not text:
        return text
    return "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)


def _domain_of(url: str) -> str:
    try:
        from urllib.parse import urlparse

        return urlparse(url).netloc.replace("www.", "")
    except Exception:  # pragma: no cover - defensive
        return ""


def _parse_published_at(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class TavilyService:
    def __init__(self):
        settings = get_settings()
        if not settings.tavily_api_key:
            raise ProviderError("tavily", "TAVILY_API_KEY가 설정되지 않았습니다.")
        self._client = TavilyClient(api_key=settings.tavily_api_key)
        self._max_results = (
            min(settings.tavily_max_results_per_query, 2)
            if settings.pipeline_fast_mode
            else settings.tavily_max_results_per_query
        )
        self._search_depth = "basic" if settings.pipeline_fast_mode else "advanced"
        self._max_retries = settings.provider_max_retries

    def search(self, query: str, recency_required: bool = False) -> list[TavilyResult]:
        @retry(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call():
            return self._client.search(
                query=query,
                search_depth=self._search_depth,
                max_results=self._max_results,
                include_raw_content=False,
                time_range="year" if recency_required else None,
            )

        try:
            response = _call()
        except Exception as exc:
            raise ProviderError("tavily", f"Tavily 검색 실패: {exc}") from exc

        results = []
        for item in response.get("results", []):
            url = item.get("url", "")
            domain = _domain_of(url)
            content = _sanitize_text(item.get("content") or "")
            title = _sanitize_text(item.get("title") or url)
            results.append(
                TavilyResult(
                    title=title,
                    url=url,
                    domain=domain,
                    content=content,
                    source_type=classify_source_type(domain),
                    published_at=_parse_published_at(item.get("published_date")),
                    search_query=query,
                    content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                )
            )
        return results


def search_many(queries: list[str], recency_required: bool = False) -> list[TavilyResult]:
    """Search multiple queries in parallel, de-duplicating by URL. Any single-query
    failure is logged and skipped rather than failing the whole batch."""
    settings = get_settings()
    service = TavilyService()
    unique_queries: list[str] = []
    seen_queries: set[str] = set()
    for query in queries:
        normalized = query.strip()
        if not normalized or normalized in seen_queries:
            continue
        seen_queries.add(normalized)
        unique_queries.append(normalized)

    if settings.pipeline_fast_mode:
        unique_queries = unique_queries[: settings.fast_mode_tavily_max_queries]

    if not unique_queries:
        return []

    seen_urls: set[str] = set()
    results: list[TavilyResult] = []

    def _search_one(query: str) -> list[TavilyResult]:
        return service.search(query, recency_required=recency_required)

    max_workers = min(6, len(unique_queries))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_search_one, query): query for query in unique_queries}
        for future in as_completed(futures):
            query = futures[future]
            try:
                batch = future.result()
            except ProviderError as exc:
                logger.warning("tavily_query_failed query=%s error=%s", query, exc)
                continue
            for result in batch:
                if result.url in seen_urls:
                    continue
                seen_urls.add(result.url)
                results.append(result)
    return results
