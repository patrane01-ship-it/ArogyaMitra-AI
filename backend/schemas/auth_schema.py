"""
ArogyaMitra AI - Auth Schemas
Pydantic request/response models for authentication endpoints.
Per FEATURES_PHASE2.md §2.1.
"""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request Schemas ────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars, 1 uppercase, 1 number)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, max_length=20, description="Gender (optional)")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Opaque refresh token")


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password")


# ── Response Schemas ───────────────────────────────────────────

class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    age: Optional[int] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserProfileResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterResponse(BaseModel):
    message: str = "Registration successful"
    user: UserProfileResponse


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class MessageResponse(BaseModel):
    message: str
