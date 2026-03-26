"""
Base DAO (Data Access Object) class providing common database operations.

This module defines the base DAO class with common CRUD operations
that can be inherited by specific DAO classes for different models.
"""

from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.base import BaseModel
from app.utils.logger import get_logger
from app.utils.exceptions import (
    DatabaseError,
    RecordNotFoundError,
    DuplicateRecordError,
    QueryError,
    IntegrityError
)

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseDAO(Generic[T]):
    """
    Base Data Access Object class providing common CRUD operations.

    This class should be inherited by specific DAO classes for each model.
    It provides generic implementations for common database operations.

    Attributes:
        model: The SQLAlchemy model class this DAO operates on.
    """

    model: type[T]

    def __init__(self, session: Session):
        """
        Initialize the DAO with a database session.

        Args:
            session: SQLAlchemy database session.
        """
        self.session = session

    def create(self, **kwargs) -> T:
        """
        Create a new record in the database.

        Args:
            **kwargs: Model attributes as keyword arguments.

        Returns:
            T: The created model instance.

        Raises:
            DuplicateRecordError: If a record with unique constraints already exists.
            DatabaseError: If there's an error creating the record.
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.flush()
            logger.debug(f"Created {self.model.__name__} with id={instance.id}")
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = str(e)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                logger.warning(f"Duplicate record for {self.model.__name__}: {e}")
                raise DuplicateRecordError(
                    message=f"Duplicate {self.model.__name__} record",
                    details={"error": error_msg}
                ) from e
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise DatabaseError(
                message=f"Failed to create {self.model.__name__}",
                details={"error": error_msg}
            ) from e

    def get_by_id(self, record_id: int) -> Optional[T]:
        """
        Retrieve a record by its ID.

        Args:
            record_id: The ID of the record to retrieve.

        Returns:
            Optional[T]: The model instance if found, None otherwise.
        """
        try:
            return self.session.query(self.model).filter_by(id=record_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id={record_id}: {e}")
            raise QueryError(
                message=f"Failed to get {self.model.__name__} by ID",
                details={"error": str(e), "id": record_id}
            ) from e

    def get_by_id_or_raise(self, record_id: int) -> T:
        """
        Retrieve a record by its ID or raise an error if not found.

        Args:
            record_id: The ID of the record to retrieve.

        Returns:
            T: The model instance.

        Raises:
            RecordNotFoundError: If the record is not found.
        """
        instance = self.get_by_id(record_id)
        if instance is None:
            logger.warning(f"{self.model.__name__} with id={record_id} not found")
            raise RecordNotFoundError(
                message=f"{self.model.__name__} with id={record_id} not found",
                details={"id": record_id}
            )
        return instance

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Retrieve all records of this model.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List[T]: List of model instances.
        """
        try:
            query = self.session.query(self.model)
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise QueryError(
                message=f"Failed to get all {self.model.__name__}",
                details={"error": str(e)}
            ) from e

    def filter_by(self, **kwargs) -> List[T]:
        """
        Filter records by given criteria.

        Args:
            **kwargs: Filter criteria as keyword arguments.

        Returns:
            List[T]: List of model instances matching the criteria.
        """
        try:
            return self.session.query(self.model).filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            logger.error(f"Error filtering {self.model.__name__}: {e}")
            raise QueryError(
                message=f"Failed to filter {self.model.__name__}",
                details={"error": str(e), "criteria": kwargs}
            ) from e

    def filter_one(self, **kwargs) -> Optional[T]:
        """
        Filter records by given criteria and return the first match.

        Args:
            **kwargs: Filter criteria as keyword arguments.

        Returns:
            Optional[T]: First matching model instance, or None if no match.
        """
        try:
            return self.session.query(self.model).filter_by(**kwargs).first()
        except SQLAlchemyError as e:
            logger.error(f"Error filtering {self.model.__name__}: {e}")
            raise QueryError(
                message=f"Failed to filter {self.model.__name__}",
                details={"error": str(e), "criteria": kwargs}
            ) from e

    def update(self, record_id: int, **kwargs) -> T:
        """
        Update a record by its ID.

        Args:
            record_id: The ID of the record to update.
            **kwargs: Fields to update as keyword arguments.

        Returns:
            T: The updated model instance.

        Raises:
            RecordNotFoundError: If the record is not found.
            IntegrityError: If the update violates database constraints.
            DatabaseError: If there's an error updating the record.
        """
        instance = self.get_by_id_or_raise(record_id)
        try:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.flush()
            logger.debug(f"Updated {self.model.__name__} with id={record_id}")
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = str(e)
            if "integrity" in error_msg.lower() or "constraint" in error_msg.lower():
                logger.warning(f"Integrity error updating {self.model.__name__} id={record_id}: {e}")
                raise IntegrityError(
                    message=f"Integrity constraint violation updating {self.model.__name__}",
                    details={"error": error_msg, "id": record_id}
                ) from e
            logger.error(f"Error updating {self.model.__name__} id={record_id}: {e}")
            raise DatabaseError(
                message=f"Failed to update {self.model.__name__}",
                details={"error": error_msg, "id": record_id}
            ) from e

    def delete(self, record_id: int) -> bool:
        """
        Delete a record by its ID.

        Args:
            record_id: The ID of the record to delete.

        Returns:
            bool: True if the record was deleted successfully.

        Raises:
            RecordNotFoundError: If the record is not found.
            DatabaseError: If there's an error deleting the record.
        """
        instance = self.get_by_id_or_raise(record_id)
        try:
            self.session.delete(instance)
            self.session.flush()
            logger.debug(f"Deleted {self.model.__name__} with id={record_id}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting {self.model.__name__} id={record_id}: {e}")
            raise DatabaseError(
                message=f"Failed to delete {self.model.__name__}",
                details={"error": str(e), "id": record_id}
            ) from e

    def count(self, **kwargs) -> int:
        """
        Count the number of records matching the given criteria.

        Args:
            **kwargs: Filter criteria as keyword arguments.

        Returns:
            int: Number of matching records.
        """
        try:
            query = self.session.query(self.model)
            if kwargs:
                query = query.filter_by(**kwargs)
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise QueryError(
                message=f"Failed to count {self.model.__name__}",
                details={"error": str(e), "criteria": kwargs}
            ) from e

    def exists(self, **kwargs) -> bool:
        """
        Check if any records exist matching the given criteria.

        Args:
            **kwargs: Filter criteria as keyword arguments.

        Returns:
            bool: True if matching records exist, False otherwise.
        """
        return self.count(**kwargs) > 0

    def bulk_create(self, instances: List[Dict[str, Any]]) -> List[T]:
        """
        Bulk create multiple records.

        Args:
            instances: List of dictionaries containing model attributes.

        Returns:
            List[T]: List of created model instances.

        Raises:
            DatabaseError: If there's an error creating the records.
        """
        try:
            objects = [self.model(**data) for data in instances]
            self.session.bulk_save_objects(objects, return_defaults=True)
            self.session.flush()
            logger.debug(f"Bulk created {len(objects)} {self.model.__name__} records")
            return objects
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise DatabaseError(
                message=f"Failed to bulk create {self.model.__name__}",
                details={"error": str(e), "count": len(instances)}
            ) from e

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        filter_criteria: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc_order: bool = False
    ) -> Dict[str, Any]:
        """
        Paginate records with optional filtering and sorting.

        Args:
            page: Page number (1-based).
            per_page: Number of records per page.
            filter_criteria: Optional filter criteria.
            order_by: Optional field name to sort by.
            desc_order: Whether to sort in descending order.

        Returns:
            Dict[str, Any]: Pagination result containing items, total, page, and per_page.
        """
        try:
            query = self.session.query(self.model)

            if filter_criteria:
                query = query.filter_by(**filter_criteria)

            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if desc_order:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))

            total = query.count()
            offset = (page - 1) * per_page
            items = query.offset(offset).limit(per_page).all()

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        except SQLAlchemyError as e:
            logger.error(f"Error paginating {self.model.__name__}: {e}")
            raise QueryError(
                message=f"Failed to paginate {self.model.__name__}",
                details={"error": str(e), "page": page, "per_page": per_page}
            ) from e
