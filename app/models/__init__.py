"""
Database models package.

This package contains all SQLAlchemy database models for the application.
"""

from app.models.base import Base, BaseModel
from app.models.student import Student
from app.models.class_model import Class
from app.models.statistics import StatisticsRecord

# Export all models for easy access
__all__ = ["Base", "BaseModel", "Student", "Class", "StatisticsRecord"]
