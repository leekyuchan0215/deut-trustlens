"""Claim Extraction (docs/PROMPTS.md #7) and Claim Consolidation (#8).

Both steps run on the Judge client (JUDGE_PROVIDER/JUDGE_MODEL, falling back
to gpt->claude->gemini) so extraction/consolidation logic is not biased
toward whichever provider happens to answer first.
"""
import json
import logging

from app.agents.prompts import (
    CLAIM_CONSOLIDATION_SYSTEM,
    CLAIM_EXTRACTION_SYSTEM,
    claim_consolidation_prompt,
    claim_extraction_prompt,
)
from app.agents.schemas import ClaimConsolidationOutput, ClaimExtractionOutput
from app.services.llm.base import LLMClient, call_json

logger = logging.getLogger("trustlens.agents.claim")


def extract_claims(
    judge_client: LLMClient, question: str, provider: str, response_text: str
) -> tuple[ClaimExtractionOutput | None, dict]:
    parsed, meta = call_json(
        judge_client,
        CLAIM_EXTRACTION_SYSTEM,
        claim_extraction_prompt(question, provider, response_text),
        ClaimExtractionOutput,
        max_tokens=3200,
    )
    if parsed is not None and parsed.provider != provider:
        parsed.provider = provider
    return parsed, meta


def consolidate_claims(
    judge_client: LLMClient,
    claims_by_provider: dict[str, list],
) -> tuple[ClaimConsolidationOutput | None, dict]:
    def _dump(provider: str) -> str:
        items = claims_by_provider.get(provider, [])
        return json.dumps([c.model_dump() for c in items], ensure_ascii=False)

    parsed, meta = call_json(
        judge_client,
        CLAIM_CONSOLIDATION_SYSTEM,
        claim_consolidation_prompt(_dump("gpt"), _dump("claude"), _dump("gemini")),
        ClaimConsolidationOutput,
        max_tokens=4000,
    )
    return parsed, meta
