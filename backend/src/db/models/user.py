"""User model — MSE / SNP / Admin portal users."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class UserRole(str, Enum):
    MSE = "mse"
    SNP = "snp"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[str] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.MSE.value
    )
    mobile: Mapped[str | None] = mapped_column(String(15), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    mse_profile: Mapped["MSE"] = relationship("MSE", back_populates="user", uselist=False)
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")
