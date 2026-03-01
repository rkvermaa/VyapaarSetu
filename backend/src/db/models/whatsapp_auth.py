"""WhatsApp auth model — stores Baileys credentials per bot session."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSON

from src.db.base import Base


class WhatsAppAuth(Base):
    """Stores Baileys WhatsApp auth credentials in the database."""

    __tablename__ = "whatsapp_auth"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="WhatsApp Bot")
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    creds: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    keys: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="disconnected"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def has_credentials(self) -> bool:
        """Check if this session has stored Baileys credentials."""
        return bool(self.creds and self.creds.get("me"))
