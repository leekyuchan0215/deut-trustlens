import json

from app.agents.prompts import RISK_ANALYSIS_SYSTEM, risk_analysis_prompt
from app.agents.schemas import RiskAnalysisOutput
from app.services.llm.base import LLMClient, call_json


def analyze_risks(
    judge_client: LLMClient,
    claims: list[dict],
    verification_results: list[dict],
    evidences: list[dict],
    cross_review: dict,
) -> tuple[RiskAnalysisOutput | None, dict]:
    return call_json(
        judge_client,
        RISK_ANALYSIS_SYSTEM,
        risk_analysis_prompt(
            json.dumps(claims, ensure_ascii=False),
            json.dumps(verification_results, ensure_ascii=False),
            json.dumps(evidences, ensure_ascii=False),
            json.dumps(cross_review, ensure_ascii=False),
        ),
        RiskAnalysisOutput,
        max_tokens=1500,
    )
