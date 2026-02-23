"""SNP (Seller Network Participant) model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class SNP(Base):
    __tablename__ = "snps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    platform_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ONDC capabilities
    ondc_live_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supported_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    supported_states: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    b2b: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    b2c: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Performance metrics
    avg_onboarding_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    capability_score: Mapped[float] = mapped_column(Float, default=75.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    mse_matches: Mapped[list["MSEMatch"]] = relationship("MSEMatch", back_populates="snp")
