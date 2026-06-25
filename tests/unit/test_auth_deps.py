"""Unit tests for the auth_deps module.

Tests cover JWT token decoding, current user extraction,
and role-based access control dependency.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from jose import JWTError

from service.auth_deps import get_current_user, require_role
from models.user import User


class MockCredentials:
    """Mock for HTTPAuthorizationCredentials."""
    def __init__(self, token: str):
        self.credentials = token
        self.scheme = "Bearer"


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token(self, db_session, monkeypatch):
        """Test get_current_user returns user with valid JWT."""
        # Arrange - mock JWT decode
        payload = {"sub": "1"}
        monkeypatch.setattr(
            "service.auth_deps.jwt.decode",
            MagicMock(return_value=payload),
        )

        # Mock Redis calls to avoid connection errors
        async def mock_get_cached(*args):
            return None
        async def mock_cache_user(*args, **kwargs):
            return None
        monkeypatch.setattr("service.auth_service.get_cached_user", mock_get_cached)
        monkeypatch.setattr("service.auth_service.cache_user", mock_cache_user)

        # Create a real user in the test database
        from repository.auth_repository import AuthRepository
        repo = AuthRepository(db_session)
        user = await repo.create_user(
            username="depstest",
            email="depstest@example.com",
            password_hash="hash",
            verification_token="token",
        )

        # Act
        result = await get_current_user(
            credentials=MockCredentials("valid-token"),
            db=db_session,
        )

        # Assert
        assert result is not None
        assert result.id == user.id
        assert result.username == "depstest"

    @pytest.mark.asyncio
    async def test_invalid_token(self, db_session, monkeypatch):
        """Test get_current_user raises 401 with invalid JWT."""
        # Arrange - mock JWT decode to raise JWTError
        monkeypatch.setattr(
            "service.auth_deps.jwt.decode",
            MagicMock(side_effect=JWTError("Invalid token")),
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                credentials=MockCredentials("invalid-token"),
                db=db_session,
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_sub_claim(self, db_session, monkeypatch):
        """Test get_current_user raises 401 when sub claim is missing."""
        # Arrange - mock JWT decode with no sub
        payload = {"other_claim": "value"}
        monkeypatch.setattr(
            "service.auth_deps.jwt.decode",
            MagicMock(return_value=payload),
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                credentials=MockCredentials("token-no-sub"),
                db=db_session,
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found(self, db_session, monkeypatch):
        """Test get_current_user raises 401 when user doesn't exist."""
        # Arrange - mock JWT decode with valid sub
        payload = {"sub": "9999"}
        monkeypatch.setattr(
            "service.auth_deps.jwt.decode",
            MagicMock(return_value=payload),
        )

        # Mock Redis calls to avoid connection errors
        async def mock_get_cached(*args):
            return None
        async def mock_cache_user(*args, **kwargs):
            return None
        monkeypatch.setattr("service.auth_service.get_cached_user", mock_get_cached)
        monkeypatch.setattr("service.auth_service.cache_user", mock_cache_user)

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                credentials=MockCredentials("token-for-nonexistent"),
                db=db_session,
            )
        assert exc_info.value.status_code == 401


class TestRequireRole:
    """Test suite for require_role dependency."""

    @pytest.mark.asyncio
    async def test_admin_role_allowed(self):
        """Test require_role('admin') allows admin user."""
        # Arrange
        admin_user = User(
            id=1,
            username="admin",
            email="admin@example.com",
            password_hash="hash",
            role="admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        role_checker = require_role("admin")

        # Act
        result = await role_checker(current_user=admin_user)

        # Assert
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_user_role_denied_for_admin(self):
        """Test require_role('admin') raises 403 for regular user."""
        # Arrange
        regular_user = User(
            id=2,
            username="user",
            email="user@example.com",
            password_hash="hash",
            role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        role_checker = require_role("admin")

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=regular_user)
        assert exc_info.value.status_code == 403
        assert "admin" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_user_role_allowed(self):
        """Test require_role('user') allows regular user."""
        # Arrange
        regular_user = User(
            id=3,
            username="user",
            email="user@example.com",
            password_hash="hash",
            role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        role_checker = require_role("user")

        # Act
        result = await role_checker(current_user=regular_user)

        # Assert
        assert result == regular_user

    @pytest.mark.asyncio
    async def test_custom_role_denied(self):
        """Test require_role denies user with mismatching role."""
        # Arrange
        viewer_user = User(
            id=4,
            username="viewer",
            email="viewer@example.com",
            password_hash="hash",
            role="viewer",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        role_checker = require_role("admin")

        # Act / Assert
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=viewer_user)
        assert exc_info.value.status_code == 403