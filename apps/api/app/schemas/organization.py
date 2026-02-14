from pydantic import BaseModel
from uuid import UUID
from app.models.organization import OrgRole, MemberType

class OrgBase(BaseModel):
    name: str

class OrgCreate(OrgBase):
    pass

class Org(OrgBase):
    id: UUID
    slug: str | None = None
    owner_id: UUID

    class Config:
        from_attributes = True

class OrgMemberBase(BaseModel):
    role: OrgRole
    member_type: MemberType

class OrgMember(OrgMemberBase):
    user_id: UUID
    org_id: UUID
    
    class Config:
        from_attributes = True
