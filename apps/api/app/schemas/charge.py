from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.org_charge import ChargeStatus, ChargeType
from app.models.org_member import OrgRole


class OrgChargeBase(BaseModel):
    org_member_id: UUID
    cycle_key: str
    type: ChargeType
    status: ChargeStatus
    amount: float


class OrgChargeUser(BaseModel):
    id: UUID
    email: str
    full_name: str | None = None

    class Config:
        from_attributes = True


class OrgChargeMember(BaseModel):
    id: UUID
    user_id: UUID
    org_id: UUID
    role: OrgRole
    user: OrgChargeUser

    class Config:
        from_attributes = True


class OrgChargeResponse(OrgChargeBase):
    id: UUID
    org_id: UUID
    ledger_entry_id: UUID | None = None
    created_by_id: UUID | None = None
    paid_at: datetime | None = None
    voided_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    org_member: OrgChargeMember

    class Config:
        from_attributes = True


class OrgChargeListResponse(BaseModel):
    items: list[OrgChargeResponse]


class UpdateChargeStatusRequest(BaseModel):
    status: ChargeStatus

