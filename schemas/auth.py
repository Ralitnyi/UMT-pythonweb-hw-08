from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=255, description="User password")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: str
    avatar_url: str | None = None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class RequestEmail(BaseModel):
    """Schema for requesting email verification"""
    email: EmailStr