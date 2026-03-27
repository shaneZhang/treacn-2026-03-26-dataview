"""测试配置"""
import sys
from pathlib import Path
import pytest
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config, DatabaseType
from core.database import DatabaseFactory
from models import Base


@pytest.fixture(scope='session')
def test_config():
    """测试配置fixture"""
    config = Config.get_instance()
    config.database_type = DatabaseType.SQLITE
    config.database_config['path'] = ':memory:'
    yield config
    Config._instance = None
    Config._initialized = False


@pytest.fixture(scope='function')
def test_db(test_config):
    """测试数据库fixture"""
    db_factory = DatabaseFactory.get_instance()
    db_factory.create_tables()
    
    yield db_factory
    
    db_factory.drop_tables()
    DatabaseFactory._instance = None
    DatabaseFactory._engine = None
    DatabaseFactory._session_factory = None


@pytest.fixture
def sample_student_data():
    """示例学生数据"""
    return {
        'student_id': '10001',
        'name': '张三',
        'gender': '男',
        'grade': '三年级',
        'age': 9,
        'enrollment_date': date(2022, 9, 1)
    }


@pytest.fixture
def sample_record_data():
    """示例身高记录数据"""
    return {
        'record_date': date.today(),
        'height': 130.5,
        'weight': 28.0,
        'age_at_record': 9,
        'grade_at_record': '三年级'
    }
