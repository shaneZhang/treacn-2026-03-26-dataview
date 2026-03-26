"""
Logging configuration for the Student Height Analysis system.

This module provides a centralized logging setup with both console and file output.
It supports different log levels, rotating file handlers, and JSON formatting.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from typing import Optional

from app.config.settings import settings


def setup_logging() -> logging.Logger:
    """
    Configure and set up the application logger.

    Returns:
        logging.Logger: Configured logger instance.

    This function sets up:
    - Console handler with human-readable format
    - Rotating file handler with JSON format
    - Different log levels for console and file output
    - Proper exception logging
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger("student_height_analysis")
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
    logger.propagate = False

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    json_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s %(lineno)d"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=_parse_size(settings.log_max_size),
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    # Set logging levels for third-party libraries
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    logger.info("Logging system initialized successfully")
    return logger


def _parse_size(size_str: str) -> int:
    """
    Parse size string (like '10MB') to bytes.

    Args:
        size_str: Size string with unit (KB, MB, GB).

    Returns:
        int: Size in bytes.

    Raises:
        ValueError: If the size format is not recognized.
    """
    units = {
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
    }

    size_str = size_str.strip().upper()
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                size = float(size_str[:-len(unit)])
                return int(size * multiplier)
            except ValueError:
                pass

    raise ValueError(f"Invalid size format: {size_str}. Use KB, MB, or GB.")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Optional name for the logger, defaults to the application logger.

    Returns:
        logging.Logger: Logger instance.
    """
    if name:
        return logging.getLogger(f"student_height_analysis.{name}")
    return logging.getLogger("student_height_analysis")


# Initialize logging when the module is imported
logger = setup_logging()
