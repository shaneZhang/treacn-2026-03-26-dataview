"""
数据访问层 (DAO)

提供数据库模型和访问对象。
"""

from src.dao.models import (
    Base,
    Student,
    ClassInfo,
    HeightRecord,
    StatisticsRecord,
    ImportExportLog,
    Gender,
    BMICategory,
    Grade,
)

from src.dao.database import (
    DatabaseManager,
    get_database_manager,
    get_engine,
    get_session,
    create_tables,
    drop_tables,
)

from src.dao.student_dao import StudentDAO, HeightRecordDAO
from src.dao.class_dao import ClassDAO

__all__ = [
    # Models
    "Base",
    "Student",
    "ClassInfo",
    "HeightRecord",
    "StatisticsRecord",
    "ImportExportLog",
    "Gender",
    "BMICategory",
    "Grade",
    # Database
    "DatabaseManager",
    "get_database_manager",
    "get_engine",
    "get_session",
    "create_tables",
    "drop_tables",
    # DAOs
    "StudentDAO",
    "HeightRecordDAO",
    "ClassDAO",
]
