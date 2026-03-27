"""
DAO层单元测试
"""

import pytest
from src.dao.student_dao import StudentDAO, HeightRecordDAO
from src.dao.class_dao import ClassDAO
from src.dao.models import Student, ClassInfo, HeightRecord


class TestStudentDAO:
    """测试学生DAO"""

    def test_create_student(self, db_session, sample_student_data):
        """测试创建学生"""
        dao = StudentDAO(db_session)
        student = dao.create(sample_student_data[0])

        assert student is not None
        assert student.student_id == sample_student_data[0]['student_id']
        assert student.name == sample_student_data[0]['name']

    def test_get_by_id(self, db_session, sample_student_data):
        """测试根据ID获取学生"""
        dao = StudentDAO(db_session)
        created = dao.create(sample_student_data[0])

        retrieved = dao.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.student_id == created.student_id

    def test_get_by_student_id(self, db_session, sample_student_data):
        """测试根据学号获取学生"""
        dao = StudentDAO(db_session)
        created = dao.create(sample_student_data[0])

        retrieved = dao.get_by_student_id(created.student_id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_by_condition(self, db_session, sample_student_data):
        """测试条件查询"""
        dao = StudentDAO(db_session)
        for data in sample_student_data:
            dao.create(data)

        # 按年级查询
        results = dao.get_by_condition(grade='一年级')
        assert len(results) == 2

        # 按性别查询
        results = dao.get_by_condition(gender='男')
        assert len(results) == 2

    def test_update_student(self, db_session, sample_student_data):
        """测试更新学生"""
        dao = StudentDAO(db_session)
        created = dao.create(sample_student_data[0])

        updated = dao.update(created.id, {'height': 125.0})
        assert updated.height == 125.0

    def test_delete_student(self, db_session, sample_student_data):
        """测试删除学生"""
        dao = StudentDAO(db_session)
        created = dao.create(sample_student_data[0])

        result = dao.delete(created.id)
        assert result is True

        deleted = dao.get_by_id(created.id)
        assert deleted is None

    def test_count(self, db_session, sample_student_data):
        """测试计数"""
        dao = StudentDAO(db_session)
        initial_count = dao.count()

        dao.create(sample_student_data[0])
        assert dao.count() == initial_count + 1


class TestClassDAO:
    """测试班级DAO"""

    def test_create_class(self, db_session):
        """测试创建班级"""
        dao = ClassDAO(db_session)
        class_data = {
            'grade': '一年级',
            'class_number': 1,
            'class_name': '一年级1班'
        }

        created = dao.create(class_data)
        assert created.grade == '一年级'
        assert created.class_number == 1

    def test_get_by_grade_and_number(self, db_session):
        """测试根据年级和班级编号查询"""
        dao = ClassDAO(db_session)
        class_data = {
            'grade': '一年级',
            'class_number': 1,
            'class_name': '一年级1班'
        }
        dao.create(class_data)

        result = dao.get_by_grade_and_number('一年级', 1)
        assert result is not None
        assert result.class_name == '一年级1班'


class TestHeightRecordDAO:
    """测试身高记录DAO"""

    def test_create_record(self, db_session, sample_student_data):
        """测试创建身高记录"""
        # 先创建学生
        student_dao = StudentDAO(db_session)
        student = student_dao.create(sample_student_data[0])

        # 创建身高记录
        record_dao = HeightRecordDAO(db_session)
        record_data = {
            'student_id': student.id,
            'height': 120.0,
            'weight': 22.0,
            'record_date': '2024-01-01',
            'age': 7
        }

        created = record_dao.create(record_data)
        assert created.height == 120.0
        assert created.student_id == student.id

    def test_get_by_student(self, db_session, sample_student_data):
        """测试获取学生的身高记录"""
        # 先创建学生
        student_dao = StudentDAO(db_session)
        student = student_dao.create(sample_student_data[0])

        # 创建多条记录
        record_dao = HeightRecordDAO(db_session)
        for i in range(3):
            record_dao.create({
                'student_id': student.id,
                'height': 120.0 + i,
                'weight': 22.0 + i,
                'record_date': f'2024-0{i+1}-01',
                'age': 7
            })

        records = record_dao.get_by_student(student.id)
        assert len(records) == 3
