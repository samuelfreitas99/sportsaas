from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema
from app.schemas.token import Token
from app.routers.deps import get_current_user
from datetime import timedelta
from app.core.config import settings
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from json import JSONDecodeError

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=UserSchema)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login_access_token(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    email: str | None = None
    password: str | None = None

    content_type = (request.headers.get("content-type") or "").lower()

    # 1) JSON (recomendado)
    if "application/json" in content_type:
        try:
            data = await request.json()
        except JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        except Exception:
            # evita 500 por body estranho / stream / etc
            raise HTTPException(status_code=400, detail="Invalid request body")

        if isinstance(data, dict):
            email = data.get("email")
            password = data.get("password")

    # 2) Form (compat opcional: username/password)
    elif (
        "application/x-www-form-urlencoded" in content_type
        or "multipart/form-data" in content_type
    ):
        form = await request.form()
        email = form.get("email") or form.get("username")
        password = form.get("password")

    # 3) Sem content-type ou outros: tenta JSON, se falhar, tenta form (sem quebrar)
    else:
        # tenta JSON
        try:
            data = await request.json()
            if isinstance(data, dict):
                email = data.get("email")
                password = data.get("password")
        except Exception:
            # tenta form
            try:
                form = await request.form()
                email = form.get("email") or form.get("username")
                password = form.get("password")
            except Exception:
                pass

    if not email or not password:
        raise HTTPException(status_code=422, detail="email/password required")

    user = db.query(User).filter(User.email == email).first()
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        subject=user.email, expires_delta=refresh_token_expires
    )

    cookie_kwargs: dict = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie("access_token", access_token, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh_token, **cookie_kwargs)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh")
def refresh_token(response: Response, request: Request, db: Session = Depends(get_db)):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
        )

    try:
        payload = jwt.decode(
            refresh, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise JWTError("invalid token type")
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )

    cookie_kwargs: dict = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie("access_token", access_token, **cookie_kwargs)
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    # se COOKIE_DOMAIN estiver vazio, delete_cookie recebe domain=None (ok)
    response.delete_cookie("access_token", path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", path="/", domain=settings.COOKIE_DOMAIN)
    return {"ok": True}
