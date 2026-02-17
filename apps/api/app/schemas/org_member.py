from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.org_member import OrgRole


class OrgMemberBase(BaseModel):
    role: OrgRole = OrgRole.MEMBER


class OrgMemberCreate(OrgMemberBase):
    email: EmailStr


class OrgMemberUpdateRole(BaseModel):
    role: OrgRole


class OrgMemberUser(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None

    class Config:
        from_attributes = True


class OrgMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    org_id: UUID
    role: OrgRole
    created_at: datetime
    updated_at: datetime
    user: OrgMemberUser

    class Config:
        from_attributes = True
