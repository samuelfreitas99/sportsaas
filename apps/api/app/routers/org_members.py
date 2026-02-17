from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.org_member import OrgMember, OrgRole
from app.models.user import User
from app.routers.deps import get_current_user, require_org_member
from app.schemas.org_member import (
    OrgMemberCreate,
    OrgMemberResponse,
    OrgMemberUpdate,
    OrgMemberUpdateRole,
)

router = APIRouter()


def _get_membership(db: Session, org_id: UUID, user_id: UUID) -> OrgMember | None:
    return (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
        .first()
    )


def _count_owners(db: Session, org_id: UUID) -> int:
    return (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.role == OrgRole.OWNER)
        .count()
    )


def _can_manage(current_role: OrgRole, target_role: OrgRole) -> bool:
    if current_role == OrgRole.OWNER:
        return True
    if current_role == OrgRole.ADMIN:
        return target_role == OrgRole.MEMBER
    return False


@router.get("/orgs/{org_id}/members", response_model=list[OrgMemberResponse])
def list_members(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)
    members = (
        db.query(OrgMember)
        .options(joinedload(OrgMember.user))
        .filter(OrgMember.org_id == org_id)
        .order_by(OrgMember.created_at.asc())
        .all()
    )
    return members


@router.post("/orgs/{org_id}/members", response_model=OrgMemberResponse)
def add_member(
    org_id: UUID,
    payload: OrgMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    my_membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not my_membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if my_membership.role == OrgRole.MEMBER:
        raise HTTPException(status_code=403, detail="Not authorized")

    if my_membership.role == OrgRole.ADMIN and payload.role != OrgRole.MEMBER:
        raise HTTPException(status_code=403, detail="Not authorized to assign this role")

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    exists = _get_membership(db=db, org_id=org_id, user_id=user.id)
    if exists:
        raise HTTPException(status_code=409, detail="User already a member")

    member = OrgMember(user_id=user.id, org_id=org_id, role=payload.role)
    db.add(member)
    db.commit()
    db.refresh(member)

    member = (
        db.query(OrgMember)
        .options(joinedload(OrgMember.user))
        .filter(OrgMember.id == member.id)
        .first()
    )
    return member


@router.patch("/orgs/{org_id}/members/{member_id}/role", response_model=OrgMemberResponse)
def update_member_role(
    org_id: UUID,
    member_id: UUID,
    payload: OrgMemberUpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    my_membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not my_membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if my_membership.id == member_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    target = (
        db.query(OrgMember)
        .options(joinedload(OrgMember.user))
        .filter(OrgMember.id == member_id, OrgMember.org_id == org_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if not _can_manage(my_membership.role, target.role):
        raise HTTPException(status_code=403, detail="Not authorized")

    if my_membership.role == OrgRole.ADMIN and payload.role == OrgRole.OWNER:
        raise HTTPException(status_code=403, detail="Not authorized to assign this role")

    if target.role == OrgRole.OWNER and payload.role != OrgRole.OWNER:
        if _count_owners(db=db, org_id=org_id) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove last OWNER")

    target.role = payload.role
    db.commit()
    db.refresh(target)
    return target


@router.patch("/orgs/{org_id}/members/{member_id}", response_model=OrgMemberResponse)
def update_member(
    org_id: UUID,
    member_id: UUID,
    payload: OrgMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    my_membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not my_membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    target = (
        db.query(OrgMember)
        .options(joinedload(OrgMember.user))
        .filter(OrgMember.id == member_id, OrgMember.org_id == org_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    data = payload.model_dump(exclude_unset=True)
    wants_nickname = "nickname" in data
    wants_member_type = "member_type" in data
    wants_is_active = "is_active" in data

    is_admin = my_membership.role in (OrgRole.OWNER, OrgRole.ADMIN)
    is_self = my_membership.id == target.id

    if wants_member_type or wants_is_active:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")

    if wants_nickname:
        if not (is_admin or is_self):
            raise HTTPException(status_code=403, detail="Not authorized")
        target.nickname = data["nickname"]
    if wants_member_type:
        target.member_type = data["member_type"]
    if wants_is_active:
        target.is_active = data["is_active"]

    db.commit()
    db.refresh(target)
    return target


@router.delete("/orgs/{org_id}/members/{member_id}")
def remove_member(
    org_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_org_member(org_id=org_id, db=db, current_user=current_user)

    my_membership = _get_membership(db=db, org_id=org_id, user_id=current_user.id)
    if not my_membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    target = (
        db.query(OrgMember)
        .filter(OrgMember.id == member_id, OrgMember.org_id == org_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if my_membership.id == target.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    if not _can_manage(my_membership.role, target.role):
        raise HTTPException(status_code=403, detail="Not authorized")

    if target.role == OrgRole.OWNER and _count_owners(db=db, org_id=org_id) <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove last OWNER")

    db.delete(target)
    db.commit()
    return {"ok": True}
