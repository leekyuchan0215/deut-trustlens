import uuid

from sqlalchemy import Computed, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class DocumentChunk(CreatedAtMixin, Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("search_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', COALESCE(content, ''))", persisted=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_index"
        ),
        UniqueConstraint(
            "document_id", "chunk_hash", name="uq_document_chunks_document_hash"
        ),
        Index("idx_document_chunks_document", "document_id"),
        Index("idx_document_chunks_search_vector", "search_vector", postgresql_using="gin"),
        Index("idx_document_chunks_hash", "chunk_hash"),
    )
