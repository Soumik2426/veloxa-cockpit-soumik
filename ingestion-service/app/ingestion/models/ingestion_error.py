import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IngestionError(Base):

    __tablename__ = "ingestion_error"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ingestion_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_job.id"),
        nullable=False,
        index=True
    )

    ingestion_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_file.id"),
        nullable=True,
        index=True
    )

    error_stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    error_details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
