from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.org_billing_settings import BillingCycle, BillingMode


class OrgBillingSettingsBase(BaseModel):
    billing_mode: BillingMode
    cycle: BillingCycle
    cycle_weeks: int | None = None
    anchor_date: date
    due_day: int
    membership_amount: float
    session_amount: float


class OrgBillingSettingsPut(OrgBillingSettingsBase):
    pass


class OrgBillingSettingsResponse(OrgBillingSettingsBase):
    id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateChargesRequest(BaseModel):
    cycle_key: str | None = None
    force: bool = False

