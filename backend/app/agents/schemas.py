"""Pydantic validation models for every LLM JSON output defined in
docs/PROMPTS.md. Enums are validated against the exact value lists in
app/utils/enums.py — nothing outside those lists is accepted.
"""
from pydantic import BaseModel, Field, field_validator

from app.utils.enums import (
    CLAIM_IMPORTANCE_VALUES,
    CLAIM_TYPE_VALUES,
    QUESTION_TYPE_VALUES,
    SOURCE_TYPE_VALUES,
    VERIFICATION_BASIS_VALUES,
    VERIFICATION_STATUS_VALUES,
)


def _enum_validator(values: list[str]):
    def _validate(v: str) -> str:
        if v not in values:
            raise ValueError(f"'{v}' is not one of {values}")
        return v

    return _validate


class QuestionAnalysisOutput(BaseModel):
    original_question: str
    refined_question: str
    question_type: str
    verification_basis: str
    suggested_keywords: list[str] = Field(default_factory=list, max_length=8)

    _v_qt = field_validator("question_type")(_enum_validator(QUESTION_TYPE_VALUES))
    _v_vb = field_validator("verification_basis")(_enum_validator(VERIFICATION_BASIS_VALUES))


class ExtractedClaim(BaseModel):
    claim_text: str
    normalized_claim: str
    claim_type: str
    importance: str
    verification_basis: str

    _v_ct = field_validator("claim_type")(_enum_validator(CLAIM_TYPE_VALUES))
    _v_imp = field_validator("importance")(_enum_validator(CLAIM_IMPORTANCE_VALUES))
    _v_vb = field_validator("verification_basis")(_enum_validator(VERIFICATION_BASIS_VALUES))


class ClaimExtractionOutput(BaseModel):
    provider: str
    claims: list[ExtractedClaim] = Field(default_factory=list, max_length=12)


class ConsolidatedClaim(BaseModel):
    claim_key: str
    claim_text: str
    normalized_claim: str
    claim_type: str
    importance: str
    verification_basis: str
    source_models: list[str]
    consolidation_reason: str = ""

    _v_ct = field_validator("claim_type")(_enum_validator(CLAIM_TYPE_VALUES))
    _v_imp = field_validator("importance")(_enum_validator(CLAIM_IMPORTANCE_VALUES))
    _v_vb = field_validator("verification_basis")(_enum_validator(VERIFICATION_BASIS_VALUES))

    @field_validator("source_models")
    @classmethod
    def _v_source_models(cls, v: list[str]) -> list[str]:
        allowed = {"gpt", "claude", "gemini"}
        return [m for m in v if m in allowed]


class ClaimConsolidationOutput(BaseModel):
    claims: list[ConsolidatedClaim] = Field(default_factory=list, max_length=12)


class VerificationStrategyOutput(BaseModel):
    verification_basis: str
    reason: str = ""
    requires_web_search: bool = False
    requires_deterministic_check: bool = False

    _v_vb = field_validator("verification_basis")(_enum_validator(VERIFICATION_BASIS_VALUES))


class DeterministicExtractionOutput(BaseModel):
    """Bridges a natural-language Claim into a structured, backend-computable
    check. The LLM only extracts structure; the actual result is always
    computed independently by app/services/deterministic_verification.py.
    """

    check_type: str
    input_expression: str | None = None
    ai_claimed_result: str | None = None
    from_unit: str | None = None
    to_unit: str | None = None
    value: float | None = None
    from_base: int | None = None
    to_base: int | None = None
    variables: dict[str, float] = Field(default_factory=dict)

    @field_validator("check_type")
    @classmethod
    def _v_check_type(cls, v: str) -> str:
        allowed = {
            "calculator",
            "unit_conversion",
            "base_conversion",
            "logic_evaluation",
            "formula",
            "safe_code_execution",
            "rule_based",
        }
        if v not in allowed:
            raise ValueError(f"'{v}' is not a valid check_type")
        return v


class SearchQueryGenerationOutput(BaseModel):
    requires_web_search: bool = True
    keyword_queries: list[str] = Field(default_factory=list, max_length=3)
    semantic_queries: list[str] = Field(default_factory=list, max_length=3)
    preferred_source_types: list[str] = Field(default_factory=list)
    recency_required: bool = False


