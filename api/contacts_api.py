from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from service.contacts_service import ContactService
from schemas.contact import ContactCreate, ContactUpdate, ContactResponse


router = APIRouter(prefix='/api/contacts', tags=['contacts'])


@router.post('/', response_model=ContactResponse, status_code=201)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    """Create a new contact"""
    service = ContactService(db)
    try:
        return await service.create_contact(contact)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/', response_model=list[ContactResponse])
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get all contacts with pagination"""
    service = ContactService(db)
    return await service.get_all_contacts(skip=skip, limit=limit)


@router.get('/search', response_model=list[ContactResponse])
async def search_contacts(
    name: str | None = Query(None),
    surname: str | None = Query(None),
    email: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Search contacts by name, surname, or email"""
    service = ContactService(db)
    return await service.search_contacts(
        name=name,
        surname=surname,
        email=email,
        skip=skip,
        limit=limit
    )


@router.get('/birthdays', response_model=list[ContactResponse])
async def get_upcoming_birthdays(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get contacts with birthdays in the next N days"""
    service = ContactService(db)
    return await service.get_upcoming_birthdays(days=days)


@router.get('/{contact_id}', response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Get contact by ID"""
    service = ContactService(db)
    contact = await service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    return contact


@router.put('/{contact_id}', response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a contact"""
    service = ContactService(db)
    updated_contact = await service.update_contact(contact_id, contact)
    if not updated_contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    return updated_contact


@router.delete('/{contact_id}', status_code=204)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a contact"""
    service = ContactService(db)
    if not await service.delete_contact(contact_id):
        raise HTTPException(status_code=404, detail='Contact not found')
