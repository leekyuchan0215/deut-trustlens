import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class SearchDocument(CreatedAtMixin, Base):
    __tablename__ = "search_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, server_default="unknown")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    searched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    search_query: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("question_id", "url", name="uq_search_documents_question_url"),
        CheckConstraint(
            "source_type IN ('official','government','academic','paper',"
            "'documentation','news','blog','community','unknown')",
            name="ck_search_documents_source_type",
        ),
        Index("idx_search_documents_question", "question_id"),
        Index("idx_search_documents_source_type", "source_type"),
        Index("idx_search_documents_published_at", "published_at"),
        Index("idx_search_documents_content_hash", "content_hash"),
    )
