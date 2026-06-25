"""Base declarative class for SQLAlchemy ORM models.

This module defines the base class that all database models inherit from.
It provides the declarative foundation for SQLAlchemy ORM mapping.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models.

    This class serves as the declarative base for SQLAlchemy ORM.
    All model classes should inherit from this class to enable
    automatic table mapping and metadata tracking.

    Attributes:
        metadata: SQLAlchemy MetaData object that collects table information
            from all subclasses.
    """
    pass