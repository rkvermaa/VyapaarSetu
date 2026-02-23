"""ONDC Category taxonomy model (RET10-RET19)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class OndcCategory(Base):
    __tablename__ = "ondc_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. ONDC:RET16
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), default="retail", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # MSE types that typically sell in this category
    mse_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Attribute schemas
    required_attributes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    optional_attributes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # For RAG context
    example_products: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
