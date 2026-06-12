from datetime import date, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.contact import Contact


class ContactRepository:
    """Repository for database operations on contacts"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, surname: str, email: str, phone: str,
                     date_of_birth: date, other_info: str | None = None) -> Contact:
        """Create a new contact"""
        contact = Contact(
            name=name,
            surname=surname,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            other_info=other_info
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_by_id(self, contact_id: int) -> Contact | None:
        """Get contact by ID"""
        result = await self.db.execute(select(Contact).where(Contact.id == contact_id))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Get all contacts with pagination"""
        result = await self.db.execute(select(Contact).offset(skip).limit(limit))
        return result.scalars().all()

    async def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Search contacts by first name"""
        result = await self.db.execute(
            select(Contact)
            .where(Contact.name.ilike(f"%{name}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_by_surname(self, surname: str, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Search contacts by last name"""
        result = await self.db.execute(
            select(Contact)
            .where(Contact.surname.ilike(f"%{surname}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search_by_email(self, email: str, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Search contacts by email"""
        result = await self.db.execute(
            select(Contact)
            .where(Contact.email.ilike(f"%{email}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def search(self, name: str | None = None, surname: str | None = None,
                     email: str | None = None, skip: int = 0, limit: int = 100) -> list[Contact]:
        """Search contacts by multiple criteria"""
        stmt = select(Contact)
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

    async def get_birthdays_within_days(self, days: int = 7) -> list[Contact]:
        """Get contacts with birthdays in the next N days"""
        today = date.today()
        end_date = today + timedelta(days=days)

        result = await self.db.execute(select(Contact))
        all_contacts = result.scalars().all()

        contacts = []
        for contact in all_contacts:
            next_birthday = contact.date_of_birth.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            if today <= next_birthday <= end_date:
                contacts.append(contact)
        return contacts

    async def update(self, contact_id: int, **kwargs) -> Contact | None:
        """Update contact"""
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def delete(self, contact_id: int) -> bool:
        """Delete contact"""
        contact = await self.get_by_id(contact_id)
        if not contact:
            return False

        await self.db.delete(contact)
        await self.db.commit()
        return True

    async def contact_exists(self, email: str = None, phone: str = None) -> bool:
        """Check if contact exists by email or phone"""
        stmt = select(Contact)
        filters = []
        if email:
            filters.append(Contact.email == email)
        if phone:
            filters.append(Contact.phone == phone)
        if filters:
            stmt = stmt.where(or_(*filters))
            result = await self.db.execute(stmt)
            return result.scalars().first() is not None
        return False
