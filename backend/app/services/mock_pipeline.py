"""Mock analysis pipeline: advances a Question through the pipeline stages
and persists all analysis artifacts, using the same table structure Real
Mode will use. Runs in a background thread started from the /api/analyze
and /api/reanalyze routers.
"""
import logging
import random
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Claim, FinalResult, Question, TrustScore
from app.services import mock_data_generator as gen
from app.services.pipeline_common import advance_stage as _advance
from app.services.pipeline_common import mark_failed as _mark_failed
from app.services.trust_score_calculator import ClaimScoreInput, calculate_model_score, calculate_trust_score
from app.utils.enums import PIPELINE_STEPS

logger = logging.getLogger("trustlens.mock_pipeline")


def _sleep_stage() -> None:
    time.sleep(random.uniform(0.08, 0.2))


def run_pipeline(question_id: str) -> None:
    db = SessionLocal()
    try:
        _run(db, question_id)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("mock pipeline failed for question_id=%s", question_id)
        db.rollback()
        _mark_failed(db, question_id, "MOCK_PIPELINE_ERROR", "Mock 분석 처리 중 오류가 발생했습니다.")
    finally:
        db.close()


def _run(db: Session, question_id: str) -> None:
    question = db.get(Question, question_id)
    if question is None:
        return

    question.status = "processing"
    question.started_at = datetime.now(timezone.utc)
    db.add(question)
    db.commit()

    ai_responses: list = []
    claims: list[Claim] = []
    deterministic_checks: list = []
    documents: list = []
    chunks: list = []
    evidences: list = []
    risks: list = []
    cross_review: dict = {}

    for stage, display_stage, percent in PIPELINE_STEPS:
        started = time.monotonic()
        _sleep_stage()

        if stage == "ai_generation":
            ai_responses = gen.build_ai_responses(question)
            db.add_all(ai_responses)
            db.flush()

        elif stage == "claim_consolidation":
            claims = gen.build_claims(question)
            db.add_all(claims)
            db.flush()

        elif stage == "deterministic_verification":
            deterministic_checks = gen.build_deterministic_checks(claims)
            db.add_all(deterministic_checks)
            db.flush()

        elif stage == "document_storage":
            documents = gen.build_search_documents(question)
            db.add_all(documents)
            db.flush()

        elif stage == "embedding":
            chunks = gen.build_chunks(documents)
            db.add_all(chunks)
            db.flush()
            embeddings = gen.build_embeddings(chunks, documents)
            db.add_all(embeddings)
            db.flush()

        elif stage == "evidence_selection":
            evidences = gen.build_evidences_and_verify_claims(
                claims, documents, chunks, deterministic_checks
            )
            db.add_all(evidences)
            db.flush()

        elif stage == "risk_analysis":
            risks = gen.build_risks(question, claims, evidences)
            db.add_all(risks)
            cross_review = gen.build_cross_review(claims)
            db.flush()

        elif stage == "result_storage":
            _finalize(db, question, ai_responses, claims, evidences, risks, cross_review, documents, deterministic_checks)

        duration_ms = round((time.monotonic() - started) * 1000)
        _advance(db, question, stage, display_stage, percent, duration_ms)

    question.status = "completed"
    question.completed_at = datetime.now(timezone.utc)
    db.add(question)
    db.commit()


