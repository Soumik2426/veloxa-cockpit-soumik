import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IngestionJob(Base):

    __tablename__ = "ingestion_job"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    source_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_connection.id"),
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    trigger_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="MANUAL"
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    discovered_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    processed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
