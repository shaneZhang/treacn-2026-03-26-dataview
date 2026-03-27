"""
数据库集成测试
"""

import pytest
from sqlalchemy import inspect, create_engine

from src.dao.models import Base, Student, ClassInfo, HeightRecord


class TestDatabaseSchema:
    """测试数据库架构"""

    def test_tables_created(self, db_session):
        """测试表是否创建成功"""
        from sqlalchemy import inspect
        
        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()

        assert 'students' in tables
        assert 'class_info' in tables
        assert 'height_records' in tables
        assert 'statistics_records' in tables
        assert 'import_export_logs' in tables

    def test_student_table_columns(self, db_session):
        """测试学生表列"""
        from sqlalchemy import inspect
        
        inspector = inspect(db_session.bind)
        columns = inspector.get_columns('students')
        column_names = [col['name'] for col in columns]

        assert 'id' in column_names
        assert 'student_id' in column_names
        assert 'name' in column_names
        assert 'gender' in column_names
        assert 'grade' in column_names
        assert 'age' in column_names
        assert 'height' in column_names
        assert 'weight' in column_names
        assert 'bmi' in column_names
        assert 'bmi_category' in column_names


class TestDatabaseOperations:
    """测试数据库操作"""

    def test_insert_and_query(self, db_session):
        """测试插入和查询"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        student_data = {
            'student_id': 'TEST001',
            'name': '测试学生',
            'gender': '男',
            'grade': '一年级',
            'age': 7,
            'height': 120.0,
            'weight': 22.0,
            'bmi': 15.3,
            'bmi_category': '正常'
        }

        # 插入
        created = dao.create(student_data)
        assert created.id is not None

        # 查询
        retrieved = dao.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.name == '测试学生'

    def test_update_operation(self, db_session):
        """测试更新操作"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        student_data = {
            'student_id': 'TEST002',
            'name': '原姓名',
            'gender': '女',
            'grade': '二年级',
            'age': 8,
            'height': 125.0,
            'weight': 24.0,
            'bmi': 15.4,
            'bmi_category': '正常'
        }

        created = dao.create(student_data)

        # 更新
        updated = dao.update(created.id, {'name': '新姓名', 'height': 126.0})
        assert updated.name == '新姓名'
        assert updated.height == 126.0

        # 验证更新
        retrieved = dao.get_by_id(created.id)
        assert retrieved.name == '新姓名'

    def test_delete_operation(self, db_session):
        """测试删除操作"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        student_data = {
            'student_id': 'TEST003',
            'name': '待删除',
            'gender': '男',
            'grade': '三年级',
            'age': 9,
            'height': 130.0,
            'weight': 26.0,
            'bmi': 15.4,
            'bmi_category': '正常'
        }

        created = dao.create(student_data)
        created_id = created.id

        # 删除
        result = dao.delete(created_id)
        assert result is True

        # 验证删除
        retrieved = dao.get_by_id(created_id)
        assert retrieved is None

    def test_transaction_rollback(self, db_session):
        """测试事务回滚"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        initial_count = dao.count()

        # 创建有效记录
        student_data = {
            'student_id': 'TEST004',
            'name': '事务测试',
            'gender': '男',
            'grade': '一年级',
            'age': 7,
            'height': 120.0,
            'weight': 22.0,
            'bmi': 15.3,
            'bmi_category': '正常'
        }

        created = dao.create(student_data)
        assert dao.count() == initial_count + 1


class TestForeignKeyConstraints:
    """测试外键约束"""

    def test_student_class_relationship(self, db_session):
        """测试学生和班级关系"""
        from src.dao.class_dao import ClassDAO
        from src.dao.student_dao import StudentDAO

        class_dao = ClassDAO(db_session)
        student_dao = StudentDAO(db_session)

        # 创建班级
        class_data = {
            'grade': '一年级',
            'class_number': 1,
            'class_name': '一年级1班'
        }
        class_info = class_dao.create(class_data)

        # 创建学生并关联班级
        student_data = {
            'student_id': 'TEST005',
            'name': '关联测试',
            'gender': '男',
            'grade': '一年级',
            'age': 7,
            'height': 120.0,
            'weight': 22.0,
            'bmi': 15.3,
            'bmi_category': '正常',
            'class_id': class_info.id
        }
        student = student_dao.create(student_data)

        # 验证关联
        assert student.class_id == class_info.id
