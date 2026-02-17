from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.org_member import MemberType


class PublicUser(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class CaptainRef(BaseModel):
    type: str
    id: UUID


class CaptainsSetRequest(BaseModel):
    captain_a: CaptainRef | None = None
    captain_b: CaptainRef | None = None
    mode: str = "MANUAL"


class CaptainResolvedMember(BaseModel):
    type: str = "MEMBER"
    org_member_id: UUID
    nickname: str | None = None
    member_type: MemberType
    included: bool
    billable: bool
    user: PublicUser

    class Config:
        from_attributes = True


class CaptainResolvedGuest(BaseModel):
    type: str = "GUEST"
    game_guest_id: UUID
    name: str
    phone: str | None = None
    billable: bool
    source: str


class CaptainsResolved(BaseModel):
    captain_a: CaptainResolvedMember | CaptainResolvedGuest | None = None
    captain_b: CaptainResolvedMember | CaptainResolvedGuest | None = None


class TeamMemberItem(BaseModel):
    org_member_id: UUID
    nickname: str | None = None
    member_type: MemberType
    included: bool
    billable: bool
    user: PublicUser

    class Config:
        from_attributes = True


class TeamGuestItem(BaseModel):
    game_guest_id: UUID
    name: str
    phone: str | None = None
    billable: bool
    source: str


class TeamSide(BaseModel):
    members: list[TeamMemberItem]
    guests: list[TeamGuestItem]


class TeamsResponse(BaseModel):
    team_a: TeamSide
    team_b: TeamSide


class TeamTarget(BaseModel):
    type: str
    id: UUID


class TeamAssignmentSetRequest(BaseModel):
    target: TeamTarget
    team: str | None = None
