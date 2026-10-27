import jwt
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models import StudentProfile, User
from app.deps import DB, CurrentUser
from app.schemas.common import LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut
from app.services.governance import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
        role=user.role,  # type: ignore[arg-type]
    )


@router.post("/register", response_model=TokenPair, status_code=201)
def register(body: RegisterIn, db: DB) -> TokenPair:
    """Public sign-up always creates a student. Staff accounts are created by an admin."""
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=email, full_name=body.full_name, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    db.add(StudentProfile(user_id=user.id))
    db.commit()
    return _tokens(user)


@router.post("/login", response_model=TokenPair)
def login(body: LoginIn, db: DB) -> TokenPair:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.role != "student":
        audit(db, user.id, "staff_login")
        db.commit()
    return _tokens(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshIn, db: DB) -> TokenPair:
    try:
        claims = decode_token(body.refresh_token, "refresh")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from None
    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return _tokens(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
