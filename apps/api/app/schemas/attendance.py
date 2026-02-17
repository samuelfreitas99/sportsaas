from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.game import AttendanceStatus


class AttendanceSetRequest(BaseModel):
    status: AttendanceStatus


class AttendanceCounts(BaseModel):
    going: int
    maybe: int
    not_going: int


class AttendanceMemberUser(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class AttendanceMember(BaseModel):
    id: UUID
    nickname: str | None = None
    user: AttendanceMemberUser

    class Config:
        from_attributes = True


class AttendanceRow(BaseModel):
    id: UUID
    org_id: UUID
    org_member_id: UUID
    game_id: UUID
    status: AttendanceStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GameAttendanceSummary(BaseModel):
    counts: AttendanceCounts
    my_status: AttendanceStatus | None = None
    going_members: list[AttendanceMember]

