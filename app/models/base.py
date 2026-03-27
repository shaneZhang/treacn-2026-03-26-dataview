"""
Base model class for all database models.

This module defines the base SQLAlchemy model class with common
fields and functionality for all database models.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields and methods.

    All database models should inherit from this class to have
    access to common fields like id, created_at, and updated_at.
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def save(self, session: Session, commit: bool = True) -> None:
        """
        Save the model instance to the database.

        Args:
            session: SQLAlchemy database session.
            commit: Whether to commit the transaction after saving.
        """
        session.add(self)
        if commit:
            session.commit()

    def delete(self, session: Session, commit: bool = True) -> None:
        """
        Delete the model instance from the database.

        Args:
            session: SQLAlchemy database session.
            commit: Whether to commit the transaction after deleting.
        """
        session.delete(self)
        if commit:
            session.commit()

    def refresh(self, session: Session) -> None:
        """
        Refresh the model instance with data from the database.

        Args:
            session: SQLAlchemy database session.
        """
        session.refresh(self)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.

        Returns:
            Dictionary representation of the model.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """
        Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model data.

        Returns:
            New model instance.
        """
        return cls(**data)

    def update_from_dict(self, data: Dict[str, Any], session: Session, commit: bool = True) -> None:
        """
        Update the model instance from a dictionary.

        Args:
            data: Dictionary containing fields to update.
            session: SQLAlchemy database session.
            commit: Whether to commit the transaction after updating.
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ["id", "created_at", "updated_at"]:
                setattr(self, key, value)
        if commit:
            session.commit()

    def __repr__(self) -> str:
        """
        Return a string representation of the model instance.

        Returns:
            String representation of the model.
        """
        return f"<{self.__class__.__name__}(id={self.id})>"
