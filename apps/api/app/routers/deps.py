from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData

from app.models.org_member import OrgMember, OrgRole

def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get("access_token")
    return cookie_token.strip() if cookie_token else None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        token_data = TokenData(email=email)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.email == token_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_org_member(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMember:
    membership = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id, OrgMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not a member of this org",
        )

    return membership


def require_org_admin(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMember:
    membership = require_org_member(org_id=org_id, db=db, current_user=current_user)
    if membership.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
    return membership


def require_org_owner(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMember:
    membership = require_org_member(org_id=org_id, db=db, current_user=current_user)
    if membership.role != OrgRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
    return membership
