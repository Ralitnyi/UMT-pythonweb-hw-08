"""Pydantic schemas for contact management.

This module defines request/response data models for creating, updating,
and querying contacts in the address book.
"""

from datetime import date
from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    """Base schema with common contact fields.

    Attributes:
        name: Contact's first name (1-50 characters).
        surname: Contact's last name (1-50 characters).
        email: Contact's email address.
        phone: Contact's phone number (1-20 characters).
        date_of_birth: Contact's date of birth.
        other_info: Optional additional notes (max 255 characters).
    """
    name: str = Field(..., min_length=1, max_length=50, description="Contact first name")
    surname: str = Field(..., min_length=1, max_length=50, description="Contact last name")
    email: EmailStr = Field(..., description="Contact email address")
    phone: str = Field(..., min_length=1, max_length=20, description="Contact phone number")
    date_of_birth: date = Field(..., description="Contact date of birth")
    other_info: str | None = Field(None, max_length=255, description="Additional information")


class ContactCreate(ContactBase):
    """Schema for creating a new contact.

    Inherits all fields from ContactBase. All fields are required
    except other_info.
    """
    pass


class ContactUpdate(BaseModel):
    """Schema for updating an existing contact.

    All fields are optional — only provided fields will be updated.

    Attributes:
        name: New first name.
        surname: New last name.
        email: New email address.
        phone: New phone number.
        date_of_birth: New date of birth.
        other_info: New additional information.
    """
    name: str | None = Field(None, min_length=1, max_length=50, description="Contact first name")
    surname: str | None = Field(None, min_length=1, max_length=50, description="Contact last name")
    email: EmailStr | None = Field(None, description="Contact email address")
    phone: str | None = Field(None, min_length=1, max_length=20, description="Contact phone number")
    date_of_birth: date | None = Field(None, description="Contact date of birth")
    other_info: str | None = Field(None, max_length=255, description="Additional information")


class ContactResponse(ContactBase):
    """Schema for contact data in API responses.

    Extends ContactBase with the contact's unique identifier.

    Attributes:
        id: Contact's unique identifier.
    """
    id: int = Field(..., description="Contact ID")

    class Config:
        from_attributes = True