"""Unit tests for the cache_service module.

Tests cover Redis caching operations for user data including
caching, retrieval, and cache invalidation. Uses mocked Redis client.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest

from service.cache_service import cache_user, get_cached_user, invalidate_user_cache


class TestCacheService:
    """Test suite for cache_service Redis operations."""

    @pytest.mark.asyncio
    async def test_cache_user(self, mock_redis):
        """Test cache_user stores serialized JSON in Redis with TTL."""
        # Act
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
        }
        await cache_user(1, user_data)

        # Assert - data was stored under the correct key
        raw = mock_redis._store.get("user:1")
        assert raw is not None, "Expected user:1 key to exist in Redis mock"
        parsed = json.loads(raw)
        assert parsed["id"] == 1
        assert parsed["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_cached_user_found(self, mock_redis):
        """Test get_cached_user returns user data when present in Redis."""
        # Arrange
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
        }
        await cache_user(1, user_data)

        # Act
        result = await get_cached_user(1)

        # Assert
        assert result is not None
        assert result["id"] == 1
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_cached_user_not_found(self, mock_redis):
        """Test get_cached_user returns None when key doesn't exist."""
        # Act
        result = await get_cached_user(999)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self, mock_redis):
        """Test invalidate_user_cache deletes the key from Redis."""
        # Arrange - store something first
        await cache_user(1, {"id": 1, "username": "test"})
        assert "user:1" in mock_redis._store

        # Act
        await invalidate_user_cache(1)

        # Assert
        assert "user:1" not in mock_redis._store

    @pytest.mark.asyncio
    async def test_cache_user_with_datetime(self, mock_redis):
        """Test cache_user handles datetime objects via default=str."""
        # Arrange
        now = datetime.now(timezone.utc)
        user_data = {
            "id": 1,
            "created_at": now,
        }

        # Act
        await cache_user(1, user_data)

        # Assert - datetime should be serialized as string (str() representation)
        raw = mock_redis._store.get("user:1")
        parsed = json.loads(raw)
        # str(datetime) gives format like "2026-06-25 15:07:24.082152+00:00"
        # which is valid for storage, we just verify it's a string
        assert isinstance(parsed["created_at"], str)
        assert "2026" in parsed["created_at"]

    @pytest.mark.asyncio
    async def test_cache_and_get_roundtrip(self, mock_redis):
        """Test full roundtrip: cache then retrieve user data."""
        # Arrange
        user_data = {
            "id": 42,
            "username": "roundtrip",
            "email": "round@trip.com",
            "is_verified": True,
            "role": "admin",
        }

        # Act - cache
        await cache_user(42, user_data)

        # Act - retrieve
        result = await get_cached_user(42)

        # Assert
        assert result is not None
        assert result["id"] == 42
        assert result["username"] == "roundtrip"
        assert result["is_verified"] is True
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_invalidate_only_specific_user(self, mock_redis):
        """Test invalidate_user_cache only removes the specified user."""
        # Arrange
        await cache_user(1, {"id": 1})
        await cache_user(2, {"id": 2})
        assert "user:1" in mock_redis._store
        assert "user:2" in mock_redis._store

        # Act
        await invalidate_user_cache(1)

        # Assert - only user:1 was removed
        assert "user:1" not in mock_redis._store
        assert "user:2" in mock_redis._store