from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class BillingMode(str, enum.Enum):
    MEMBERSHIP = "MEMBERSHIP"
    PER_SESSION = "PER_SESSION"
    HYBRID = "HYBRID"


class BillingCycle(str, enum.Enum):
    MONTHLY = "MONTHLY"
    WEEKLY = "WEEKLY"
    CUSTOM_WEEKS = "CUSTOM_WEEKS"


class OrgBillingSettings(Base):
    __tablename__ = "org_billing_settings"
    __table_args__ = (UniqueConstraint("org_id", name="uq_org_billing_settings_org_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    billing_mode: Mapped[BillingMode] = mapped_column(
        Enum(BillingMode, name="billing_mode"),
        default=BillingMode.HYBRID,
        nullable=False,
    )

    cycle: Mapped[BillingCycle] = mapped_column(
        Enum(BillingCycle, name="billing_cycle"),
        default=BillingCycle.MONTHLY,
        nullable=False,
    )

    cycle_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    anchor_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    membership_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    session_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization")
