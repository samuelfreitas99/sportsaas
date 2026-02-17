from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.game import AttendanceStatus
from app.models.org_member import MemberType
from app.schemas.draft import DraftSummary
from app.schemas.teams import CaptainsResolved, TeamsResponse


class GameDetailCreatedBy(BaseModel):
    org_member_id: UUID
    user_id: UUID
    email: EmailStr
    full_name: str | None = None
    nickname: str | None = None


class GameDetailAttendanceSummary(BaseModel):
    going_count: int
    maybe_count: int
    not_going_count: int


class GameDetailAttendanceItemUser(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class GameDetailAttendanceItem(BaseModel):
    org_member_id: UUID
    status: AttendanceStatus
    member_type: MemberType
    included: bool
    billable: bool
    nickname: str | None = None
    user: GameDetailAttendanceItemUser

    class Config:
        from_attributes = True


class GameDetailGuest(BaseModel):
    id: UUID
    name: str
    phone: str | None = None
    billable: bool
    source: str


class GameDetailResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    sport: str | None = None
    location: str | None = None
    start_at: datetime
    created_by: GameDetailCreatedBy | None = None

    attendance_summary: GameDetailAttendanceSummary
    attendance_list: list[GameDetailAttendanceItem]
    game_guests: list[GameDetailGuest]
    captains: CaptainsResolved
    teams: TeamsResponse
    draft: DraftSummary
