from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.db.session import get_db
from app.models.game import AttendanceStatus, Game, GameAttendance
from app.models.ledger import LedgerEntry, LedgerType
from app.models.org_billing_settings import BillingCycle, BillingMode, OrgBillingSettings
from app.models.org_charge import ChargeStatus, ChargeType, OrgCharge
from app.models.org_member import MemberType, OrgMember, OrgRole
from app.models.user import User
from app.routers.deps import get_current_user, require_org_member
from app.schemas.billing import (
    GenerateChargesRequest,
    OrgBillingSettingsPut,
    OrgBillingSettingsResponse,
)
from app.schemas.charge import OrgChargeResponse, UpdateChargeStatusRequest

router = APIRouter()


def _get_membership(db: Session, org_id: UUID, user_id: UUID) -> OrgMember | None:
    return (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
        .first()
    )


def _require_billing_manager(db: Session, org_id: UUID, current_user: User) -> OrgMember:
    membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    if membership.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")
    return membership


def _get_or_create_settings(db: Session, org_id: UUID) -> OrgBillingSettings:
    settings = db.query(OrgBillingSettings).filter(OrgBillingSettings.org_id == org_id).first()
    if settings:
        return settings
    settings = OrgBillingSettings(
        org_id=org_id,
        billing_mode=BillingMode.HYBRID,
        cycle=BillingCycle.MONTHLY,
        cycle_weeks=None,
        anchor_date=date.today(),
        due_day=1,
        membership_amount=0,
        session_amount=0,
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def _month_range_utc(start: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start.replace(day=1), time.min, tzinfo=timezone.utc)
    if start.month == 12:
        end_month = date(start.year + 1, 1, 1)
    else:
        end_month = date(start.year, start.month + 1, 1)
    end_dt = datetime.combine(end_month, time.min, tzinfo=timezone.utc)
    return start_dt, end_dt


def _week_range_utc(iso_year: int, iso_week: int) -> tuple[datetime, datetime]:
    start_dt = datetime.fromisocalendar(iso_year, iso_week, 1).replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=7)
    return start_dt, end_dt


