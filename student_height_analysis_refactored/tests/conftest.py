"""
Pytest配置文件

定义测试固件和共享配置。
"""

import os
import sys
import pytest
from typing import Generator

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.dao.database import DatabaseManager
from src.dao.models import Base
from src.dao.student_dao import StudentDAO, HeightRecordDAO
from src.dao.class_dao import ClassDAO
from src.service.data_generator import DataGeneratorService
from src.service.analysis_service import AnalysisService
from src.visualization.visualizer import HeightVisualizer


@pytest.fixture(scope="session")
def test_db_path() -> str:
    """测试数据库路径"""
    return ":memory:"


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """提供数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    
    # 创建内存数据库引擎
    engine = create_engine('sqlite:///:memory:')
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    # 创建会话工厂
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # 清理
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def student_dao(db_session) -> StudentDAO:
    """提供学生DAO实例"""
    return StudentDAO(db_session)


@pytest.fixture
def height_record_dao(db_session) -> HeightRecordDAO:
    """提供身高记录DAO实例"""
    return HeightRecordDAO(db_session)


@pytest.fixture
def class_dao(db_session) -> ClassDAO:
    """提供班级DAO实例"""
    return ClassDAO(db_session)


@pytest.fixture
def data_generator(db_session) -> DataGeneratorService:
    """提供数据生成服务实例"""
    return DataGeneratorService(db_session)


@pytest.fixture
def analysis_service(db_session) -> AnalysisService:
    """提供分析服务实例"""
    return AnalysisService(db_session)


@pytest.fixture
def visualizer(db_session) -> HeightVisualizer:
    """提供可视化器实例"""
    return HeightVisualizer(db_session)


@pytest.fixture
def sample_student_data() -> list:
    """提供示例学生数据"""
    return [
        {
            'student_id': 'STU202400001',
            'name': '张三',
            'gender': '男',
            'grade': '一年级',
            'age': 7,
            'height': 120.5,
            'weight': 22.0,
            'bmi': 15.1,
            'bmi_category': '正常',
            'enrollment_date': '2024-09-01',
        },
        {
            'student_id': 'STU202400002',
            'name': '李四',
            'gender': '女',
            'grade': '一年级',
            'age': 6,
            'height': 118.0,
            'weight': 20.5,
            'bmi': 14.7,
            'bmi_category': '正常',
            'enrollment_date': '2024-09-01',
        },
        {
            'student_id': 'STU202400003',
            'name': '王五',
            'gender': '男',
            'grade': '二年级',
            'age': 8,
            'height': 126.0,
            'weight': 25.0,
            'bmi': 15.7,
            'bmi_category': '正常',
            'enrollment_date': '2023-09-01',
        },
    ]
