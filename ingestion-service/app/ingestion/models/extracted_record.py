import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExtractedRecord(Base):

    __tablename__ = "extracted_record"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ingestion_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_file.id"),
        nullable=False,
        index=True
    )

    record_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    record_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    source_locator: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    extracted_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    extraction_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    extraction_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SUCCESS"
    )

    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
