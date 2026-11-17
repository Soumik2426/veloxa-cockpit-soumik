import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    Float,
    text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExtractionCandidate(Base):

    __tablename__ = "extraction_candidate"

    __table_args__ = (
        CheckConstraint(
            "confidence_score IS NULL OR "
            "confidence_score BETWEEN 0 AND 1",
            name="ck_extraction_candidate_confidence_score"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    extracted_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extracted_record.id"),
        nullable=False,
        index=True
    )

    candidate_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    candidate_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb")
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'")
    )

    review_required: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
        nullable=False
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )
