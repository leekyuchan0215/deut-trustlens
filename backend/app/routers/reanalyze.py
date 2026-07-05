from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.uuid_utils import parse_question_id
from app.db.session import get_db
from app.models import Question
from app.schemas.analyze import ReanalyzeRequest, ReanalyzeResponse
from app.services import mock_pipeline

router = APIRouter(tags=["reanalyze"])


@router.post("/api/reanalyze/{question_id}", response_model=ReanalyzeResponse, status_code=202)
def reanalyze(
    question_id: str,
    payload: ReanalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ReanalyzeResponse:
    settings = get_settings()
    if not settings.use_mock:
        raise ApiError(
            code="REAL_MODE_NOT_IMPLEMENTED",
            message="Real Mode는 아직 구현되지 않았습니다. USE_MOCK=true로 실행해 주세요.",
            status_code=503,
        )

    original = db.get(Question, parse_question_id(question_id))
    if original is None:
        raise ApiError(
            code="QUESTION_NOT_FOUND",
            message="요청한 분석 기록을 찾을 수 없습니다.",
            status_code=404,
        )

    answer_purpose = payload.answer_purpose if payload and payload.answer_purpose else original.answer_purpose

    new_question = Question(
        original_question=original.original_question,
        refined_question=original.refined_question,
        selected_question=original.selected_question,
        answer_purpose=answer_purpose,
        question_type=original.question_type,
        verification_basis=original.verification_basis,
        suggested_keywords=original.suggested_keywords,
        tags=original.tags,
        status="queued",
        current_stage="question_analysis",
        display_stage="question_analysis",
        progress_percent=0,
        stage_details=[],
        execution_mode="mock",
        reanalysis_of_question_id=original.id,
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    background_tasks.add_task(mock_pipeline.run_pipeline, str(new_question.id))

    return ReanalyzeResponse(
        original_question_id=str(original.id),
        question_id=str(new_question.id),
        status=new_question.status,
        current_stage=new_question.current_stage,
        display_stage=new_question.display_stage,
        progress_percent=new_question.progress_percent,
        message="재검증 작업이 생성되었습니다.",
        created_at=new_question.created_at,
    )
