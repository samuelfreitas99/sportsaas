from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, Enum, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class LedgerType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    type: Mapped[LedgerType] = mapped_column(
        Enum(LedgerType, name="ledger_type"), default=LedgerType.EXPENSE, nullable=False
    )

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # opcional: vincular a um membro da org (pra breakdown mensalista/convidado depois)
    related_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("org_members.id"), nullable=True
    )

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization", back_populates="ledger_entries")
    related_member = relationship("OrgMember")
    creator = relationship("User")
