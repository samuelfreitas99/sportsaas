from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.game import AttendanceStatus, Game, GameAttendance
from app.models.org_billing_settings import BillingMode
from app.models.org_charge import ChargeStatus, ChargeType, OrgCharge
from app.models.org_member import MemberType, OrgMember
from app.routers.billing import _get_or_create_settings, _compute_cycle  # já existe no teu billing.py

def generate_charges_for_org(
    *,
    db: Session,
    org_id: UUID,
    force: bool = False,
    cycle_key_override: str | None = None,
    created_by_id: UUID | None = None,
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

    # MEMBERSHIP
    if settings.billing_mode in (BillingMode.MEMBERSHIP, BillingMode.HYBRID):
        for m in members:
            if m.member_type == MemberType.MONTHLY:
                ensure_charge(
                    m,
                    ChargeType.MEMBERSHIP,
                    float(settings.membership_amount),
                    cycle_key_value=cycle_key,
                )

    # PER_SESSION por jogo (GUEST + GOING)
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

        member_by_id = {m.id: m for m in members}
        for r in rows:
            member = member_by_id.get(r.org_member_id)
            if not member:
                continue
            ensure_charge(
                member,
                ChargeType.PER_SESSION,
                float(settings.session_amount),
                cycle_key_value=f"GAME:{r.game_id}",
                game_id=r.game_id,
            )

    db.commit()
    return {"cycle_key": cycle_key, "created": created, "skipped": skipped}
