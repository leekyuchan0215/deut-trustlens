import json

from app.agents.prompts import FINAL_ANSWER_SYSTEM, final_answer_prompt
from app.agents.schemas import FinalAnswerOutput
from app.services.llm.base import LLMClient, call_json


def generate_final_answer(
    judge_client: LLMClient,
    original_question: str,
    refined_question: str | None,
    selected_question: str,
    answer_purpose: str,
    claims: list[dict],
    deterministic_checks: list[dict],
    verification_results: list[dict],
    evidences: list[dict],
    cross_review: dict,
    risk_analysis: list[dict],
) -> tuple[FinalAnswerOutput | None, dict]:
    return call_json(
        judge_client,
        FINAL_ANSWER_SYSTEM,
        final_answer_prompt(
            original_question,
            refined_question or selected_question,
            selected_question,
            answer_purpose,
            json.dumps(claims, ensure_ascii=False),
            json.dumps(deterministic_checks, ensure_ascii=False),
            json.dumps(verification_results, ensure_ascii=False),
            json.dumps(evidences, ensure_ascii=False),
            json.dumps(cross_review, ensure_ascii=False),
            json.dumps(risk_analysis, ensure_ascii=False),
        ),
        FinalAnswerOutput,
        max_tokens=2000,
    )
