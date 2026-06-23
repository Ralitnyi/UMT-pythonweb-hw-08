from datetime import datetime, timedelta, timezone
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from repository.auth_repository import AuthRepository
from schemas.auth import UserCreate, UserResponse, TokenResponse
from models.user import User

from db import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def generate_verification_token() -> str:
    """Generate a unique verification token"""
    return str(uuid.uuid4())


class AuthService:
    """Service layer for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.repository = AuthRepository(db)

    async def register(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        # Check if email already exists
        existing = await self.repository.get_by_email(user_data.email)
        if existing:
            raise ValueError('User with this email already exists')

        # Check if username already exists
        existing = await self.repository.get_by_username(user_data.username)
        if existing:
            raise ValueError('User with this username already exists')

        # Hash password and create user
        password_hash = get_password_hash(user_data.password)
        verification_token = generate_verification_token()
        user = await self.repository.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            verification_token=verification_token,
        )
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate user and return JWT token"""
        user = await self.repository.get_by_email(email)
        if not user:
            raise ValueError('Invalid email or password')

        if not verify_password(password, user.password_hash):
            raise ValueError('Invalid email or password')

        # Generate JWT
        access_token = create_access_token({'sub': str(user.id)})
        return TokenResponse(access_token=access_token)

    async def verify_email(self, token: str) -> UserResponse:
        """Verify user email with token"""
        user = await self.repository.get_by_verification_token(token)
        if not user:
            raise ValueError('Invalid verification token')

        verified_user = await self.repository.verify_user(user)
        return UserResponse.model_validate(verified_user)

    async def get_current_user(self, user_id: int) -> User | None:
        """Get user by ID"""
        return await self.repository.get_by_id(user_id)

    async def update_avatar(self, user_id: int, avatar_url: str) -> UserResponse:
        """Update user avatar"""
        user = await self.repository.update_avatar(user_id, avatar_url)
        if not user:
            raise ValueError('User not found')
        return UserResponse.model_validate(user)