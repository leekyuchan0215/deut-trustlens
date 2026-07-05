from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AIResponse,
    Claim,
    DeterministicCheck,
    Evidence,
    FinalResult,
    Question,
    Risk,
    TrustScore,
)
from app.schemas.common import (
    AIResponseObject,
    ClaimObject,
    ClaimSummary,
    CitationObject,
    CrossReviewObject,
    DeterministicCheckObject,
    EvidenceObject,
    FinalResultObject,
    ModelScoreObject,
    RiskObject,
    SourceSummary,
    TrustScoreBreakdown,
)
from app.schemas.result import ResultDetailResponse, ResultSummaryResponse


def _model_scores(ai_responses: list[AIResponse]) -> list[ModelScoreObject]:
    return [
        ModelScoreObject(
            provider=r.provider,
            model_name=r.model_name,
            score=float(r.model_score) if r.model_score is not None else None,
            grade=r.model_grade,
            reason=r.model_score_reason,
        )
        for r in ai_responses
    ]


def _claim_summary(claims: list[Claim]) -> ClaimSummary:
    return ClaimSummary(
        total=len(claims),
        core=len([c for c in claims if c.importance == "core"]),
        supporting=len([c for c in claims if c.importance == "supporting"]),
        verified=len([c for c in claims if c.verification_status == "verified"]),
        weak_evidence=len([c for c in claims if c.verification_status == "weak_evidence"]),
        unsupported=len([c for c in claims if c.verification_status == "unsupported"]),
        contradicted=len([c for c in claims if c.verification_status == "contradicted"]),
    )


def _trust_score_breakdown(trust_score: TrustScore) -> TrustScoreBreakdown:
    return TrustScoreBreakdown(
        evidence_support_score=float(trust_score.evidence_support_score),
        source_quality_score=float(trust_score.source_quality_score),
        consensus_score=float(trust_score.consensus_score),
        logic_score=float(trust_score.logic_score),
        freshness_score=float(trust_score.freshness_score),
        base_score=float(trust_score.base_score),
        contradiction_penalty=float(trust_score.contradiction_penalty),
        risk_penalty=float(trust_score.risk_penalty),
        total_score=float(trust_score.total_score),
        grade=trust_score.grade,
        score_reasons=trust_score.score_reasons,
        strengths=trust_score.strengths,
        deductions=trust_score.deductions,
        calculation_detail=trust_score.calculation_detail,
        formula_version=trust_score.formula_version,
    )


def build_result_summary(db: Session, question: Question) -> ResultSummaryResponse:
    ai_responses = db.execute(select(AIResponse).where(AIResponse.question_id == question.id)).scalars().all()
    claims = db.execute(select(Claim).where(Claim.question_id == question.id)).scalars().all()
    trust_score = db.execute(
        select(TrustScore).where(TrustScore.question_id == question.id)
    ).scalar_one()
    final_result = db.execute(
        select(FinalResult).where(FinalResult.question_id == question.id)
    ).scalar_one()

    return ResultSummaryResponse(
        question_id=str(question.id),
        status=question.status,
        original_question=question.original_question,
        refined_question=question.refined_question,
        selected_question=question.selected_question,
        answer_purpose=question.answer_purpose,
        question_type=question.question_type,
        verification_basis=question.verification_basis,
        trust_score=float(trust_score.total_score),
        grade=trust_score.grade,
        summary=final_result.summary,
        final_answer=final_result.final_answer,
        cautions=final_result.cautions,
        trust_score_breakdown=_trust_score_breakdown(trust_score),
        model_scores=_model_scores(ai_responses),
        claim_summary=_claim_summary(claims),
        source_summary=SourceSummary(**final_result.source_summary),
        key_issues=final_result.key_issues,
        created_at=question.created_at,
        completed_at=question.completed_at,
    )


