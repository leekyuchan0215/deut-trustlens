"""Verification Strategy classification (#9), Deterministic extraction (#10),
Search Query generation (#11), Evidence evaluation (#12) and Claim
Verification (#13) from docs/PROMPTS.md. All run on the Judge client.
"""
import json
from datetime import datetime, timezone

from app.agents.prompts import (
    CLAIM_VERIFICATION_SYSTEM,
    DETERMINISTIC_EXTRACTION_SYSTEM,
    EVIDENCE_EVALUATION_SYSTEM,
    SEARCH_QUERY_SYSTEM,
    VERIFICATION_STRATEGY_SYSTEM,
    claim_verification_prompt,
    deterministic_extraction_prompt,
    evidence_evaluation_prompt,
    search_query_prompt,
    verification_strategy_prompt,
)
from app.agents.schemas import (
    ClaimVerificationOutput,
    DeterministicExtractionOutput,
    EvidenceEvaluationOutput,
    SearchQueryGenerationOutput,
    VerificationStrategyOutput,
)
from app.services.llm.base import LLMClient, call_json


def classify_verification_basis(
    judge_client: LLMClient, claim_text: str
) -> tuple[VerificationStrategyOutput | None, dict]:
    return call_json(
        judge_client,
        VERIFICATION_STRATEGY_SYSTEM,
        verification_strategy_prompt(claim_text),
        VerificationStrategyOutput,
        max_tokens=400,
    )


def extract_deterministic(
    judge_client: LLMClient, claim_text: str
) -> tuple[DeterministicExtractionOutput | None, dict]:
    return call_json(
        judge_client,
        DETERMINISTIC_EXTRACTION_SYSTEM,
        deterministic_extraction_prompt(claim_text),
        DeterministicExtractionOutput,
        max_tokens=500,
    )


def generate_search_queries(
    judge_client: LLMClient, claim_text: str, verification_basis: str
) -> tuple[SearchQueryGenerationOutput | None, dict]:
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return call_json(
        judge_client,
        SEARCH_QUERY_SYSTEM,
        search_query_prompt(claim_text, verification_basis, current_date),
        SearchQueryGenerationOutput,
        max_tokens=600,
    )


def evaluate_evidence(
    judge_client: LLMClient, claim_text: str, candidates: list[dict]
) -> tuple[EvidenceEvaluationOutput | None, dict]:
    return call_json(
        judge_client,
        EVIDENCE_EVALUATION_SYSTEM,
        evidence_evaluation_prompt(claim_text, json.dumps(candidates, ensure_ascii=False)),
        EvidenceEvaluationOutput,
        max_tokens=1800,
    )


def verify_claim(
    judge_client: LLMClient,
    claim_text: str,
    verification_basis: str,
    deterministic_check: dict | None,
    evidences: list[dict],
) -> tuple[ClaimVerificationOutput | None, dict]:
    return call_json(
        judge_client,
        CLAIM_VERIFICATION_SYSTEM,
        claim_verification_prompt(
            claim_text,
            verification_basis,
            json.dumps(deterministic_check, ensure_ascii=False) if deterministic_check else "null",
            json.dumps(evidences, ensure_ascii=False),
        ),
        ClaimVerificationOutput,
        max_tokens=1200,
    )
