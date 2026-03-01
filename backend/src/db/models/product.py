"""Product / catalogue item model."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class ProductStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    LISTED = "listed"


class ProductSource(str, Enum):
    WEB = "web"
    WHATSAPP = "whatsapp"
    VOICE = "voice"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mses.id"), nullable=False
    )

    # Raw input
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI-generated structured data
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ondc_category_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Attributes as JSON (mrp, moq, material, hsn_code, etc.)
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Compliance
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    missing_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=ProductStatus.DRAFT.value, nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(20), default=ProductSource.WEB.value, nullable=False
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
    mse: Mapped["MSE"] = relationship("MSE", back_populates="products")
