"""Unit tests for the AuthService class.

Tests cover the core business logic of AuthService including
registration, login, email verification, password reset,
and Redis cache integration. Uses mocked repository layer.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from service.auth_service import AuthService
from service.cache_service import cache_user, get_cached_user, invalidate_user_cache
from models.user import User
from schemas.auth import UserCreate


@pytest.fixture
def mock_db():
    """Create a mocked async database session."""
    return AsyncMock()


@pytest.fixture
def auth_service(mock_db):
    """Create an AuthService with a mocked database session."""
    return AuthService(mock_db)


@pytest.fixture
def sample_user():
    """Create a sample user ORM instance for testing."""
    from datetime import datetime, timezone
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$hashed_password",
        role="user",
        is_verified=False,
        verification_token="verify-token-123",
        reset_token=None,
        reset_token_expiry=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestAuthService:
    """Test suite for AuthService business logic."""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_db, sample_user):
        """Test register creates a user and returns User ORM instance."""
        # Arrange
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="secure123",
        )
        auth_service.repository.get_by_email = AsyncMock(return_value=None)
        auth_service.repository.get_by_username = AsyncMock(return_value=None)
        auth_service.repository.create_user = AsyncMock(return_value=sample_user)

        # Act
        result = await auth_service.register(user_data)

        # Assert
        assert result is sample_user
        auth_service.repository.get_by_email.assert_awaited_once_with("new@example.com")
        auth_service.repository.get_by_username.assert_awaited_once_with("newuser")
        auth_service.repository.create_user.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, sample_user):
        """Test register raises ValueError when email already exists."""
        # Arrange
        user_data = UserCreate(
            username="newuser",
            email="test@example.com",
            password="secure123",
        )
        auth_service.repository.get_by_email = AsyncMock(return_value=sample_user)

        # Act / Assert
        with pytest.raises(ValueError, match="User with this email already exists"):
            await auth_service.register(user_data)

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_service, sample_user):
        """Test register raises ValueError when username already exists."""
        # Arrange
        user_data = UserCreate(
            username="testuser",
            email="new@example.com",
            password="secure123",
        )
        auth_service.repository.get_by_email = AsyncMock(return_value=None)
        auth_service.repository.get_by_username = AsyncMock(return_value=sample_user)

        # Act / Assert
        with pytest.raises(ValueError, match="User with this username already exists"):
            await auth_service.register(user_data)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_db, sample_user, monkeypatch):
        """Test login returns TokenResponse with access_token."""
        # Arrange
        sample_user.password_hash = "$2b$12$testhash"
        auth_service.repository.get_by_email = AsyncMock(return_value=sample_user)

        # Mock verify_password to return True
        async def mock_cache_user(*args, **kwargs):
            return None
        monkeypatch.setattr("service.auth_service.cache_user", mock_cache_user)

        mock_verify = MagicMock(return_value=True)
        monkeypatch.setattr("service.auth_service.verify_password", mock_verify)

        mock_create_token = MagicMock(return_value="test-jwt-token")
        monkeypatch.setattr("service.auth_service.create_access_token", mock_create_token)

        # Act
        result = await auth_service.login("test@example.com", "password123")

        # Assert
        assert result.access_token == "test-jwt-token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, auth_service):
        """Test login raises ValueError with non-existent email."""
        # Arrange
        auth_service.repository.get_by_email = AsyncMock(return_value=None)

        # Act / Assert
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login("nonexistent@example.com", "password")

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, sample_user):
        """Test login raises ValueError with wrong password."""
        # Arrange
        auth_service.repository.get_by_email = AsyncMock(return_value=sample_user)

        with patch("service.auth_service.verify_password", return_value=False):
            # Act / Assert
            with pytest.raises(ValueError, match="Invalid email or password"):
                await auth_service.login("test@example.com", "wrongpassword")

    @pytest.mark.asyncio
    async def test_verify_email_success(self, auth_service, sample_user, monkeypatch):
        """Test verify_email validates token and marks user as verified."""
        # Arrange
        now = datetime.now(timezone.utc)
        auth_service.repository.get_by_verification_token = AsyncMock(return_value=sample_user)

        verified_user = User(
            id=sample_user.id,
            username=sample_user.username,
            email=sample_user.email,
            password_hash=sample_user.password_hash,
            is_verified=True,
            verification_token=None,
            role="user",
            created_at=now,
            updated_at=now,
        )
        auth_service.repository.verify_user = AsyncMock(return_value=verified_user)

        async def mock_invalidate(user_id):
            return None
        monkeypatch.setattr("service.auth_service.invalidate_user_cache", mock_invalidate)

        # Act
        result = await auth_service.verify_email("verify-token-123")

        # Assert
        assert result.is_verified is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, auth_service):
        """Test verify_email raises ValueError with invalid token."""
        # Arrange
        auth_service.repository.get_by_verification_token = AsyncMock(return_value=None)

        # Act / Assert
        with pytest.raises(ValueError, match="Invalid verification token"):
            await auth_service.verify_email("invalid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_from_cache(self, auth_service, monkeypatch):
        """Test get_current_user returns cached user when available."""
        # Arrange
        cached_data = {
            "id": 1,
            "username": "cacheduser",
            "email": "cached@example.com",
            "avatar_url": None,
            "is_verified": True,
            "role": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        async def mock_get_cached(user_id):
            return cached_data
        monkeypatch.setattr("service.auth_service.get_cached_user", mock_get_cached)

        # Act
        result = await auth_service.get_current_user(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.username == "cacheduser"

    @pytest.mark.asyncio
    async def test_get_current_user_from_db(self, auth_service, sample_user, monkeypatch):
        """Test get_current_user falls back to DB when cache is empty."""
        # Arrange
        async def mock_get_cached(user_id):
            return None
        monkeypatch.setattr("service.auth_service.get_cached_user", mock_get_cached)

        async def mock_cache(user_id, data):
            return None
        monkeypatch.setattr("service.auth_service.cache_user", mock_cache)

        auth_service.repository.get_by_id = AsyncMock(return_value=sample_user)

        # Act
        result = await auth_service.get_current_user(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, auth_service, monkeypatch):
        """Test get_current_user returns None when user doesn't exist."""
        # Arrange
        async def mock_get_cached(user_id):
            return None
        monkeypatch.setattr("service.auth_service.get_cached_user", mock_get_cached)
        auth_service.repository.get_by_id = AsyncMock(return_value=None)

        # Act
        result = await auth_service.get_current_user(999)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_avatar_success(self, auth_service, sample_user, monkeypatch):
        """Test update_avatar updates URL and invalidates cache."""
        # Arrange
        updated_user = User(
            id=sample_user.id,
            username=sample_user.username,
            email=sample_user.email,
            password_hash=sample_user.password_hash,
            avatar_url="http://example.com/new-avatar.jpg",
            is_verified=True,
            role="user",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        auth_service.repository.update_avatar = AsyncMock(return_value=updated_user)

        async def mock_invalidate(user_id):
            return None
        monkeypatch.setattr("service.auth_service.invalidate_user_cache", mock_invalidate)

        # Act
        result = await auth_service.update_avatar(1, "http://example.com/new-avatar.jpg")

        # Assert
        assert result.avatar_url == "http://example.com/new-avatar.jpg"

    @pytest.mark.asyncio
    async def test_update_avatar_user_not_found(self, auth_service):
        """Test update_avatar raises ValueError when user not found."""
        # Arrange
        auth_service.repository.update_avatar = AsyncMock(return_value=None)

        # Act / Assert
        with pytest.raises(ValueError, match="User not found"):
            await auth_service.update_avatar(999, "http://example.com/avatar.jpg")

    @pytest.mark.asyncio
    async def test_request_password_reset_existing_user(self, auth_service, sample_user, monkeypatch):
        """Test request_password_reset returns token for existing user."""
        # Arrange
        auth_service.repository.get_by_email = AsyncMock(return_value=sample_user)

        mock_generate = MagicMock(return_value="reset-token-abc")
        monkeypatch.setattr("service.auth_service.generate_reset_token", mock_generate)
        auth_service.repository.set_reset_token = AsyncMock(return_value=sample_user)

        # Act
        result = await auth_service.request_password_reset("test@example.com")

        # Assert
        assert result == "reset-token-abc"
        auth_service.repository.set_reset_token.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, auth_service):
        """Test request_password_reset returns None for non-existent user."""
        # Arrange
        auth_service.repository.get_by_email = AsyncMock(return_value=None)

        # Act
        result = await auth_service.request_password_reset("nonexistent@example.com")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_reset_password_success(self, auth_service, sample_user, monkeypatch):
        """Test reset_password updates password and invalidates cache."""
        # Arrange
        sample_user.reset_token = "valid-reset-token"
        sample_user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        auth_service.repository.get_by_reset_token = AsyncMock(return_value=sample_user)

        updated_user = User(
            id=sample_user.id,
            username=sample_user.username,
            email=sample_user.email,
            password_hash="new-hashed-password",
            is_verified=True,
            role="user",
            reset_token=None,
            reset_token_expiry=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        auth_service.repository.update_password = AsyncMock(return_value=updated_user)

        async def mock_invalidate(user_id):
            return None
        monkeypatch.setattr("service.auth_service.invalidate_user_cache", mock_invalidate)

        with patch("service.auth_service.get_password_hash", return_value="new-hashed-password"):
            # Act
            result = await auth_service.reset_password("valid-reset-token", "newpassword123")

        # Assert
        assert result is not None
        # Verify password was updated
        auth_service.repository.update_password.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, auth_service):
        """Test reset_password raises ValueError with invalid token."""
        # Arrange
        auth_service.repository.get_by_reset_token = AsyncMock(return_value=None)

        # Act / Assert
        with pytest.raises(ValueError, match="Invalid or expired reset token"):
            await auth_service.reset_password("invalid-token", "newpassword")

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self, auth_service, sample_user):
        """Test reset_password raises ValueError with expired token."""
        # Arrange
        sample_user.reset_token = "expired-token"
        sample_user.reset_token_expiry = datetime.now(timezone.utc) - timedelta(hours=1)
        auth_service.repository.get_by_reset_token = AsyncMock(return_value=sample_user)

        # Act / Assert
        with pytest.raises(ValueError, match="Reset token has expired"):
            await auth_service.reset_password("expired-token", "newpassword")