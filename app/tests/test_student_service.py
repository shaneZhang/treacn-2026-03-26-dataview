"""
Unit tests for the StudentService class.

This module contains tests for student-related functionality including:
- Student creation, retrieval, update, and deletion
- Data validation
- Query operations
"""

import pytest
from datetime import date, datetime
from typing import List

from app.models.student import Student
from app.service.student_service import StudentService
from app.utils.exceptions import ValidationError, RecordNotFoundError


class TestStudentService:
    """Test cases for StudentService."""

    def test_create_student(self, test_session):
        """
        Test creating a new student with valid data.
        
        Steps:
        1. Create a StudentService instance
        2. Create a new student with valid data
        3. Verify the student was created correctly
        
        Expected: Student should be created with all fields correctly set.
        """
        service = StudentService(test_session)
        
        student = service.create_student(
            student_id=1001,
            name="张三",
            gender="男",
            grade="一年级",
            age=7,
            height_cm=125.5,
            weight_kg=28.5,
            enrollment_date=date.today()
        )
        
        assert student is not None
        assert student.student_id == 1001
        assert student.name == "张三"
        assert student.gender == "男"
        assert student.grade == "一年级"
        assert student.age == 7
        assert student.height_cm == 125.5
        assert student.weight_kg == 28.5
        assert student.bmi == pytest.approx(18.1, 0.1)

    def test_create_student_duplicate_student_id(self, test_session):
        """
        Test creating a student with duplicate student_id.
        
        Expected: ValidationError should be raised.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 1002,
            "name": "李四",
            "gender": "女",
            "grade": "二年级",
            "age": 8,
            "height_cm": 130.0,
            "weight_kg": 30.0,
            "enrollment_date": date.today()
        }
        
        # Create first student
        service.create_student(**student_data)
        
        # Try to create another student with same student_id
        with pytest.raises(ValidationError):
            service.create_student(**student_data)

    def test_create_student_invalid_gender(self, test_session):
        """
        Test creating a student with invalid gender.
        
        Expected: ValidationError should be raised.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 1003,
            "name": "王五",
            "gender": "其他",  # Invalid gender
            "grade": "三年级",
            "age": 9,
            "height_cm": 135.0,
            "weight_kg": 35.0,
            "enrollment_date": date.today()
        }
        
        with pytest.raises(ValidationError):
            service.create_student(**student_data)

    def test_get_student_by_id(self, test_session):
        """
        Test retrieving a student by ID.
        
        Expected: Correct student should be returned.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 1004,
            "name": "赵六",
            "gender": "男",
            "grade": "四年级",
            "age": 10,
            "height_cm": 140.0,
            "weight_kg": 40.0,
            "enrollment_date": date.today()
        }
        
        created_student = service.create_student(**student_data)
        retrieved_student = service.get_student_by_id(created_student.id)
        
        assert retrieved_student is not None
        assert retrieved_student.student_id == 1004
        assert retrieved_student.name == "赵六"

    def test_get_student_by_student_id(self, test_session):
        """
        Test retrieving a student by student_id.
        
        Expected: Correct student should be returned.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 1005,
            "name": "钱七",
            "gender": "女",
            "grade": "五年级",
            "age": 11,
            "height_cm": 145.0,
            "weight_kg": 45.0,
            "enrollment_date": date.today()
        }
        
        service.create_student(**student_data)
        retrieved_student = service.get_student_by_student_id(1005)
        
        assert retrieved_student is not None
        assert retrieved_student.name == "钱七"

    def test_get_student_not_found(self, test_session):
        """
        Test retrieving a non-existent student.
        
        Expected: RecordNotFoundError should be raised.
        """
        service = StudentService(test_session)
        
        with pytest.raises(RecordNotFoundError):
            service.get_student_by_id(99999)

    def test_update_student(self, test_session):
        """
        Test updating a student's information.
        
        Expected: Student's information should be updated correctly.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 1006,
            "name": "孙八",
            "gender": "男",
            "grade": "六年级",
            "age": 12,
            "height_cm": 150.0,
            "weight_kg": 50.0,
            "enrollment_date": date.today()
        }
        
        student = service.create_student(**student_data)
        
        update_data = {
            "height_cm": 152.5,
            "weight_kg": 52.0,
            "age": 13
        }
        
        updated_student = service.update_student(student.id, update_data)
        
        assert updated_student.height_cm == 152.5
        assert updated_student.weight_kg == 52.0
        assert updated_student.age == 13
        assert updated_student.name == "孙八"  # Unchanged field

    def test_delete_student(self, test_session):
        """
        Test deleting a student.
        
        Expected: Student should be deleted and not retrievable afterward.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 1007,
            "name": "周九",
            "gender": "女",
            "grade": "一年级",
            "age": 7,
            "height_cm": 120.0,
            "weight_kg": 25.0,
            "enrollment_date": date.today()
        }
        
        student = service.create_student(**student_data)
        service.delete_student(student.id)
        
        with pytest.raises(RecordNotFoundError):
            service.get_student_by_id(student.id)

    def test_get_students_by_grade(self, test_session):
        """
        Test retrieving students by grade.
        
        Expected: Only students from the specified grade should be returned.
        """
        service = StudentService(test_session)
        
        # Create students in different grades
        for i in range(5):
            service.create_student({
                "student_id": 2001 + i,
                "name": f"学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "一年级",
                "age": 7,
                "height_cm": 120.0 + i,
                "weight_kg": 25.0 + i,
                "enrollment_date": date.today()
            })
        
        for i in range(3):
            service.create_student({
                "student_id": 3001 + i,
                "name": f"其他学生{i}",
                "gender": "男",
                "grade": "二年级",
                "age": 8,
                "height_cm": 130.0 + i,
                "weight_kg": 30.0 + i,
                "enrollment_date": date.today()
            })
        
        grade1_students = service.get_students_by_grade("一年级")
        assert len(grade1_students) >= 5

    def test_get_all_students(self, test_session):
        """
        Test retrieving all students.
        
        Expected: All students in the database should be returned.
        """
        service = StudentService(test_session)
        
        # Create some students
        for i in range(3):
            service.create_student({
                "student_id": 4001 + i,
                "name": f"测试学生{i}",
                "gender": "女",
                "grade": "三年级",
                "age": 9,
                "height_cm": 135.0,
                "weight_kg": 35.0,
                "enrollment_date": date.today()
            })
        
        all_students = service.get_all_students()
        assert len(all_students) >= 3

    def test_student_bmi_calculation(self, test_session):
        """
        Test BMI calculation for a student.
        
        Expected: BMI should be calculated correctly based on height and weight.
        """
        service = StudentService(test_session)
        
        student_data = {
            "student_id": 5001,
            "name": "BMI测试",
            "gender": "男",
            "grade": "四年级",
            "age": 10,
            "height_cm": 150.0,  # 1.5 meters
            "weight_kg": 45.0,   # 45 kg
            "enrollment_date": date.today()
        }
        
        student = service.create_student(**student_data)
        
        # BMI = weight (kg) / (height (m))^2
        # BMI = 45 / (1.5)^2 = 45 / 2.25 = 20.0
        assert student.bmi == pytest.approx(20.0, 0.01)

    def test_student_bmi_category(self, test_session):
        """
        Test BMI category classification.
        
        Expected: Correct BMI category should be returned.
        """
        service = StudentService(test_session)
        
        # Underweight
        student1 = service.create_student({
            "student_id": 6001,
            "name": "偏瘦学生",
            "gender": "男",
            "grade": "五年级",
            "age": 11,
            "height_cm": 150.0,
            "weight_kg": 40.0,  # BMI ~17.8
            "enrollment_date": date.today()
        })
        
        # Normal weight
        student2 = service.create_student({
            "student_id": 6002,
            "name": "正常学生",
            "gender": "女",
            "grade": "五年级",
            "age": 11,
            "height_cm": 150.0,
            "weight_kg": 50.0,  # BMI ~22.2
            "enrollment_date": date.today()
        })
        
        assert student1.bmi_category() in ["偏瘦", "正常"]
        assert student2.bmi_category() in ["正常", "超重"]

    def test_bulk_create_students(self, test_session):
        """
        Test bulk creation of students.
        
        Expected: All students should be created successfully.
        """
        service = StudentService(test_session)
        
        students_data = [
            {
                "student_id": 7001 + i,
                "name": f"批量学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "六年级",
                "age": 12,
                "height_cm": 150.0 + i,
                "weight_kg": 45.0 + i,
                "enrollment_date": date.today()
            }
            for i in range(10)
        ]
        
        results = service.bulk_create_students(students_data)
        
        assert len(results["created"]) == 10
        assert results["errors"] == []
