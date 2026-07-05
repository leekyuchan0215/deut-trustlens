import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, SmallInteger, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    original_question: Mapped[str] = mapped_column(Text, nullable=False)
    refined_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    question_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    verification_basis: Mapped[str | None] = mapped_column(String(40), nullable=True)
    suggested_keywords: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="queued")
    current_stage: Mapped[str] = mapped_column(
        String(60), nullable=False, server_default="question_analysis"
    )
    display_stage: Mapped[str] = mapped_column(
        String(60), nullable=False, server_default="question_analysis"
    )
    progress_percent: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="0"
    )
    stage_details: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    estimated_remaining_seconds: Mapped[int | None] = mapped_column(nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False, server_default="mock")
    reanalysis_of_question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ai_responses: Mapped[list["AIResponse"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    claims: Mapped[list["Claim"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "answer_purpose IN ('fact_check','concept_understanding','decision_support',"
            "'evidence_focused','risk_analysis')",
            name="ck_questions_answer_purpose",
        ),
        CheckConstraint(
            "status IN ('queued','processing','completed','failed')",
            name="ck_questions_status",
        ),
        CheckConstraint(
            "progress_percent BETWEEN 0 AND 100", name="ck_questions_progress"
        ),
        CheckConstraint(
            "execution_mode IN ('mock','real')", name="ck_questions_execution_mode"
        ),
        Index("idx_questions_status", "status"),
        Index("idx_questions_created_at", "created_at"),
        Index("idx_questions_answer_purpose", "answer_purpose"),
        Index("idx_questions_question_type", "question_type"),
        Index("idx_questions_verification_basis", "verification_basis"),
        Index("idx_questions_reanalysis", "reanalysis_of_question_id"),
        Index("idx_questions_tags_gin", "tags", postgresql_using="gin"),
    )