def _compute_cycle(settings: OrgBillingSettings, cycle_key: str | None) -> tuple[str, datetime, datetime]:
    now = datetime.now(timezone.utc)

    if settings.cycle == BillingCycle.MONTHLY:
        if cycle_key:
            try:
                y, m = cycle_key.split("-")
                y_i = int(y)
                m_i = int(m)
                start_date = date(y_i, m_i, 1)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cycle_key for MONTHLY (expected YYYY-MM)")
        else:
            start_date = date(now.year, now.month, 1)
            cycle_key = f"{now.year:04d}-{now.month:02d}"
        start_dt, end_dt = _month_range_utc(start_date)
        return cycle_key, start_dt, end_dt

    if settings.cycle == BillingCycle.WEEKLY:
        if cycle_key:
            try:
                y, w = cycle_key.split("-W")
                iso_year = int(y)
                iso_week = int(w)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cycle_key for WEEKLY (expected YYYY-Www)")
        else:
            iso = now.isocalendar()
            iso_year = iso.year
            iso_week = iso.week
            cycle_key = f"{iso_year:04d}-W{iso_week:02d}"
        start_dt, end_dt = _week_range_utc(iso_year, iso_week)
        return cycle_key, start_dt, end_dt

    if settings.cycle == BillingCycle.CUSTOM_WEEKS:
        if not settings.cycle_weeks or settings.cycle_weeks <= 0:
            raise HTTPException(status_code=400, detail="cycle_weeks is required for CUSTOM_WEEKS")
        period_days = settings.cycle_weeks * 7
        anchor = settings.anchor_date
        if cycle_key:
            try:
                start_date = date.fromisoformat(cycle_key)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid cycle_key for CUSTOM_WEEKS (expected YYYY-MM-DD)")
        else:
            delta_days = (date.today() - anchor).days
            n = max(0, delta_days // period_days)
            start_date = anchor + timedelta(days=n * period_days)
            cycle_key = start_date.isoformat()
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_dt = start_dt + timedelta(days=period_days)
        return cycle_key, start_dt, end_dt

    raise HTTPException(status_code=400, detail="Unsupported billing cycle")


@router.get("/orgs/{org_id}/billing-settings", response_model=OrgBillingSettingsResponse)
def get_billing_settings(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_billing_manager(db=db, org_id=org_id, current_user=current_user)
    return _get_or_create_settings(db=db, org_id=org_id)


@router.put("/orgs/{org_id}/billing-settings", response_model=OrgBillingSettingsResponse)
def put_billing_settings(
    org_id: UUID,
    payload: OrgBillingSettingsPut,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_billing_manager(db=db, org_id=org_id, current_user=current_user)

    if payload.cycle == BillingCycle.CUSTOM_WEEKS and (not payload.cycle_weeks or payload.cycle_weeks <= 0):
        raise HTTPException(status_code=400, detail="cycle_weeks must be > 0 for CUSTOM_WEEKS")

    if payload.due_day < 1 or payload.due_day > 31:
        raise HTTPException(status_code=400, detail="due_day must be between 1 and 31")

    settings = _get_or_create_settings(db=db, org_id=org_id)
    settings.billing_mode = payload.billing_mode
    settings.cycle = payload.cycle
    settings.cycle_weeks = payload.cycle_weeks
    settings.anchor_date = payload.anchor_date
    settings.due_day = payload.due_day
    settings.membership_amount = payload.membership_amount
    settings.session_amount = payload.session_amount

    db.commit()
    db.refresh(settings)
    return settings




@router.post("/orgs/{org_id}/charges/generate")
def generate_charges(
    org_id: UUID,
    payload: GenerateChargesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_billing_manager(db=db, org_id=org_id, current_user=current_user)

    return _generate_charges_core(
        db=db,
        org_id=org_id,
        force=payload.force,
        cycle_key_override=payload.cycle_key,
        created_by_id=current_user.id,
    )




@router.get("/orgs/{org_id}/charges", response_model=list[OrgChargeResponse])
def list_charges(
    org_id: UUID,
    cycle_key: str | None = None,
    member_id: UUID | None = None,
    status: ChargeStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_billing_manager(db=db, org_id=org_id, current_user=current_user)

    q = (
        db.query(OrgCharge)
        .options(joinedload(OrgCharge.org_member).joinedload(OrgMember.user))
        .filter(OrgCharge.org_id == org_id)
        .order_by(OrgCharge.created_at.desc())
    )
    if cycle_key:
        q = q.filter(OrgCharge.cycle_key == cycle_key)
    if member_id:
        q = q.filter(OrgCharge.org_member_id == member_id)
    if status:
        q = q.filter(OrgCharge.status == status)
    return q.all()


@router.patch("/orgs/{org_id}/charges/{charge_id}", response_model=OrgChargeResponse)
def update_charge_status(
    org_id: UUID,
    charge_id: UUID,
    payload: UpdateChargeStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_billing_manager(db=db, org_id=org_id, current_user=current_user)

    charge = (
        db.query(OrgCharge)
        .options(joinedload(OrgCharge.org_member).joinedload(OrgMember.user))
        .filter(OrgCharge.org_id == org_id, OrgCharge.id == charge_id)
        .first()
    )
    if not charge:
        raise HTTPException(status_code=404, detail="Charge not found")

    if payload.status == ChargeStatus.PAID:
        if charge.status == ChargeStatus.PAID:
            return charge
        if charge.status == ChargeStatus.VOID:
            raise HTTPException(status_code=400, detail="Cannot pay a VOID charge")

        now = datetime.now(timezone.utc)
        charge.status = ChargeStatus.PAID
        charge.paid_at = now
        charge.voided_at = None

        if not charge.ledger_entry_id:
            entry = LedgerEntry(
                org_id=org_id,
                type=LedgerType.INCOME,
                amount=charge.amount,
                description=f"Charge paid: {charge.cycle_key} ({charge.type.value})",
                occurred_at=now,
                related_member_id=charge.org_member_id,
                created_by_id=current_user.id,
            )
            db.add(entry)
            db.flush()
            charge.ledger_entry_id = entry.id
            charge.created_by_id = current_user.id

        db.commit()
        db.refresh(charge)
        return charge

    if payload.status == ChargeStatus.VOID:
        if charge.status == ChargeStatus.PAID:
            raise HTTPException(status_code=400, detail="Cannot void a PAID charge")
        if charge.status == ChargeStatus.VOID:
            return charge
        charge.status = ChargeStatus.VOID
        charge.voided_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(charge)
        return charge

    raise HTTPException(status_code=400, detail="Unsupported status transition")

def _generate_charges_core(
    *,
    db: Session,
    org_id: UUID,
    force: bool,
    cycle_key_override: str | None,
    created_by_id: UUID | None,
) -> dict:
    settings = _get_or_create_settings(db=db, org_id=org_id)
    cycle_key, start_dt, end_dt = _compute_cycle(settings=settings, cycle_key=cycle_key_override)

    members: list[OrgMember] = db.query(OrgMember).filter(OrgMember.org_id == org_id).all()

    created = 0
    skipped = 0

    def ensure_charge(
        member: OrgMember,
        charge_type: ChargeType,
        amount: float,
        cycle_key_value: str,
        game_id: UUID | None = None,
    ) -> None:
        nonlocal created, skipped

        existing = (
            db.query(OrgCharge)
            .filter(
                OrgCharge.org_id == org_id,
                OrgCharge.org_member_id == member.id,
                OrgCharge.cycle_key == cycle_key_value,
                OrgCharge.type == charge_type,
            )
            .first()
        )

        if existing:
            if existing.status == ChargeStatus.PAID:
                skipped += 1
                return
            if not force:
                skipped += 1
                return

            existing.amount = amount
            existing.game_id = game_id

            if existing.status == ChargeStatus.VOID:
                existing.status = ChargeStatus.PENDING
                existing.voided_at = None

            skipped += 1
            return

        charge = OrgCharge(
            org_id=org_id,
            org_member_id=member.id,
            cycle_key=cycle_key_value,
            type=charge_type,
            status=ChargeStatus.PENDING,
            amount=amount,
            created_by_id=created_by_id,
            game_id=game_id,
        )
        db.add(charge)
        created += 1

    # MEMBERSHIP (MONTHLY)
    if settings.billing_mode in (BillingMode.MEMBERSHIP, BillingMode.HYBRID):
        for m in members:
            if m.member_type == MemberType.MONTHLY:
                ensure_charge(
                    m,
                    ChargeType.MEMBERSHIP,
                    float(settings.membership_amount),
                    cycle_key_value=cycle_key,
                )

    # PER_SESSION (por jogo)
    if settings.billing_mode in (BillingMode.PER_SESSION, BillingMode.HYBRID):
        rows = (
            db.query(Game.id.label("game_id"), OrgMember.id.label("org_member_id"))
            .join(GameAttendance, GameAttendance.game_id == Game.id)
            .join(
                OrgMember,
                (OrgMember.org_id == Game.org_id) & (OrgMember.user_id == GameAttendance.user_id),
            )
            .filter(
                Game.org_id == org_id,
                Game.start_at >= start_dt,
                Game.start_at < end_dt,
                GameAttendance.status == AttendanceStatus.GOING,
                OrgMember.member_type == MemberType.GUEST,
            )
            .distinct()
            .all()
        )

        # map rápido pra evitar next(...) N vezes
        members_by_id = {m.id: m for m in members}

        for r in rows:
            member = members_by_id.get(r.org_member_id)
            if not member:
                continue

            game_cycle_key = f"GAME:{r.game_id}"
            ensure_charge(
                member,
                ChargeType.PER_SESSION,
                float(settings.session_amount),
                cycle_key_value=game_cycle_key,
                game_id=r.game_id,
            )

    db.commit()
    return {"cycle_key": cycle_key, "created": created, "skipped": skipped}
