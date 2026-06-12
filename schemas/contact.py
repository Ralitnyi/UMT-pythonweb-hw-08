from datetime import date
from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    """Base schema for contact data"""
    name: str = Field(..., min_length=1, max_length=50, description="Contact first name")
    surname: str = Field(..., min_length=1, max_length=50, description="Contact last name")
    email: EmailStr = Field(..., description="Contact email address")
    phone: str = Field(..., min_length=1, max_length=20, description="Contact phone number")
    date_of_birth: date = Field(..., description="Contact date of birth")
    other_info: str | None = Field(None, max_length=255, description="Additional information")


class ContactCreate(ContactBase):
    """Schema for creating a new contact"""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    name: str | None = Field(None, min_length=1, max_length=50, description="Contact first name")
    surname: str | None = Field(None, min_length=1, max_length=50, description="Contact last name")
    email: EmailStr | None = Field(None, description="Contact email address")
    phone: str | None = Field(None, min_length=1, max_length=20, description="Contact phone number")
    date_of_birth: date | None = Field(None, description="Contact date of birth")
    other_info: str | None = Field(None, max_length=255, description="Additional information")


class ContactResponse(ContactBase):
    """Schema for contact response"""
    id: int = Field(..., description="Contact ID")
    
    class Config:
        from_attributes = True
