from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import (
    AIResponseObject,
    ClaimObject,
    ClaimSummary,
    CrossReviewObject,
    DeterministicCheckObject,
    EvidenceObject,
    FinalResultObject,
    ModelScoreObject,
    RiskObject,
    SourceSummary,
    TrustScoreBreakdown,
)


class ResultSummaryResponse(BaseModel):
    question_id: str
    status: str
    original_question: str
    refined_question: str | None = None
    selected_question: str
    answer_purpose: str
    question_type: str | None = None
    verification_basis: str | None = None
    trust_score: float
    grade: str
    summary: str
    final_answer: str
    cautions: list[str]
    trust_score_breakdown: TrustScoreBreakdown
    model_scores: list[ModelScoreObject]
    claim_summary: ClaimSummary
    source_summary: SourceSummary
    key_issues: list[str]
    created_at: datetime
    completed_at: datetime | None = None


class ResultDetailResponse(BaseModel):
    question_id: str
    status: str
    original_question: str
    refined_question: str | None = None
    selected_question: str
    answer_purpose: str
    question_type: str | None = None
    verification_basis: str | None = None
    ai_responses: list[AIResponseObject]
    model_scores: list[ModelScoreObject]
    claims: list[ClaimObject]
    deterministic_checks: list[DeterministicCheckObject]
    evidences: list[EvidenceObject]
    cross_review: CrossReviewObject
    risk_analysis: list[RiskObject]
    trust_score_breakdown: TrustScoreBreakdown
    source_summary: SourceSummary
    claim_distribution: dict
    claim_evidence_relations: list[dict]
    final_result: FinalResultObject
    created_at: datetime
    completed_at: datetime | None = None
