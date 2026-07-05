from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.agents.question_agent import analyze_question as analyze_question_llm
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Question
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services import mock_pipeline, real_pipeline
from app.services.question_analysis import classify_question, extract_keywords

router = APIRouter(tags=["analyze"])


@router.post("/api/analyze", response_model=AnalyzeResponse, status_code=202)
def create_analysis(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    settings = get_settings()
    use_mock = settings.use_mock

    if use_mock:
        question_type, verification_basis = classify_question(payload.question)
        keywords = extract_keywords(payload.question)
    else:
        analysis, _mode = analyze_question_llm(payload.question, payload.answer_purpose)
        question_type = analysis.question_type
        verification_basis = analysis.verification_basis
        keywords = analysis.suggested_keywords

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
        execution_mode="mock" if use_mock else "real",
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    pipeline = mock_pipeline if use_mock else real_pipeline
    background_tasks.add_task(pipeline.run_pipeline, str(question.id))

    return AnalyzeResponse(
        question_id=str(question.id),
        status=question.status,
        current_stage=question.current_stage,
        display_stage=question.display_stage,
        progress_percent=question.progress_percent,
        message="검증 작업이 생성되었습니다.",
        created_at=question.created_at,
    )
