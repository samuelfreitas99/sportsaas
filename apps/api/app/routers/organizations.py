from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.organization import Organization, OrgMember, OrgRole
from app.schemas.organization import OrgCreate, Org, OrgMember as OrgMemberSchema
from app.routers.deps import get_current_user
from app.models.user import User
from uuid import UUID, uuid4

router = APIRouter()

def _make_slug(name: str) -> str:
    base = name.strip().lower().replace(" ", "-")
    base = "-".join(filter(None, base.split("-")))  # evita ----
    return f"{base}-{str(uuid4())[:8]}"

@router.post("/", response_model=Org)
def create_org(
    org_in: OrgCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # tenta garantir unicidade
    slug = _make_slug(org_in.name)
    for _ in range(3):
        exists = db.query(Organization).filter(Organization.slug == slug).first()
        if not exists:
            break
        slug = _make_slug(org_in.name)
    else:
        raise HTTPException(status_code=400, detail="Could not generate unique slug")

    db_org = Organization(name=org_in.name, slug=slug, owner_id=current_user.id)
    db.add(db_org)
    db.flush()

    member = OrgMember(user_id=current_user.id, org_id=db_org.id, role=OrgRole.OWNER)
    db.add(member)

    db.commit()
    db.refresh(db_org)
    return db_org

@router.get("/", response_model=list[Org])
def read_orgs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get orgs where user is a member
    orgs = (
        db.query(Organization)
        .join(OrgMember)
        .filter(OrgMember.user_id == current_user.id)
        .all()
    )
    return orgs

@router.get("/{org_id}/members", response_model=list[OrgMemberSchema])
def read_members(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = (
        db.query(OrgMember)
        .filter(OrgMember.user_id == current_user.id, OrgMember.org_id == org_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    members = db.query(OrgMember).filter(OrgMember.org_id == org_id).all()
    return members
