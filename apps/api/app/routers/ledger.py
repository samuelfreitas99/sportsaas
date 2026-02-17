from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.ledger import LedgerEntry, LedgerType
from app.models.organization import OrgMember, OrgRole
from app.schemas.ledger import LedgerEntryCreate, LedgerEntry as LedgerEntrySchema
from app.routers.deps import get_current_user
from app.models.user import User

from app.routers.deps import require_org_member

router = APIRouter()

@router.post("/orgs/{org_id}/ledger", response_model=LedgerEntrySchema)
def create_ledger_entry(
    org_id: UUID,
    entry_in: LedgerEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    membership = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == current_user.id, OrgMember.org_id == org_id)
        .first()
    )
    if membership is None or membership.role not in [OrgRole.ADMIN, OrgRole.OWNER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    entry = LedgerEntry(
        **entry_in.model_dump(),
        org_id=org_id,
        created_by_id=current_user.id,  # ✅ NOME CERTO
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/orgs/{org_id}/ledger", response_model=list[LedgerEntrySchema])
def read_ledger(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    return db.query(LedgerEntry).filter(LedgerEntry.org_id == org_id).all()

@router.get("/orgs/{org_id}/ledger/summary")
def get_ledger_summary(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    income = (
        db.query(func.sum(LedgerEntry.amount))
        .filter(LedgerEntry.org_id == org_id, LedgerEntry.type == LedgerType.INCOME)
        .scalar()
        or 0
    )
    expense = (
        db.query(func.sum(LedgerEntry.amount))
        .filter(LedgerEntry.org_id == org_id, LedgerEntry.type == LedgerType.EXPENSE)
        .scalar()
        or 0
    )

    return {"total_income": float(income), "total_expense": float(expense), "balance": float(income - expense)}
