from sqlalchemy.ext.asyncio import AsyncSession

from repository.contacts_repository import ContactRepository
from schemas.contact import ContactCreate, ContactUpdate, ContactResponse


class ContactService:
    """Service layer for contact operations"""

    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, contact_data: ContactCreate) -> ContactResponse:
        """Create a new contact"""
        contact = await self.repository.create(
            name=contact_data.name,
            surname=contact_data.surname,
            email=contact_data.email,
            phone=contact_data.phone,
            date_of_birth=contact_data.date_of_birth,
            other_info=contact_data.other_info
        )
        return ContactResponse.model_validate(contact)

    async def get_contact(self, contact_id: int) -> ContactResponse | None:
        """Get contact by ID"""
        contact = await self.repository.get_by_id(contact_id)
        if not contact:
            return None
        return ContactResponse.model_validate(contact)

    async def get_all_contacts(self, skip: int = 0, limit: int = 100) -> list[ContactResponse]:
        """Get all contacts"""
        contacts = await self.repository.get_all(skip=skip, limit=limit)
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def search_contacts(
            self,
            name: str | None = None,
            surname: str | None = None,
            email: str | None = None,
            skip: int = 0,
            limit: int = 100) -> list[ContactResponse]:
        """Search contacts by criteria"""
        contacts = await self.repository.search(
            name=name,
            surname=surname,
            email=email,
            skip=skip,
            limit=limit
        )
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def get_upcoming_birthdays(self, days: int = 7) -> list[ContactResponse]:
        """Get contacts with upcoming birthdays"""
        contacts = await self.repository.get_birthdays_within_days(days=days)
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate) -> ContactResponse | None:
        """Update contact"""
        update_data = contact_data.model_dump(exclude_unset=True)
        contact = await self.repository.update(contact_id, **update_data)

        if not contact:
            return None
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete contact"""
        return await self.repository.delete(contact_id)
