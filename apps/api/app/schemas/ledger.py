from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.ledger import LedgerType


class LedgerEntryBase(BaseModel):
    type: LedgerType
    amount: float
    description: str | None = None
    occurred_at: datetime
    related_member_id: UUID | None = None


class LedgerEntryCreate(LedgerEntryBase):
    pass


class LedgerEntry(LedgerEntryBase):
    id: UUID
    org_id: UUID
    created_by_id: UUID | None = None

    class Config:
        from_attributes = True


class LedgerSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
