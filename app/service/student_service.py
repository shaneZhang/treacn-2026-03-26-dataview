"""
Student service class for student-related business logic.

This module provides student-related business operations including
CRUD operations, data validation, and statistics calculation.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date
import pandas as pd
import numpy as np

from app.service.base_service import BaseService
from app.models.student import Student
from app.utils.observer import EventType
from app.utils.logger import get_logger
from app.utils.exceptions import (
    ValidationError,
    MissingFieldError,
    RecordNotFoundError,
    InvalidDataError
)

logger = get_logger(__name__)


class StudentService(BaseService):
    """
    Service class for student-related business operations.

    This class provides methods for managing student data, including
    CRUD operations, validation, and statistics calculation.
    """

    # Chinese grade to numeric mapping
    GRADE_ORDER = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
    GRADE_TO_NUM = {grade: i + 1 for i, grade in enumerate(GRADE_ORDER)}

    # Standard heights based on Chinese children growth standards (2023)
    STANDARD_HEIGHTS = {
        '一年级': {'男': 120.0, '女': 119.0},
        '二年级': {'男': 125.0, '女': 124.0},
        '三年级': {'男': 130.0, '女': 129.0},
        '四年级': {'男': 135.0, '女': 134.0},
        '五年级': {'男': 140.0, '女': 140.0},
        '六年级': {'男': 147.0, '女': 148.0},
    }

    def validate_student_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate student data before creating or updating.

        Args:
            data: Dictionary containing student data.

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of error messages)
        """
        errors = []
        required_fields = ['student_id', 'name', 'gender', 'grade', 'age', 'height_cm', 'weight_kg']

        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate gender
        if data['gender'] not in ['男', '女']:
            errors.append(f"Invalid gender: {data['gender']}. Must be '男' or '女'.")

        # Validate grade
        if data['grade'] not in self.GRADE_ORDER:
            errors.append(f"Invalid grade: {data['grade']}. Must be one of: {', '.join(self.GRADE_ORDER)}")

        # Validate age (6-13 for primary school)
        if not (6 <= data['age'] <= 13):
            errors.append(f"Invalid age: {data['age']}. Must be between 6 and 13.")

        # Validate height (reasonable range for primary school students: 100-180 cm)
        if not (100 <= data['height_cm'] <= 180):
            errors.append(f"Invalid height: {data['height_cm']} cm. Must be between 100 and 180 cm.")

        # Validate weight (reasonable range for primary school students: 20-100 kg)
        if not (20 <= data['weight_kg'] <= 100):
            errors.append(f"Invalid weight: {data['weight_kg']} kg. Must be between 20 and 100 kg.")

        # Validate student_id (should be positive integer)
        if not isinstance(data['student_id'], int) or data['student_id'] <= 0:
            errors.append(f"Invalid student_id: {data['student_id']}. Must be a positive integer.")

        return len(errors) == 0, errors

    def create_student(self, data: Dict[str, Any] = None, **kwargs) -> Student:
        """
        Create a new student with validation.

        Args:
            data: Dictionary containing student data (alternative to kwargs).
            **kwargs: Student data fields (used if data is None).

        Returns:
            Student: Created student instance.

        Raises:
            ValidationError: If the student data is invalid or student_id already exists.
        """
        if data is not None:
            student_data = data
        else:
            student_data = kwargs

        is_valid, errors = self.validate_student_data(student_data)
        if not is_valid:
            error_msg = "; ".join(errors)
            logger.warning(f"Student validation failed: {error_msg}")
            raise ValidationError(
                message="Invalid student data",
                details={"errors": errors}
            )

        # Check for duplicate student_id before attempting creation
        student_id = student_data.get('student_id')
        if student_id is not None:
            existing = self.dao.student.get_by_student_id(student_id)
            if existing is not None:
                error_msg = f"Student with student_id {student_id} already exists"
                logger.warning(error_msg)
                raise ValidationError(
                    message=error_msg,
                    details={"student_id": student_id}
                )

        with self.transaction():
            student = self.dao.student.create(**student_data)

            self.emit_event(
                EventType.STUDENT_CREATED,
                data={"student_id": student.student_id, "id": student.id},
                source="StudentService.create_student"
            )

            logger.info(f"Created student: {student.name} (ID: {student.student_id})")
            return student

    def get_student(self, student_id: int) -> Optional[Student]:
        """
        Get a student by their database ID.

        Args:
            student_id: Database ID of the student.

        Returns:
            Optional[Student]: Student instance if found, None otherwise.
        """
        return self.dao.student.get_by_id(student_id)

    def get_student_by_id(self, student_id: int) -> Student:
        """
        Get a student by their database ID, raising an exception if not found.

        Args:
            student_id: Database ID of the student.

        Returns:
            Student: Student instance if found.

        Raises:
            RecordNotFoundError: If the student is not found.
        """
        student = self.dao.student.get_by_id(student_id)
        if not student:
            raise RecordNotFoundError(
                message=f"Student with ID {student_id} not found"
            )
        return student

    def get_student_by_student_id(self, student_id: int) -> Optional[Student]:
        """
        Get a student by their external student ID.

        Args:
            student_id: External student identifier.

        Returns:
            Optional[Student]: Student instance if found, None otherwise.
        """
        return self.dao.student.get_by_student_id(student_id)

    def update_student(self, student_id: int, data: Dict[str, Any] = None, **kwargs) -> Student:
        """
        Update a student's information.

        Args:
            student_id: Database ID of the student.
            data: Dictionary of fields to update (alternative to **kwargs).
            **kwargs: Fields to update (used if data is None).

        Returns:
            Student: Updated student instance.

        Raises:
            RecordNotFoundError: If the student is not found.
            ValidationError: If the update data is invalid.
        """
        if data is not None:
            update_data = data
        else:
            update_data = kwargs

        student = self.dao.student.get_by_id(student_id)
        if not student:
            raise RecordNotFoundError(
                message=f"Student with ID {student_id} not found"
            )

        # Validate only the fields being updated
        if update_data:
            current_data = student.to_dict()
            current_data.update(update_data)
            is_valid, errors = self.validate_student_data(current_data)
            if not is_valid:
                error_msg = "; ".join(errors)
                logger.warning(f"Student update validation failed: {error_msg}")
                raise ValidationError(
                    message="Invalid student update data",
                    details={"errors": errors}
                )

        with self.transaction():
            updated_student = self.dao.student.update(student_id, **update_data)

            self.emit_event(
                EventType.STUDENT_UPDATED,
                data={"student_id": updated_student.student_id, "id": updated_student.id},
                source="StudentService.update_student"
            )

            logger.info(f"Updated student: {updated_student.name} (ID: {updated_student.student_id})")
            return updated_student

    def delete_student(self, student_id: int) -> bool:
        """
        Delete a student.

        Args:
            student_id: Database ID of the student.

        Returns:
            bool: True if deleted successfully.

        Raises:
            RecordNotFoundError: If the student is not found.
        """
        student = self.dao.student.get_by_id(student_id)
        if not student:
            raise RecordNotFoundError(
                message=f"Student with ID {student_id} not found"
            )

        with self.transaction():
            result = self.dao.student.delete(student_id)

            self.emit_event(
                EventType.STUDENT_DELETED,
                data={"student_id": student.student_id, "id": student_id},
                source="StudentService.delete_student"
            )

            logger.info(f"Deleted student: {student.name} (ID: {student.student_id})")
            return result

    def get_students_by_grade(self, grade: str) -> List[Student]:
        """
        Get all students in a specific grade.

        Args:
            grade: Grade level.

        Returns:
            List[Student]: List of students in the grade.
        """
        return self.dao.student.get_by_grade(grade)

    def get_students_by_gender(self, gender: str) -> List[Student]:
        """
        Get all students of a specific gender.

        Args:
            gender: Gender ('男' or '女').

        Returns:
            List[Student]: List of students of the specified gender.
        """
        return self.dao.student.get_by_gender(gender)

    def get_all_students(self) -> List[Student]:
        """
        Get all students from the database.

        Returns:
            List[Student]: List of all student instances.
        """
        return self.dao.student.get_all()

    def get_students_dataframe(self) -> pd.DataFrame:
        """
        Get all students as a pandas DataFrame.

        Returns:
            pandas.DataFrame: DataFrame containing all student data.
        """
        students = self.dao.student.get_all()
        data = []
        for student in students:
            student_dict = student.to_dict()
            # Convert datetime objects to strings
            if 'enrollment_date' in student_dict and student_dict['enrollment_date']:
                student_dict['enrollment_date'] = str(student_dict['enrollment_date'])
            data.append(student_dict)
        return pd.DataFrame(data)

    def calculate_basic_statistics(self) -> Dict[str, Any]:
        """
        Calculate basic statistics for all students.

        Returns:
            Dict[str, Any]: Dictionary containing basic statistics.
        """
        df = self.get_students_dataframe()
        if df.empty:
            return {
                'total_students': 0,
                'male_count': 0,
                'female_count': 0,
                'average_height': None,
                'height_std': None,
                'min_height': None,
                'max_height': None,
                'median_height': None
            }

        return {
            'total_students': len(df),
            'male_count': len(df[df['gender'] == '男']),
            'female_count': len(df[df['gender'] == '女']),
            'average_height': round(df['height_cm'].mean(), 2),
            'height_std': round(df['height_cm'].std(), 2),
            'min_height': df['height_cm'].min(),
            'max_height': df['height_cm'].max(),
            'median_height': round(df['height_cm'].median(), 2)
        }

    def calculate_grade_statistics(self, grade: str) -> Dict[str, Any]:
        """
        Calculate statistics for a specific grade.

        Args:
            grade: Grade level.

        Returns:
            Dict[str, Any]: Dictionary containing grade statistics.
        """
        students = self.dao.student.get_by_grade(grade)
        if not students:
            return {
                'grade': grade,
                'student_count': 0,
                'average_height': None,
                'height_std': None,
                'average_weight': None,
                'weight_std': None
            }

        heights = [s.height_cm for s in students]
        weights = [s.weight_kg for s in students]

        return {
            'grade': grade,
            'student_count': len(students),
            'average_height': round(sum(heights) / len(heights), 2),
            'height_std': round(float(np.std(heights)), 2),
            'average_weight': round(sum(weights) / len(weights), 2),
            'weight_std': round(float(np.std(weights)), 2)
        }

    def calculate_gender_statistics(self, grade: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate statistics grouped by gender.

        Args:
            grade: Optional grade filter.

        Returns:
            Dict[str, Any]: Dictionary containing gender statistics.
        """
        if grade:
            male_students = self.dao.student.get_by_grade_and_gender(grade, '男')
            female_students = self.dao.student.get_by_grade_and_gender(grade, '女')
        else:
            male_students = self.dao.student.get_by_gender('男')
            female_students = self.dao.student.get_by_gender('女')

        def calc_stats(students):
            if not students:
                return {'count': 0, 'avg_height': None, 'avg_weight': None}
            heights = [s.height_cm for s in students]
            weights = [s.weight_kg for s in students]
            return {
                'count': len(students),
                'avg_height': round(sum(heights) / len(heights), 2),
                'avg_weight': round(sum(weights) / len(weights), 2)
            }

        return {
            'grade': grade,
            'male': calc_stats(male_students),
            'female': calc_stats(female_students)
        }

    def calculate_height_distribution(self) -> Dict[str, int]:
        """
        Calculate the distribution of students by height ranges.

        Returns:
            Dict[str, int]: Dictionary mapping height ranges to student counts.
        """
        bins = [0, 110, 120, 130, 140, 150, 160, 200]
        labels = ['<110cm', '110-120cm', '120-130cm', '130-140cm', '140-150cm', '150-160cm', '>160cm']

        df = self.get_students_dataframe()
        if df.empty:
            return {label: 0 for label in labels}

        df['height_range'] = pd.cut(
            df['height_cm'],
            bins=bins,
            labels=labels,
            right=False
        )
        distribution = df['height_range'].value_counts().sort_index().to_dict()

        # Ensure all labels are present in the result
        for label in labels:
            if label not in distribution:
                distribution[label] = 0

        return distribution

    def calculate_bmi_distribution(self) -> Dict[str, Any]:
        """
        Calculate BMI distribution for all students.

        Returns:
            Dict[str, Any]: Dictionary containing BMI distribution.
        """
        students = self.dao.student.get_all()
        if not students:
            return {
                'underweight': 0,
                'normal': 0,
                'overweight': 0,
                'obese': 0,
                'by_grade': {}
            }

        bmi_categories = {'偏瘦': 0, '正常': 0, '超重': 0, '肥胖': 0}
        grade_bmi = {}

        for student in students:
            category = student.bmi_category()
            bmi_categories[category] += 1

            if student.grade not in grade_bmi:
                grade_bmi[student.grade] = {'偏瘦': 0, '正常': 0, '超重': 0, '肥胖': 0}
            grade_bmi[student.grade][category] += 1

        return {
            'categories': bmi_categories,
            'by_grade': grade_bmi
        }

    def compare_with_standard(self, grade: str) -> Dict[str, Any]:
        """
        Compare grade height statistics with standard heights.

        Args:
            grade: Grade level.

        Returns:
            Dict[str, Any]: Comparison results.
        """
        male_students = self.dao.student.get_by_grade_and_gender(grade, '男')
        female_students = self.dao.student.get_by_grade_and_gender(grade, '女')

        standard = self.STANDARD_HEIGHTS.get(grade, {'男': 0, '女': 0})

        def compare(students, gender):
            if not students:
                return {
                    'gender': gender,
                    'actual': None,
                    'standard': standard[gender],
                    'difference': None,
                    'percent_diff': None
                }
            avg_height = sum(s.height_cm for s in students) / len(students)
            diff = avg_height - standard[gender]
            percent_diff = (diff / standard[gender]) * 100 if standard[gender] > 0 else 0
            return {
                'gender': gender,
                'actual': round(avg_height, 2),
                'standard': standard[gender],
                'difference': round(diff, 2),
                'percent_diff': round(percent_diff, 2)
            }

        return {
            'grade': grade,
            'male': compare(male_students, '男'),
            'female': compare(female_students, '女')
        }

    def bulk_import_students(self, students_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk import students from a list of dictionaries.

        Args:
            students_data: List of student data dictionaries.

        Returns:
            Dict[str, Any]: Import results including success and error counts.
        """
        successful = []
        failed = []

        for i, data in enumerate(students_data):
            try:
                is_valid, errors = self.validate_student_data(data)
                if not is_valid:
                    failed.append({
                        'index': i,
                        'data': data,
                        'errors': errors
                    })
                    continue

                successful.append(data)
            except Exception as e:
                failed.append({
                    'index': i,
                    'data': data,
                    'errors': [str(e)]
                })

        if successful:
            with self.transaction():
                self.dao.student.bulk_create(successful)

                self.emit_event(
                    EventType.STUDENT_BULK_IMPORTED,
                    data={'count': len(successful)},
                    source="StudentService.bulk_import_students"
                )

        result = {
            'total': len(students_data),
            'successful': len(successful),
            'created': successful,  # List of created students for backward compatibility
            'failed': len(failed),
            'errors': failed
        }

        logger.info(
            f"Bulk import completed: {len(successful)} successful, {len(failed)} failed"
        )

        return result

    def bulk_create_students(self, students_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk create multiple students (alias for bulk_import_students).

        Args:
            students_data: List of student data dictionaries.

        Returns:
            Dict[str, Any]: Result containing created students and any errors.
        """
        return self.bulk_import_students(students_data)

    def get_students_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        grade: Optional[str] = None,
        gender: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of students with optional filters.

        Args:
            page: Page number (1-based).
            per_page: Number of items per page.
            grade: Optional grade filter.
            gender: Optional gender filter.
            search: Optional search term for name or student_id.

        Returns:
            Dict[str, Any]: Paginated results.
        """
        filter_criteria = {}
        if grade:
            filter_criteria['grade'] = grade
        if gender:
            filter_criteria['gender'] = gender

        # TODO: Implement search functionality in DAO
        result = self.dao.student.paginate(
            page=page,
            per_page=per_page,
            filter_criteria=filter_criteria,
            order_by='student_id'
        )

        # Convert items to dictionaries
        result['items'] = [student.to_dict() for student in result['items']]
        return result
