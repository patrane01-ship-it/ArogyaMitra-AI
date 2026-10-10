"""
ArogyaMitra AI - Auth Router
Registration, login, token refresh, profile management, and logout endpoints.
Per FEATURES_PHASE2.md §2.1 and PRODUCTION_BACKEND.md §5.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, Request, Cookie
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.logger import logger
from backend.database import get_db
from backend.models.user import User
from backend.repositories.user_repo import UserRepository
from backend.services.auth_service import AuthService
from backend.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    RegisterResponse,
    TokenResponse,
    RefreshResponse,
    UserProfileResponse,
    LogoutResponse,
    MessageResponse,
)
from backend.exceptions.arogya_errors import (
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    WeakPasswordError,
    UserNotFoundError,
)
from backend.core.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# Refresh token cookie name
_REFRESH_COOKIE = "arogya_refresh"
_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400  # seconds


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set httpOnly secure cookie with refresh token."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="strict",
        secure=settings.ENVIRONMENT == "production",
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(key=_REFRESH_COOKIE, httponly=True, samesite="strict")


# ── POST /api/auth/register ────────────────────────────────────
@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    - Validates password strength
    - Hashes password with bcrypt
    - Returns user profile (no tokens on register; user must log in)
    """
    AuthService.validate_password_strength(body.password)

    user = User(
        email=body.email.strip().lower(),
        hashed_password=AuthService.hash_password(body.password),
        full_name=body.full_name.strip(),
        date_of_birth=body.date_of_birth,
        gender=body.gender,
    )
    user.validate()

    repo = UserRepository(db)
    created = await repo.create(user)
    await db.commit()

    logger.info(f"[Auth] New user registered: {created.email} | id={created.user_id}")
    return RegisterResponse(
        message="Registration successful. Please log in.",
        user=UserProfileResponse(**created.to_dict()),
    )


# ── POST /api/auth/login ───────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and issue JWT access token + httpOnly refresh cookie.
    """
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    if not user or not AuthService.verify_password(body.password, user.hashed_password):
        raise InvalidCredentialsError()

    # Issue tokens
    access_token = AuthService.create_access_token(user.user_id, user.email)
    raw_refresh, hashed_refresh = AuthService.create_refresh_token()

    # Persist refresh token hash
    await repo.set_refresh_token_hash(user.user_id, hashed_refresh)
    await repo.update_last_login(user.user_id)
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)

    logger.info(f"[Auth] User logged in: {user.email} | id={user.user_id}")
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfileResponse(**user.to_dict()),
    )


# ── POST /api/auth/refresh ─────────────────────────────────────
@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    cookie_refresh: Optional[str] = Cookie(default=None, alias=_REFRESH_COOKIE),
):
    """
    Rotate refresh token and issue a new access token.
    Accepts refresh token from httpOnly cookie (preferred) or request body.
    """
    # Accept token from cookie or fallback to Authorization header (for mobile)
    raw_token = cookie_refresh
    if not raw_token:
        # Try Authorization: Bearer <refresh_token>
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:]

    if not raw_token:
        raise InvalidTokenError("No refresh token provided")

    hashed = AuthService.hash_refresh_token(raw_token)

    # Find user by refresh token hash
    from sqlalchemy import select
    from backend.models.user import User as UserModel
    stmt = select(UserModel).where(
        UserModel.refresh_token_hash == hashed,
        UserModel.is_active.is_(True),
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise InvalidTokenError("Refresh token is invalid or has been revoked")

    # Rotate: issue new access + refresh
    access_token = AuthService.create_access_token(user.user_id, user.email)
    new_raw, new_hashed = AuthService.create_refresh_token()

    repo = UserRepository(db)
    await repo.set_refresh_token_hash(user.user_id, new_hashed)
    await db.commit()

    _set_refresh_cookie(response, new_raw)

    logger.debug(f"[Auth] Token rotated for user_id={user.user_id}")
    return RefreshResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── POST /api/auth/logout ──────────────────────────────────────
@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Invalidate user session: clear refresh token hash and cookie.
    """
    repo = UserRepository(db)
    await repo.set_refresh_token_hash(user_id, None)
    await db.commit()

    _clear_refresh_cookie(response)

    logger.info(f"[Auth] User logged out: user_id={user_id}")
    return LogoutResponse()


# ── GET /api/auth/me ───────────────────────────────────────────
@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user's profile."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundError()
    return UserProfileResponse(**user.to_dict())


# ── PATCH /api/auth/me ─────────────────────────────────────────
@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile fields."""
    repo = UserRepository(db)
    updated = await repo.update_profile(
        user_id=user_id,
        full_name=body.full_name,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
    )
    await db.commit()

    if not updated:
        raise UserNotFoundError()

    return UserProfileResponse(**updated.to_dict())


# ── POST /api/auth/change-password ────────────────────────────
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    - Verifies current password before accepting new one.
    - Validates new password strength.
    - Rotates refresh token to force re-login on all other devices.
    """
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundError()

    if not AuthService.verify_password(body.current_password, user.hashed_password):
        raise InvalidCredentialsError("Current password is incorrect")

    AuthService.validate_password_strength(body.new_password)
    user.hashed_password = AuthService.hash_password(body.new_password)
    # Invalidate all refresh tokens (force re-login everywhere)
    user.refresh_token_hash = None
    await db.commit()

    logger.info(f"[Auth] Password changed for user_id={user_id}")
    return MessageResponse(message="Password changed successfully. Please log in again.")
