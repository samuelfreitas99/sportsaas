from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.game import Game
from app.models.game_guest import GameGuest
from app.models.org_guest import OrgGuest
from app.models.org_member import OrgMember, OrgRole
from app.models.user import User
from app.routers.deps import get_current_user, require_org_member
from app.schemas.guest import (
    GameGuestCreate,
    GameGuestResponse,
    OrgGuestCreate,
    OrgGuestResponse,
    OrgGuestUpdate,
)

router = APIRouter()


def _get_membership(db: Session, org_id: UUID, user_id: UUID) -> OrgMember | None:
    return (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
        .first()
    )


def _require_admin(db: Session, org_id: UUID, current_user: User) -> OrgMember:
    membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    if membership.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized")
    return membership


def _norm(s: str | None) -> str | None:
    if s is None:
        return None
    v = s.strip()
    return v if v else None


@router.get("/orgs/{org_id}/guests", response_model=list[OrgGuestResponse])
def list_org_guests(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    return db.query(OrgGuest).filter(OrgGuest.org_id == org_id).order_by(OrgGuest.created_at.asc()).all()


@router.post("/orgs/{org_id}/guests", response_model=OrgGuestResponse)
def create_org_guest(
    org_id: UUID,
    payload: OrgGuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    name = _norm(payload.name)
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    phone = _norm(payload.phone)

    if phone:
        existing = (
            db.query(OrgGuest)
            .filter(OrgGuest.org_id == org_id, OrgGuest.phone == phone)
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Guest with this phone already exists")

    guest = OrgGuest(org_id=org_id, name=name, phone=phone)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


@router.patch("/orgs/{org_id}/guests/{guest_id}", response_model=OrgGuestResponse)
def update_org_guest(
    org_id: UUID,
    guest_id: UUID,
    payload: OrgGuestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin(db=db, org_id=org_id, current_user=current_user)

    guest = db.query(OrgGuest).filter(OrgGuest.org_id == org_id, OrgGuest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        name = _norm(data["name"])
        if not name:
            raise HTTPException(status_code=400, detail="name cannot be empty")
        guest.name = name
    if "phone" in data:
        phone = _norm(data["phone"])
        if phone:
            existing = (
                db.query(OrgGuest)
                .filter(OrgGuest.org_id == org_id, OrgGuest.phone == phone, OrgGuest.id != guest_id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=409, detail="Guest with this phone already exists")
        guest.phone = phone

    db.commit()
    db.refresh(guest)
    return guest


@router.delete("/orgs/{org_id}/guests/{guest_id}")
def delete_org_guest(
    org_id: UUID,
    guest_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    _require_admin(db=db, org_id=org_id, current_user=current_user)

    guest = db.query(OrgGuest).filter(OrgGuest.org_id == org_id, OrgGuest.id == guest_id).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    in_use = db.query(GameGuest).filter(GameGuest.org_guest_id == guest_id).first()
    if in_use:
        raise HTTPException(status_code=409, detail="Guest is in use by game guests")

    db.delete(guest)
    db.commit()
    return {"ok": True}


@router.get("/orgs/{org_id}/games/{game_id}/guests", response_model=list[GameGuestResponse])
def list_game_guests(
    org_id: UUID,
    game_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    rows = (
        db.query(GameGuest)
        .filter(GameGuest.org_id == org_id, GameGuest.game_id == game_id)
        .order_by(GameGuest.created_at.asc())
        .all()
    )

    is_admin = membership.role in (OrgRole.OWNER, OrgRole.ADMIN)
    out: list[GameGuestResponse] = []
    for r in rows:
        out.append(
            GameGuestResponse(
                id=r.id,
                org_id=r.org_id,
                game_id=r.game_id,
                org_guest_id=r.org_guest_id,
                name=r.name,
                phone=r.phone,
                created_by_member_id=r.created_by_member_id,
                can_delete=is_admin or (r.created_by_member_id == membership.id),
                source="GAME_GUEST",
                billable=True,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return out


@router.post("/orgs/{org_id}/games/{game_id}/guests", response_model=GameGuestResponse)
def create_game_guest(
    org_id: UUID,
    game_id: UUID,
    payload: GameGuestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if payload.org_guest_id:
        org_guest = (
            db.query(OrgGuest)
            .filter(OrgGuest.id == payload.org_guest_id, OrgGuest.org_id == org_id)
            .first()
        )
        if not org_guest:
            raise HTTPException(status_code=404, detail="Org guest not found")
        name = _norm(org_guest.name)
        phone = _norm(org_guest.phone)
        org_guest_id = org_guest.id
    else:
        name = _norm(payload.name)
        if not name:
            raise HTTPException(status_code=400, detail="name is required when org_guest_id is not provided")
        phone = _norm(payload.phone)
        org_guest_id = None

    exists = (
        db.query(GameGuest)
        .filter(
            GameGuest.game_id == game_id,
            func.lower(func.btrim(GameGuest.name)) == name.lower(),
            func.coalesce(func.btrim(GameGuest.phone), "") == (phone or ""),
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Guest already added to this game")

    row = GameGuest(
        org_id=org_id,
        game_id=game_id,
        org_guest_id=org_guest_id,
        name=name,
        phone=phone,
        created_by_member_id=membership.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    is_admin = membership.role in (OrgRole.OWNER, OrgRole.ADMIN)
    return GameGuestResponse(
        id=row.id,
        org_id=row.org_id,
        game_id=row.game_id,
        org_guest_id=row.org_guest_id,
        name=row.name,
        phone=row.phone,
        created_by_member_id=row.created_by_member_id,
        can_delete=is_admin or (row.created_by_member_id == membership.id),
        source="GAME_GUEST",
        billable=True,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/orgs/{org_id}/games/{game_id}/guests/{game_guest_id}")
def delete_game_guest(
    org_id: UUID,
    game_id: UUID,
    game_guest_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    game = db.query(Game).filter(Game.id == game_id, Game.org_id == org_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    row = (
        db.query(GameGuest)
        .filter(GameGuest.id == game_guest_id, GameGuest.org_id == org_id, GameGuest.game_id == game_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Game guest not found")

    is_admin = membership.role in (OrgRole.OWNER, OrgRole.ADMIN)
    if not (is_admin or row.created_by_member_id == membership.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(row)
    db.commit()
    return {"ok": True}
