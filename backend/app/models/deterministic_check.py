import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class DeterministicCheck(CreatedAtMixin, Base):
    __tablename__ = "deterministic_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    check_type: Mapped[str] = mapped_column(String(40), nullable=False)
    input_expression: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_claimed_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False)
    verification_confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    verification_reason: Mapped[str] = mapped_column(Text, nullable=False)
    execution_detail: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    limitations: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    __table_args__ = (
        CheckConstraint(
            "check_type IN ('calculator','unit_conversion','base_conversion',"
            "'logic_evaluation','formula','safe_code_execution','rule_based')",
            name="ck_deterministic_checks_type",
        ),
        CheckConstraint(
            "verification_status IN ('verified','weak_evidence','unsupported','contradicted')",
            name="ck_deterministic_checks_status",
        ),
        CheckConstraint(
            "verification_confidence BETWEEN 0 AND 100",
            name="ck_deterministic_confidence",
        ),
        Index("idx_deterministic_checks_question", "question_id"),
        Index("idx_deterministic_checks_claim", "claim_id"),
        Index("idx_deterministic_checks_passed", "check_passed"),
    )
