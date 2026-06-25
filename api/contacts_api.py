"""Contact management API routes.

This module defines the FastAPI router for contact CRUD operations
including creating, reading, updating, deleting contacts, as well as
searching and querying upcoming birthdays.
"""

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
    """Create a new contact for the authenticated user.

    Args:
        contact: Contact creation data.
        db: Async database session.
        current_user: The authenticated user.

    Returns:
        ContactResponse: The newly created contact.

    Raises:
        HTTPException 400: If the contact data is invalid.
    """
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
    """Get all contacts for the authenticated user with pagination.

    Args:
        skip: Number of contacts to skip for pagination.
        limit: Maximum number of contacts to return (1-1000).
        db: Async database session.
        current_user: The authenticated user.

    Returns:
        list[ContactResponse]: List of contacts belonging to the user.
    """
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
    """Search contacts by name, surname, or email.

    At least one search parameter is recommended. Uses case-insensitive
    partial matching. Multiple criteria are combined with OR logic.

    Args:
        name: Optional name to search for.
        surname: Optional surname to search for.
        email: Optional email to search for.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Async database session.
        current_user: The authenticated user.

    Returns:
        list[ContactResponse]: List of matching contacts.
    """
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
    """Get contacts with birthdays in the next N days.

    Calculates upcoming birthdays for all contacts and filters those
    whose next birthday falls within the specified range.

    Args:
        days: Number of days to look ahead (1-365, default: 7).
        db: Async database session.
        current_user: The authenticated user.

    Returns:
        list[ContactResponse]: Contacts with upcoming birthdays.
    """
    service = ContactService(db)
    return await service.get_upcoming_birthdays(user_id=current_user.id, days=days)


@router.get('/{contact_id}', response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific contact by ID.

    Args:
        contact_id: The contact's unique identifier.
        db: Async database session.
        current_user: The authenticated user.

    Returns:
        ContactResponse: The requested contact data.

    Raises:
        HTTPException 404: If the contact is not found or doesn't belong to the user.
    """
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
    """Update a contact with partial data.

    Only the fields provided in the request body will be updated.

    Args:
        contact_id: The contact's unique identifier.
        contact: Update data (only provided fields are applied).
        db: Async database session.
        current_user: The authenticated user.

    Returns:
        ContactResponse: The updated contact data.

    Raises:
        HTTPException 404: If the contact is not found.
    """
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
    """Delete a contact by ID.

    Args:
        contact_id: The contact's unique identifier.
        db: Async database session.
        current_user: The authenticated user.

    Raises:
        HTTPException 404: If the contact is not found.
    """
    service = ContactService(db)
    if not await service.delete_contact(contact_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found')