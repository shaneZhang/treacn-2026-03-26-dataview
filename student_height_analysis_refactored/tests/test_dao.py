"""
学生DAO单元测试
"""
import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError

from core.dao import StudentDAO
from models import Student
from utils import StudentNotFoundException, DuplicateDataException


class TestStudentDAO:
    """学生DAO测试类"""
    
    def test_create_student(self, test_db, sample_student_data):
        """测试创建学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        student = dao.create(sample_student_data)
        
        assert student.id is not None
        assert student.student_id == sample_student_data['student_id']
        assert student.name == sample_student_data['name']
        assert student.gender == sample_student_data['gender']
        assert student.grade == sample_student_data['grade']
        assert student.age == sample_student_data['age']
    
    def test_create_duplicate_student(self, test_db, sample_student_data):
        """测试创建重复学号的学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        dao.create(sample_student_data)
        
        with pytest.raises(DuplicateDataException):
            dao.create(sample_student_data)
    
    def test_get_by_id(self, test_db, sample_student_data):
        """测试根据ID获取学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        created = dao.create(sample_student_data)
        found = dao.get_by_id(created.id)
        
        assert found.id == created.id
        assert found.student_id == created.student_id
    
    def test_get_by_id_not_found(self, test_db):
        """测试获取不存在的学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        with pytest.raises(StudentNotFoundException):
            dao.get_by_id(99999)
    
    def test_get_by_student_number(self, test_db, sample_student_data):
        """测试根据学号获取学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        created = dao.create(sample_student_data)
        found = dao.get_by_student_number(sample_student_data['student_id'])
        
        assert found.id == created.id
    
    def test_get_all(self, test_db):
        """测试获取所有学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        for i in range(5):
            dao.create({
                'student_id': f'1000{i}',
                'name': f'学生{i}',
                'gender': '男' if i % 2 == 0 else '女',
                'grade': '三年级',
                'age': 9,
                'enrollment_date': date.today()
            })
        
        students = dao.get_all(limit=10)
        
        assert len(students) == 5
    
    def test_get_all_with_filter(self, test_db):
        """测试带过滤条件获取学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        dao.create({
            'student_id': '10001',
            'name': '张三',
            'gender': '男',
            'grade': '三年级',
            'age': 9,
            'enrollment_date': date.today()
        })
        
        dao.create({
            'student_id': '10002',
            'name': '李四',
            'gender': '女',
            'grade': '四年级',
            'age': 10,
            'enrollment_date': date.today()
        })
        
        students = dao.get_all(grade='三年级')
        assert len(students) == 1
        
        students = dao.get_all(gender='女')
        assert len(students) == 1
    
    def test_update_student(self, test_db, sample_student_data):
        """测试更新学生信息"""
        dao = StudentDAO(session=test_db.get_session())
        
        created = dao.create(sample_student_data)
        
        updated = dao.update(created.id, {'age': 10, 'grade': '四年级'})
        
        assert updated.age == 10
        assert updated.grade == '四年级'
    
    def test_delete_student(self, test_db, sample_student_data):
        """测试删除学生"""
        dao = StudentDAO(session=test_db.get_session())
        
        created = dao.create(sample_student_data)
        
        result = dao.delete(created.id)
        assert result is True
        
        with pytest.raises(StudentNotFoundException):
            dao.get_by_id(created.id)
    
    def test_count(self, test_db):
        """测试统计学生数量"""
        dao = StudentDAO(session=test_db.get_session())
        
        for i in range(3):
            dao.create({
                'student_id': f'1000{i}',
                'name': f'学生{i}',
                'gender': '男' if i % 2 == 0 else '女',
                'grade': '三年级',
                'age': 9,
                'enrollment_date': date.today()
            })
        
        count = dao.count()
        assert count == 3
        
        count = dao.count(gender='男')
        assert count == 2