def _finalize(
    db: Session,
    question: Question,
    ai_responses: list,
    claims: list[Claim],
    evidences: list,
    risks: list,
    cross_review: dict,
    documents: list,
    deterministic_checks: list,
) -> None:
    claim_inputs = []
    evidence_quality_by_claim: dict = {}
    for evidence in evidences:
        evidence_quality_by_claim.setdefault(evidence.claim_id, []).append(
            float(evidence.source_quality_score)
        )

    for claim in claims:
        claim_inputs.append(
            ClaimScoreInput(
                importance=claim.importance,
                verification_status=claim.verification_status,
                consensus_score=float(claim.consensus_score) if claim.consensus_score is not None else None,
                deterministic_verified=(
                    claim.verification_basis == "deterministic" and claim.verification_status == "verified"
                ),
                evidence_source_quality=evidence_quality_by_claim.get(claim.id, []),
            )
        )

    logic_issue_count = len(cross_review.get("logic_issues", []))
    outdated_risk_count = len([r for r in risks if r.risk_type == "outdated_information"])
    contradiction_penalty = sum(float(r.penalty) for r in risks if r.risk_type == "contradiction")
    risk_penalty = sum(float(r.penalty) for r in risks if r.risk_type != "contradiction")

    score = calculate_trust_score(
        claims=claim_inputs,
        contradiction_penalty=contradiction_penalty,
        risk_penalty=risk_penalty,
        logic_issue_count=logic_issue_count,
        outdated_risk_count=outdated_risk_count,
        question_type=question.question_type or "general",
        verification_basis=question.verification_basis or "mixed",
    )

    claims_by_provider: dict[str, list[ClaimScoreInput]] = {}
    for claim, claim_input in zip(claims, claim_inputs):
        for provider in claim.source_models:
            claims_by_provider.setdefault(provider, []).append(claim_input)

    for response in ai_responses:
        model_score, model_grade, reason = calculate_model_score(
            claims_by_provider.get(response.provider, [])
        )
        response.model_score = model_score
        response.model_grade = model_grade
        response.model_score_reason = reason
        response.model_score_detail = {"claim_count": len(claims_by_provider.get(response.provider, []))}
        db.add(response)

    trust_score_row = TrustScore(
        question_id=question.id,
        evidence_support_score=score["evidence_support_score"],
        source_quality_score=score["source_quality_score"],
        consensus_score=score["consensus_score"],
        logic_score=score["logic_score"],
        freshness_score=score["freshness_score"],
        base_score=score["base_score"],
        contradiction_penalty=score["contradiction_penalty"],
        risk_penalty=score["risk_penalty"],
        total_score=score["total_score"],
        grade=score["grade"],
        score_reasons=score["score_reasons"],
        strengths=score["strengths"],
        deductions=score["deductions"],
        calculation_detail=score["calculation_detail"],
    )
    db.add(trust_score_row)

    verified_core = [c for c in claims if c.importance == "core" and c.verification_status == "verified"]
    weak_or_unsupported = [
        c for c in claims if c.verification_status in ("weak_evidence", "unsupported", "contradicted")
    ]

    core_summary = "; ".join(c.claim_text for c in verified_core) or "핵심 Claim 검증 결과가 충분하지 않습니다."
    final_answer = (
        f"[MOCK] '{question.selected_question}'에 대한 최종 검증 답변입니다. "
        f"검증된 핵심 주장: {core_summary}"
    )
    cautions = [
        f"{c.display_id}은(는) 근거가 제한적이므로 참고용으로만 사용하세요." for c in weak_or_unsupported
    ]

    citations = []
    for evidence in evidences:
        if evidence.relation != "support":
            continue
        citations.append(
            {
                "evidence_id": str(evidence.id),
                "title": evidence.title,
                "url": evidence.url,
            }
        )

    claim_distribution = {
        "verified": len([c for c in claims if c.verification_status == "verified"]),
        "weak_evidence": len([c for c in claims if c.verification_status == "weak_evidence"]),
        "unsupported": len([c for c in claims if c.verification_status == "unsupported"]),
        "contradicted": len([c for c in claims if c.verification_status == "contradicted"]),
    }

    claim_evidence_relations = [
        {"claim_id": str(e.claim_id), "evidence_id": str(e.id), "relation": e.relation} for e in evidences
    ]

    source_summary = {
        "total_documents": len(documents),
        "used_evidences": len(evidences),
        "web_documents": len([d for d in documents if d.source_type not in ("official", "government")]),
        "academic_papers": len([d for d in documents if d.source_type in ("academic", "paper")]),
        "technical_blogs": len([d for d in documents if d.source_type == "blog"]),
        "official_documents": len([d for d in documents if d.source_type == "official"]),
        "government_sources": len([d for d in documents if d.source_type == "government"]),
        "deterministic_checks": len(deterministic_checks),
    }

    final_result_row = FinalResult(
        question_id=question.id,
        summary=f"[MOCK] '{question.selected_question}'에 대한 핵심 요약입니다.",
        final_answer=final_answer,
        cautions=cautions,
        citations=citations,
        key_issues=[mp["description"] for mp in cross_review.get("missing_points", [])][:3],
        cross_review=cross_review,
        source_summary=source_summary,
        claim_distribution=claim_distribution,
        claim_evidence_relations=claim_evidence_relations,
        final_answer_mode="mock",
        cross_review_mode="mock",
        judge_provider=None,
        judge_model=None,
        judge_attempts=0,
        fallback_reason=None,
    )
    db.add(final_result_row)
    db.flush()
