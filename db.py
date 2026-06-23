import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/contacts_db')
    debug: bool = False

    # JWT settings
    secret_key: str = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    algorithm: str = os.getenv('ALGORITHM', 'HS256')
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

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

if settings.database_url.startswith('postgresql://'):
    database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
else:
    database_url = settings.database_url

engine = create_async_engine(database_url, echo=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    """Dependency function to get an async database session"""
    async with SessionLocal() as db:
        yield db