def build_result_detail(db: Session, question: Question) -> ResultDetailResponse:
    ai_responses = db.execute(select(AIResponse).where(AIResponse.question_id == question.id)).scalars().all()
    claims = db.execute(select(Claim).where(Claim.question_id == question.id)).scalars().all()
    deterministic_checks = db.execute(
        select(DeterministicCheck).where(DeterministicCheck.question_id == question.id)
    ).scalars().all()
    evidences = db.execute(select(Evidence).where(Evidence.question_id == question.id)).scalars().all()
    risks = db.execute(select(Risk).where(Risk.question_id == question.id)).scalars().all()
    trust_score = db.execute(
        select(TrustScore).where(TrustScore.question_id == question.id)
    ).scalar_one()
    final_result = db.execute(
        select(FinalResult).where(FinalResult.question_id == question.id)
    ).scalar_one()

    evidence_count_by_claim: dict = {}
    evidence_ids_by_claim: dict = {}
    for e in evidences:
        evidence_count_by_claim[e.claim_id] = evidence_count_by_claim.get(e.claim_id, 0) + 1
        evidence_ids_by_claim.setdefault(e.claim_id, []).append(str(e.id))

    risk_level_by_claim: dict = {}
    for r in risks:
        if r.claim_id is not None:
            risk_level_by_claim[r.claim_id] = r.risk_level

    claim_objects = [
        ClaimObject(
            id=str(c.id),
            display_id=c.display_id,
            claim_text=c.claim_text,
            normalized_claim=c.normalized_claim,
            claim_type=c.claim_type,
            importance=c.importance,
            verification_basis=c.verification_basis,
            source_models=c.source_models,
            consensus_score=float(c.consensus_score) if c.consensus_score is not None else None,
            consensus_level=c.consensus_level,
            verification_status=c.verification_status,
            verification_confidence=float(c.verification_confidence) if c.verification_confidence is not None else None,
            verification_reason=c.verification_reason,
            verification_mode=c.verification_mode,
            direct_evidence_strength=float(c.direct_evidence_strength) if c.direct_evidence_strength is not None else None,
            cross_source_agreement=float(c.cross_source_agreement) if c.cross_source_agreement is not None else None,
            risk_level=risk_level_by_claim.get(c.id),
            evidence_count=evidence_count_by_claim.get(c.id, 0),
            evidence_ids=evidence_ids_by_claim.get(c.id, []),
            positive_factors=c.positive_factors,
            deductions=c.deductions,
            limitations=c.limitations,
        )
        for c in claims
    ]

    return ResultDetailResponse(
        question_id=str(question.id),
        status=question.status,
        original_question=question.original_question,
        refined_question=question.refined_question,
        selected_question=question.selected_question,
        answer_purpose=question.answer_purpose,
        question_type=question.question_type,
        verification_basis=question.verification_basis,
        ai_responses=[
            AIResponseObject(
                id=str(r.id),
                provider=r.provider,
                model_name=r.model_name,
                status=r.status,
                response_text=r.response_text,
                latency_ms=r.latency_ms,
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
                total_tokens=r.total_tokens,
                estimated_cost=float(r.estimated_cost) if r.estimated_cost is not None else None,
                error_message=r.error_message,
            )
            for r in ai_responses
        ],
        model_scores=_model_scores(ai_responses),
        claims=claim_objects,
        deterministic_checks=[
            DeterministicCheckObject(
                id=str(d.id),
                claim_id=str(d.claim_id),
                check_type=d.check_type,
                input_expression=d.input_expression,
                expected_result=d.expected_result,
                ai_claimed_result=d.ai_claimed_result,
                check_passed=d.check_passed,
                verification_status=d.verification_status,
                verification_confidence=float(d.verification_confidence),
                verification_reason=d.verification_reason,
                limitations=d.limitations,
            )
            for d in deterministic_checks
        ],
        evidences=[
            EvidenceObject(
                id=str(e.id),
                claim_id=str(e.claim_id),
                title=e.title,
                url=e.url,
                domain=e.domain,
                snippet=e.snippet,
                source_name=e.source_name,
                source_type=e.source_type,
                published_at=e.published_at,
                searched_at=e.searched_at,
                relation=e.relation,
                keyword_score=float(e.keyword_score) if e.keyword_score is not None else None,
                vector_score=float(e.vector_score) if e.vector_score is not None else None,
                hybrid_score=float(e.hybrid_score) if e.hybrid_score is not None else None,
                source_quality_score=float(e.source_quality_score),
                directness_score=float(e.directness_score),
                support_score=float(e.support_score),
                rank=e.rank,
            )
            for e in evidences
        ],
        cross_review=CrossReviewObject(**final_result.cross_review),
        risk_analysis=[
            RiskObject(
                id=str(r.id),
                claim_id=str(r.claim_id) if r.claim_id else None,
                risk_type=r.risk_type,
                risk_level=r.risk_level,
                description=r.description,
                affects_core_answer=r.affects_core_answer,
                resolved_by_evidence=r.resolved_by_evidence,
                penalty=float(r.penalty),
                detected_by=r.detected_by,
            )
            for r in risks
        ],
        trust_score_breakdown=_trust_score_breakdown(trust_score),
        source_summary=SourceSummary(**final_result.source_summary),
        claim_distribution=final_result.claim_distribution,
        claim_evidence_relations=final_result.claim_evidence_relations,
        final_result=FinalResultObject(
            summary=final_result.summary,
            final_answer=final_result.final_answer,
            cautions=final_result.cautions,
            citations=[CitationObject(**c) for c in final_result.citations],
            final_answer_mode=final_result.final_answer_mode,
            cross_review_mode=final_result.cross_review_mode,
            judge_provider=final_result.judge_provider,
            judge_model=final_result.judge_model,
            judge_attempts=final_result.judge_attempts,
            fallback_reason=final_result.fallback_reason,
        ),
        created_at=question.created_at,
        completed_at=question.completed_at,
    )
