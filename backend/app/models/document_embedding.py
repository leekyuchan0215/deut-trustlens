import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin

EMBEDDING_DIMENSION = 1536


class DocumentEmbedding(CreatedAtMixin, Base):
    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    embedding_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(150), nullable=False)
    dimension: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=str(EMBEDDING_DIMENSION)
    )
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    __table_args__ = (
        CheckConstraint(
            f"dimension = {EMBEDDING_DIMENSION}", name="ck_document_embeddings_dimension"
        ),
        Index("idx_document_embeddings_chunk", "chunk_id"),
        Index(
            "idx_document_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
