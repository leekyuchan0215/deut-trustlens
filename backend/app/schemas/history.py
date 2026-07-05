from datetime import datetime

from pydantic import BaseModel


class HistoryItem(BaseModel):
    question_id: str
    question: str
    answer_purpose: str
    question_type: str | None = None
    verification_basis: str | None = None
    status: str
    providers: list[str]
    model_names: list[str]
    trust_score: float | None = None
    grade: str | None = None
    summary: str | None = None
    tags: list[str]
    created_at: datetime
    completed_at: datetime | None = None


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    limit: int
    offset: int
