from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.game_draft import DraftStatus
from app.models.game_team import TeamSide
from app.models.org_member import MemberType
from app.schemas.teams import PublicUser, TeamsResponse


class DraftStartResponse(BaseModel):
    status: DraftStatus


class DraftPickRequest(BaseModel):
    team_side: TeamSide
    org_member_id: UUID | None = None
    game_guest_id: UUID | None = None


class DraftPickItemMember(BaseModel):
    type: str = "MEMBER"
    org_member_id: UUID
    nickname: str | None = None
    member_type: MemberType
    included: bool
    billable: bool
    user: PublicUser


class DraftPickItemGuest(BaseModel):
    type: str = "GUEST"
    game_guest_id: UUID
    name: str
    phone: str | None = None
    billable: bool
    source: str


class DraftPickResponse(BaseModel):
    id: UUID
    round_number: int
    pick_number: int
    team_side: TeamSide
    created_at: datetime
    item: DraftPickItemMember | DraftPickItemGuest

    class Config:
        from_attributes = True


class DraftSummary(BaseModel):
    status: DraftStatus
    current_turn_team_side: TeamSide | None = None
    picks_count: int
    remaining_count: int


class DraftStateResponse(BaseModel):
    status: DraftStatus
    order_mode: str
    current_pick_index: int
    current_turn_team_side: TeamSide | None = None
    picks: list[DraftPickResponse]
    remaining_pool: list[DraftPickItemMember | DraftPickItemGuest]
    teams: TeamsResponse
