from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OrgGuestBase(BaseModel):
    name: str
    phone: str | None = None


class OrgGuestCreate(OrgGuestBase):
    pass


class OrgGuestUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None


class OrgGuestResponse(OrgGuestBase):
    id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GameGuestBase(BaseModel):
    name: str
    phone: str | None = None


class GameGuestCreate(BaseModel):
    org_guest_id: UUID | None = None
    name: str | None = None
    phone: str | None = None


class GameGuestResponse(GameGuestBase):
    id: UUID
    org_id: UUID
    game_id: UUID
    org_guest_id: UUID | None = None
    created_by_member_id: UUID
    can_delete: bool
    source: str
    billable: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
