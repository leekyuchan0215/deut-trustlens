from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.init_db import check_db_connected, check_pgvector_enabled
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    db_connected = check_db_connected(db)
    pgvector_enabled = check_pgvector_enabled(db) if db_connected else False
    return HealthResponse(
        status="ok" if db_connected else "degraded",
        service="TrustLens API",
        environment=settings.app_env,
        use_mock=settings.use_mock,
        database_connected=db_connected,
        pgvector_enabled=pgvector_enabled,
    )
