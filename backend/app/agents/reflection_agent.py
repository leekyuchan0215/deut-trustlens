import json

from app.agents.prompts import REFLECTION_SYSTEM, reflection_prompt
from app.agents.schemas import FinalAnswerOutput, ReflectionOutput
from app.services.llm.base import LLMClient, call_json


def reflect(
    judge_client: LLMClient,
    selected_question: str,
    draft_final_answer: FinalAnswerOutput,
    claims: list[dict],
    verification_results: list[dict],
    evidences: list[dict],
) -> tuple[ReflectionOutput | None, dict]:
    return call_json(
        judge_client,
        REFLECTION_SYSTEM,
        reflection_prompt(
            selected_question,
            json.dumps(draft_final_answer.model_dump(), ensure_ascii=False),
            json.dumps(claims, ensure_ascii=False),
            json.dumps(verification_results, ensure_ascii=False),
            json.dumps(evidences, ensure_ascii=False),
        ),
        ReflectionOutput,
        max_tokens=2000,
    )
