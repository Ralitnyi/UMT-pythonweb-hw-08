"""Integration tests for the contacts API routes.

Tests cover CRUD operations for contacts, search functionality,
and upcoming birthdays endpoint using a real SQLite database
and mocked external services.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, mock_redis) -> str:
    """Create a test user and return an authentication token."""
    await client.post("/api/auth/register", json={
        "username": "contactuser",
        "email": "contactuser@example.com",
        "password": "testpassword123",
    })
    login_response = await client.post("/api/auth/login", json={
        "email": "contactuser@example.com",
        "password": "testpassword123",
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    return login_response.json()["access_token"]


@pytest.fixture
def auth_header(auth_token: str) -> dict:
    """Return Authorization header with bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestContactsAPI:
    """Integration tests for contacts endpoints."""

    @pytest.mark.asyncio
    async def test_create_contact(self, client: AsyncClient, auth_header):
        """Test creating a contact returns 201 with contact data."""
        # Arrange
        contact_data = {
            "name": "John",
            "surname": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "date_of_birth": "1990-01-15",
            "other_info": "Test note",
        }

        # Act
        response = await client.post("/api/contacts/", json=contact_data, headers=auth_header)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John"
        assert data["surname"] == "Doe"
        assert data["email"] == "john@example.com"
        assert data["phone"] == "+1234567890"
        assert data["date_of_birth"] == "1990-01-15"
        assert data["other_info"] == "Test note"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_contact_unauthenticated(self, client: AsyncClient):
        """Test creating a contact without auth returns 401."""
        # Arrange
        contact_data = {
            "name": "Ghost",
            "surname": "User",
            "email": "ghost@example.com",
            "phone": "+0000000000",
            "date_of_birth": "1990-01-01",
        }

        # Act
        response = await client.post("/api/contacts/", json=contact_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_all_contacts(self, client: AsyncClient, auth_header):
        """Test getting all contacts returns list."""
        # Arrange - create two contacts
        contact1 = {
            "name": "Alice",
            "surname": "Smith",
            "email": "alice@example.com",
            "phone": "+1111111111",
            "date_of_birth": "1992-03-20",
        }
        contact2 = {
            "name": "Bob",
            "surname": "Johnson",
            "email": "bob@example.com",
            "phone": "+2222222222",
            "date_of_birth": "1985-07-10",
        }
        await client.post("/api/contacts/", json=contact1, headers=auth_header)
        await client.post("/api/contacts/", json=contact2, headers=auth_header)

        # Act
        response = await client.get("/api/contacts/", headers=auth_header)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_contact_by_id(self, client: AsyncClient, auth_header):
        """Test getting a specific contact by ID."""
        # Arrange
        create_response = await client.post("/api/contacts/", json={
            "name": "Specific",
            "surname": "Contact",
            "email": "specific@example.com",
            "phone": "+3333333333",
            "date_of_birth": "1995-12-25",
        }, headers=auth_header)
        contact_id = create_response.json()["id"]

        # Act
        response = await client.get(f"/api/contacts/{contact_id}", headers=auth_header)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Specific"
        assert data["id"] == contact_id

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, client: AsyncClient, auth_header):
        """Test getting a non-existent contact returns 404."""
        # Act
        response = await client.get("/api/contacts/9999", headers=auth_header)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_contact(self, client: AsyncClient, auth_header):
        """Test updating a contact modifies only provided fields."""
        # Arrange
        create_response = await client.post("/api/contacts/", json={
            "name": "Updatable",
            "surname": "Person",
            "email": "update@example.com",
            "phone": "+4444444444",
            "date_of_birth": "1988-06-15",
        }, headers=auth_header)
        contact_id = create_response.json()["id"]

        # Act - update only the name
        response = await client.put(
            f"/api/contacts/{contact_id}",
            json={"name": "UpdatedName"},
            headers=auth_header,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UpdatedName"
        assert data["surname"] == "Person"  # unchanged

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, client: AsyncClient, auth_header):
        """Test updating a non-existent contact returns 404."""
        # Act
        response = await client.put(
            "/api/contacts/9999",
            json={"name": "Ghost"},
            headers=auth_header,
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contact(self, client: AsyncClient, auth_header):
        """Test deleting a contact returns 204."""
        # Arrange
        create_response = await client.post("/api/contacts/", json={
            "name": "Deletable",
            "surname": "User",
            "email": "delete@example.com",
            "phone": "+5555555555",
            "date_of_birth": "1993-09-01",
        }, headers=auth_header)
        contact_id = create_response.json()["id"]

        # Act
        response = await client.delete(f"/api/contacts/{contact_id}", headers=auth_header)

        # Assert
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(self, client: AsyncClient, auth_header):
        """Test deleting a non-existent contact returns 404."""
        # Act
        response = await client.delete("/api/contacts/9999", headers=auth_header)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_contacts_by_name(self, client: AsyncClient, auth_header):
        """Test searching contacts by name returns matching results."""
        # Arrange
        await client.post("/api/contacts/", json={
            "name": "Searchable",
            "surname": "One",
            "email": "search1@example.com",
            "phone": "+6666666666",
            "date_of_birth": "1991-04-10",
        }, headers=auth_header)
        await client.post("/api/contacts/", json={
            "name": "Other",
            "surname": "Two",
            "email": "search2@example.com",
            "phone": "+7777777777",
            "date_of_birth": "1992-05-11",
        }, headers=auth_header)

        # Act
        response = await client.get("/api/contacts/search?name=Searchable", headers=auth_header)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Searchable"

    @pytest.mark.asyncio
    async def test_search_contacts_by_surname(self, client: AsyncClient, auth_header):
        """Test searching contacts by surname returns matching results."""
        # Arrange
        await client.post("/api/contacts/", json={
            "name": "Findable",
            "surname": "Target",
            "email": "find@example.com",
            "phone": "+8888888888",
            "date_of_birth": "1994-08-20",
        }, headers=auth_header)

        # Act
        response = await client.get("/api/contacts/search?surname=Target", headers=auth_header)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["surname"] == "Target"

    @pytest.mark.asyncio
    async def test_search_contacts_no_results(self, client: AsyncClient, auth_header):
        """Test search with no matching results returns empty list."""
        # Act
        response = await client.get("/api/contacts/search?name=NonExistentName", headers=auth_header)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_upcoming_birthdays(self, client: AsyncClient, auth_header):
        """Test upcoming birthdays endpoint returns contacts with birthdays soon."""
        # Arrange
        await client.post("/api/contacts/", json={
            "name": "Birthday",
            "surname": "Person",
            "email": "bday@example.com",
            "phone": "+9999999999",
            "date_of_birth": "1990-01-01",
        }, headers=auth_header)

        # Act
        response = await client.get("/api/contacts/birthdays?days=365", headers=auth_header)

        # Assert
        assert response.status_code == 200
        data = response.json()
        # With days=365, should find the birthday contact
        assert len(data) >= 1