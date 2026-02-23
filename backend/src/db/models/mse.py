"""MSE (Micro & Small Enterprise) profile model."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class MajorActivity(str, Enum):
    MANUFACTURING = "manufacturing"
    SERVICES = "services"


class TransactionType(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    BOTH = "both"


class OnboardingStatus(str, Enum):
    REGISTERED = "registered"
    PROFILE_COMPLETE = "profile_complete"
    CATALOGUE_READY = "catalogue_ready"
    SNP_SELECTED = "snp_selected"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    LIVE = "live"


class MSE(Base):
    __tablename__ = "mses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )

    # Udyam details
    udyam_number: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nic_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    major_activity: Mapped[str | None] = mapped_column(
        SAEnum(MajorActivity, name="major_activity"), nullable=True
    )

    # Location
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Business size
    turnover: Mapped[float | None] = mapped_column(Float, nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Commerce preferences
    transaction_type: Mapped[str | None] = mapped_column(
        SAEnum(TransactionType, name="transaction_type"), nullable=True
    )
    target_states: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Contact
    whatsapp_number: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # Onboarding tracking
    onboarding_status: Mapped[str] = mapped_column(
        SAEnum(OnboardingStatus, name="onboarding_status"),
        default=OnboardingStatus.REGISTERED.value,
        nullable=False,
    )
    selected_snp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("snps.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mse_profile")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="mse")
    snp_matches: Mapped[list["MSEMatch"]] = relationship("MSEMatch", back_populates="mse")
    selected_snp: Mapped["SNP | None"] = relationship("SNP", foreign_keys=[selected_snp_id])
