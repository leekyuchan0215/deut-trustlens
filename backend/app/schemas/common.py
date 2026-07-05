from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ModelScoreObject(BaseModel):
    provider: str
    model_name: str
    score: float | None = None
    grade: str | None = None
    reason: str | None = None


class AIResponseObject(BaseModel):
    id: str
    provider: str
    model_name: str
    status: str
    response_text: str | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    error_message: str | None = None


class ClaimObject(BaseModel):
    id: str
    display_id: str
    claim_text: str
    normalized_claim: str
    claim_type: str
    importance: str
    verification_basis: str
    source_models: list[str]
    consensus_score: float | None = None
    consensus_level: str | None = None
    verification_status: str
    verification_confidence: float | None = None
    verification_reason: str | None = None
    verification_mode: str | None = None
    direct_evidence_strength: float | None = None
    cross_source_agreement: float | None = None
    risk_level: str | None = None
    evidence_count: int = 0
    evidence_ids: list[str] = []
    positive_factors: list[str] = []
    deductions: list[str] = []
    limitations: list[str] = []


class DeterministicCheckObject(BaseModel):
    id: str
    claim_id: str
    check_type: str
    input_expression: str | None = None
    expected_result: str | None = None
    ai_claimed_result: str | None = None
    check_passed: bool
    verification_status: str
    verification_confidence: float
    verification_reason: str
    limitations: list[str] = []


class EvidenceObject(BaseModel):
    id: str
    claim_id: str
    title: str
    url: str | None = None
    domain: str | None = None
    snippet: str
    source_name: str | None = None
    source_type: str
    published_at: datetime | None = None
    searched_at: datetime | None = None
    relation: str
    keyword_score: float | None = None
    vector_score: float | None = None
    hybrid_score: float | None = None
    source_quality_score: float
    directness_score: float
    support_score: float
    rank: int


class CrossReviewSemanticConsensus(BaseModel):
    claim_id: str
    meaning: str
    agreeing_models: list[str]
    consensus_level: str


class CrossReviewMissingPoint(BaseModel):
    description: str
    affects_core_answer: bool


class CrossReviewObject(BaseModel):
    semantic_consensus: list[CrossReviewSemanticConsensus] = []
    consensus: list[str] = []
    contradictions: list[str] = []
    model_additions: dict[str, list[str]] = {}
    missing_points: list[CrossReviewMissingPoint] = []
    overclaims: list[str] = []
    logic_issues: list[str] = []
    model_strengths: dict[str, list[str]] = {}
    model_weaknesses: dict[str, list[str]] = {}
    cross_review_mode: str


class RiskObject(BaseModel):
    id: str
    claim_id: str | None = None
    risk_type: str
    risk_level: str
    description: str
    affects_core_answer: bool
    resolved_by_evidence: bool
    penalty: float
    detected_by: str


class ScoreReasonDetail(BaseModel):
    score: float
    reason: str
    verification_basis: str | None = None
    positive_factors: list[str] = []
    negative_factors: list[str] = []


class TrustScoreBreakdown(BaseModel):
    evidence_support_score: float
    source_quality_score: float
    consensus_score: float
    logic_score: float
    freshness_score: float
    base_score: float
    contradiction_penalty: float
    risk_penalty: float
    total_score: float
    grade: str
    score_reasons: dict[str, ScoreReasonDetail]
    strengths: list[str] = []
    deductions: list[str] = []
    calculation_detail: dict
    formula_version: str


class CitationObject(BaseModel):
    evidence_id: str
    title: str
    url: str | None = None


class FinalResultObject(BaseModel):
    summary: str
    final_answer: str
    cautions: list[str] = []
    citations: list[CitationObject] = []
    final_answer_mode: str
    cross_review_mode: str
    judge_provider: str | None = None
    judge_model: str | None = None
    judge_attempts: int
    fallback_reason: str | None = None


class ClaimSummary(BaseModel):
    total: int
    core: int
    supporting: int
    verified: int
    weak_evidence: int
    unsupported: int
    contradicted: int


class SourceSummary(BaseModel):
    total_documents: int = 0
    used_evidences: int = 0
    web_documents: int = 0
    academic_papers: int = 0
    technical_blogs: int = 0
    official_documents: int = 0
    government_sources: int = 0
    deterministic_checks: int = 0
