from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
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


class OrgMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("user_id", "org_id", name="uq_org_members_user_org"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )

    role: Mapped[OrgRole] = mapped_column(Enum(OrgRole, name="org_role"), default=OrgRole.MEMBER, nullable=False)
    member_type: Mapped[MemberType] = mapped_column(
        Enum(MemberType, name="member_type"), default=MemberType.MONTHLY, nullable=False
    )
    nickname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="members")
