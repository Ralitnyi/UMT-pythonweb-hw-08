"""Unit tests for the AuthRepository class.

Tests cover all database operations for user authentication including
creation, lookups by various fields, email verification, and password
reset flows. Uses mocked async database sessions.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from repository.auth_repository import AuthRepository
from models.user import User


@pytest.fixture
def mock_db():
    """Create a mocked async database session."""
    return AsyncMock()


@pytest.fixture
def auth_repo(mock_db):
    """Create an AuthRepository with a mocked database session."""
    return AuthRepository(mock_db)


@pytest.fixture
def sample_user():
    """Create a sample user instance for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        role="user",
        is_verified=False,
        verification_token="verify-token-123",
        reset_token=None,
        reset_token_expiry=None,
    )


class TestAuthRepository:
    """Test suite for AuthRepository database operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, auth_repo, mock_db):
        """Test creating a new user returns a User with correct attributes."""
        # Arrange
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await auth_repo.create_user(
            username="newuser",
            email="new@example.com",
            password_hash="hash123",
            verification_token="token-abc",
        )

        # Assert
        assert isinstance(result, User)
        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.password_hash == "hash123"
        assert result.verification_token == "token-abc"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, auth_repo, mock_db, sample_user):
        """Test get_by_id returns the correct user when found."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, auth_repo, mock_db):
        """Test get_by_id returns None when user does not exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_id(999)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, auth_repo, mock_db, sample_user):
        """Test get_by_email returns the correct user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_email("test@example.com")

        # Assert
        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, auth_repo, mock_db):
        """Test get_by_email returns None when email does not exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_email("nonexistent@example.com")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_username_found(self, auth_repo, mock_db, sample_user):
        """Test get_by_username returns the correct user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_username("testuser")

        # Assert
        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, auth_repo, mock_db):
        """Test get_by_username returns None when username does not exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_username("unknown")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_verification_token_found(self, auth_repo, mock_db, sample_user):
        """Test get_by_verification_token returns the correct user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_verification_token("verify-token-123")

        # Assert
        assert result is not None
        assert result.verification_token == "verify-token-123"

    @pytest.mark.asyncio
    async def test_get_by_verification_token_not_found(self, auth_repo, mock_db):
        """Test get_by_verification_token returns None for invalid token."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_verification_token("invalid-token")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_reset_token_found(self, auth_repo, mock_db, sample_user):
        """Test get_by_reset_token returns the correct user."""
        # Arrange
        sample_user.reset_token = "reset-token-456"
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_reset_token("reset-token-456")

        # Assert
        assert result is not None
        assert result.reset_token == "reset-token-456"

    @pytest.mark.asyncio
    async def test_get_by_reset_token_not_found(self, auth_repo, mock_db):
        """Test get_by_reset_token returns None for invalid token."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.get_by_reset_token("invalid-reset-token")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_avatar_success(self, auth_repo, mock_db, sample_user):
        """Test update_avatar successfully updates the avatar URL."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await auth_repo.update_avatar(1, "http://example.com/avatar.jpg")

        # Assert
        assert result is not None
        assert result.avatar_url == "http://example.com/avatar.jpg"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_avatar_user_not_found(self, auth_repo, mock_db):
        """Test update_avatar returns None when user not found."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await auth_repo.update_avatar(999, "http://example.com/avatar.jpg")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_user(self, auth_repo, mock_db, sample_user):
        """Test verify_user marks user as verified and clears token."""
        # Arrange
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        assert sample_user.is_verified is False
        assert sample_user.verification_token is not None

        # Act
        result = await auth_repo.verify_user(sample_user)

        # Assert
        assert result.is_verified is True
        assert result.verification_token is None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_reset_token(self, auth_repo, mock_db, sample_user):
        """Test set_reset_token stores the reset token and expiry."""
        # Arrange
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        expiry = datetime.now(timezone.utc)

        # Act
        result = await auth_repo.set_reset_token(sample_user, "new-reset-token", expiry)

        # Assert
        assert result.reset_token == "new-reset-token"
        assert result.reset_token_expiry == expiry
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_password(self, auth_repo, mock_db, sample_user):
        """Test update_password changes password and clears reset fields."""
        # Arrange
        sample_user.reset_token = "existing-token"
        sample_user.reset_token_expiry = datetime.now(timezone.utc)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await auth_repo.update_password(sample_user, "new-hashed-password")

        # Assert
        assert result.password_hash == "new-hashed-password"
        assert result.reset_token is None
        assert result.reset_token_expiry is None
        mock_db.commit.assert_called_once()