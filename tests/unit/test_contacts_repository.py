"""Unit tests for the ContactRepository class.

Tests cover all CRUD operations, search functionality, and birthday
queries for the Contact model using mocked async database sessions.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

from repository.contacts_repository import ContactRepository
from models.contact import Contact


@pytest.fixture
def mock_db():
    """Create a mocked async database session."""
    return AsyncMock()


@pytest.fixture
def contact_repo(mock_db):
    """Create a ContactRepository with a mocked database session."""
    return ContactRepository(mock_db)


@pytest.fixture
def sample_contact():
    """Create a sample contact instance for testing."""
    return Contact(
        id=1,
        name="John",
        surname="Doe",
        email="john@example.com",
        phone="+1234567890",
        date_of_birth=date(1990, 1, 15),
        other_info="Test note",
        user_id=1,
    )


class TestContactRepository:
    """Test suite for ContactRepository database operations."""

    @pytest.mark.asyncio
    async def test_create(self, contact_repo, mock_db):
        """Test creating a new contact returns a Contact with correct attributes."""
        # Arrange
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await contact_repo.create(
            name="Jane",
            surname="Smith",
            email="jane@example.com",
            phone="+0987654321",
            date_of_birth=date(1992, 5, 20),
            user_id=1,
            other_info="Friend from work",
        )

        # Assert
        assert isinstance(result, Contact)
        assert result.name == "Jane"
        assert result.surname == "Smith"
        assert result.email == "jane@example.com"
        assert result.phone == "+0987654321"
        assert result.date_of_birth == date(1992, 5, 20)
        assert result.other_info == "Friend from work"
        assert result.user_id == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_without_optional_fields(self, contact_repo, mock_db):
        """Test creating a contact without optional other_info."""
        # Arrange
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await contact_repo.create(
            name="Bob",
            surname="Builder",
            email="bob@example.com",
            phone="+111111111",
            date_of_birth=date(1985, 3, 10),
            user_id=2,
        )

        # Assert
        assert result.other_info is None
        assert result.name == "Bob"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, contact_repo, mock_db, sample_contact):
        """Test get_by_id returns the correct contact."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_contact
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_by_id(1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.name == "John"
        assert result.email == "john@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, contact_repo, mock_db):
        """Test get_by_id returns None when contact does not exist."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_by_id(999)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_with_user_filter(self, contact_repo, mock_db, sample_contact):
        """Test get_by_id with user_id filter returns correct contact."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_contact
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_by_id(1, user_id=1)

        # Assert
        assert result is not None
        assert result.id == 1
        assert result.user_id == 1

    @pytest.mark.asyncio
    async def test_get_all(self, contact_repo, mock_db, sample_contact):
        """Test get_all returns all contacts for a user."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_contact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_all(user_id=1)

        # Assert
        assert len(result) == 1
        assert result[0].user_id == 1

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, contact_repo, mock_db):
        """Test get_all respects skip and limit parameters."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_all(user_id=1, skip=10, limit=20)

        # Assert
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_by_name(self, contact_repo, mock_db, sample_contact):
        """Test search finds contacts by partial name match."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_contact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.search(user_id=1, name="John")

        # Assert
        assert len(result) == 1
        assert result[0].name == "John"

    @pytest.mark.asyncio
    async def test_search_by_surname(self, contact_repo, mock_db, sample_contact):
        """Test search finds contacts by partial surname match."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_contact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.search(user_id=1, surname="Doe")

        # Assert
        assert len(result) == 1
        assert result[0].surname == "Doe"

    @pytest.mark.asyncio
    async def test_search_by_email(self, contact_repo, mock_db, sample_contact):
        """Test search finds contacts by partial email match."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_contact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.search(user_id=1, email="john@example.com")

        # Assert
        assert len(result) == 1
        assert result[0].email == "john@example.com"

    @pytest.mark.asyncio
    async def test_search_no_criteria(self, contact_repo, mock_db, sample_contact):
        """Test search with no criteria returns all contacts."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_contact]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.search(user_id=1)

        # Assert
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_birthdays_within_days(self, contact_repo, mock_db):
        """Test get_birthdays_within_days returns contacts with upcoming birthdays."""
        # Arrange
        today = date.today()
        # Create a contact whose birthday is 3 days from now
        future_birthday = (today + timedelta(days=3)).replace(year=1990)
        contact_with_upcoming_birthday = Contact(
            id=2,
            name="Birthday",
            surname="Person",
            email="birthday@example.com",
            phone="+123",
            date_of_birth=future_birthday,
            user_id=1,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [contact_with_upcoming_birthday]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_birthdays_within_days(user_id=1, days=7)

        # Assert
        assert len(result) == 1
        assert result[0].name == "Birthday"

    @pytest.mark.asyncio
    async def test_get_birthdays_no_results(self, contact_repo, mock_db):
        """Test get_birthdays_within_days returns empty list when no birthdays upcoming."""
        # Arrange
        today = date.today()
        # Create a contact whose birthday is far in the future
        far_birthday = (today + timedelta(days=100)).replace(year=1990)
        contact_with_far_birthday = Contact(
            id=3,
            name="Far",
            surname="Away",
            email="far@example.com",
            phone="+456",
            date_of_birth=far_birthday,
            user_id=1,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [contact_with_far_birthday]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.get_birthdays_within_days(user_id=1, days=7)

        # Assert
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_success(self, contact_repo, mock_db, sample_contact):
        """Test update modifies contact fields correctly."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_contact
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Act
        result = await contact_repo.update(1, 1, name="Jonathan", phone="+999999")

        # Assert
        assert result is not None
        assert result.name == "Jonathan"
        assert result.phone == "+999999"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self, contact_repo, mock_db):
        """Test update returns None when contact not found."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.update(999, 1, name="Ghost")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_success(self, contact_repo, mock_db, sample_contact):
        """Test delete removes a contact and returns True."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_contact
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        # Act
        result = await contact_repo.delete(1, 1)

        # Assert
        assert result is True
        mock_db.delete.assert_called_once_with(sample_contact)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, contact_repo, mock_db):
        """Test delete returns False when contact not found."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await contact_repo.delete(999, 1)

        # Assert
        assert result is False