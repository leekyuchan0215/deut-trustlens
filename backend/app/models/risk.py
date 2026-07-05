import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class Risk(CreatedAtMixin, Base):
    __tablename__ = "risks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=True
    )
    risk_key: Mapped[str] = mapped_column(String(150), nullable=False)
    risk_type: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affects_core_answer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    resolved_by_evidence: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    penalty: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    detected_by: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("question_id", "risk_key", name="uq_risks_question_key"),
        CheckConstraint(
            "risk_type IN ('hallucination','source_credibility',"
            "'outdated_information','contradiction')",
            name="ck_risks_type",
        ),
        CheckConstraint("risk_level IN ('low','medium','high')", name="ck_risks_level"),
        CheckConstraint("penalty BETWEEN 0 AND 40", name="ck_risks_penalty"),
        Index("idx_risks_question", "question_id"),
        Index("idx_risks_claim", "claim_id"),
        Index("idx_risks_level", "risk_level"),
    )
