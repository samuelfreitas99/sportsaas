from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.game import AttendanceStatus

class GameBase(BaseModel):
    title: str
    sport: str
    location: str
    start_at: datetime
    notes: str | None = None

class GameCreate(GameBase):
    pass

class Game(GameBase):
    id: UUID
    org_id: UUID

    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    status: AttendanceStatus

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    user_id: UUID
    game_id: UUID

    class Config:
        from_attributes = True
