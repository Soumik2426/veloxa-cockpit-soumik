import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SourceConnection(Base):

    __tablename__ = "source_connection"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    connector_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    config: Mapped[dict] = mapped_column(
        "configuration",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb")
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACTIVE",
        server_default=text("'ACTIVE'")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        nullable=False
    )
