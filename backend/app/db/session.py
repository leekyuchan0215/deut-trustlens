from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
# expire_on_commit=False: pipelines hold ORM objects across many short
# commits (per-stage progress updates) and read their attributes afterward,
# including from worker threads during parallel LLM calls. With the default
# (True), any attribute access after a commit triggers an implicit SELECT —
# unsafe when that access happens off the thread that owns the Session.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
