from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.game_team import TeamSide


class DraftStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class GameDraft(Base):
    __tablename__ = "game_drafts"
    __table_args__ = (
        UniqueConstraint("game_id", name="uq_game_drafts_game_id"),
        Index("ix_game_drafts_org_id", "org_id"),
        Index("ix_game_drafts_game_id", "game_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)

    status: Mapped[DraftStatus] = mapped_column(Enum(DraftStatus, name="draft_status"), nullable=False)
    order_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="ABBA")
    current_pick_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    game = relationship("Game")
    picks = relationship("GameDraftPick", back_populates="draft", cascade="all, delete-orphan")


class GameDraftPick(Base):
    __tablename__ = "game_draft_picks"
    __table_args__ = (
        Index("ix_game_draft_picks_org_id", "org_id"),
        Index("ix_game_draft_picks_game_id", "game_id"),
        Index("ix_game_draft_picks_draft_id", "draft_id"),
        UniqueConstraint("draft_id", "pick_number", name="uq_game_draft_picks_draft_pick_number"),
        CheckConstraint(
            "(org_member_id IS NOT NULL AND game_guest_id IS NULL) OR (org_member_id IS NULL AND game_guest_id IS NOT NULL)",
            name="ck_game_draft_picks_exactly_one_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    draft_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("game_drafts.id"), nullable=False)

    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pick_number: Mapped[int] = mapped_column(Integer, nullable=False)
    team_side: Mapped[TeamSide] = mapped_column(Enum(TeamSide, name="team_side"), nullable=False)

    org_member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("org_members.id"), nullable=True)
    game_guest_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("game_guests.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    draft = relationship("GameDraft", back_populates="picks")
    org_member = relationship("OrgMember")
    game_guest = relationship("GameGuest")
