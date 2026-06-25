"""Contact model representing a contact entry owned by a user.

This module defines the Contact ORM model that stores contact information
such as name, email, phone, date of birth, and additional notes.
Each contact is associated with a specific user.
"""

from datetime import date
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Contact(Base):
    """Represents a contact entry in the user's address book.

    Maps to the 'contacts' database table. Each contact belongs to a single
    user and stores personal information including name, contact details,
    and date of birth for birthday tracking.

    Attributes:
        id: Primary key identifier.
        name: Contact's first name (max 50 chars).
        surname: Contact's last name (max 50 chars).
        email: Contact's email address (max 50 chars).
        phone: Contact's phone number (max 20 chars).
        date_of_birth: Contact's date of birth for birthday features.
        other_info: Optional additional notes (max 255 chars).
        user_id: Foreign key referencing the owning user.
        user: User model instance that owns this contact.
    """

    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(nullable=False)
    other_info: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    user: Mapped['User'] = relationship('User', back_populates='contacts')