"""
Data Access Object (DAO) package.

This package contains all DAO classes for database operations,
providing a clean separation between business logic and data access.
"""

from app.dao.base_dao import BaseDAO
from app.dao.student_dao import StudentDAO
from app.dao.class_dao import ClassDAO
from app.dao.statistics_dao import StatisticsRecordDAO

# DAO Factory for easy access
class DAOFactory:
    """
    Factory class to create DAO instances.

    This factory provides a convenient way to create DAO instances
    with a given database session.
    """

    def __init__(self, session):
        """
        Initialize the DAO factory with a database session.

        Args:
            session: SQLAlchemy database session.
        """
        self.session = session

    @property
    def student(self) -> StudentDAO:
        """Get StudentDAO instance."""
        return StudentDAO(self.session)

    @property
    def class_(self) -> ClassDAO:
        """Get ClassDAO instance."""
        return ClassDAO(self.session)

    @property
    def statistics(self) -> StatisticsRecordDAO:
        """Get StatisticsRecordDAO instance."""
        return StatisticsRecordDAO(self.session)


# Export all DAO classes and factory
__all__ = [
    "BaseDAO",
    "StudentDAO",
    "ClassDAO",
    "StatisticsRecordDAO",
    "DAOFactory"
]
