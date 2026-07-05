import uuid

from app.core.errors import ApiError


def parse_question_id(question_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(question_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise ApiError(
            code="QUESTION_NOT_FOUND",
            message="요청한 분석 기록을 찾을 수 없습니다.",
            status_code=404,
        ) from exc
