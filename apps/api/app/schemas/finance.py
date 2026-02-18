from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class FinanceSummaryResponse(BaseModel):
    org_id: str
    income_total: float
    expense_total: float
    balance: float
    pending_charges_total: float
    paid_charges_total: float
    pending_charges_count: int
    paid_charges_count: int


class LedgerEntryOut(BaseModel):
    id: str
    type: str
    amount: float
    description: str | None = None
    occurred_at: datetime
    related_member_id: str | None = None
    created_by_id: str | None = None


class ChargeOutMini(BaseModel):
    id: str
    org_member_id: str
    cycle_key: str
    type: str
    status: str
    amount: float
    game_id: str | None = None
    ledger_entry_id: str | None = None
    created_at: datetime


class FinanceRecentResponse(BaseModel):
    org_id: str
    ledger: list[LedgerEntryOut]
    charges: list[ChargeOutMini]


class FinanceDashboardResponse(BaseModel):
    summary: FinanceSummaryResponse
    recent: FinanceRecentResponse
