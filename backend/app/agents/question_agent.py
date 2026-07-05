"""Real-mode question analysis/refinement (docs/PROMPTS.md #5).

Falls back to the existing rule-based classifier (app/services/question_analysis.py)
if the LLM call or JSON validation fails, so /api/refine-prompt and the
pipeline's question_analysis stage always return a usable result.
"""
import logging
from datetime import datetime, timezone

from app.agents.prompts import QUESTION_ANALYSIS_SYSTEM, question_analysis_prompt
from app.agents.schemas import QuestionAnalysisOutput
from app.services import question_analysis as rule_based
from app.services.llm.base import call_json
from app.services.llm.router import get_client
from app.services.llm.base import ProviderError

logger = logging.getLogger("trustlens.agents.question")


def analyze_question(question: str, answer_purpose: str) -> tuple[QuestionAnalysisOutput, str]:
    """Returns (result, mode) where mode is 'llm_judge' or 'rule_fallback'."""
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        client = get_client("gpt")
        parsed, meta = call_json(
            client,
            QUESTION_ANALYSIS_SYSTEM,
            question_analysis_prompt(question, answer_purpose, current_date),
            QuestionAnalysisOutput,
            max_tokens=800,
        )
        if parsed is not None:
            return parsed, "llm_judge"
        logger.warning("question_analysis_llm_failed error=%s", meta.get("error"))
    except ProviderError as exc:
        logger.warning("question_analysis_provider_unavailable error=%s", exc)

    question_type, verification_basis = rule_based.classify_question(question)
    keywords = rule_based.extract_keywords(question)
    refined = rule_based.refine_question(question, answer_purpose, question_type).removeprefix("[MOCK] ")
    return (
        QuestionAnalysisOutput(
            original_question=question,
            refined_question=refined,
            question_type=question_type,
            verification_basis=verification_basis,
            suggested_keywords=keywords,
        ),
        "rule_fallback",
    )
