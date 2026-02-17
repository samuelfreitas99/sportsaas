from pydantic import BaseModel
from uuid import UUID

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
