"""
StatisticsRecord model for storing analysis results.

This module defines the StatisticsRecord model for storing
statistical analysis results for different time periods and groups.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional
from datetime import date
import json

from app.models.base import BaseModel


class StatisticsRecord(BaseModel):
    """
    StatisticsRecord model for storing analysis results.

    This model stores pre-computed statistical data for different
    time periods, grades, and demographic groups to enable
    quick retrieval and reporting.

    Attributes:
        record_type: Type of statistics (e.g., 'grade_summary', 'gender_summary', 'bmi_analysis')
        period_start: Start date of the statistics period
        period_end: End date of the statistics period
        grade: Grade level (if applicable)
        gender: Gender (if applicable)
        total_students: Total number of students in the group
        average_height: Average height in centimeters
        height_standard_deviation: Standard deviation of heights
        min_height: Minimum height in centimeters
        max_height: Maximum height in centimeters
        median_height: Median height in centimeters
        average_weight: Average weight in kilograms
        weight_standard_deviation: Standard deviation of weights
        average_bmi: Average BMI
        bmi_distribution: JSON string containing BMI category distribution
        height_percentiles: JSON string containing height percentiles
        comparison_to_standard: JSON string containing comparison to standard heights
        growth_data: JSON string containing growth trend data
        student_id: Foreign key to Student model (if record is for a single student)
        class_id: Foreign key to Class model (if record is for a class)
        student: Relationship to Student model
        class_: Relationship to Class model
        notes: Additional notes or comments about the statistics
    """

    __tablename__ = "statistics_records"

    record_type = Column(String(50), nullable=False, index=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    grade = Column(String(20), nullable=True, index=True)
    gender = Column(String(10), nullable=True, index=True)

    # Core statistics
    total_students = Column(Integer, default=0)
    average_height = Column(Float, nullable=True)
    height_standard_deviation = Column(Float, nullable=True)
    min_height = Column(Float, nullable=True)
    max_height = Column(Float, nullable=True)
    median_height = Column(Float, nullable=True)
    average_weight = Column(Float, nullable=True)
    weight_standard_deviation = Column(Float, nullable=True)
    average_bmi = Column(Float, nullable=True)

    # JSON fields for complex data
    bmi_distribution = Column(Text, nullable=True)  # JSON string
    height_percentiles = Column(Text, nullable=True)  # JSON string
    comparison_to_standard = Column(Text, nullable=True)  # JSON string
    growth_data = Column(Text, nullable=True)  # JSON string

    # Foreign keys
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="statistics")
    class_ = relationship("Class", back_populates="statistics")

    # Additional fields
    notes = Column(Text, nullable=True)

    @staticmethod
    def _to_json(data: Any) -> str:
        """
        Convert data to a JSON string.

        Args:
            data: Data to convert to JSON.

        Returns:
            str: JSON string representation of the data.
        """
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _from_json(json_str: Optional[str]) -> Any:
        """
        Parse a JSON string back to data.

        Args:
            json_str: JSON string to parse.

        Returns:
            Any: Parsed data or None if input is None.
        """
        if json_str is None:
            return None
        return json.loads(json_str)

    def set_bmi_distribution(self, distribution: Dict[str, int]) -> None:
        """
        Set the BMI distribution data.

        Args:
            distribution: Dictionary mapping BMI categories to counts.
        """
        self.bmi_distribution = self._to_json(distribution)

    def get_bmi_distribution(self) -> Optional[Dict[str, int]]:
        """
        Get the BMI distribution data.

        Returns:
            Optional[Dict[str, int]]: BMI distribution dictionary or None.
        """
        return self._from_json(self.bmi_distribution)

    def set_height_percentiles(self, percentiles: Dict[str, float]) -> None:
        """
        Set the height percentiles data.

        Args:
            percentiles: Dictionary mapping percentile names to values.
        """
        self.height_percentiles = self._to_json(percentiles)

    def get_height_percentiles(self) -> Optional[Dict[str, float]]:
        """
        Get the height percentiles data.

        Returns:
            Optional[Dict[str, float]]: Height percentiles dictionary or None.
        """
        return self._from_json(self.height_percentiles)

    def set_comparison_to_standard(self, comparison: Dict[str, Any]) -> None:
        """
        Set the comparison to standard heights data.

        Args:
            comparison: Dictionary containing comparison data.
        """
        self.comparison_to_standard = self._to_json(comparison)

    def get_comparison_to_standard(self) -> Optional[Dict[str, Any]]:
        """
        Get the comparison to standard heights data.

        Returns:
            Optional[Dict[str, Any]]: Comparison dictionary or None.
        """
        return self._from_json(self.comparison_to_standard)

    def set_growth_data(self, growth: Dict[str, Any]) -> None:
        """
        Set the growth trend data.

        Args:
            growth: Dictionary containing growth trend data.
        """
        self.growth_data = self._to_json(growth)

    def get_growth_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the growth trend data.

        Returns:
            Optional[Dict[str, Any]]: Growth trend dictionary or None.
        """
        return self._from_json(self.growth_data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the statistics record to a dictionary.

        Returns:
            Dictionary representation of the statistics record.
        """
        return {
            "id": self.id,
            "record_type": self.record_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "grade": self.grade,
            "gender": self.gender,
            "total_students": self.total_students,
            "average_height": self.average_height,
            "height_standard_deviation": self.height_standard_deviation,
            "min_height": self.min_height,
            "max_height": self.max_height,
            "median_height": self.median_height,
            "average_weight": self.average_weight,
            "weight_standard_deviation": self.weight_standard_deviation,
            "average_bmi": self.average_bmi,
            "bmi_distribution": self.get_bmi_distribution(),
            "height_percentiles": self.get_height_percentiles(),
            "comparison_to_standard": self.get_comparison_to_standard(),
            "growth_data": self.get_growth_data(),
            "student_id": self.student_id,
            "class_id": self.class_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the statistics record.

        Returns:
            String representation with record ID, type, and grade.
        """
        return (
            f"<StatisticsRecord(id={self.id}, record_type='{self.record_type}', "
            f"grade='{self.grade}', period_start='{self.period_start}')>"
        )
