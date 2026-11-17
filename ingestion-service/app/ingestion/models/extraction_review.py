import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExtractionReview(Base):

    __tablename__ = "extraction_review"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    extraction_candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extraction_candidate.id"),
        nullable=False,
        index=True
    )

    reviewer: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    corrected_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )
