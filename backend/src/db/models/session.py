"""Chat session model."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class SessionType(str, Enum):
    GENERAL = "general"
    ONBOARDING = "onboarding"
    CATALOGUING = "cataloguing"
    MATCHING = "matching"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), default="web", nullable=False)
    session_type: Mapped[str] = mapped_column(
        SAEnum(SessionType, name="session_type"),
        default=SessionType.GENERAL.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(SessionStatus, name="session_status"),
        default=SessionStatus.ACTIVE.value,
        nullable=False,
    )
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="session")
