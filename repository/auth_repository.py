from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class AuthRepository:
    """Repository for database operations on users"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, username: str, email: str, password_hash: str, verification_token: str) -> User:
        """Create a new user"""
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
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """Get user by username"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_verification_token(self, token: str) -> User | None:
        """Get user by verification token"""
        result = await self.db.execute(select(User).where(User.verification_token == token))
        return result.scalars().first()

    async def update_avatar(self, user_id: int, avatar_url: str) -> User | None:
        """Update user avatar"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def verify_user(self, user: User) -> User:
        """Mark user as verified"""
        user.is_verified = True
        user.verification_token = None
        await self.db.commit()
        await self.db.refresh(user)
        return user