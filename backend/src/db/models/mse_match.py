"""MSE-SNP match results model."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Float, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class MatchStatus(str, Enum):
    SUGGESTED = "suggested"
    SELECTED = "selected"
    REJECTED = "rejected"


class MSEMatch(Base):
    __tablename__ = "mse_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mses.id"), nullable=False
    )
    snp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("snps.id"), nullable=False
    )

    # Scoring
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    category_overlap_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    geography_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transaction_type_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    capacity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    status: Mapped[str] = mapped_column(
        SAEnum(MatchStatus, name="match_status"),
        default=MatchStatus.SUGGESTED.value,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    mse: Mapped["MSE"] = relationship("MSE", back_populates="snp_matches")
    snp: Mapped["SNP"] = relationship("SNP", back_populates="mse_matches")
