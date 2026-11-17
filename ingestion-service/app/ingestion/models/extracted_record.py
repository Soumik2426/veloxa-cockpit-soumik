import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Float,
    text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExtractedRecord(Base):

    __tablename__ = "extracted_record"

    __table_args__ = (
        UniqueConstraint(
            "ingestion_file_id",
            "record_type",
            "record_key",
            name="uq_extracted_record_file_type_key"
        ),
        CheckConstraint(
            "confidence_score IS NULL OR "
            "confidence_score BETWEEN 0 AND 1",
            name="ck_extracted_record_confidence_score"
        ),
        CheckConstraint(
            "extraction_status IN ('SUCCESS', 'REJECTED')",
            name="ck_extracted_record_extraction_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
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
        default=dict,
        server_default=text("'{}'::jsonb")
    )

    extracted_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb")
    )

    extraction_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    extraction_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SUCCESS",
        server_default=text("'SUCCESS'")
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )
