# apps/api/app/routers/finance.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.deps import get_current_user, require_org_member
from app.models.user import User
from app.models.ledger import LedgerEntry, LedgerType
from app.models.org_charge import OrgCharge, ChargeStatus

router = APIRouter(tags=["finance"])


@router.get("/orgs/{org_id}/finance/summary")
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

    # totals de charges por status
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


@router.get("/orgs/{org_id}/finance/recent")
def finance_recent(
    org_id: UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    lim = max(1, min(limit, 100))

    ledger = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.org_id == org_id)
        .order_by(LedgerEntry.occurred_at.desc())
        .limit(lim)
        .all()
    )
    charges = (
        db.query(OrgCharge)
        .filter(OrgCharge.org_id == org_id)
        .order_by(OrgCharge.created_at.desc())
        .limit(lim)
        .all()
    )

    # retorna só campos simples (sem schema por enquanto)
    return {
        "org_id": str(org_id),
        "ledger": [
            {
                "id": str(x.id),
                "type": x.type,
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
                "type": c.type,
                "status": c.status,
                "amount": float(c.amount),
                "game_id": str(getattr(c, "game_id")) if getattr(c, "game_id", None) else None,
                "ledger_entry_id": str(c.ledger_entry_id) if c.ledger_entry_id else None,
                "created_at": c.created_at,
            }
            for c in charges
        ],
    }