class SelectedEvidence(BaseModel):
    evidence_id: str
    source_type: str
    relation: str = "support"
    source_quality_score: float = Field(ge=0, le=100)
    directness_score: float = Field(ge=0, le=100)
    support_score: float = Field(ge=0, le=100)
    selection_reason: str = ""

    _v_st = field_validator("source_type")(_enum_validator(SOURCE_TYPE_VALUES))


class EvidenceEvaluationOutput(BaseModel):
    selected_evidences: list[SelectedEvidence] = Field(default_factory=list)
    excluded_evidences: list[str] = Field(default_factory=list)


class ClaimVerificationOutput(BaseModel):
    verification_basis: str
    verification_status: str
    verification_confidence: float = Field(ge=0, le=100)
    verification_reason: str = ""
    direct_evidence_strength: float = Field(ge=0, le=100, default=0)
    cross_source_agreement: float = Field(ge=0, le=100, default=0)
    evidence_ids: list[str] = Field(default_factory=list)
    positive_factors: list[str] = Field(default_factory=list)
    deductions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    _v_vb = field_validator("verification_basis")(_enum_validator(VERIFICATION_BASIS_VALUES))
    _v_vs = field_validator("verification_status")(
        _enum_validator([v for v in VERIFICATION_STATUS_VALUES if v != "pending"])
    )


class SemanticConsensusItem(BaseModel):
    claim_id: str
    meaning: str = ""
    agreeing_models: list[str] = Field(default_factory=list)
    consensus_level: str = "medium"


class MissingPointItem(BaseModel):
    description: str
    affects_core_answer: bool = False


def _stringify_review_items(items: list) -> list[str]:
    """The Judge sometimes returns contradictions/overclaims/logic_issues as
    structured objects (e.g. {"model": "claude", "claim": "..."}) instead of
    plain strings, even though docs/API_SPEC.md #14 defines these as
    list[str]. Normalize here so the stored result always matches the API
    contract in app/schemas/common.py::CrossReviewObject."""
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            text = item.get("claim") or item.get("description") or item.get("reason") or item.get("text")
            model = item.get("model")
            if text and model:
                result.append(f"[{model}] {text}")
            elif text:
                result.append(str(text))
            else:
                result.append(", ".join(f"{k}: {v}" for k, v in item.items()))
        else:
            result.append(str(item))
    return result


class CrossReviewOutput(BaseModel):
    semantic_consensus: list[SemanticConsensusItem] = Field(default_factory=list)
    consensus: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    model_additions: dict[str, list[str]] = Field(
        default_factory=lambda: {"gpt": [], "claude": [], "gemini": []}
    )
    missing_points: list[MissingPointItem] = Field(default_factory=list)
    overclaims: list[str] = Field(default_factory=list)
    logic_issues: list[str] = Field(default_factory=list)
    model_strengths: dict[str, list[str]] = Field(
        default_factory=lambda: {"gpt": [], "claude": [], "gemini": []}
    )
    model_weaknesses: dict[str, list[str]] = Field(
        default_factory=lambda: {"gpt": [], "claude": [], "gemini": []}
    )

    @field_validator("contradictions", "overclaims", "logic_issues", mode="before")
    @classmethod
    def _normalize_review_items(cls, v):
        if not isinstance(v, list):
            return v
        return _stringify_review_items(v)


class RiskItem(BaseModel):
    risk_type: str
    risk_level: str
    description: str
    affected_claim_ids: list[str] = Field(default_factory=list)
    affects_core_answer: bool = False
    resolved_by_evidence: bool = False

    @field_validator("risk_type")
    @classmethod
    def _v_risk_type(cls, v: str) -> str:
        allowed = {"hallucination", "source_credibility", "outdated_information", "contradiction"}
        if v not in allowed:
            raise ValueError(f"'{v}' is not a valid risk_type")
        return v

    @field_validator("risk_level")
    @classmethod
    def _v_risk_level(cls, v: str) -> str:
        if v not in {"low", "medium", "high"}:
            raise ValueError(f"'{v}' is not a valid risk_level")
        return v


class RiskAnalysisOutput(BaseModel):
    risks: list[RiskItem] = Field(default_factory=list)


class CitationItem(BaseModel):
    evidence_id: str
    title: str = ""
    url: str | None = None


class FinalAnswerOutput(BaseModel):
    summary: str
    final_answer: str
    cautions: list[str] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)


class ReflectionOutput(BaseModel):
    passed: bool = True
    issues: list[str] = Field(default_factory=list)
    revised: FinalAnswerOutput | None = None
