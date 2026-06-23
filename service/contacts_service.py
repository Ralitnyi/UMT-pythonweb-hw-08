from sqlalchemy.ext.asyncio import AsyncSession

from repository.contacts_repository import ContactRepository
from schemas.contact import ContactCreate, ContactUpdate, ContactResponse


class ContactService:
    """Service layer for contact operations"""

    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, contact_data: ContactCreate, user_id: int) -> ContactResponse:
        """Create a new contact"""
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
        """Get contact by ID"""
        contact = await self.repository.get_by_id(contact_id, user_id)
        if not contact:
            return None
        return ContactResponse.model_validate(contact)

    async def get_all_contacts(self, user_id: int, skip: int = 0, limit: int = 100) -> list[ContactResponse]:
        """Get all contacts for user"""
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
        """Search contacts by criteria"""
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
        """Get contacts with upcoming birthdays"""
        contacts = await self.repository.get_birthdays_within_days(user_id=user_id, days=days)
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user_id: int) -> ContactResponse | None:
        """Update contact"""
        update_data = contact_data.model_dump(exclude_unset=True)
        contact = await self.repository.update(contact_id, user_id, **update_data)

        if not contact:
            return None
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: int, user_id: int) -> bool:
        """Delete contact"""
        return await self.repository.delete(contact_id, user_id)
