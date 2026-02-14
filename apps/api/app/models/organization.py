from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class OrgRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class MemberType(str, enum.Enum):
    MONTHLY = "MONTHLY"
    GUEST = "GUEST"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)

    # bate com o schema (owner_id: UUID) e com o router (owner_id=current_user.id)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    members = relationship("OrgMember", back_populates="organization", cascade="all, delete-orphan")
    invites = relationship("OrgInvite", back_populates="organization", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="organization", cascade="all, delete-orphan")
    games = relationship("Game", back_populates="organization", cascade="all, delete-orphan")



class OrgMember(Base):
    __tablename__ = "org_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    role: Mapped[OrgRole] = mapped_column(Enum(OrgRole, name="org_role"), default=OrgRole.MEMBER, nullable=False)
    member_type: Mapped[MemberType] = mapped_column(
        Enum(MemberType, name="member_type"), default=MemberType.GUEST, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="members")


class OrgInvite(Base):
    __tablename__ = "org_invites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    role: Mapped[OrgRole] = mapped_column(Enum(OrgRole, name="org_invite_role"), default=OrgRole.MEMBER, nullable=False)

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization", back_populates="invites")
