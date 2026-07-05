import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class TrustScore(TimestampMixin, Base):
    __tablename__ = "trust_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    evidence_support_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    source_quality_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    consensus_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    logic_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    freshness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    base_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    contradiction_penalty: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="0"
    )
    risk_penalty: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    total_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    score_reasons: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    strengths: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    deductions: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    calculation_detail: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    formula_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1.1")

    __table_args__ = (
        CheckConstraint(
            "evidence_support_score BETWEEN 0 AND 100"
            " AND source_quality_score BETWEEN 0 AND 100"
            " AND consensus_score BETWEEN 0 AND 100"
            " AND logic_score BETWEEN 0 AND 100"
            " AND freshness_score BETWEEN 0 AND 100"
            " AND base_score BETWEEN 0 AND 100"
            " AND total_score BETWEEN 0 AND 100",
            name="ck_trust_scores_components",
        ),
        CheckConstraint(
            "contradiction_penalty >= 0 AND risk_penalty >= 0",
            name="ck_trust_scores_penalties",
        ),
        Index("idx_trust_scores_total_score", "total_score"),
    )
