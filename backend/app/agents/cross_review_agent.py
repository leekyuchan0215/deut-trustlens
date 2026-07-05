import json

from app.agents.prompts import CROSS_REVIEW_SYSTEM, cross_review_prompt
from app.agents.schemas import CrossReviewOutput
from app.services.llm.base import LLMClient, call_json


def cross_review(
    judge_client: LLMClient,
    question: str,
    gpt_response: str | None,
    claude_response: str | None,
    gemini_response: str | None,
    claims: list[dict],
    verification_results: list[dict],
) -> tuple[CrossReviewOutput | None, dict]:
    return call_json(
        judge_client,
        CROSS_REVIEW_SYSTEM,
        cross_review_prompt(
            question,
            gpt_response or "(응답 없음)",
            claude_response or "(응답 없음)",
            gemini_response or "(응답 없음)",
            json.dumps(claims, ensure_ascii=False),
            json.dumps(verification_results, ensure_ascii=False),
        ),
        CrossReviewOutput,
        max_tokens=2500,
    )
