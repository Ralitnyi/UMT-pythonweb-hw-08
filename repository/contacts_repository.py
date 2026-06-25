"""Data access layer for contact management operations.

This module provides the ContactRepository class which encapsulates all
database operations related to contacts, including CRUD operations,
search functionality, and birthday queries.
"""

from datetime import date, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.contact import Contact


class ContactRepository:
    """Repository for database operations on contacts.

    Handles all direct database interactions for the Contact model.
    Provides methods for creating, querying, updating, deleting contacts,
    and performing specialized searches.

    Args:
        db: An async SQLAlchemy session for database operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, surname: str, email: str, phone: str,
                     date_of_birth: date, user_id: int, other_info: str | None = None) -> Contact:
        """Create a new contact in the database.

        Args:
            name: Contact's first name.
            surname: Contact's last name.
            email: Contact's email address.
            phone: Contact's phone number.
            date_of_birth: Contact's date of birth.
            user_id: ID of the user who owns this contact.
            other_info: Optional additional notes about the contact.

        Returns:
            Contact: The newly created contact instance.
        """
        contact = Contact(
            name=name,
            surname=surname,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            other_info=other_info,
            user_id=user_id
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_by_id(self, contact_id: int, user_id: int | None = None) -> Contact | None:
        """Get a contact by its ID, optionally filtered by user.

        Args:
            contact_id: The contact's unique identifier.
            user_id: Optional user ID to restrict ownership.

        Returns:
            Contact | None: The contact if found, None otherwise.
        """
        stmt = select(Contact).where(Contact.id == contact_id)
        if user_id is not None:
            stmt = stmt.where(Contact.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Get all contacts for a specific user with pagination.

        Args:
            user_id: The user's unique identifier.
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            list[Contact]: List of contacts belonging to the user.
        """
        result = await self.db.execute(
            select(Contact)
            .where(Contact.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search(self, user_id: int, name: str | None = None, surname: str | None = None,
                     email: str | None = None, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Search contacts by name, surname, or email with case-insensitive matching.

        At least one search criterion must be provided. Multiple criteria
        are combined with OR logic.

        Args:
            user_id: The user's unique identifier.
            name: Optional name to search for (partial match).
            surname: Optional surname to search for (partial match).
            email: Optional email to search for (partial match).
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            list[Contact]: List of matching contacts.
        """
        stmt = select(Contact).where(Contact.user_id == user_id)
        filters = []
        if name:
            filters.append(Contact.name.ilike(f"%{name}%"))
        if surname:
            filters.append(Contact.surname.ilike(f"%{surname}%"))
        if email:
            filters.append(Contact.email.ilike(f"%{email}%"))

        if filters:
            stmt = stmt.where(or_(*filters))

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_birthdays_within_days(self, user_id: int, days: int = 7) -> list[Contact]:
        """Get contacts whose birthdays fall within the next N days.

        Calculates the next birthday for each contact (handling year-end
        wrapping) and checks if it falls within the specified range.

        Args:
            user_id: The user's unique identifier.
            days: Number of days to look ahead (default: 7).

        Returns:
            list[Contact]: Contacts with upcoming birthdays.
        """
        today = date.today()
        end_date = today + timedelta(days=days)

        result = await self.db.execute(
            select(Contact).where(Contact.user_id == user_id)
        )
        all_contacts = result.scalars().all()

        contacts = []
        for contact in all_contacts:
            next_birthday = contact.date_of_birth.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            if today <= next_birthday <= end_date:
                contacts.append(contact)
        return contacts

    async def update(self, contact_id: int, user_id: int, **kwargs) -> Contact | None:
        """Update a contact's fields with the provided keyword arguments.

        Only non-None values will be applied to the contact.

        Args:
            contact_id: The contact's unique identifier.
            user_id: The user's unique identifier for ownership check.
            **kwargs: Field names and their new values to update.

        Returns:
            Contact | None: The updated contact if found, None otherwise.
        """
        contact = await self.get_by_id(contact_id, user_id)
        if not contact:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete(self, contact_id: int, user_id: int) -> bool:
        """Delete a contact by its ID, scoped to the user.

        Args:
            contact_id: The contact's unique identifier.
            user_id: The user's unique identifier for ownership check.

        Returns:
            bool: True if the contact was deleted, False if not found.
        """
        contact = await self.get_by_id(contact_id, user_id)
        if not contact:
            return False

        await self.db.delete(contact)
        await self.db.commit()
        return True