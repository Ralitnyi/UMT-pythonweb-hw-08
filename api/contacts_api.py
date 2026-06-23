from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from service.contacts_service import ContactService
from service.auth_deps import get_current_user
from schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from models.user import User


router = APIRouter(prefix='/api/contacts', tags=['contacts'])


@router.post('/', response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new contact"""
    service = ContactService(db)
    try:
        return await service.create_contact(contact, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get('/', response_model=list[ContactResponse])
async def get_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all contacts for current user with pagination"""
    service = ContactService(db)
    return await service.get_all_contacts(user_id=current_user.id, skip=skip, limit=limit)


@router.get('/search', response_model=list[ContactResponse])
async def search_contacts(
    name: str | None = Query(None),
    surname: str | None = Query(None),
    email: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search contacts by name, surname, or email"""
    service = ContactService(db)
    return await service.search_contacts(
        user_id=current_user.id,
        name=name,
        surname=surname,
        email=email,
        skip=skip,
        limit=limit,
    )


@router.get('/birthdays', response_model=list[ContactResponse])
async def get_upcoming_birthdays(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contacts with birthdays in the next N days"""
    service = ContactService(db)
    return await service.get_upcoming_birthdays(user_id=current_user.id, days=days)


@router.get('/{contact_id}', response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contact by ID"""
    service = ContactService(db)
    contact = await service.get_contact(contact_id, user_id=current_user.id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return contact


@router.put('/{contact_id}', response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a contact"""
    service = ContactService(db)
    updated_contact = await service.update_contact(contact_id, contact, user_id=current_user.id)
    if not updated_contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')
    return updated_contact


@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a contact"""
    service = ContactService(db)
    if not await service.delete_contact(contact_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')