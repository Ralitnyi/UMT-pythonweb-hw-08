"""Pydantic schemas for authentication and user management.

This module defines request/response data models for user registration,
login, email verification, password reset, and profile operations.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration request.

    Attributes:
        username: Unique display name (3-50 characters).
        email: Valid email address for the user.
        password: Password for authentication (6-255 characters).
    """
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=255, description="User password")


class UserResponse(BaseModel):
    """Schema for user data in API responses.

    Attributes:
        id: User's unique identifier.
        username: User's display name.
        email: User's email address.
        avatar_url: Optional URL to user's avatar.
        is_verified: Email verification status.
        role: User role for authorization ('user' or 'admin').
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.
    """
    id: int
    username: str
    email: str
    avatar_url: str | None = None
    is_verified: bool
    role: str = 'user'
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response after successful login.

    Attributes:
        access_token: JWT access token string.
        token_type: Token type, always 'bearer'.
    """
    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    """Schema for user login request.

    Attributes:
        email: User's email address.
        password: User's password.
    """
    email: EmailStr
    password: str


class RequestEmail(BaseModel):
    """Schema for requesting a new email verification link.

    Attributes:
        email: The email address to send verification to.
    """
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset email.

    Attributes:
        email: The email address associated with the account.
    """
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming a password reset with a new password.

    Attributes:
        token: Reset token received via email.
        new_password: New password (6-255 characters).
    """
    token: str = Field(..., description="Reset token received via email")
    new_password: str = Field(..., min_length=6, max_length=255, description="New password")