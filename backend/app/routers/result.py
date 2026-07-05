from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.uuid_utils import parse_question_id
from app.db.session import get_db
from app.models import Question
from app.schemas.result import ResultDetailResponse, ResultSummaryResponse
from app.services.result_builder import build_result_detail, build_result_summary

router = APIRouter(tags=["result"])


def _get_completed_question(db: Session, question_id: str) -> Question:
    question = db.get(Question, parse_question_id(question_id))
    if question is None:
        raise ApiError(
            code="QUESTION_NOT_FOUND",
            message="요청한 분석 기록을 찾을 수 없습니다.",
            status_code=404,
        )
    if question.status == "failed":
        raise ApiError(
            code="ANALYSIS_FAILED",
            message=question.error_message or "분석이 실패했습니다.",
            status_code=409,
        )
    if question.status != "completed":
        raise ApiError(
            code="RESULT_NOT_READY",
            message="아직 결과가 준비되지 않았습니다.",
            status_code=409,
        )
    return question


@router.get("/api/result/{question_id}", response_model=ResultSummaryResponse)
def get_result_summary(question_id: str, db: Session = Depends(get_db)) -> ResultSummaryResponse:
    question = _get_completed_question(db, question_id)
    return build_result_summary(db, question)


@router.get("/api/result/{question_id}/detail", response_model=ResultDetailResponse)
def get_result_detail(question_id: str, db: Session = Depends(get_db)) -> ResultDetailResponse:
    question = _get_completed_question(db, question_id)
    return build_result_detail(db, question)
