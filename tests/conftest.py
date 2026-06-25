"""Shared fixtures and test configuration for all tests.

This module provides pytest fixtures for testing with a SQLite in-memory
database, mocked Redis, and HTTP test client for the FastAPI application.
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from models.base import Base
from db import get_db, settings


# Use in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite://"

# Override settings for testing
settings.database_url = TEST_DATABASE_URL
settings.secret_key = "test-secret-key"
settings.algorithm = "HS256"
settings.access_token_expire_minutes = 30


def get_test_engine():
    """Create a new engine for test database."""
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory database session for each test.

    Creates all tables before the test and drops them after.
    """
    engine = get_test_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP test client with overridden database dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def mock_redis(monkeypatch):
    """Mock Redis operations to prevent real Redis connections.

    Patches redis_client in ALL modules that import it to avoid
    the 'from db import redis_client' import-time binding issue.
    """

    class MockRedis:
        """In-memory mock for Redis client."""

        def __init__(self):
            self._store = {}

        async def setex(self, key, ttl, value):
            self._store[key] = value

        async def get(self, key):
            return self._store.get(key, None)

        async def delete(self, key):
            self._store.pop(key, None)

    mock_redis_instance = MockRedis()

    # Patch at the source (db module)
    monkeypatch.setattr("db.redis_client", mock_redis_instance)

    # Also patch in all modules that do 'from db import redis_client'
    # to avoid the import-time reference binding issue
    import service.cache_service
    monkeypatch.setattr(service.cache_service, "redis_client", mock_redis_instance)

    return mock_redis_instance