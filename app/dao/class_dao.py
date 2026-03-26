"""
Class DAO (Data Access Object) class for class-related database operations.

This module extends the BaseDAO to provide class-specific database operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.dao.base_dao import BaseDAO
from app.models.class_model import Class
from app.utils.logger import get_logger
from app.utils.exceptions import QueryError

logger = get_logger(__name__)


class ClassDAO(BaseDAO[Class]):
    """
    Data Access Object class for Class model.

    Provides class-specific database operations in addition to
    the common CRUD operations from BaseDAO.
    """

    model = Class

    def get_by_grade_and_number(self, grade: str, class_number: int) -> Optional[Class]:
        """
        Get a class by grade and class number.

        Args:
            grade: Grade level (e.g., '一年级', '二年级').
            class_number: Class number within the grade.

        Returns:
            Optional[Class]: Class instance if found, None otherwise.
        """
        try:
            return self.session.query(Class).filter_by(
                grade=grade,
                class_number=class_number
            ).first()
        except Exception as e:
            logger.error(f"Error getting class by grade={grade}, number={class_number}: {e}")
            raise QueryError(
                message="Failed to get class by grade and number",
                details={"error": str(e), "grade": grade, "class_number": class_number}
            ) from e

    def get_by_grade(self, grade: str) -> List[Class]:
        """
        Get all classes in a specific grade.

        Args:
            grade: Grade level.

        Returns:
            List[Class]: List of classes in the grade.
        """
        try:
            return self.session.query(Class).filter_by(grade=grade).order_by(Class.class_number).all()
        except Exception as e:
            logger.error(f"Error getting classes by grade={grade}: {e}")
            raise QueryError(
                message="Failed to get classes by grade",
                details={"error": str(e), "grade": grade}
            ) from e

    def get_with_students(self, class_id: int) -> Optional[Class]:
        """
        Get a class with its associated students (eager loading).

        Args:
            class_id: Class database ID.

        Returns:
            Optional[Class]: Class instance with students loaded, None if not found.
        """
        try:
            return self.session.query(Class).options(
                joinedload(Class.students)
            ).filter_by(id=class_id).first()
        except Exception as e:
            logger.error(f"Error getting class with students id={class_id}: {e}")
            raise QueryError(
                message="Failed to get class with students",
                details={"error": str(e), "class_id": class_id}
            ) from e

    def get_all_with_student_counts(self) -> List[Dict[str, Any]]:
        """
        Get all classes with student count information.

        Returns:
            List[Dict[str, Any]]: List of class dictionaries with student counts.
        """
        try:
            classes = self.session.query(Class).order_by(Class.grade, Class.class_number).all()
            return [cls.to_dict() for cls in classes]
        except Exception as e:
            logger.error(f"Error getting classes with student counts: {e}")
            raise QueryError(
                message="Failed to get classes with student counts",
                details={"error": str(e)}
            ) from e

    def get_class_statistics(self, class_id: int) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific class.

        Args:
            class_id: Class database ID.

        Returns:
            Dict[str, Any]: Class statistics including student count, averages, etc.
        """
        cls = self.get_by_id_or_raise(class_id)
        return cls.to_dict(include_students=False)

    def get_grade_summary(self, grade: str) -> Dict[str, Any]:
        """
        Get a summary of all classes in a grade.

        Args:
            grade: Grade level.

        Returns:
            Dict[str, Any]: Grade summary including total students, average height, etc.
        """
        try:
            classes = self.get_by_grade(grade)
            total_students = sum(cls.student_count for cls in classes)
            avg_heights = [cls.average_height for cls in classes if cls.average_height > 0]
            avg_weights = [cls.average_weight for cls in classes if cls.average_weight > 0]

            return {
                'grade': grade,
                'class_count': len(classes),
                'total_students': total_students,
                'average_height': round(sum(avg_heights) / len(avg_heights), 2) if avg_heights else None,
                'average_weight': round(sum(avg_weights) / len(avg_weights), 2) if avg_weights else None,
                'classes': [cls.to_dict() for cls in classes]
            }
        except Exception as e:
            logger.error(f"Error getting grade summary for grade={grade}: {e}")
            raise QueryError(
                message="Failed to get grade summary",
                details={"error": str(e), "grade": grade}
            ) from e

    def get_classes_by_teacher(self, teacher_name: str) -> List[Class]:
        """
        Get all classes taught by a specific teacher.

        Args:
            teacher_name: Name of the teacher.

        Returns:
            List[Class]: List of classes taught by the teacher.
        """
        try:
            return self.session.query(Class).filter(
                Class.teacher_name.like(f'%{teacher_name}%')
            ).all()
        except Exception as e:
            logger.error(f"Error getting classes by teacher='{teacher_name}': {e}")
            raise QueryError(
                message="Failed to get classes by teacher",
                details={"error": str(e), "teacher_name": teacher_name}
            ) from e

    def get_classes_by_classroom(self, classroom: str) -> List[Class]:
        """
        Get all classes in a specific classroom.

        Args:
            classroom: Classroom location/number.

        Returns:
            List[Class]: List of classes in the classroom.
        """
        try:
            return self.session.query(Class).filter_by(classroom=classroom).all()
        except Exception as e:
            logger.error(f"Error getting classes by classroom='{classroom}': {e}")
            raise QueryError(
                message="Failed to get classes by classroom",
                details={"error": str(e), "classroom": classroom}
            ) from e

    def get_distinct_grades(self) -> List[str]:
        """
        Get a list of all distinct grades that have classes.

        Returns:
            List[str]: List of distinct grades.
        """
        try:
            result = self.session.query(Class.grade).distinct().order_by(Class.grade).all()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting distinct grades from classes: {e}")
            raise QueryError(
                message="Failed to get distinct grades from classes",
                details={"error": str(e)}
            ) from e

    def get_available_class_number(self, grade: str) -> int:
        """
        Get the next available class number for a given grade.

        Args:
            grade: Grade level.

        Returns:
            int: Next available class number.
        """
        try:
            max_number = self.session.query(func.max(Class.class_number)).filter_by(grade=grade).scalar()
            return (max_number or 0) + 1
        except Exception as e:
            logger.error(f"Error getting available class number for grade={grade}: {e}")
            raise QueryError(
                message="Failed to get available class number",
                details={"error": str(e), "grade": grade}
            ) from e

    def add_student_to_class(self, class_id: int, student_id: int) -> bool:
        """
        Add a student to a class (update student's class_id).

        Args:
            class_id: Class database ID.
            student_id: Student database ID.

        Returns:
            bool: True if successful.

        Note:
            This operation actually updates the Student record, not the Class record.
            Consider using the StudentDAO for this operation.
        """
        from app.models.student import Student
        try:
            student = self.session.query(Student).filter_by(id=student_id).first()
            if student:
                student.class_id = class_id
                self.session.flush()
                logger.debug(f"Added student {student_id} to class {class_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding student {student_id} to class {class_id}: {e}")
            raise QueryError(
                message="Failed to add student to class",
                details={"error": str(e), "class_id": class_id, "student_id": student_id}
            ) from e

    def remove_student_from_class(self, class_id: int, student_id: int) -> bool:
        """
        Remove a student from a class (set student's class_id to None).

        Args:
            class_id: Class database ID.
            student_id: Student database ID.

        Returns:
            bool: True if successful.
        """
        from app.models.student import Student
        try:
            student = self.session.query(Student).filter_by(
                id=student_id,
                class_id=class_id
            ).first()
            if student:
                student.class_id = None
                self.session.flush()
                logger.debug(f"Removed student {student_id} from class {class_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing student {student_id} from class {class_id}: {e}")
            raise QueryError(
                message="Failed to remove student from class",
                details={"error": str(e), "class_id": class_id, "student_id": student_id}
            ) from e
