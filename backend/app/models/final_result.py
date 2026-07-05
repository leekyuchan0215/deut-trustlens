import uuid

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class FinalResult(TimestampMixin, Base):
    __tablename__ = "final_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    final_answer: Mapped[str] = mapped_column(Text, nullable=False)
    cautions: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    citations: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    key_issues: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    cross_review: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source_summary: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    claim_distribution: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    claim_evidence_relations: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    final_answer_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    cross_review_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    judge_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    judge_model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    judge_attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )
    fallback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1.1")

    __table_args__ = (
        CheckConstraint("judge_attempts >= 0", name="ck_final_results_judge_attempts"),
    )
