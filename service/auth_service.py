"""Service layer for authentication and user management.

This module implements the business logic for user authentication,
including registration, login, email verification, password reset,
and user profile management with Redis caching integration.
"""

from datetime import datetime, timedelta, timezone
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from repository.auth_repository import AuthRepository
from schemas.auth import UserCreate, UserResponse, TokenResponse
from models.user import User
from service.cache_service import cache_user, get_cached_user, invalidate_user_cache

from db import settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

RESET_TOKEN_EXPIRE_MINUTES = 15


def get_password_hash(password: str) -> str:
    """Hash a plain text password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        str: The bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash.

    Args:
        plain_password: The plain text password to check.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token with an expiry claim.

    Args:
        data: Dictionary containing claims to encode (must include 'sub').

    Returns:
        str: The encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def generate_verification_token() -> str:
    """Generate a unique UUID-based token for email verification.

    Returns:
        str: A unique verification token string.
    """
    return str(uuid.uuid4())


def generate_reset_token() -> str:
    """Generate a unique UUID-based token for password reset.

    Returns:
        str: A unique reset token string.
    """
    return str(uuid.uuid4())


def user_to_dict(user: User) -> dict:
    """Convert a User model instance to a serializable dictionary for Redis caching.

    Args:
        user: The User model instance to convert.

    Returns:
        dict: Dictionary with user data suitable for JSON serialization.
    """
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'avatar_url': user.avatar_url,
        'is_verified': user.is_verified,
        'role': user.role,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None,
    }


class AuthService:
    """Service layer for authentication operations.

    Orchestrates business logic for user registration, login,
    email verification, password reset, and profile updates.
    Integrates with Redis caching for performance optimization.

    Args:
        db: An async SQLAlchemy session for database operations.
    """

    def __init__(self, db: AsyncSession):
        self.repository = AuthRepository(db)

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user account.

        Validates that the email and username are unique, hashes the
        password, creates the user record, and returns the user data.

        Args:
            user_data: Registration data including username, email, and password.

        Returns:
            User: The newly created user ORM instance.

        Raises:
            ValueError: If the email or username already exists.
        """
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
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user and return a JWT token.

        Verifies the email/password combination, caches the user data
        in Redis, and issues a JWT access token.

        Args:
            email: The user's email address.
            password: The user's plain text password.

        Returns:
            TokenResponse: JWT access token.

        Raises:
            ValueError: If the email or password is invalid.
        """
        user = await self.repository.get_by_email(email)
        if not user:
            raise ValueError('Invalid email or password')

        if not verify_password(password, user.password_hash):
            raise ValueError('Invalid email or password')

        # Cache the user data
        await cache_user(user.id, user_to_dict(user))

        # Generate JWT
        access_token = create_access_token({'sub': str(user.id)})
        return TokenResponse(access_token=access_token)

    async def verify_email(self, token: str) -> UserResponse:
        """Verify a user's email address using a verification token.

        Looks up the user by token, marks them as verified, and
        invalidates the Redis cache.

        Args:
            token: The email verification token.

        Returns:
            UserResponse: The updated user data with verification flag set.

        Raises:
            ValueError: If the verification token is invalid.
        """
        user = await self.repository.get_by_verification_token(token)
        if not user:
            raise ValueError('Invalid verification token')

        verified_user = await self.repository.verify_user(user)
        # Invalidate cache after verification
        await invalidate_user_cache(verified_user.id)
        return UserResponse.model_validate(verified_user)

    async def get_current_user(self, user_id: int) -> User | None:
        """Retrieve a user by ID, checking Redis cache first.

        Implements a cache-aside pattern: tries Redis first, falls back
        to database, and caches the result for future requests.

        Args:
            user_id: The user's unique identifier.

        Returns:
            User | None: The user if found, None otherwise.
        """
        # Try cache first
        cached = await get_cached_user(user_id)
        if cached is not None:
            # Reconstruct User-like object from cached data
            user = User(
                id=cached['id'],
                username=cached['username'],
                email=cached['email'],
                avatar_url=cached.get('avatar_url'),
                is_verified=cached.get('is_verified', False),
                role=cached.get('role', 'user'),
                created_at=datetime.fromisoformat(cached['created_at']) if cached.get('created_at') else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(cached['updated_at']) if cached.get('updated_at') else datetime.now(timezone.utc),
            )
            return user

        # Fallback to DB
        user = await self.repository.get_by_id(user_id)
        if user:
            # Cache for future requests
            await cache_user(user_id, user_to_dict(user))
        return user

    async def update_avatar(self, user_id: int, avatar_url: str) -> UserResponse:
        """Update a user's avatar URL and invalidate cache.

        Args:
            user_id: The user's unique identifier.
            avatar_url: The new avatar image URL.

        Returns:
            UserResponse: The updated user data.

        Raises:
            ValueError: If the user is not found.
        """
        user = await self.repository.update_avatar(user_id, avatar_url)
        if not user:
            raise ValueError('User not found')
        # Invalidate cache so next request gets fresh data
        await invalidate_user_cache(user_id)
        return UserResponse.model_validate(user)

    async def request_password_reset(self, email: str) -> str | None:
        """Generate and store a password reset token for the user.

        Uses a security best practice: returns the same response whether
        the email exists or not, to prevent email enumeration attacks.

        Args:
            email: The email address to send the reset token to.

        Returns:
            str | None: The reset token if user exists, None otherwise.
        """
        user = await self.repository.get_by_email(email)
        if not user:
            return None

        reset_token = generate_reset_token()
        expiry = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        await self.repository.set_reset_token(user, reset_token, expiry)
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> UserResponse:
        """Reset a user's password using a valid reset token.

        Validates the token, checks expiry, updates the password,
        clears the reset token, and invalidates the cache.

        Args:
            token: The password reset token.
            new_password: The new plain text password.

        Returns:
            UserResponse: The updated user data.

        Raises:
            ValueError: If the token is invalid or expired.
        """
        user = await self.repository.get_by_reset_token(token)
        if not user:
            raise ValueError('Invalid or expired reset token')

        # Check expiry
        if user.reset_token_expiry is None or user.reset_token_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError('Reset token has expired')

        # Update password and clear token
        password_hash = get_password_hash(new_password)
        updated_user = await self.repository.update_password(user, password_hash)
        # Invalidate cache since user data changed
        await invalidate_user_cache(updated_user.id)
        return UserResponse.model_validate(updated_user)