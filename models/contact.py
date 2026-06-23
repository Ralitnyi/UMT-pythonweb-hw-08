from datetime import date
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Contact(Base):
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
    