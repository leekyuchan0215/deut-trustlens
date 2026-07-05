from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models import Question
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services import mock_pipeline
from app.services.question_analysis import classify_question, extract_keywords

router = APIRouter(tags=["analyze"])


@router.post("/api/analyze", response_model=AnalyzeResponse, status_code=202)
def create_analysis(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    settings = get_settings()
    if not settings.use_mock:
        raise ApiError(
            code="REAL_MODE_NOT_IMPLEMENTED",
            message="Real Mode는 아직 구현되지 않았습니다. USE_MOCK=true로 실행해 주세요.",
            status_code=503,
        )

    question_type, verification_basis = classify_question(payload.question)
    keywords = extract_keywords(payload.question)

    question = Question(
        original_question=payload.original_question,
        refined_question=payload.refined_question,
        selected_question=payload.question,
        answer_purpose=payload.answer_purpose,
        question_type=question_type,
        verification_basis=verification_basis,
        suggested_keywords=keywords,
        tags=keywords[:2],
        status="queued",
        current_stage="question_analysis",
        display_stage="question_analysis",
        progress_percent=0,
        stage_details=[],
        execution_mode="mock",
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    background_tasks.add_task(mock_pipeline.run_pipeline, str(question.id))

    return AnalyzeResponse(
        question_id=str(question.id),
        status=question.status,
        current_stage=question.current_stage,
        display_stage=question.display_stage,
        progress_percent=question.progress_percent,
        message="검증 작업이 생성되었습니다.",
        created_at=question.created_at,
    )
