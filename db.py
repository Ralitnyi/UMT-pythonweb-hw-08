import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/contacts_db')
    debug: bool = False

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


