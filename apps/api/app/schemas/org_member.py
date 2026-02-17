from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.org_member import MemberType, OrgRole


class OrgMemberBase(BaseModel):
    role: OrgRole = OrgRole.MEMBER


class OrgMemberCreate(OrgMemberBase):
    email: EmailStr


class OrgMemberUpdateRole(BaseModel):
    role: OrgRole


class OrgMemberUpdate(BaseModel):
    nickname: str | None = None
    member_type: MemberType | None = None
    is_active: bool | None = None


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
    member_type: MemberType
    nickname: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user: OrgMemberUser

    class Config:
        from_attributes = True
