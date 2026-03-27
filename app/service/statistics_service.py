"""
Statistics service for generating and managing statistical records.

This module provides functionality for generating, storing, and retrieving
statistical analysis results for student height data.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import numpy as np

from app.service.base_service import BaseService
from app.service.student_service import StudentService
from app.models.statistics import StatisticsRecord
from app.utils.observer import EventType, Observer
from app.utils.logger import get_logger
from app.utils.exceptions import AnalysisError

logger = get_logger(__name__)


class StatisticsService(BaseService):
    """
    Service class for statistics generation and management.

    This class provides methods for generating statistical analyses,
    storing results in the database, and retrieving historical statistics.
    It also implements the Observer pattern to automatically update
    statistics when student data changes.
    """

    def __init__(self, session=None):
        """Initialize the statistics service."""
        super().__init__(session)
        self._student_service = StudentService(session)
        self._scheduled_updates = []

    def supports_event(self, event_type: EventType) -> bool:
        """
        Check if this service supports a specific event type.

        Args:
            event_type: The event type to check.

        Returns:
            bool: True if the event type is supported.
        """
        return event_type in [
            EventType.STUDENT_CREATED,
            EventType.STUDENT_UPDATED,
            EventType.STUDENT_DELETED,
            EventType.STUDENT_BULK_IMPORTED
        ]

    def on_event(self, event) -> None:
        """
        Handle events from the event manager.

        Args:
            event: The event to handle.
        """
        if self.supports_event(event.event_type):
            logger.info(f"Statistics service received event: {event.event_type.value}")
            self.schedule_update(event)

    def schedule_update(self, event) -> None:
        """
        Schedule a statistics update based on an event.

        Args:
            event: The event that triggered the update.
        """
        self._scheduled_updates.append({
            'event': event,
            'timestamp': datetime.now()
        })
        logger.debug(f"Scheduled statistics update for event: {event.event_type.value}")

    def process_scheduled_updates(self) -> Dict[str, Any]:
        """
        Process all scheduled statistics updates.

        Returns:
            Dict[str, Any]: Results of the update processing.
        """
        if not self._scheduled_updates:
            return {'updates_processed': 0, 'message': 'No scheduled updates to process'}

        # Group updates by grade to avoid redundant calculations
        grades_to_update = set()
        for update in self._scheduled_updates:
            event_data = update['event'].data
            if 'grade' in event_data:
                grades_to_update.add(event_data['grade'])

        # Generate statistics for affected grades
        results = []
        for grade in grades_to_update:
            try:
                result = self.generate_grade_statistics(grade)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate statistics for grade {grade}: {e}")

        # Clear scheduled updates
        self._scheduled_updates.clear()

        return {
            'updates_processed': len(results),
            'grades_updated': list(grades_to_update),
            'results': results
        }

    def generate_grade_statistics(
        self,
        grade: str,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Generate statistics for a specific grade.

        Args:
            grade: Grade level.
            period_start: Start of the statistics period (defaults to beginning of semester).
            period_end: End of the statistics period (defaults to today).
            save: Whether to save the statistics to the database.

        Returns:
            Dict[str, Any]: Generated statistics.

        Raises:
            AnalysisError: If statistics generation fails.
        """
        try:
            # Set default period if not provided
            if period_end is None:
                period_end = date.today()
            if period_start is None:
                # Default to current school year (September to June)
                current_year = period_end.year
                if period_end.month < 9:
                    period_start = date(current_year - 1, 9, 1)
                else:
                    period_start = date(current_year, 9, 1)

            # Get student data
            students = self.dao.student.get_by_grade(grade)
            if not students:
                logger.warning(f"No students found for grade {grade}")
                return {
                    'grade': grade,
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat(),
                    'total_students': 0,
                    'message': 'No student data available'
                }

            # Calculate statistics
            heights = [s.height_cm for s in students]
            weights = [s.weight_kg for s in students]
            bmis = [s.bmi for s in students if s.bmi > 0]

            stats = {
                'grade': grade,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'total_students': len(students),
                'average_height': round(float(np.mean(heights)), 2),
                'height_standard_deviation': round(float(np.std(heights)), 2),
                'min_height': float(np.min(heights)),
                'max_height': float(np.max(heights)),
                'median_height': round(float(np.median(heights)), 2),
                'average_weight': round(float(np.mean(weights)), 2),
                'weight_standard_deviation': round(float(np.std(weights)), 2),
                'average_bmi': round(float(np.mean(bmis)), 2) if bmis else None
            }

            # Calculate BMI distribution
            bmi_distribution = {'偏瘦': 0, '正常': 0, '超重': 0, '肥胖': 0}
            for student in students:
                category = student.bmi_category()
                bmi_distribution[category] += 1
            stats['bmi_distribution'] = bmi_distribution

            # Calculate height percentiles
            percentiles = [3, 10, 25, 50, 75, 90, 97]
            height_percentiles = {}
            for p in percentiles:
                height_percentiles[f'P{p}'] = round(float(np.percentile(heights, p)), 1)
            stats['height_percentiles'] = height_percentiles

            # Compare with standard heights
            comparison = self._student_service.compare_with_standard(grade)
            stats['comparison_to_standard'] = comparison

            # Calculate growth data (comparison with previous grade)
            grade_order = StudentService.GRADE_ORDER
            grade_index = grade_order.index(grade) if grade in grade_order else -1
            if grade_index > 0:
                previous_grade = grade_order[grade_index - 1]
                previous_stats = self.get_latest_grade_statistics(previous_grade)
                if previous_stats:
                    growth = {
                        'from_grade': previous_grade,
                        'to_grade': grade,
                        'height_increase': round(stats['average_height'] - previous_stats.get('average_height', 0), 2)
                    }
                    stats['growth_data'] = growth

            # Save to database if requested
            if save:
                self._save_grade_statistics(grade, period_start, period_end, stats)
                logger.info(f"Generated and saved statistics for grade {grade}")

            self.emit_event(
                EventType.STATISTICS_GENERATED,
                data={'grade': grade, 'period_start': period_start.isoformat()},
                source="StatisticsService.generate_grade_statistics"
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to generate statistics for grade {grade}: {e}")
            raise AnalysisError(
                message=f"Statistics generation failed for grade {grade}",
                details={"error": str(e)}
            ) from e

    def _save_grade_statistics(
        self,
        grade: str,
        period_start: date,
        period_end: date,
        statistics: Dict[str, Any]
    ) -> StatisticsRecord:
        """
        Save grade statistics to the database.

        Args:
            grade: Grade level.
            period_start: Start of the statistics period.
            period_end: End of the statistics period.
            statistics: Statistics data to save.

        Returns:
            StatisticsRecord: Saved statistics record.
        """
        with self.transaction():
            record = self.dao.statistics.create_grade_summary(
                grade=grade,
                period_start=period_start,
                period_end=period_end,
                statistics=statistics
            )
            return record

    def generate_all_grade_statistics(
        self,
        save: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate statistics for all grades.

        Args:
            save: Whether to save the statistics to the database.

        Returns:
            List[Dict[str, Any]]: List of statistics for each grade.
        """
        results = []
        for grade in StudentService.GRADE_ORDER:
            try:
                stats = self.generate_grade_statistics(grade, save=save)
                results.append(stats)
            except Exception as e:
                logger.error(f"Failed to generate statistics for grade {grade}: {e}")
                results.append({
                    'grade': grade,
                    'error': str(e)
                })
        return results

    def get_latest_grade_statistics(
        self,
        grade: str,
        record_type: str = 'grade_summary'
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest statistics for a specific grade.

        Args:
            grade: Grade level.
            record_type: Type of statistics record.

        Returns:
            Optional[Dict[str, Any]]: Latest statistics if available.
        """
        record = self.dao.statistics.get_latest_by_type(record_type, grade)
        return record.to_dict() if record else None

    def get_statistics_history(
        self,
        grade: Optional[str] = None,
        record_type: str = 'grade_summary',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get historical statistics records.

        Args:
            grade: Optional grade filter.
            record_type: Type of statistics record.
            limit: Maximum number of records to return.

        Returns:
            List[Dict[str, Any]]: List of historical statistics records.
        """
        records = self.dao.statistics.get_by_record_type(record_type)

        if grade:
            records = [r for r in records if r.grade == grade]

        records = records[:limit]
        return [record.to_dict() for record in records]

    def generate_gender_statistics(
        self,
        grade: Optional[str] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Generate statistics grouped by gender.

        Args:
            grade: Optional grade filter.
            save: Whether to save the statistics to the database.

        Returns:
            Dict[str, Any]: Gender-based statistics.
        """
        results = self._student_service.calculate_gender_statistics(grade)

        if save:
            # Save male statistics
            if results.get('male', {}).get('count', 0) > 0:
                self._save_gender_statistics('男', results['male'], grade)

            # Save female statistics
            if results.get('female', {}).get('count', 0) > 0:
                self._save_gender_statistics('女', results['female'], grade)

        return results

    def _save_gender_statistics(
        self,
        gender: str,
        statistics: Dict[str, Any],
        grade: Optional[str] = None
    ) -> StatisticsRecord:
        """
        Save gender-based statistics to the database.

        Args:
            gender: Gender ('男' or '女').
            statistics: Statistics data to save.
            grade: Optional grade level.

        Returns:
            StatisticsRecord: Saved statistics record.
        """
        period_start = date.today().replace(month=9, day=1)
        period_end = date.today()

        with self.transaction():
            record = self.dao.statistics.create_gender_summary(
                gender=gender,
                period_start=period_start,
                period_end=period_end,
                statistics={
                    'total_students': statistics.get('count', 0),
                    'average_height': statistics.get('avg_height'),
                    'average_weight': statistics.get('avg_weight'),
                    'grade': grade
                }
            )
            if grade:
                record.grade = grade
            return record

    def generate_comparison_report(
        self,
        output_format: str = 'dict'  # 'dict' or 'text'
    ) -> Any:
        """
        Generate a comprehensive comparison report.

        Args:
            output_format: Output format ('dict' or 'text').

        Returns:
            Any: Comparison report in the requested format.
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'basic_statistics': self._student_service.calculate_basic_statistics(),
            'grade_comparisons': [],
            'bmi_analysis': self._student_service.calculate_bmi_distribution()
        }

        # Generate grade comparisons
        for grade in StudentService.GRADE_ORDER:
            comparison = self._student_service.compare_with_standard(grade)
            report['grade_comparisons'].append(comparison)

        if output_format == 'text':
            return self._format_comparison_report_text(report)

        return report

    def _format_comparison_report_text(self, report: Dict[str, Any]) -> str:
        """
        Format the comparison report as human-readable text.

        Args:
            report: Comparison report dictionary.

        Returns:
            str: Formatted text report.
        """
        lines = []
        lines.append("=" * 80)
        lines.append("学生身高数据对比报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {report['generated_at']}")
        lines.append("")

        # Basic statistics
        basic = report['basic_statistics']
        lines.append("【基本统计】")
        lines.append(f"  总学生数: {basic['total_students']}")
        lines.append(f"  男生人数: {basic['male_count']}")
        lines.append(f"  女生人数: {basic['female_count']}")
        lines.append(f"  平均身高: {basic['average_height']} cm")
        lines.append(f"  身高范围: {basic['min_height']} cm - {basic['max_height']} cm")
        lines.append("")

        # Grade comparisons
        lines.append("【各年级与标准身高对比】")
        lines.append("")
        for comparison in report['grade_comparisons']:
            grade = comparison['grade']
            male = comparison['male']
            female = comparison['female']

            lines.append(f"{grade}:")
            if male['actual'] is not None:
                lines.append(f"  男生: {male['actual']} cm (标准: {male['standard']} cm, 差异: {male['difference']:+} cm)")
            if female['actual'] is not None:
                lines.append(f"  女生: {female['actual']} cm (标准: {female['standard']} cm, 差异: {female['difference']:+} cm)")
            lines.append("")

        # BMI analysis
        bmi = report['bmi_analysis']
        lines.append("【BMI分布】")
        for category, count in bmi['categories'].items():
            lines.append(f"  {category}: {count} 人")
        lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def get_statistics_by_period(
        self,
        start_date: date,
        end_date: Optional[date] = None,
        grade: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get statistics records for a specific time period.

        Args:
            start_date: Start of the period.
            end_date: End of the period (defaults to today).
            grade: Optional grade filter.

        Returns:
            List[Dict[str, Any]]: List of statistics records.
        """
        records = self.dao.statistics.get_by_period(start_date, end_date)

        if grade:
            records = [r for r in records if r.grade == grade]

        return [record.to_dict() for record in records]

    def delete_statistics(self, record_id: int) -> bool:
        """
        Delete a statistics record.

        Args:
            record_id: Database ID of the statistics record.

        Returns:
            bool: True if deleted successfully.
        """
        return self.dao.statistics.delete(record_id)

    def calculate_grade_statistics(
        self,
        grade: str,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate statistics for a specific grade.
        Alias for generate_grade_statistics.

        Args:
            grade: Grade to calculate statistics for.
            save: Whether to save the statistics to the database.

        Returns:
            Dict[str, Any]: Calculated statistics.
        """
        return self.generate_grade_statistics(grade=grade, save=save)

    def calculate_gender_statistics(
        self,
        grade: str = None,
        gender: str = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate statistics grouped by gender.

        Args:
            grade: Optional grade to filter by.
            gender: Optional gender to filter by.
            save: Whether to save the statistics to the database.

        Returns:
            Dict[str, Any]: Calculated statistics.
        """
        df = self._student_service.get_students_dataframe()
        
        if df.empty:
            return {}
        
        if grade:
            df = df[df['grade'] == grade]
        if gender:
            df = df[df['gender'] == gender]
        
        result = {
            'grade': grade,
            'gender': gender,
            'total_students': len(df),
            'avg_height': df['height_cm'].mean() if len(df) > 0 else 0,
            'avg_weight': df['weight_kg'].mean() if len(df) > 0 else 0,
            'avg_bmi': df['bmi'].mean() if len(df) > 0 else 0
        }
        
        # Add min/max values
        if len(df) > 0:
            result.update({
                'min_height': df['height_cm'].min(),
                'max_height': df['height_cm'].max(),
                'min_weight': df['weight_kg'].min(),
                'max_weight': df['weight_kg'].max()
            })
        
        return result

    def calculate_all_grades_statistics(
        self,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate statistics for all grades.
        Alias for generate_all_grade_statistics.

        Args:
            save: Whether to save the statistics to the database.

        Returns:
            Dict[str, Any]: Calculated statistics.
        """
        return self.generate_all_grade_statistics(save=save)

    def calculate_bmi_distribution(self, grade: str = None) -> Dict[str, int]:
        """
        Calculate the distribution of students by BMI category.

        Args:
            grade: Optional grade to filter by.

        Returns:
            Dict[str, int]: Count of students in each BMI category.
        """
        df = self._student_service.get_students_dataframe()
        
        if df.empty:
            return {}
        
        if grade:
            df = df[df['grade'] == grade]
        
        bmi_categories = df.apply(lambda x: self._get_bmi_category(x['bmi']), axis=1)
        category_counts = bmi_categories.value_counts().to_dict()
        
        # Ensure all categories are present
        for category in ['偏瘦', '正常', '超重', '肥胖']:
            if category not in category_counts:
                category_counts[category] = 0
        
        return category_counts

    def _get_bmi_category(self, bmi: float) -> str:
        """
        Get the BMI category for a given BMI value.

        Args:
            bmi: BMI value.

        Returns:
            str: BMI category.
        """
        if bmi < 15:
            return "偏瘦"
        elif bmi < 20:
            return "正常"
        elif bmi < 24:
            return "超重"
        else:
            return "肥胖"

    def calculate_height_percentiles(self, grade: str = None) -> Dict[str, float]:
        """
        Calculate height percentiles (25th, 50th, 75th).

        Args:
            grade: Optional grade to filter by.

        Returns:
            Dict[str, float]: Height percentiles.
        """
        df = self._student_service.get_students_dataframe()
        
        if df.empty:
            return {}
        
        if grade:
            df = df[df['grade'] == grade]
        
        if len(df) == 0:
            return {}
        
        return {
            'p3': df['height_cm'].quantile(0.03),
            'p10': df['height_cm'].quantile(0.10),
            'p25': df['height_cm'].quantile(0.25),
            'p50': df['height_cm'].quantile(0.50),
            'p75': df['height_cm'].quantile(0.75),
            'p90': df['height_cm'].quantile(0.90),
            'p97': df['height_cm'].quantile(0.97),
            'min': df['height_cm'].min(),
            'max': df['height_cm'].max()
        }

    def calculate_height_distribution(self, grade: str = None) -> Dict[str, Any]:
        """
        Calculate the distribution of students by height ranges.

        Args:
            grade: Optional grade to filter by.

        Returns:
            Dict[str, Any]: Height distribution statistics.
        """
        df = self._student_service.get_students_dataframe()
        
        if df.empty:
            return {}
        
        if grade:
            df = df[df['grade'] == grade]
        
        height_ranges = {
            '100-110cm': len(df[(df['height_cm'] >= 100) & (df['height_cm'] < 110)]),
            '110-120cm': len(df[(df['height_cm'] >= 110) & (df['height_cm'] < 120)]),
            '120-130cm': len(df[(df['height_cm'] >= 120) & (df['height_cm'] < 130)]),
            '130-140cm': len(df[(df['height_cm'] >= 130) & (df['height_cm'] < 140)]),
            '140-150cm': len(df[(df['height_cm'] >= 140) & (df['height_cm'] < 150)]),
            '150-160cm': len(df[(df['height_cm'] >= 150) & (df['height_cm'] < 160)]),
            '160cm+': len(df[df['height_cm'] >= 160])
        }
        
        return height_ranges

    def compare_to_standard(self, grade: str = None) -> Dict[str, Any]:
        """
        Compare student heights to national standards.

        Args:
            grade: Optional grade to filter by.

        Returns:
            Dict[str, Any]: Comparison results.
        """
        df = self._student_service.get_students_dataframe()
        
        if df.empty:
            return {}
        
        # National standard heights by grade (simplified example)
        standard_heights = {
            '一年级': 125,
            '二年级': 130,
            '三年级': 135,
            '四年级': 140,
            '五年级': 145,
            '六年级': 150
        }
        
        if grade:
            # Single grade comparison - return flat structure with gender breakdown
            grade_data = df[df['grade'] == grade]
            if grade_data.empty:
                return {}
            
            avg_height = grade_data['height_cm'].mean()
            standard = standard_heights.get(grade, 135)
            
            # Gender comparison
            male_data = grade_data[grade_data['gender'] == '男']
            female_data = grade_data[grade_data['gender'] == '女']
            
            gender_comparison = {}
            if not male_data.empty:
                gender_comparison['男'] = {
                    'average': male_data['height_cm'].mean(),
                    'standard': standard,
                    'difference': male_data['height_cm'].mean() - standard,
                    'above_standard': len(male_data[male_data['height_cm'] > standard]),
                    'total': len(male_data)
                }
            if not female_data.empty:
                gender_comparison['女'] = {
                    'average': female_data['height_cm'].mean(),
                    'standard': standard,
                    'difference': female_data['height_cm'].mean() - standard,
                    'above_standard': len(female_data[female_data['height_cm'] > standard]),
                    'total': len(female_data)
                }
            
            return {
                'grade': grade,
                'overall': {
                    'average': avg_height,
                    'standard': standard,
                    'difference': avg_height - standard,
                    'above_standard': len(grade_data[grade_data['height_cm'] > standard]),
                    'total': len(grade_data)
                },
                'gender_comparison': gender_comparison,
                'average': avg_height,
                'standard': standard,
                'difference': avg_height - standard,
                'above_standard': len(grade_data[grade_data['height_cm'] > standard]),
                'total': len(grade_data)
            }
        else:
            # All grades comparison - return dict with grade keys
            comparison = {}
            for g in StudentService.GRADE_ORDER:
                grade_data = df[df['grade'] == g]
                if not grade_data.empty:
                    avg_height = grade_data['height_cm'].mean()
                    standard = standard_heights.get(g, 135)
                    comparison[g] = {
                        'average': avg_height,
                        'standard': standard,
                        'difference': avg_height - standard,
                        'above_standard': len(grade_data[grade_data['height_cm'] > standard]),
                        'total': len(grade_data)
                    }
            return comparison

    def get_growth_trend(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Get growth trend statistics over time.

        Args:
            start_date: Start date for trend analysis.
            end_date: End date for trend analysis.

        Returns:
            List[Dict[str, Any]]: Growth trend data as a list of grade statistics.
        """
        df = self._student_service.get_students_dataframe()
        
        if df.empty:
            return []
        
        trend_data = []
        for grade in StudentService.GRADE_ORDER:
            grade_data = df[df['grade'] == grade]
            if not grade_data.empty:
                trend_data.append({
                    'grade': grade,
                    'average_height': grade_data['height_cm'].mean(),
                    'avg_height': grade_data['height_cm'].mean(),
                    'average_weight': grade_data['weight_kg'].mean(),
                    'avg_weight': grade_data['weight_kg'].mean(),
                    'avg_bmi': grade_data['bmi'].mean(),
                    'count': len(grade_data)
                })
        
        return trend_data
