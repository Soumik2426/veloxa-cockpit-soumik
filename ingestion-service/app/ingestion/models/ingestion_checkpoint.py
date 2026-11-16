import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IngestionCheckpoint(Base):

    __tablename__ = "ingestion_checkpoint"

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

    checkpoint_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    checkpoint_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    checkpoint_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
