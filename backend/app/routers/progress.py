from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.uuid_utils import parse_question_id
from app.db.session import get_db
from app.models import Question
from app.schemas.progress import ProgressResponse
from app.services.progress_builder import build_progress_response

router = APIRouter(tags=["progress"])


@router.get("/api/progress/{question_id}", response_model=ProgressResponse)
def get_progress(question_id: str, db: Session = Depends(get_db)) -> ProgressResponse:
    question = db.get(Question, parse_question_id(question_id))
    if question is None:
        raise ApiError(
            code="QUESTION_NOT_FOUND",
            message="요청한 분석 기록을 찾을 수 없습니다.",
            status_code=404,
        )
    return build_progress_response(db, question)
