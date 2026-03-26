"""
Student DAO (Data Access Object) class for student-related database operations.

This module extends the BaseDAO to provide student-specific database operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.dao.base_dao import BaseDAO
from app.models.student import Student
from app.utils.logger import get_logger
from app.utils.exceptions import QueryError

logger = get_logger(__name__)


class StudentDAO(BaseDAO[Student]):
    """
    Data Access Object class for Student model.

    Provides student-specific database operations in addition to
    the common CRUD operations from BaseDAO.
    """

    model = Student

    def get_by_student_id(self, student_id: int) -> Optional[Student]:
        """
        Get a student by their external student ID.

        Args:
            student_id: External student identifier.

        Returns:
            Optional[Student]: Student instance if found, None otherwise.
        """
        try:
            return self.session.query(Student).filter_by(student_id=student_id).first()
        except Exception as e:
            logger.error(f"Error getting student by student_id={student_id}: {e}")
            raise QueryError(
                message="Failed to get student by student ID",
                details={"error": str(e), "student_id": student_id}
            ) from e

    def get_by_grade(self, grade: str) -> List[Student]:
        """
        Get all students in a specific grade.

        Args:
            grade: Grade level (e.g., '一年级', '二年级').

        Returns:
            List[Student]: List of students in the grade.
        """
        try:
            return self.session.query(Student).filter_by(grade=grade).all()
        except Exception as e:
            logger.error(f"Error getting students by grade={grade}: {e}")
            raise QueryError(
                message="Failed to get students by grade",
                details={"error": str(e), "grade": grade}
            ) from e

    def get_by_gender(self, gender: str) -> List[Student]:
        """
        Get all students of a specific gender.

        Args:
            gender: Gender ('男' or '女').

        Returns:
            List[Student]: List of students of the specified gender.
        """
        try:
            return self.session.query(Student).filter_by(gender=gender).all()
        except Exception as e:
            logger.error(f"Error getting students by gender={gender}: {e}")
            raise QueryError(
                message="Failed to get students by gender",
                details={"error": str(e), "gender": gender}
            ) from e

    def get_by_grade_and_gender(self, grade: str, gender: str) -> List[Student]:
        """
        Get students filtered by both grade and gender.

        Args:
            grade: Grade level.
            gender: Gender.

        Returns:
            List[Student]: List of matching students.
        """
        try:
            return self.session.query(Student).filter_by(grade=grade, gender=gender).all()
        except Exception as e:
            logger.error(f"Error getting students by grade={grade}, gender={gender}: {e}")
            raise QueryError(
                message="Failed to get students by grade and gender",
                details={"error": str(e), "grade": grade, "gender": gender}
            ) from e

    def get_by_class_id(self, class_id: int) -> List[Student]:
        """
        Get all students in a specific class.

        Args:
            class_id: Class database ID.

        Returns:
            List[Student]: List of students in the class.
        """
        try:
            return self.session.query(Student).filter_by(class_id=class_id).all()
        except Exception as e:
            logger.error(f"Error getting students by class_id={class_id}: {e}")
            raise QueryError(
                message="Failed to get students by class ID",
                details={"error": str(e), "class_id": class_id}
            ) from e

    def get_by_age_range(self, min_age: int, max_age: int) -> List[Student]:
        """
        Get students within a specific age range.

        Args:
            min_age: Minimum age (inclusive).
            max_age: Maximum age (inclusive).

        Returns:
            List[Student]: List of students in the age range.
        """
        try:
            return self.session.query(Student).filter(
                and_(Student.age >= min_age, Student.age <= max_age)
            ).all()
        except Exception as e:
            logger.error(f"Error getting students by age range {min_age}-{max_age}: {e}")
            raise QueryError(
                message="Failed to get students by age range",
                details={"error": str(e), "min_age": min_age, "max_age": max_age}
            ) from e

    def get_by_height_range(self, min_height: float, max_height: float) -> List[Student]:
        """
        Get students within a specific height range.

        Args:
            min_height: Minimum height in centimeters (inclusive).
            max_height: Maximum height in centimeters (inclusive).

        Returns:
            List[Student]: List of students in the height range.
        """
        try:
            return self.session.query(Student).filter(
                and_(Student.height_cm >= min_height, Student.height_cm <= max_height)
            ).all()
        except Exception as e:
            logger.error(f"Error getting students by height range {min_height}-{max_height}: {e}")
            raise QueryError(
                message="Failed to get students by height range",
                details={"error": str(e), "min_height": min_height, "max_height": max_height}
            ) from e

    def get_by_bmi_range(self, min_bmi: float, max_bmi: float) -> List[Student]:
        """
        Get students within a specific BMI range.

        Args:
            min_bmi: Minimum BMI (inclusive).
            max_bmi: Maximum BMI (inclusive).

        Returns:
            List[Student]: List of students in the BMI range.
        """
        try:
            # BMI is calculated as weight(kg) / (height(m))^2
            return self.session.query(Student).filter(
                and_(
                    Student.weight_kg / ((Student.height_cm / 100) ** 2) >= min_bmi,
                    Student.weight_kg / ((Student.height_cm / 100) ** 2) <= max_bmi
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting students by BMI range {min_bmi}-{max_bmi}: {e}")
            raise QueryError(
                message="Failed to get students by BMI range",
                details={"error": str(e), "min_bmi": min_bmi, "max_bmi": max_bmi}
            ) from e

    def get_height_statistics_by_grade(self, grade: str) -> Dict[str, Any]:
        """
        Get height statistics for a specific grade.

        Args:
            grade: Grade level.

        Returns:
            Dict[str, Any]: Statistics including count, mean, std, min, max, median.
        """
        try:
            result = self.session.query(
                func.count(Student.id).label('count'),
                func.avg(Student.height_cm).label('mean'),
                func.stddev(Student.height_cm).label('std'),
                func.min(Student.height_cm).label('min'),
                func.max(Student.height_cm).label('max')
            ).filter_by(grade=grade).first()

            return {
                'count': result.count,
                'mean': round(result.mean, 2) if result.mean else None,
                'std': round(result.std, 2) if result.std else None,
                'min': result.min,
                'max': result.max
            }
        except Exception as e:
            logger.error(f"Error getting height statistics for grade={grade}: {e}")
            raise QueryError(
                message="Failed to get height statistics by grade",
                details={"error": str(e), "grade": grade}
            ) from e

    def get_distinct_grades(self) -> List[str]:
        """
        Get a list of all distinct grades in the database.

        Returns:
            List[str]: List of distinct grades.
        """
        try:
            result = self.session.query(Student.grade).distinct().order_by(Student.grade).all()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting distinct grades: {e}")
            raise QueryError(
                message="Failed to get distinct grades",
                details={"error": str(e)}
            ) from e

    def search_students(self, search_term: str) -> List[Student]:
        """
        Search students by name or student_id.

        Args:
            search_term: Search term to match against name or student_id.

        Returns:
            List[Student]: List of matching students.
        """
        try:
            return self.session.query(Student).filter(
                (Student.name.like(f'%{search_term}%')) |
                (Student.student_id.cast(String).like(f'%{search_term}%'))
            ).all()
        except Exception as e:
            logger.error(f"Error searching students with term='{search_term}': {e}")
            raise QueryError(
                message="Failed to search students",
                details={"error": str(e), "search_term": search_term}
            ) from e

    def get_all_students_dataframe(self) -> Any:
        """
        Get all students as a pandas DataFrame.

        Returns:
            pandas.DataFrame: DataFrame containing all student data.
        """
        import pandas as pd
        try:
            students = self.get_all()
            data = [student.to_dict() for student in students]
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting students DataFrame: {e}")
            raise QueryError(
                message="Failed to get students DataFrame",
                details={"error": str(e)}
            ) from e
