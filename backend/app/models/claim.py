import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Claim(TimestampMixin, Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    display_id: Mapped[str] = mapped_column(String(20), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_claim: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(40), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False)
    verification_basis: Mapped[str] = mapped_column(String(40), nullable=False)
    source_models: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    consensus_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    consensus_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="pending"
    )
    verification_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    verification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    direct_evidence_strength: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cross_source_agreement: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    positive_factors: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    deductions: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    limitations: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    question: Mapped["Question"] = relationship(back_populates="claims")

    __table_args__ = (
        UniqueConstraint("question_id", "display_id", name="uq_claims_question_display_id"),
        CheckConstraint("importance IN ('core','supporting')", name="ck_claims_importance"),
        CheckConstraint(
            "verification_status IN ('pending','verified','weak_evidence','unsupported','contradicted')",
            name="ck_claims_verification_status",
        ),
        CheckConstraint(
            "consensus_score IS NULL OR consensus_score BETWEEN 0 AND 100",
            name="ck_claims_consensus_score",
        ),
        CheckConstraint(
            "verification_confidence IS NULL OR verification_confidence BETWEEN 0 AND 100",
            name="ck_claims_verification_confidence",
        ),
        CheckConstraint(
            "direct_evidence_strength IS NULL OR direct_evidence_strength BETWEEN 0 AND 100",
            name="ck_claims_direct_evidence_strength",
        ),
        CheckConstraint(
            "cross_source_agreement IS NULL OR cross_source_agreement BETWEEN 0 AND 100",
            name="ck_claims_cross_source_agreement",
        ),
        Index("idx_claims_question", "question_id"),
        Index("idx_claims_importance", "question_id", "importance"),
        Index("idx_claims_verification_status", "question_id", "verification_status"),
        Index("idx_claims_verification_basis", "question_id", "verification_basis"),
        Index("idx_claims_source_models_gin", "source_models", postgresql_using="gin"),
    )
