from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.user import User as UserSchema, UserUpdate

router = APIRouter()


@router.get("/users/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/users/me", response_model=UserSchema)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data:
        current_user.full_name = data["full_name"]
    if "avatar_url" in data:
        current_user.avatar_url = data["avatar_url"]
    if "phone" in data:
        current_user.phone = data["phone"]

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
