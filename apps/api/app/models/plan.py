from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Feature Flags
    has_draft_live: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_center_sports: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_bookings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_marketplace: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    subscriptions = relationship("OrgSubscription", back_populates="plan", cascade="all, delete-orphan")


class OrgSubscription(Base):
    __tablename__ = "org_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization")
    plan = relationship("Plan", back_populates="subscriptions")
