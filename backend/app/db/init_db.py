from sqlalchemy import text
from sqlalchemy.orm import Session


def check_db_connected(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def check_pgvector_enabled(db: Session) -> bool:
    try:
        result = db.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).first()
        return result is not None
    except Exception:
        return False
