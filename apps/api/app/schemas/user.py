from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None

class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None

class User(UserBase):
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True
