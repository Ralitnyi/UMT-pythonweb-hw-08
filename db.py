"""Database configuration and session management.

This module provides the SQLAlchemy async engine, session factory,
and Redis client configuration. Settings are loaded from environment
variables via Pydantic's BaseSettings.
"""

import os
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Reads from .env file or environment variables. Provides settings for
    database connection, JWT authentication, Redis caching, Cloudinary
    image storage, and email service.

    Attributes:
        database_url: PostgreSQL connection string.
        debug: Enable debug mode.
        secret_key: Secret key for JWT token signing.
        algorithm: JWT signing algorithm (default: HS256).
        access_token_expire_minutes: JWT token lifetime in minutes.
        redis_url: Redis connection URL for caching.
        cloudinary_cloud_name: Cloudinary cloud name for image uploads.
        cloudinary_api_key: Cloudinary API key.
        cloudinary_api_secret: Cloudinary API secret.
        mail_username: SMTP username for email sending.
        mail_password: SMTP password.
        mail_from: Sender email address.
        mail_port: SMTP server port.
        mail_server: SMTP server hostname.
    """

    database_url: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/contacts_db')
    debug: bool = False

    # JWT settings
    secret_key: str = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    algorithm: str = os.getenv('ALGORITHM', 'HS256')
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

    # Redis settings
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Cloudinary settings
    cloudinary_cloud_name: str = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    cloudinary_api_key: str = os.getenv('CLOUDINARY_API_KEY', '')
    cloudinary_api_secret: str = os.getenv('CLOUDINARY_API_SECRET', '')

    # Email settings
    mail_username: str = os.getenv('MAIL_USERNAME', '')
    mail_password: str = os.getenv('MAIL_PASSWORD', '')
    mail_from: str = os.getenv('MAIL_FROM', '')
    mail_port: int = int(os.getenv('MAIL_PORT', '587'))
    mail_server: str = os.getenv('MAIL_SERVER', '')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'allow'


settings = Settings()

# Redis client
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

if settings.database_url.startswith('postgresql://'):
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
else:
    database_url = settings.database_url

engine = create_async_engine(database_url, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    """Dependency function to get an async database session.

    Provides a FastAPI-compatible async generator that yields a database
    session and automatically handles cleanup via the context manager.

    Yields:
        AsyncSession: An SQLAlchemy async session bound to the engine.
    """
    async with SessionLocal() as db:
        yield db