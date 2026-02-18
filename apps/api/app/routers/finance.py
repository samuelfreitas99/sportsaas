# apps/api/app/routers/finance.py
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.deps import get_current_user, require_org_member
from app.models.user import User
from app.models.ledger import LedgerEntry, LedgerType
from app.models.org_charge import OrgCharge, ChargeStatus
from app.schemas.finance import (
    FinanceSummaryResponse,
    FinanceRecentResponse,
    FinanceDashboardResponse,
)

router = APIRouter(tags=["finance"])


@router.get("/orgs/{org_id}/finance/summary", response_model=FinanceSummaryResponse)
def finance_summary(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    income_total = (
        db.query(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .filter(LedgerEntry.org_id == org_id, LedgerEntry.type == LedgerType.INCOME)
        .scalar()
        or 0
    )
    expense_total = (
        db.query(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .filter(LedgerEntry.org_id == org_id, LedgerEntry.type == LedgerType.EXPENSE)
        .scalar()
        or 0
    )

    charges_agg = (
        db.query(
            func.coalesce(
                func.sum(case((OrgCharge.status == ChargeStatus.PENDING, OrgCharge.amount), else_=0)),
                0,
            ).label("pending_total"),
            func.coalesce(
                func.sum(case((OrgCharge.status == ChargeStatus.PAID, OrgCharge.amount), else_=0)),
                0,
            ).label("paid_total"),
            func.coalesce(func.sum(case((OrgCharge.status == ChargeStatus.PENDING, 1), else_=0)), 0).label(
                "pending_count"
            ),
            func.coalesce(func.sum(case((OrgCharge.status == ChargeStatus.PAID, 1), else_=0)), 0).label("paid_count"),
        )
        .filter(OrgCharge.org_id == org_id)
        .one()
    )

    balance = float(income_total) - float(expense_total)

    return {
        "org_id": str(org_id),
        "income_total": float(income_total),
        "expense_total": float(expense_total),
        "balance": float(balance),
        "pending_charges_total": float(charges_agg.pending_total),
        "paid_charges_total": float(charges_agg.paid_total),
        "pending_charges_count": int(charges_agg.pending_count),
        "paid_charges_count": int(charges_agg.paid_count),
    }


@router.get("/orgs/{org_id}/finance/recent", response_model=FinanceRecentResponse)
def finance_recent(
    org_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    ledger = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.org_id == org_id)
        .order_by(LedgerEntry.occurred_at.desc())
        .limit(limit)
        .all()
    )
    charges = (
        db.query(OrgCharge)
        .filter(OrgCharge.org_id == org_id)
        .order_by(OrgCharge.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "org_id": str(org_id),
        "ledger": [
            {
                "id": str(x.id),
                "type": x.type.value if hasattr(x.type, "value") else str(x.type),
                "amount": float(x.amount),
                "description": x.description,
                "occurred_at": x.occurred_at,
                "related_member_id": str(x.related_member_id) if x.related_member_id else None,
                "created_by_id": str(x.created_by_id) if x.created_by_id else None,
            }
            for x in ledger
        ],
        "charges": [
            {
                "id": str(c.id),
                "org_member_id": str(c.org_member_id),
                "cycle_key": c.cycle_key,
                "type": c.type.value if hasattr(c.type, "value") else str(c.type),
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "amount": float(c.amount),
                "game_id": str(getattr(c, "game_id")) if getattr(c, "game_id", None) else None,
                "ledger_entry_id": str(c.ledger_entry_id) if c.ledger_entry_id else None,
                "created_at": c.created_at,
            }
            for c in charges
        ],
    }


@router.get("/orgs/{org_id}/finance/dashboard")
def finance_dashboard(
    org_id: UUID,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    # -------- SUMMARY COM PERÍODO --------
    ledger_query = db.query(LedgerEntry).filter(LedgerEntry.org_id == org_id)

    if start:
        ledger_query = ledger_query.filter(LedgerEntry.occurred_at >= start)
    if end:
        ledger_query = ledger_query.filter(LedgerEntry.occurred_at <= end)

    income_total = (
        ledger_query.filter(LedgerEntry.type == LedgerType.INCOME)
        .with_entities(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .scalar()
        or 0
    )

    expense_total = (
        ledger_query.filter(LedgerEntry.type == LedgerType.EXPENSE)
        .with_entities(func.coalesce(func.sum(LedgerEntry.amount), 0))
        .scalar()
        or 0
    )

    balance = float(income_total) - float(expense_total)

    # -------- CHARGES --------
    charges_query = db.query(OrgCharge).filter(OrgCharge.org_id == org_id)

    if start:
        charges_query = charges_query.filter(OrgCharge.created_at >= start)
    if end:
        charges_query = charges_query.filter(OrgCharge.created_at <= end)

    pending_total = (
        charges_query.filter(OrgCharge.status == ChargeStatus.PENDING)
        .with_entities(func.coalesce(func.sum(OrgCharge.amount), 0))
        .scalar()
        or 0
    )

    paid_total = (
        charges_query.filter(OrgCharge.status == ChargeStatus.PAID)
        .with_entities(func.coalesce(func.sum(OrgCharge.amount), 0))
        .scalar()
        or 0
    )

    # -------- RECENT --------
    recent_ledger = (
        ledger_query.order_by(LedgerEntry.occurred_at.desc())
        .limit(limit)
        .all()
    )

    recent_charges = (
        charges_query.order_by(OrgCharge.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "org_id": str(org_id),
        "period": {
            "start": start,
            "end": end,
        },
        "summary": {
            "income_total": float(income_total),
            "expense_total": float(expense_total),
            "balance": float(balance),
            "pending_charges_total": float(pending_total),
            "paid_charges_total": float(paid_total),
        },
        "recent": {
            "ledger": [
                {
                    "id": str(x.id),
                    "type": str(x.type),
                    "amount": float(x.amount),
                    "description": x.description,
                    "occurred_at": x.occurred_at,
                }
                for x in recent_ledger
            ],
            "charges": [
                {
                    "id": str(c.id),
                    "status": str(c.status),
                    "type": str(c.type),
                    "amount": float(c.amount),
                    "created_at": c.created_at,
                }
                for c in recent_charges
            ],
        },
    }
