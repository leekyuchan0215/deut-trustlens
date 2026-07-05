"""Independent, parallel multi-AI answer generation (docs/PROMPTS.md #6,
docs/FEATURES.md F-06). GPT/Claude/Gemini never see each other's answers."""
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

from app.agents.prompts import ANSWER_GENERATION_SYSTEM, answer_generation_prompt
from app.core.config import get_settings
from app.services.llm.base import ProviderError
from app.services.llm.router import get_client

logger = logging.getLogger("trustlens.agents.answer")

_PROVIDERS = ["gpt", "claude", "gemini"]

# Rough per-1K-token USD estimates for the estimated_cost column; not billed,
# only shown for UI transparency (docs/API_SPEC.md #10 estimated_cost).
_COST_PER_1K_TOKENS = {
    "gpt": (0.0025, 0.01),
    "claude": (0.003, 0.015),
    "gemini": (0.00025, 0.001),
}


@dataclass
class AnswerResult:
    provider: str
    model_name: str
    status: str
    response_text: str | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    estimated_cost: float | None
    error_code: str | None
    error_message: str | None


def _generate_one(
    provider: str, question: str, question_type: str, verification_basis: str, answer_purpose: str, current_date: str
) -> AnswerResult:
    try:
        client = get_client(provider)
    except ProviderError as exc:
        return AnswerResult(
            provider=provider,
            model_name="unavailable",
            status="failed",
            response_text=None,
            latency_ms=None,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            estimated_cost=None,
            error_code="PROVIDER_UNAVAILABLE",
            error_message=exc.message,
        )

    try:
        result = client.chat(
            ANSWER_GENERATION_SYSTEM,
            answer_generation_prompt(question, question_type, verification_basis, answer_purpose, current_date),
            max_tokens=get_settings().answer_max_tokens,
        )
    except ProviderError as exc:
        return AnswerResult(
            provider=provider,
            model_name=client.model_name,
            status="failed",
            response_text=None,
            latency_ms=None,
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
            estimated_cost=None,
            error_code="PROVIDER_CALL_FAILED",
            error_message=exc.message,
        )

    input_tokens = result.input_tokens or 0
    output_tokens = result.output_tokens or 0
    in_rate, out_rate = _COST_PER_1K_TOKENS.get(provider, (0.0, 0.0))
    estimated_cost = round((input_tokens / 1000) * in_rate + (output_tokens / 1000) * out_rate, 6)

    return AnswerResult(
        provider=provider,
        model_name=result.model_name,
        status="success",
        response_text=result.text,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=input_tokens + output_tokens,
        estimated_cost=estimated_cost,
        error_code=None,
        error_message=None,
    )


def generate_answers(
    question: str, question_type: str, verification_basis: str, answer_purpose: str
) -> list[AnswerResult]:
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with ThreadPoolExecutor(max_workers=len(_PROVIDERS)) as pool:
        futures = [
            pool.submit(_generate_one, provider, question, question_type, verification_basis, answer_purpose, current_date)
            for provider in _PROVIDERS
        ]
        return [f.result() for f in futures]
