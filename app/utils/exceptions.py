"""
Custom exception classes for the Student Height Analysis system.

This module defines a hierarchy of custom exceptions to provide
clear and specific error handling throughout the application.
"""

from typing import Optional, Dict, Any


class BaseError(Exception):
    """Base class for all custom exceptions in the application."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        """
        Initialize the base error.

        Args:
            message: Custom error message.
            details: Additional error details.
            error_code: Specific error code.
            status_code: HTTP status code (for API contexts).
        """
        self.message = message or self.message
        self.details = details or {}
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class ApplicationError(BaseError):
    """Base class for all application-specific errors."""

    status_code = 500
    error_code = "APPLICATION_ERROR"
    message = "An application error occurred"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary representation.

        Returns:
            Dict containing error information.
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }

    def __str__(self) -> str:
        """
        Return a string representation of the error.

        Returns:
            Formatted error string.
        """
        base = f"{self.error_code}: {self.message}"
        if self.details:
            base += f" - Details: {self.details}"
        return base


# Database-related exceptions
class DatabaseError(BaseError):
    """Base class for database-related errors."""

    status_code = 500
    error_code = "DATABASE_ERROR"
    message = "A database error occurred"


class ConnectionError(DatabaseError):
    """Raised when there's an issue with database connections."""

    error_code = "CONNECTION_ERROR"
    message = "Failed to establish or maintain a database connection"


class QueryError(DatabaseError):
    """Raised when a database query fails."""

    error_code = "QUERY_ERROR"
    message = "Database query execution failed"


class RecordNotFoundError(DatabaseError):
    """Raised when a requested record is not found in the database."""

    status_code = 404
    error_code = "RECORD_NOT_FOUND"
    message = "The requested record was not found"


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create a duplicate record."""

    status_code = 409
    error_code = "DUPLICATE_RECORD"
    message = "A record with the given identifier already exists"


class IntegrityError(DatabaseError):
    """Raised when a database integrity constraint is violated."""

    status_code = 400
    error_code = "INTEGRITY_ERROR"
    message = "Database integrity constraint violated"


# Data-related exceptions
class DataError(BaseError):
    """Base class for data processing errors."""

    status_code = 400
    error_code = "DATA_ERROR"
    message = "A data processing error occurred"


class InvalidDataError(DataError):
    """Raised when input data is invalid or malformed."""

    error_code = "INVALID_DATA"
    message = "The provided data is invalid or malformed"


class ValidationError(DataError):
    """Raised when data validation fails."""

    error_code = "VALIDATION_ERROR"
    message = "Data validation failed"


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""

    error_code = "MISSING_FIELD"
    message = "A required field is missing"


class FileProcessingError(DataError):
    """Raised when there's an error processing a file."""

    error_code = "FILE_PROCESSING_ERROR"
    message = "Failed to process the file"


# Configuration exceptions
class ConfigurationError(BaseError):
    """Raised when there's an issue with application configuration."""

    error_code = "CONFIGURATION_ERROR"
    message = "Application configuration error"


class MissingSettingError(ConfigurationError):
    """Raised when a required configuration setting is missing."""

    error_code = "MISSING_SETTING"
    message = "A required configuration setting is missing"


# Analysis exceptions
class AnalysisError(BaseError):
    """Raised when data analysis fails."""

    error_code = "ANALYSIS_ERROR"
    message = "Data analysis failed"


class VisualizationError(BaseError):
    """Raised when visualization generation fails."""

    error_code = "VISUALIZATION_ERROR"
    message = "Failed to generate visualization"


# IO exceptions
class ImportError(DataError):
    """Raised when data import fails."""

    error_code = "IMPORT_ERROR"
    message = "Failed to import data"


class ExportError(DataError):
    """Raised when data export fails."""

    error_code = "EXPORT_ERROR"
    message = "Failed to export data"


# Observer pattern exceptions
class ObserverError(BaseError):
    """Raised when there's an error in the observer pattern implementation."""

    error_code = "OBSERVER_ERROR"
    message = "Observer notification error"
