"""
Base service class providing common functionality for all services.

This module defines the base service class that handles common operations
and provides access to DAO factories and event management.
"""

from typing import Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.config.database import get_db_pool, db_session
from app.dao import DAOFactory
from app.utils.logger import get_logger
from app.utils.observer import get_event_manager, EventType
from app.utils.exceptions import DatabaseError

logger = get_logger(__name__)


class BaseService:
    """
    Base service class with common functionality.

    All service classes should inherit from this class to gain access
    to common functionality like database sessions, DAO factories,
    and event management.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the service with an optional database session.

        Args:
            session: Optional SQLAlchemy database session. If not provided,
                     a new session will be created when needed.
        """
        self._session = session
        self._dao_factory: Optional[DAOFactory] = None
        self._event_manager = get_event_manager()

    @property
    def session(self) -> Session:
        """
        Get the database session, creating one if necessary.

        Returns:
            Session: SQLAlchemy database session.

        Raises:
            DatabaseError: If there's an error getting the session.
        """
        if self._session is None:
            try:
                self._session = get_db_pool().get_session()
            except Exception as e:
                logger.error(f"Failed to get database session: {e}")
                raise DatabaseError(
                    message="Failed to get database session",
                    details={"error": str(e)}
                ) from e
        return self._session

    @property
    def dao(self) -> DAOFactory:
        """
        Get the DAO factory for this service.

        Returns:
            DAOFactory: DAO factory instance.
        """
        if self._dao_factory is None:
            self._dao_factory = DAOFactory(self.session)
        return self._dao_factory

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        This context manager ensures that database operations are
        committed on success and rolled back on failure.

        Yields:
            Session: Database session within the transaction.

        Raises:
            Exception: Any exception that occurs during the transaction.
        """
        session = self.session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session is not None:
            self._session.rollback()

    def close(self) -> None:
        """Close the database session if it exists."""
        if self._session is not None:
            self._session.close()
            self._session = None
            self._dao_factory = None

    def emit_event(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None
    ) -> None:
        """
        Emit an event to the event manager.

        Args:
            event_type: Type of event to emit.
            data: Optional event data.
            source: Optional event source (defaults to class name).
        """
        self._event_manager.notify_event(
            event_type=event_type,
            data=data or {},
            source=source or self.__class__.__name__
        )

    def add_observer(self, observer) -> None:
        """
        Add an observer to receive events from this service.

        Args:
            observer: The observer to add.
        """
        self._event_manager.add_observer(observer)

    def remove_observer(self, observer) -> None:
        """
        Remove an observer from this service.

        Args:
            observer: The observer to remove.
        """
        self._event_manager.remove_observer(observer)

    def __enter__(self):
        """
        Enter the context manager.

        Returns:
            BaseService: The service instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager, closing the session if necessary.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Returns:
            bool: False to propagate exceptions, True to suppress.
        """
        self.close()
        return False
