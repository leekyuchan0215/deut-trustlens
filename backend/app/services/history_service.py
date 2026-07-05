from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import AIResponse, FinalResult, Question, TrustScore
from app.schemas.history import HistoryItem, HistoryResponse

_SORT_MAP = {
    "newest": (Question.created_at, "desc"),
    "oldest": (Question.created_at, "asc"),
    "score_high": (TrustScore.total_score, "desc"),
    "score_low": (TrustScore.total_score, "asc"),
}


def get_history(
    db: Session,
    search: str | None,
    status: str | None,
    min_score: float | None,
    max_score: float | None,
    provider: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> HistoryResponse:
    query = select(Question).outerjoin(TrustScore, TrustScore.question_id == Question.id)

    if search:
        like = f"%{search}%"
        query = query.where(
            or_(Question.selected_question.ilike(like), Question.original_question.ilike(like))
        )
    if status:
        query = query.where(Question.status == status)
    if min_score is not None:
        query = query.where(TrustScore.total_score >= min_score)
    if max_score is not None:
        query = query.where(TrustScore.total_score <= max_score)
    if provider:
        query = query.where(
            Question.id.in_(
                select(AIResponse.question_id).where(
                    AIResponse.provider == provider, AIResponse.status == "success"
                )
            )
        )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    column, direction = _SORT_MAP.get(sort, _SORT_MAP["newest"])
    query = query.order_by(column.desc() if direction == "desc" else column.asc())
    query = query.limit(limit).offset(offset)

    questions = db.execute(query).scalars().unique().all()

    items = []
    for question in questions:
        trust_score = db.execute(
            select(TrustScore).where(TrustScore.question_id == question.id)
        ).scalar_one_or_none()
        final_result = db.execute(
            select(FinalResult).where(FinalResult.question_id == question.id)
        ).scalar_one_or_none()
        successful_responses = db.execute(
            select(AIResponse).where(
                AIResponse.question_id == question.id, AIResponse.status == "success"
            )
        ).scalars().all()

        items.append(
            HistoryItem(
                question_id=str(question.id),
                question=question.selected_question,
                answer_purpose=question.answer_purpose,
                question_type=question.question_type,
                verification_basis=question.verification_basis,
                status=question.status,
                providers=[r.provider for r in successful_responses],
                model_names=[r.model_name for r in successful_responses],
                trust_score=float(trust_score.total_score) if trust_score else None,
                grade=trust_score.grade if trust_score else None,
                summary=final_result.summary if final_result else None,
                tags=question.tags,
                created_at=question.created_at,
                completed_at=question.completed_at,
            )
        )

    return HistoryResponse(items=items, total=total, limit=limit, offset=offset)
