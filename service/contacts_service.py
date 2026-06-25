"""Service layer for contact management operations.

This module implements the business logic for contact CRUD operations,
search functionality, and birthday queries, delegating database access
to the ContactRepository.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from repository.contacts_repository import ContactRepository
from schemas.contact import ContactCreate, ContactUpdate, ContactResponse


class ContactService:
    """Service layer for contact operations.

    Orchestrates business logic for creating, reading, updating, deleting
    contacts, as well as searching and birthday queries.
    Delegates all database operations to ContactRepository.

    Args:
        db: An async SQLAlchemy session for database operations.
    """

    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, contact_data: ContactCreate, user_id: int) -> ContactResponse:
        """Create a new contact for the specified user.

        Args:
            contact_data: The contact creation data.
            user_id: The ID of the user who will own this contact.

        Returns:
            ContactResponse: The newly created contact data.
        """
        contact = await self.repository.create(
            name=contact_data.name,
            surname=contact_data.surname,
            email=contact_data.email,
            phone=contact_data.phone,
            date_of_birth=contact_data.date_of_birth,
            user_id=user_id,
            other_info=contact_data.other_info
        )
        return ContactResponse.model_validate(contact)

    async def get_contact(self, contact_id: int, user_id: int) -> ContactResponse | None:
        """Get a single contact by ID, scoped to the user.

        Args:
            contact_id: The contact's unique identifier.
            user_id: The user's unique identifier for ownership check.

        Returns:
            ContactResponse | None: The contact data if found, None otherwise.
        """
        contact = await self.repository.get_by_id(contact_id, user_id)
        if not contact:
            return None
        return ContactResponse.model_validate(contact)

    async def get_all_contacts(self, user_id: int, skip: int = 0, limit: int = 100) -> list[ContactResponse]:
        """Get all contacts for a user with pagination support.

        Args:
            user_id: The user's unique identifier.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            list[ContactResponse]: List of contact records.
        """
        contacts = await self.repository.get_all(user_id=user_id, skip=skip, limit=limit)
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def search_contacts(
            self,
            user_id: int,
            name: str | None = None,
            surname: str | None = None,
            email: str | None = None,
            skip: int = 0,
            limit: int = 100) -> list[ContactResponse]:
        """Search contacts by name, surname, or email.

        At least one search criterion is recommended. Multiple criteria
        are combined with OR logic for flexible searching.

        Args:
            user_id: The user's unique identifier.
            name: Optional name to search for.
            surname: Optional surname to search for.
            email: Optional email to search for.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            list[ContactResponse]: List of matching contact records.
        """
        contacts = await self.repository.search(
            user_id=user_id,
            name=name,
            surname=surname,
            email=email,
            skip=skip,
            limit=limit
        )
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def get_upcoming_birthdays(self, user_id: int, days: int = 7) -> list[ContactResponse]:
        """Get contacts with birthdays in the upcoming N days.

        Args:
            user_id: The user's unique identifier.
            days: Number of days to look ahead (default: 7).

        Returns:
            list[ContactResponse]: Contacts with upcoming birthdays.
        """
        contacts = await self.repository.get_birthdays_within_days(user_id=user_id, days=days)
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user_id: int) -> ContactResponse | None:
        """Update an existing contact with partial data.

        Only the fields provided in contact_data will be updated.

        Args:
            contact_id: The contact's unique identifier.
            contact_data: The update data (only provided fields are applied).
            user_id: The user's unique identifier for ownership check.

        Returns:
            ContactResponse | None: The updated contact data if found, None otherwise.
        """
        update_data = contact_data.model_dump(exclude_unset=True)
        contact = await self.repository.update(contact_id, user_id, **update_data)

        if not contact:
            return None
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: int, user_id: int) -> bool:
        """Delete a contact by ID, scoped to the user.

        Args:
            contact_id: The contact's unique identifier.
            user_id: The user's unique identifier for ownership check.

        Returns:
            bool: True if deleted successfully, False if not found.
        """
        return await self.repository.delete(contact_id, user_id)