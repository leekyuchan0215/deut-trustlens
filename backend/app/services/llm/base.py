"""Shared types and JSON-repair helper for all provider clients.

Every provider client (GPT/Claude/Gemini) exposes the same `.chat(...)`
interface so agents can call any of them interchangeably. Timeout and retry
are handled per-call here; JSON parsing + a single repair attempt follows
docs/PROMPTS.md #19 (first response -> parse -> validate -> repair once ->
fallback).
"""
import json
import logging
import re
from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("trustlens.llm")

T = TypeVar("T", bound=BaseModel)


class ProviderError(Exception):
    """Raised when a provider call fails after all retries."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"[{provider}] {message}")


@dataclass
class LLMCallResult:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    model_name: str


class LLMClient(Protocol):
    provider: str
    model_name: str

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> LLMCallResult:
        ...


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _strip_to_json(text: str) -> str:
    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match:
        return fence_match.group(1).strip()
    text = text.strip()
    start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not start_candidates:
        return text
    start = min(start_candidates)
    end_brace = text.rfind("}")
    end_bracket = text.rfind("]")
    end = max(end_brace, end_bracket)
    if end == -1 or end < start:
        return text
    return text[start : end + 1]


def call_json(
    client: LLMClient,
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    max_tokens: int = 2000,
) -> tuple[T | None, dict]:
    """Call the client, parse+validate JSON, repair once on failure.

    Returns (parsed_model_or_None, meta) where meta carries attempt count,
    latency, token usage and — on total failure — the last error for the
    caller's fallback_reason.
    """
    meta = {
        "provider": client.provider,
        "model_name": client.model_name,
        "attempts": 0,
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "error": None,
    }

    try:
        result = client.chat(system_prompt, user_prompt, max_tokens=max_tokens)
    except ProviderError as exc:
        meta["error"] = str(exc)
        logger.warning("llm_call_failed provider=%s schema=%s error=%s", client.provider, schema.__name__, exc)
        return None, meta
    meta["attempts"] += 1
    meta["latency_ms"] += result.latency_ms
    meta["input_tokens"] += result.input_tokens or 0
    meta["output_tokens"] += result.output_tokens or 0

    parsed, error = _try_parse(result.text, schema)
    if parsed is not None:
        return parsed, meta

    repair_prompt = (
        "다음은 JSON 형식을 지키지 않았거나 검증에 실패한 이전 응답입니다.\n\n"
        f"이전 응답:\n{result.text}\n\n"
        f"검증 오류:\n{error}\n\n"
        "의미를 유지하고 입력에 없는 사실과 URL을 추가하지 말고, "
        "요구된 JSON 스키마에 맞는 JSON만 다시 반환하세요."
    )
    try:
        repair_result = client.chat(system_prompt, repair_prompt, max_tokens=max_tokens)
        meta["attempts"] += 1
        meta["latency_ms"] += repair_result.latency_ms
        meta["input_tokens"] += repair_result.input_tokens or 0
        meta["output_tokens"] += repair_result.output_tokens or 0
        parsed, error = _try_parse(repair_result.text, schema)
        if parsed is not None:
            return parsed, meta
    except ProviderError as exc:
        error = str(exc)

    meta["error"] = error
    logger.warning("json_repair_failed provider=%s schema=%s error=%s", client.provider, schema.__name__, error)
    return None, meta


def _try_parse(text: str, schema: type[T]) -> tuple[T | None, str | None]:
    candidate = _strip_to_json(text)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error: {exc}"
    try:
        return schema.model_validate(data), None
    except ValidationError as exc:
        return None, f"Schema validation error: {exc}"
