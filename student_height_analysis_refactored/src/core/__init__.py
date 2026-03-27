"""
核心模块

包含异常处理、日志管理、观察者模式等核心功能。
"""

from src.core.exceptions import (
    BaseAppException,
    DatabaseException,
    ConnectionException,
    QueryException,
    DataValidationException,
    NotFoundException,
    ImportExportException,
    VisualizationException,
    ConfigurationException,
)

from src.core.logger import get_logger, get_logger_manager, LoggerManager

from src.core.observer import (
    DataChangeType,
    DataChangeEvent,
    Observer,
    Subject,
    LoggingObserver,
    CacheInvalidationObserver,
    NotificationObserver,
    DataChangeSubject,
    get_data_change_subject,
)

__all__ = [
    # Exceptions
    "BaseAppException",
    "DatabaseException",
    "ConnectionException",
    "QueryException",
    "DataValidationException",
    "NotFoundException",
    "ImportExportException",
    "VisualizationException",
    "ConfigurationException",
    # Logger
    "get_logger",
    "get_logger_manager",
    "LoggerManager",
    # Observer
    "DataChangeType",
    "DataChangeEvent",
    "Observer",
    "Subject",
    "LoggingObserver",
    "CacheInvalidationObserver",
    "NotificationObserver",
    "DataChangeSubject",
    "get_data_change_subject",
]
