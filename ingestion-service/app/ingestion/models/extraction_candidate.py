import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExtractionCandidate(Base):

    __tablename__ = "extraction_candidate"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
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
        default=dict
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    review_required: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
