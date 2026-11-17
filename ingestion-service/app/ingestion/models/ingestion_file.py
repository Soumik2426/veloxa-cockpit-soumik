import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    BigInteger,
    Integer,
    UniqueConstraint,
    CheckConstraint,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IngestionFile(Base):

    __tablename__ = "ingestion_file"

    __table_args__ = (
        UniqueConstraint(
            "source_connection_id",
            "relative_path",
            "checksum",
            name="uq_ingestion_file_source_path_checksum"
        ),
        CheckConstraint(
            "file_size >= 0",
            name="ck_ingestion_file_file_size"
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_ingestion_file_version"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    source_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_connection.id"),
        nullable=False,
        index=True
    )

    ingestion_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_job.id"),
        nullable=True,
        index=True
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    relative_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    file_extension: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UNKNOWN",
        server_default=text("'UNKNOWN'")
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DISCOVERED",
        server_default=text("'DISCOVERED'")
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1")
    )

    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
