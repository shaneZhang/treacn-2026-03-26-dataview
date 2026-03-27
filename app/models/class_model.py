"""
Class model representing school classes.

This module defines the Class model for storing class information
including grade, class number, teacher information, and student enrollment.
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from typing import List, Dict, Any

from app.models.base import BaseModel


class Class(BaseModel):
    """
    Class model representing school classes.

    Attributes:
        grade: Grade level (e.g., '一年级', '二年级')
        class_number: Class number within the grade (e.g., 1, 2, 3)
        name: Optional class name (e.g., '一班', '二班')
        teacher_name: Name of the class teacher
        teacher_email: Email of the class teacher
        classroom: Classroom location/number
        max_students: Maximum number of students allowed in the class
        students: Relationship to Student model
        statistics: Relationship to StatisticsRecord model
    """

    __tablename__ = "classes"

    grade = Column(String(20), nullable=False, index=True)
    class_number = Column(Integer, nullable=False)
    name = Column(String(50), nullable=True)
    teacher_name = Column(String(100), nullable=True)
    teacher_email = Column(String(100), nullable=True)
    classroom = Column(String(50), nullable=True)
    max_students = Column(Integer, default=50)

    # Relationships
    students = relationship("Student", back_populates="class_")
    statistics = relationship("StatisticsRecord", back_populates="class_")

    # Unique constraint for grade and class_number combination
    __table_args__ = (
        UniqueConstraint("grade", "class_number", name="_grade_class_number_uc"),
    )

    @property
    def student_count(self) -> int:
        """
        Get the number of students in the class.

        Returns:
            int: Number of students in the class.
        """
        return len(self.students)

    @property
    def average_height(self) -> float:
        """
        Calculate the average height of students in the class.

        Returns:
            float: Average height in centimeters, rounded to 2 decimal places.
        """
        if not self.students:
            return 0.0
        heights = [student.height_cm for student in self.students if student.height_cm > 0]
        if not heights:
            return 0.0
        return round(sum(heights) / len(heights), 2)

    @property
    def average_weight(self) -> float:
        """
        Calculate the average weight of students in the class.

        Returns:
            float: Average weight in kilograms, rounded to 2 decimal places.
        """
        if not self.students:
            return 0.0
        weights = [student.weight_kg for student in self.students if student.weight_kg > 0]
        if not weights:
            return 0.0
        return round(sum(weights) / len(weights), 2)

    @property
    def average_bmi(self) -> float:
        """
        Calculate the average BMI of students in the class.

        Returns:
            float: Average BMI, rounded to 2 decimal places.
        """
        if not self.students:
            return 0.0
        bmis = [student.bmi for student in self.students if student.bmi > 0]
        if not bmis:
            return 0.0
        return round(sum(bmis) / len(bmis), 2)

    @property
    def full_name(self) -> str:
        """
        Get the full name of the class (grade + name or grade + class number).

        Returns:
            str: Full class name (e.g., '一年级一班').
        """
        if self.name:
            return f"{self.grade}{self.name}"
        return f"{self.grade}{self.class_number}班"

    def get_students_by_gender(self, gender: str) -> List["Student"]:
        """
        Get students in the class filtered by gender.

        Args:
            gender: Gender to filter by ('男' or '女').

        Returns:
            List[Student]: List of students matching the gender.
        """
        return [student for student in self.students if student.gender == gender]

    def to_dict(self, include_students: bool = False) -> Dict[str, Any]:
        """
        Convert the class instance to a dictionary.

        Args:
            include_students: Whether to include student data in the output.

        Returns:
            Dictionary representation of the class.
        """
        data = {
            "id": self.id,
            "grade": self.grade,
            "class_number": self.class_number,
            "name": self.name,
            "full_name": self.full_name,
            "teacher_name": self.teacher_name,
            "teacher_email": self.teacher_email,
            "classroom": self.classroom,
            "max_students": self.max_students,
            "student_count": self.student_count,
            "average_height": self.average_height,
            "average_weight": self.average_weight,
            "average_bmi": self.average_bmi,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_students:
            data["students"] = [student.to_dict() for student in self.students]

        return data

    def __repr__(self) -> str:
        """
        Return a string representation of the class.

        Returns:
            String representation with class ID, grade, and class number.
        """
        return f"<Class(id={self.id}, grade='{self.grade}', class_number={self.class_number})>"
