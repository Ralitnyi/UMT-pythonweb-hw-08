"""Integration tests for the authentication API routes.

Tests cover user registration, login, email verification, password reset,
and profile retrieval using a real SQLite database and mocked external
services (Redis, email, Cloudinary).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthAPI:
    """Integration tests for auth endpoints."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, mock_redis):
        """Test successful user registration returns 201 with user data."""
        # Arrange
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        }

        # Act
        response = await client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["is_verified"] is False
        assert data["role"] == "user"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, mock_redis):
        """Test registering with an existing email returns 409."""
        # Arrange
        await client.post("/api/auth/register", json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123",
        })

        # Act
        response = await client.post("/api/auth/register", json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "password456",
        })

        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, mock_redis):
        """Test registering with an existing username returns 409."""
        # Arrange
        await client.post("/api/auth/register", json={
            "username": "shareduser",
            "email": "first@example.com",
            "password": "password123",
        })

        # Act
        response = await client.post("/api/auth/register", json={
            "username": "shareduser",
            "email": "second@example.com",
            "password": "password456",
        })

        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, mock_redis):
        """Test successful login returns JWT token."""
        # Arrange
        await client.post("/api/auth/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "testpassword123",
        })

        # Act
        response = await client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "testpassword123",
        })

        # Assert
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, mock_redis):
        """Test login with wrong password returns 401."""
        # Arrange
        await client.post("/api/auth/register", json={
            "username": "wrongpass",
            "email": "wrongpass@example.com",
            "password": "correctpassword",
        })

        # Act
        response = await client.post("/api/auth/login", json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        })

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient, mock_redis):
        """Test login with non-existent email returns 401."""
        # Act
        response = await client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "anypassword",
        })

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient, mock_redis):
        """Test /me returns current user profile when authenticated."""
        # Arrange - register and login
        await client.post("/api/auth/register", json={
            "username": "meuser",
            "email": "meuser@example.com",
            "password": "mypassword123",
        })

        login_response = await client.post("/api/auth/login", json={
            "email": "meuser@example.com",
            "password": "mypassword123",
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]

        # Act
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"
        assert data["email"] == "meuser@example.com"

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test /me returns 401 when no token provided."""
        # Act
        response = await client.get("/api/auth/me")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test /me returns 401 with invalid JWT token."""
        # Act
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncClient, mock_redis):
        """Test email verification with invalid token returns 400."""
        # Act
        response = await client.get("/api/auth/confirm_email/invalid-token")

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_email_success(self, client: AsyncClient, mock_redis):
        """Test email verification with valid token - request new verification link."""
        # Arrange - register
        await client.post("/api/auth/register", json={
            "username": "verifyuser",
            "email": "verifyuser@example.com",
            "password": "password123",
        })

        # Act - request a new verification email
        request_response = await client.post("/api/auth/request_email", json={
            "email": "verifyuser@example.com"
        })

        # Assert
        assert request_response.status_code == 200
        assert "message" in request_response.json()

    @pytest.mark.asyncio
    async def test_request_email_verification(self, client: AsyncClient, mock_redis):
        """Test requesting email verification returns success message."""
        # Arrange
        await client.post("/api/auth/register", json={
            "username": "reqemail",
            "email": "reqemail@example.com",
            "password": "password123",
        })

        # Act
        response = await client.post("/api/auth/request_email", json={
            "email": "reqemail@example.com"
        })

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_request_email_nonexistent(self, client: AsyncClient, mock_redis):
        """Test requesting email verification for non-existent user."""
        # Act
        response = await client.post("/api/auth/request_email", json={
            "email": "nonexistent@example.com"
        })

        # Assert - should return same message to prevent enumeration
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_password_reset_request(self, client: AsyncClient, mock_redis):
        """Test password reset request returns success message."""
        # Arrange
        await client.post("/api/auth/register", json={
            "username": "resetuser",
            "email": "resetuser@example.com",
            "password": "oldpassword123",
        })

        # Act
        response = await client.post("/api/auth/password-reset/request", json={
            "email": "resetuser@example.com"
        })

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_password_reset_request_nonexistent(self, client: AsyncClient, mock_redis):
        """Test password reset request for non-existent user."""
        # Act
        response = await client.post("/api/auth/password-reset/request", json={
            "email": "nonexistent@example.com"
        })

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_password_reset_confirm_invalid_token(self, client: AsyncClient, mock_redis):
        """Test password reset confirm with invalid token returns 400."""
        # Act
        response = await client.post("/api/auth/password-reset/confirm", json={
            "token": "invalid-reset-token",
            "new_password": "newpassword123"
        })

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_reset_full_flow(
        self, client: AsyncClient, mock_redis, db_session: AsyncSession
    ):
        """Test complete password reset flow: request + confirm with valid token.

        Registers a user, manually sets a reset token in the DB, then confirms
        the password reset via the API.
        """
        # Arrange - register user via API
        await client.post("/api/auth/register", json={
            "username": "fullreset",
            "email": "fullreset@example.com",
            "password": "oldpassword123",
        })

        # Use the test db_session to set a reset token directly
        from repository.auth_repository import AuthRepository
        repo = AuthRepository(db_session)
        user = await repo.get_by_email("fullreset@example.com")
        assert user is not None, "User should exist after registration"

        reset_token = str(uuid.uuid4())
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        await repo.set_reset_token(user, reset_token, expiry)

        # Act - confirm password reset with the valid token
        response = await client.post("/api/auth/password-reset/confirm", json={
            "token": reset_token,
            "new_password": "newpassword456",
        })

        # Assert
        assert response.status_code == 200, f"Password reset failed: {response.text}"
        data = response.json()
        assert data["email"] == "fullreset@example.com"
        assert data["username"] == "fullreset"

        # Verify we can login with the new password
        login_response = await client.post("/api/auth/login", json={
            "email": "fullreset@example.com",
            "password": "newpassword456",
        })
        assert login_response.status_code == 200, "Login with new password failed"

        # Verify old password no longer works
        old_login_response = await client.post("/api/auth/login", json={
            "email": "fullreset@example.com",
            "password": "oldpassword123",
        })
        assert old_login_response.status_code == 401, "Old password should not work"

    @pytest.mark.asyncio
    async def test_avatar_admin_access(self, client: AsyncClient, mock_redis):
        """Test /avatar endpoint returns 403 for regular user (not admin)."""
        # Arrange - register a regular user and get token
        await client.post("/api/auth/register", json={
            "username": "reguser",
            "email": "reguser@example.com",
            "password": "password123",
        })
        login_resp = await client.post("/api/auth/login", json={
            "email": "reguser@example.com",
            "password": "password123",
        })
        token = login_resp.json()["access_token"]

        # Act - try to update avatar as regular user
        response = await client.patch(
            "/api/auth/avatar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.jpg", b"fake-image-data", "image/jpeg")},
        )

        # Assert - regular user should get 403
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_avatar_unauthenticated(self, client: AsyncClient):
        """Test /avatar endpoint returns 401 without authentication."""
        # Act
        response = await client.patch(
            "/api/auth/avatar",
            files={"file": ("test.jpg", b"fake-image-data", "image/jpeg")},
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_avatar_admin_success(
        self, client: AsyncClient, mock_redis, db_session: AsyncSession, monkeypatch
    ):
        """Test /avatar endpoint succeeds for admin user."""
        # Arrange - create admin user via repository with the test db_session
        from repository.auth_repository import AuthRepository
        from service.auth_service import get_password_hash

        repo = AuthRepository(db_session)
        admin_user = await repo.create_user(
            username="adminuser",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            verification_token="admin-verify",
        )
        # Set role to admin
        admin_user.role = "admin"
        await db_session.commit()
        await db_session.refresh(admin_user)

        # Login as admin
        login_resp = await client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "admin123",
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]

        # Mock cloudinary upload to avoid actual API call
        async def mock_upload_avatar(*args, **kwargs):
            return "http://res.cloudinary.com/test/avatar.jpg"

        monkeypatch.setattr("api.auth_api.upload_avatar", mock_upload_avatar)

        # Act - update avatar as admin
        response = await client.patch(
            "/api/auth/avatar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("avatar.jpg", b"fake-image-data", "image/jpeg")},
        )

        # Assert
        assert response.status_code == 200, f"Avatar update failed: {response.text}"
        data = response.json()
        assert data["avatar_url"] == "http://res.cloudinary.com/test/avatar.jpg"

    @pytest.mark.asyncio
    async def test_avatar_non_image_file(
        self, client: AsyncClient, mock_redis, db_session: AsyncSession
    ):
        """Test /avatar returns 400 when file is not an image."""
        # Arrange - create admin user via repository with test db_session
        from repository.auth_repository import AuthRepository
        from service.auth_service import get_password_hash

        repo = AuthRepository(db_session)
        admin_user = await repo.create_user(
            username="admin2",
            email="admin2@example.com",
            password_hash=get_password_hash("admin123"),
            verification_token="admin-verify-2",
        )
        admin_user.role = "admin"
        await db_session.commit()

        login_resp = await client.post("/api/auth/login", json={
            "email": "admin2@example.com",
            "password": "admin123",
        })
        token = login_resp.json()["access_token"]

        # Act - try to upload a non-image file
        response = await client.patch(
            "/api/auth/avatar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.txt", b"text content", "text/plain")},
        )

        # Assert
        assert response.status_code == 400