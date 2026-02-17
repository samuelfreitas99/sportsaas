from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class TeamSide(str, enum.Enum):
    A = "A"
    B = "B"


class GameTeamMember(Base):
    __tablename__ = "game_team_members"
    __table_args__ = (
        UniqueConstraint("game_id", "org_member_id", name="uq_game_team_members_game_member"),
        Index("ix_game_team_members_org_id", "org_id"),
        Index("ix_game_team_members_game_id", "game_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    org_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("org_members.id"), nullable=False)
    team: Mapped[TeamSide] = mapped_column(Enum(TeamSide, name="team_side"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    game = relationship("Game")
    org_member = relationship("OrgMember")


class GameTeamGuest(Base):
    __tablename__ = "game_team_guests"
    __table_args__ = (
        UniqueConstraint("game_id", "game_guest_id", name="uq_game_team_guests_game_guest"),
        Index("ix_game_team_guests_org_id", "org_id"),
        Index("ix_game_team_guests_game_id", "game_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    game_guest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("game_guests.id"), nullable=False)
    team: Mapped[TeamSide] = mapped_column(Enum(TeamSide, name="team_side"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    game = relationship("Game")
    game_guest = relationship("GameGuest")
