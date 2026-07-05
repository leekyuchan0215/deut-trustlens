import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class Evidence(CreatedAtMixin, Base):
    __tablename__ = "evidences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("search_documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True
    )
    deterministic_check_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deterministic_checks.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    searched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    relation: Mapped[str] = mapped_column(String(20), nullable=False)
    keyword_score: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)
    vector_score: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)
    hybrid_score: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)
    source_quality_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    directness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    support_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "document_id IS NOT NULL OR deterministic_check_id IS NOT NULL",
            name="ck_evidences_source",
        ),
        CheckConstraint(
            "relation IN ('support','contradict','neutral')", name="ck_evidences_relation"
        ),
        CheckConstraint(
            "(keyword_score IS NULL OR keyword_score BETWEEN 0 AND 1)"
            " AND (vector_score IS NULL OR vector_score BETWEEN 0 AND 1)"
            " AND (hybrid_score IS NULL OR hybrid_score BETWEEN 0 AND 1)",
            name="ck_evidences_search_scores",
        ),
        CheckConstraint(
            "source_quality_score BETWEEN 0 AND 100"
            " AND directness_score BETWEEN 0 AND 100"
            " AND support_score BETWEEN 0 AND 100",
            name="ck_evidences_quality_scores",
        ),
        Index("idx_evidences_question", "question_id"),
        Index("idx_evidences_claim", "claim_id"),
        Index("idx_evidences_hybrid_score", "claim_id", "hybrid_score"),
        Index("idx_evidences_relation", "claim_id", "relation"),
        Index("idx_evidences_source_type", "source_type"),
    )
