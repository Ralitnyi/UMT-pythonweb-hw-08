"""User model for authentication and user management.

This module defines the User ORM model that represents application users.
Each user can have multiple contacts, manage their profile, and use
email verification and password reset features.
"""

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class User(Base):
    """Represents a registered user in the system.

    Maps to the 'users' database table. Stores authentication credentials,
    profile information, email verification status, and role-based access
    control data.

    Attributes:
        id: Primary key identifier.
        username: Unique display name (max 50 chars).
        email: Unique email address (max 100 chars).
        password_hash: Bcrypt-hashed password (max 255 chars).
        avatar_url: Optional URL to user's avatar image.
        is_verified: Whether the user's email has been verified.
        verification_token: Token for email verification flow.
        role: User role for authorization ('user' or 'admin').
        reset_token: Token for password reset flow.
        reset_token_expiry: Expiration timestamp for reset token.
        created_at: Timestamp when the user was created.
        updated_at: Timestamp of last update.
        contacts: List of Contact objects owned by this user.
    """

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default='user', nullable=False)
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="user")