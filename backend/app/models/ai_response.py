import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AIResponse(TimestampMixin, Base):
    __tablename__ = "ai_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    model_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    model_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_score_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_score_detail: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped["Question"] = relationship(back_populates="ai_responses")

    __table_args__ = (
        UniqueConstraint("question_id", "provider", name="uq_ai_responses_question_provider"),
        CheckConstraint(
            "provider IN ('gpt','claude','gemini')", name="ck_ai_responses_provider"
        ),
        CheckConstraint(
            "status IN ('pending','success','failed','timeout')",
            name="ck_ai_responses_status",
        ),
        CheckConstraint(
            "model_score IS NULL OR model_score BETWEEN 0 AND 100",
            name="ck_ai_responses_model_score",
        ),
        Index("idx_ai_responses_question", "question_id"),
        Index("idx_ai_responses_provider_status", "provider", "status"),
        Index("idx_ai_responses_model_score", "model_score"),
    )
