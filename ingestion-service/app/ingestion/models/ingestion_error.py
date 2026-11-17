import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IngestionError(Base):

    __tablename__ = "ingestion_error"

    __table_args__ = (
        CheckConstraint(
            "length(trim(error_message)) > 0",
            name="ck_ingestion_error_message_not_empty"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
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
        default=dict,
        server_default=text("'{}'::jsonb")
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )
