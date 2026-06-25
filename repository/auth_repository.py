"""Data access layer for user authentication operations.

This module provides the AuthRepository class which encapsulates all
database operations related to user accounts, including creation,
lookups by various fields, email verification, and password reset.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class AuthRepository:
    """Repository for database operations on users.

    Handles all direct database interactions for the User model.
    Provides methods for creating, querying, and updating user records.

    Args:
        db: An async SQLAlchemy session for database operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, username: str, email: str, password_hash: str, verification_token: str) -> User:
        """Create a new user in the database.

        Args:
            username: Unique display name for the user.
            email: Unique email address.
            password_hash: Bcrypt-hashed password.
            verification_token: Token for email verification.

        Returns:
            User: The newly created user instance.
        """
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            verification_token=verification_token,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by their primary key ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            User | None: The user if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by their email address.

        Args:
            email: The email address to look up.

        Returns:
            User | None: The user if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """Get a user by their username.

        Args:
            username: The username to look up.

        Returns:
            User | None: The user if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_verification_token(self, token: str) -> User | None:
        """Get a user by their email verification token.

        Args:
            token: The verification token string.

        Returns:
            User | None: The user if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.verification_token == token))
        return result.scalars().first()

    async def get_by_reset_token(self, token: str) -> User | None:
        """Get a user by their password reset token.

        Args:
            token: The password reset token string.

        Returns:
            User | None: The user if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.reset_token == token))
        return result.scalars().first()

    async def update_avatar(self, user_id: int, avatar_url: str) -> User | None:
        """Update a user's avatar URL.

        Args:
            user_id: The user's unique identifier.
            avatar_url: The new avatar image URL.

        Returns:
            User | None: The updated user if found, None otherwise.
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def verify_user(self, user: User) -> User:
        """Mark a user's email as verified and clear the verification token.

        Args:
            user: The user instance to verify.

        Returns:
            User: The updated user with verification flag set.
        """
        user.is_verified = True
        user.verification_token = None
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_reset_token(self, user: User, reset_token: str, expiry: datetime) -> User:
        """Store a password reset token and its expiry for a user.

        Args:
            user: The user instance.
            reset_token: The generated reset token string.
            expiry: Timestamp when the reset token expires.

        Returns:
            User: The updated user with reset token set.
        """
        user.reset_token = reset_token
        user.reset_token_expiry = expiry
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: User, password_hash: str) -> User:
        """Update a user's password and clear any reset tokens.

        Args:
            user: The user instance.
            password_hash: The new bcrypt-hashed password.

        Returns:
            User: The updated user with new password hash.
        """
        user.password_hash = password_hash
        user.reset_token = None
        user.reset_token_expiry = None
        await self.db.commit()
        await self.db.refresh(user)
        return user