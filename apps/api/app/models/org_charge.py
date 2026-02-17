from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ChargeStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    VOID = "VOID"


class ChargeType(str, enum.Enum):
    MEMBERSHIP = "MEMBERSHIP"
    PER_SESSION = "PER_SESSION"


class OrgCharge(Base):
    __tablename__ = "org_charges"
    __table_args__ = (
        UniqueConstraint(
            "org_id",
            "org_member_id",
            "cycle_key",
            "type",
            name="uq_org_charges_org_member_cycle_type",
        ),
        Index("ix_org_charges_org_cycle", "org_id", "cycle_key"),
        Index("ix_org_charges_org_status", "org_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    org_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_members.id"), nullable=False, index=True
    )

    cycle_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    type: Mapped[ChargeType] = mapped_column(
        Enum(ChargeType, name="charge_type"),
        nullable=False,
    )

    status: Mapped[ChargeStatus] = mapped_column(
        Enum(ChargeStatus, name="charge_status"),
        default=ChargeStatus.PENDING,
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    ledger_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_entries.id"), nullable=True
    )

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization")
    org_member = relationship("OrgMember")
    ledger_entry = relationship("LedgerEntry")
    created_by = relationship("User", foreign_keys=[created_by_id])
