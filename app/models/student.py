"""
Student model representing individual student records.

This module defines the Student model for storing student information
including personal details, grade, gender, height, and weight.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from typing import Dict, Any

from app.models.base import BaseModel


class Student(BaseModel):
    """
    Student model representing individual student records.

    Attributes:
        student_id: Unique student identifier (external ID)
        name: Student's full name
        gender: Student's gender ('男' or '女')
        grade: Student's grade (e.g., '一年级', '二年级')
        age: Student's age in years
        height_cm: Student's height in centimeters
        weight_kg: Student's weight in kilograms
        enrollment_date: Date of enrollment
        class_id: Foreign key to the class the student belongs to
        class_: Relationship to the Class model
        statistics: Relationship to the StatisticsRecord model
    """

    __tablename__ = "students"

    student_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False)  # '男' or '女'
    grade = Column(String(20), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    enrollment_date = Column(Date, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)

    # Relationships
    class_ = relationship("Class", back_populates="students")
    statistics = relationship("StatisticsRecord", back_populates="student")

    @property
    def bmi(self) -> float:
        """
        Calculate the student's BMI (Body Mass Index).

        Returns:
            float: BMI value rounded to 2 decimal places.
        """
        if self.height_cm > 0 and self.weight_kg > 0:
            return round(self.weight_kg / ((self.height_cm / 100) ** 2), 2)
        return 0.0

    def bmi_category(self) -> str:
        """
        Determine the BMI category for the student.

        Returns:
            str: BMI category ('偏瘦', '正常', '超重', '肥胖').
        """
        bmi = self.bmi
        if bmi < 15:
            return "偏瘦"
        elif bmi < 20:
            return "正常"
        elif bmi < 24:
            return "超重"
        else:
            return "肥胖"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the student instance to a dictionary.

        Returns:
            Dictionary representation of the student including calculated BMI.
        """
        data = super().to_dict()
        data["bmi"] = self.bmi
        data["bmi_category"] = self.bmi_category()
        return data

    def __repr__(self) -> str:
        """
        Return a string representation of the student.

        Returns:
            String representation with student ID, name, and grade.
        """
        return f"<Student(student_id={self.student_id}, name='{self.name}', grade='{self.grade}')>"
