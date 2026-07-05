from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIResponse, Claim, DeterministicCheck, Evidence, Question, SearchDocument
from app.schemas.progress import DisplayStep, ModelStatus, ProgressMetrics, ProgressResponse
from app.utils.enums import DISPLAY_STEP_ORDER

_MESSAGES = {
    "question_analysis": "질문을 분석하고 있습니다.",
    "ai_generation": "GPT·Claude·Gemini 답변을 생성하고 있습니다.",
    "claim_extraction": "Claim을 추출하고 통합하고 있습니다.",
    "evidence_search": "외부 근거를 검색하고 있습니다.",
    "hybrid_search": "Hybrid Search를 수행하고 있습니다.",
    "claim_verification": "Claim을 검증하고 있습니다.",
    "final_answer": "최종 답변을 생성하고 있습니다.",
}


def _build_display_steps(question: Question) -> list[DisplayStep]:
    completed_display_stages = {
        entry["display_stage"] for entry in question.stage_details if entry.get("status") == "completed"
    }
    duration_by_display_stage: dict[str, int] = {}
    for entry in question.stage_details:
        duration_by_display_stage.setdefault(entry["display_stage"], 0)
        duration_by_display_stage[entry["display_stage"]] += entry.get("duration_ms") or 0

    order = [stage for stage, _ in DISPLAY_STEP_ORDER]
    current_index = order.index(question.display_stage) if question.display_stage in order else -1

    steps = []
    for index, (stage, label) in enumerate(DISPLAY_STEP_ORDER):
        if question.status == "failed" and index == current_index:
            status = "failed"
        elif stage in completed_display_stages and (index < current_index or question.status == "completed"):
            status = "completed"
        elif index == current_index:
            status = "completed" if question.status == "completed" else "processing"
        elif index < current_index:
            status = "completed"
        else:
            status = "pending"
        steps.append(
            DisplayStep(
                stage=stage,
                label=label,
                status=status,
                duration_ms=duration_by_display_stage.get(stage) if status == "completed" else None,
            )
        )
    return steps


def build_progress_response(db: Session, question: Question) -> ProgressResponse:
    ai_responses = db.execute(
        select(AIResponse).where(AIResponse.question_id == question.id)
    ).scalars().all()
    model_statuses = [
        ModelStatus(
            provider=r.provider,
            model_name=r.model_name,
            status=r.status,
            latency_ms=r.latency_ms,
        )
        for r in ai_responses
    ]

    total_claims = db.execute(select(Claim).where(Claim.question_id == question.id)).scalars().all()
    verified_claims = [c for c in total_claims if c.verification_status == "verified"]
    deterministic_checks = db.execute(
        select(DeterministicCheck).where(DeterministicCheck.question_id == question.id)
    ).scalars().all()
    search_documents = db.execute(
        select(SearchDocument).where(SearchDocument.question_id == question.id)
    ).scalars().all()
    selected_evidences = db.execute(
        select(Evidence).where(Evidence.question_id == question.id)
    ).scalars().all()

    message = (
        question.error_message
        if question.status == "failed"
        else _MESSAGES.get(question.display_stage, "분석을 진행하고 있습니다.")
    )

    return ProgressResponse(
        question_id=str(question.id),
        status=question.status,
        current_stage=question.current_stage,
        display_stage=question.display_stage,
        progress_percent=question.progress_percent,
        message=message,
        estimated_remaining_seconds=question.estimated_remaining_seconds,
        display_steps=_build_display_steps(question),
        model_statuses=model_statuses,
        metrics=ProgressMetrics(
            total_claims=len(total_claims),
            verified_claims=len(verified_claims),
            deterministic_checks=len(deterministic_checks),
            search_documents=len(search_documents),
            selected_evidences=len(selected_evidences),
        ),
        error_message=question.error_message,
        updated_at=question.updated_at,
    )
