from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.history import HistoryResponse
from app.services.history_service import get_history

router = APIRouter(tags=["history"])


@router.get("/api/history", response_model=HistoryResponse)
def list_history(
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    max_score: float | None = Query(default=None),
    provider: str | None = Query(default=None),
    sort: str = Query(default="newest"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    return get_history(
        db=db,
        search=search,
        status=status,
        min_score=min_score,
        max_score=max_score,
        provider=provider,
        sort=sort,
        limit=limit,
        offset=offset,
    )
