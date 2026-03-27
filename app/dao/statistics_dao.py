"""
StatisticsRecord DAO (Data Access Object) class for statistics-related database operations.

This module extends the BaseDAO to provide statistics-specific database operations.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.dao.base_dao import BaseDAO
from app.models.statistics import StatisticsRecord
from app.utils.logger import get_logger
from app.utils.exceptions import QueryError

logger = get_logger(__name__)


class StatisticsRecordDAO(BaseDAO[StatisticsRecord]):
    """
    Data Access Object class for StatisticsRecord model.

    Provides statistics-specific database operations in addition to
    the common CRUD operations from BaseDAO.
    """

    model = StatisticsRecord

    def get_by_record_type(self, record_type: str) -> List[StatisticsRecord]:
        """
        Get statistics records by record type.

        Args:
            record_type: Type of statistics (e.g., 'grade_summary', 'gender_summary').

        Returns:
            List[StatisticsRecord]: List of matching statistics records.
        """
        try:
            return self.session.query(StatisticsRecord).filter_by(
                record_type=record_type
            ).order_by(desc(StatisticsRecord.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting statistics by record_type={record_type}: {e}")
            raise QueryError(
                message="Failed to get statistics by record type",
                details={"error": str(e), "record_type": record_type}
            ) from e

    def get_by_grade(self, grade: str) -> List[StatisticsRecord]:
        """
        Get statistics records by grade.

        Args:
            grade: Grade level.

        Returns:
            List[StatisticsRecord]: List of matching statistics records.
        """
        try:
            return self.session.query(StatisticsRecord).filter_by(
                grade=grade
            ).order_by(desc(StatisticsRecord.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting statistics by grade={grade}: {e}")
            raise QueryError(
                message="Failed to get statistics by grade",
                details={"error": str(e), "grade": grade}
            ) from e

    def get_by_gender(self, gender: str) -> List[StatisticsRecord]:
        """
        Get statistics records by gender.

        Args:
            gender: Gender ('男' or '女').

        Returns:
            List[StatisticsRecord]: List of matching statistics records.
        """
        try:
            return self.session.query(StatisticsRecord).filter_by(
                gender=gender
            ).order_by(desc(StatisticsRecord.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting statistics by gender={gender}: {e}")
            raise QueryError(
                message="Failed to get statistics by gender",
                details={"error": str(e), "gender": gender}
            ) from e

    def get_by_period(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[StatisticsRecord]:
        """
        Get statistics records within a specific period.

        Args:
            start_date: Start of the period.
            end_date: End of the period (defaults to today if None).

        Returns:
            List[StatisticsRecord]: List of statistics records in the period.
        """
        try:
            query = self.session.query(StatisticsRecord).filter(
                StatisticsRecord.period_start >= start_date
            )

            if end_date:
                query = query.filter(StatisticsRecord.period_end <= end_date)

            return query.order_by(desc(StatisticsRecord.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting statistics by period: {e}")
            raise QueryError(
                message="Failed to get statistics by period",
                details={"error": str(e), "start_date": start_date, "end_date": end_date}
            ) from e

    def get_latest_by_type(self, record_type: str, grade: Optional[str] = None) -> Optional[StatisticsRecord]:
        """
        Get the latest statistics record by type (and optionally grade).

        Args:
            record_type: Type of statistics.
            grade: Optional grade filter.

        Returns:
            Optional[StatisticsRecord]: Latest statistics record, None if not found.
        """
        try:
            query = self.session.query(StatisticsRecord).filter_by(
                record_type=record_type
            )

            if grade:
                query = query.filter_by(grade=grade)

            return query.order_by(desc(StatisticsRecord.created_at)).first()
        except Exception as e:
            logger.error(f"Error getting latest statistics by type={record_type}, grade={grade}: {e}")
            raise QueryError(
                message="Failed to get latest statistics by type",
                details={"error": str(e), "record_type": record_type, "grade": grade}
            ) from e

    def get_by_student_id(self, student_id: int) -> List[StatisticsRecord]:
        """
        Get statistics records for a specific student.

        Args:
            student_id: Student database ID.

        Returns:
            List[StatisticsRecord]: List of student's statistics records.
        """
        try:
            return self.session.query(StatisticsRecord).filter_by(
                student_id=student_id
            ).order_by(desc(StatisticsRecord.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting statistics by student_id={student_id}: {e}")
            raise QueryError(
                message="Failed to get statistics by student ID",
                details={"error": str(e), "student_id": student_id}
            ) from e

    def get_by_class_id(self, class_id: int) -> List[StatisticsRecord]:
        """
        Get statistics records for a specific class.

        Args:
            class_id: Class database ID.

        Returns:
            List[StatisticsRecord]: List of class's statistics records.
        """
        try:
            return self.session.query(StatisticsRecord).filter_by(
                class_id=class_id
            ).order_by(desc(StatisticsRecord.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting statistics by class_id={class_id}: {e}")
            raise QueryError(
                message="Failed to get statistics by class ID",
                details={"error": str(e), "class_id": class_id}
            ) from e

    def create_grade_summary(
        self,
        grade: str,
        period_start: date,
        period_end: date,
        statistics: Dict[str, Any]
    ) -> StatisticsRecord:
        """
        Create a grade summary statistics record.

        Args:
            grade: Grade level.
            period_start: Start date of the statistics period.
            period_end: End date of the statistics period.
            statistics: Dictionary containing statistics data.

        Returns:
            StatisticsRecord: Created statistics record.
        """
        try:
            record = StatisticsRecord(
                record_type='grade_summary',
                grade=grade,
                period_start=period_start,
                period_end=period_end,
                total_students=statistics.get('total_students', 0),
                average_height=statistics.get('average_height'),
                height_standard_deviation=statistics.get('height_standard_deviation'),
                min_height=statistics.get('min_height'),
                max_height=statistics.get('max_height'),
                median_height=statistics.get('median_height'),
                average_weight=statistics.get('average_weight'),
                weight_standard_deviation=statistics.get('weight_standard_deviation'),
                average_bmi=statistics.get('average_bmi')
            )

            if 'bmi_distribution' in statistics:
                record.set_bmi_distribution(statistics['bmi_distribution'])
            if 'height_percentiles' in statistics:
                record.set_height_percentiles(statistics['height_percentiles'])
            if 'comparison_to_standard' in statistics:
                record.set_comparison_to_standard(statistics['comparison_to_standard'])
            if 'growth_data' in statistics:
                record.set_growth_data(statistics['growth_data'])

            self.session.add(record)
            self.session.flush()
            logger.debug(f"Created grade summary for {grade}")
            return record
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating grade summary for {grade}: {e}")
            raise QueryError(
                message="Failed to create grade summary",
                details={"error": str(e), "grade": grade}
            ) from e

    def create_gender_summary(
        self,
        gender: str,
        period_start: date,
        period_end: date,
        statistics: Dict[str, Any]
    ) -> StatisticsRecord:
        """
        Create a gender summary statistics record.

        Args:
            gender: Gender ('男' or '女').
            period_start: Start date of the statistics period.
            period_end: End date of the statistics period.
            statistics: Dictionary containing statistics data.

        Returns:
            StatisticsRecord: Created statistics record.
        """
        try:
            record = StatisticsRecord(
                record_type='gender_summary',
                gender=gender,
                period_start=period_start,
                period_end=period_end,
                total_students=statistics.get('total_students', 0),
                average_height=statistics.get('average_height'),
                height_standard_deviation=statistics.get('height_standard_deviation'),
                min_height=statistics.get('min_height'),
                max_height=statistics.get('max_height'),
                median_height=statistics.get('median_height'),
                average_weight=statistics.get('average_weight'),
                weight_standard_deviation=statistics.get('weight_standard_deviation'),
                average_bmi=statistics.get('average_bmi')
            )

            if 'bmi_distribution' in statistics:
                record.set_bmi_distribution(statistics['bmi_distribution'])
            if 'height_percentiles' in statistics:
                record.set_height_percentiles(statistics['height_percentiles'])

            self.session.add(record)
            self.session.flush()
            logger.debug(f"Created gender summary for {gender}")
            return record
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating gender summary for {gender}: {e}")
            raise QueryError(
                message="Failed to create gender summary",
                details={"error": str(e), "gender": gender}
            ) from e

    def get_summary_by_type_and_period(
        self,
        record_type: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get summary statistics by type within a specific period, formatted as dictionaries.

        Args:
            record_type: Type of statistics.
            start_date: Start of the period.
            end_date: End of the period.

        Returns:
            List[Dict[str, Any]]: List of statistics records as dictionaries.
        """
        records = self.get_by_period(start_date, end_date)
        return [record.to_dict() for record in records if record.record_type == record_type]

    def bulk_create_statistics(
        self,
        statistics_list: List[Dict[str, Any]]
    ) -> List[StatisticsRecord]:
        """
        Bulk create multiple statistics records.

        Args:
            statistics_list: List of dictionaries containing statistics data.

        Returns:
            List[StatisticsRecord]: List of created statistics records.
        """
        records = []
        for data in statistics_list:
            record = StatisticsRecord(**data)

            # Handle JSON fields
            if 'bmi_distribution' in data and isinstance(data['bmi_distribution'], dict):
                record.set_bmi_distribution(data['bmi_distribution'])
            if 'height_percentiles' in data and isinstance(data['height_percentiles'], dict):
                record.set_height_percentiles(data['height_percentiles'])
            if 'comparison_to_standard' in data and isinstance(data['comparison_to_standard'], dict):
                record.set_comparison_to_standard(data['comparison_to_standard'])
            if 'growth_data' in data and isinstance(data['growth_data'], dict):
                record.set_growth_data(data['growth_data'])

            records.append(record)

        try:
            self.session.bulk_save_objects(records, return_defaults=True)
            self.session.flush()
            logger.debug(f"Bulk created {len(records)} statistics records")
            return records
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error bulk creating statistics: {e}")
            raise QueryError(
                message="Failed to bulk create statistics",
                details={"error": str(e), "count": len(statistics_list)}
            ) from e
