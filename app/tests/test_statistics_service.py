"""
Unit tests for the StatisticsService class.

This module contains tests for statistics calculation functionality including:
- Grade statistics calculation
- Height distribution statistics
- BMI statistics
- Growth trend analysis
"""

import pytest
from datetime import date
import numpy as np

from app.service.statistics_service import StatisticsService
from app.service.student_service import StudentService


class TestStatisticsService:
    """Test cases for StatisticsService."""

    def test_calculate_grade_statistics(self, test_session):
        """
        Test calculating statistics for a grade.
        
        Expected: Statistics should be calculated correctly for all students in a grade.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create test students in 一年级
        for i in range(10):
            student_service.create_student({
                "student_id": 8001 + i,
                "name": f"统计学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "一年级",
                "age": 7,
                "height_cm": 120.0 + i * 2,
                "weight_kg": 25.0 + i,
                "enrollment_date": date.today()
            })
        
        stats = stats_service.calculate_grade_statistics("一年级")
        
        assert stats is not None
        assert stats["grade"] == "一年级"
        assert stats["total_students"] >= 10
        assert "average_height" in stats
        assert "height_standard_deviation" in stats
        assert "min_height" in stats
        assert "max_height" in stats
        assert "median_height" in stats
        assert "average_weight" in stats
        assert "average_bmi" in stats

    def test_calculate_gender_statistics(self, test_session):
        """
        Test calculating statistics by gender.
        
        Expected: Statistics should be calculated separately for each gender.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create test students with known gender distribution
        for i in range(5):
            # Male students
            student_service.create_student({
                "student_id": 9001 + i,
                "name": f"男生{i}",
                "gender": "男",
                "grade": "二年级",
                "age": 8,
                "height_cm": 125.0 + i,
                "weight_kg": 30.0 + i,
                "enrollment_date": date.today()
            })
        
        for i in range(5):
            # Female students
            student_service.create_student({
                "student_id": 9101 + i,
                "name": f"女生{i}",
                "gender": "女",
                "grade": "二年级",
                "age": 8,
                "height_cm": 124.0 + i,
                "weight_kg": 28.0 + i,
                "enrollment_date": date.today()
            })
        
        stats_male = stats_service.calculate_gender_statistics("二年级", "男")
        stats_female = stats_service.calculate_gender_statistics("二年级", "女")
        
        assert stats_male["total_students"] >= 5
        assert stats_female["total_students"] >= 5
        assert stats_male["gender"] == "男"
        assert stats_female["gender"] == "女"

    def test_calculate_bmi_distribution(self, test_session):
        """
        Test calculating BMI distribution.
        
        Expected: BMI categories should be correctly counted.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create test students with varying BMI
        for i in range(10):
            height = 130.0 + i
            weight = 30.0 + i * 2  # Increasing weight to get different BMI values
            student_service.create_student({
                "student_id": 10001 + i,
                "name": f"BMI学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "三年级",
                "age": 9,
                "height_cm": height,
                "weight_kg": weight,
                "enrollment_date": date.today()
            })
        
        distribution = stats_service.calculate_bmi_distribution("三年级")
        
        assert distribution is not None
        assert "偏瘦" in distribution
        assert "正常" in distribution
        assert "超重" in distribution
        assert "肥胖" in distribution
        # Total should equal number of students
        total = sum(distribution.values())
        assert total >= 10

    def test_calculate_height_percentiles(self, test_session):
        """
        Test calculating height percentiles.
        
        Expected: Percentiles should be calculated correctly.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create test students with known height distribution
        heights = [120, 122, 125, 128, 130, 132, 135, 138, 140, 145]
        for i, height in enumerate(heights):
            student_service.create_student({
                "student_id": 11001 + i,
                "name": f"百分位学生{i}",
                "gender": "男",
                "grade": "四年级",
                "age": 10,
                "height_cm": height,
                "weight_kg": 35.0,
                "enrollment_date": date.today()
            })
        
        percentiles = stats_service.calculate_height_percentiles("四年级")
        
        assert percentiles is not None
        assert "p3" in percentiles  # 3rd percentile
        assert "p10" in percentiles  # 10th percentile
        assert "p25" in percentiles  # 25th percentile
        assert "p50" in percentiles  # 50th percentile (median)
        assert "p75" in percentiles  # 75th percentile
        assert "p90" in percentiles  # 90th percentile
        assert "p97" in percentiles  # 97th percentile

    def test_calculate_all_grades_statistics(self, test_session):
        """
        Test calculating statistics for all grades.
        
        Expected: Statistics should be returned for each grade.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create students in different grades
        grades = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        for grade in grades:
            for i in range(5):
                student_service.create_student({
                    "student_id": 12000 + grades.index(grade) * 100 + i,
                    "name": f"{grade}学生{i}",
                    "gender": "男" if i % 2 == 0 else "女",
                    "grade": grade,
                    "age": 7 + grades.index(grade),
                    "height_cm": 120.0 + grades.index(grade) * 5 + i,
                    "weight_kg": 25.0 + grades.index(grade) * 3 + i,
                    "enrollment_date": date.today()
                })
        
        all_stats = stats_service.calculate_all_grades_statistics()
        
        assert all_stats is not None
        assert len(all_stats) >= 6  # At least 6 grades
        
        # Check that each grade has statistics
        for grade_stats in all_stats:
            assert "grade" in grade_stats
            assert "total_students" in grade_stats
            assert "average_height" in grade_stats
            # Each grade should have at least 5 students
            assert grade_stats["total_students"] >= 5

    def test_compare_to_standard(self, test_session):
        """
        Test comparing student heights to standard growth charts.
        
        Expected: Comparison statistics should be generated correctly.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create test students
        for i in range(10):
            student_service.create_student({
                "student_id": 13001 + i,
                "name": f"标准对比学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "五年级",
                "age": 11,
                "height_cm": 140.0 + i * 2,
                "weight_kg": 40.0 + i,
                "enrollment_date": date.today()
            })
        
        comparison = stats_service.compare_to_standard("五年级")
        
        assert comparison is not None
        assert "grade" in comparison
        assert "gender_comparison" in comparison or "overall" in comparison

    def test_statistics_with_no_data(self, test_session):
        """
        Test statistics calculation when there are no students in a grade.
        
        Expected: Should handle empty data gracefully.
        """
        stats_service = StatisticsService(test_session)
        
        # Use a grade that has no students
        stats = stats_service.calculate_grade_statistics("不存在的年级")
        
        assert stats is not None
        assert stats["total_students"] == 0

    def test_calculate_height_distribution(self, test_session):
        """
        Test calculating height distribution in ranges.
        
        Expected: Height ranges should be correctly counted.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create students with a range of heights
        for i in range(20):
            height = 110 + i * 3  # Heights from 110 to ~167 cm
            student_service.create_student({
                "student_id": 14001 + i,
                "name": f"分布学生{i}",
                "gender": "男",
                "grade": "六年级",
                "age": 12,
                "height_cm": height,
                "weight_kg": 40.0 + i,
                "enrollment_date": date.today()
            })
        
        distribution = stats_service.calculate_height_distribution("六年级")
        
        assert distribution is not None
        # Should have multiple height ranges
        assert len(distribution) > 0
        # Total students should equal sum of distribution counts
        total = sum(distribution.values())
        assert total >= 20

    def test_get_growth_trend(self, test_session):
        """
        Test calculating growth trends across grades.
        
        Expected: Growth trend data should show increasing heights.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create students in grades 1-6 with increasing average heights
        grades = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        base_heights = [120, 125, 130, 135, 140, 147]
        
        for grade_idx, grade in enumerate(grades):
            for i in range(5):
                height = base_heights[grade_idx] + np.random.normal(0, 3)
                student_service.create_student({
                    "student_id": 15000 + grade_idx * 100 + i,
                    "name": f"成长学生{grade_idx}{i}",
                    "gender": "男",
                    "grade": grade,
                    "age": 7 + grade_idx,
                    "height_cm": float(height),
                    "weight_kg": 30.0 + grade_idx * 3,
                    "enrollment_date": date.today()
                })
        
        trend = stats_service.get_growth_trend()
        
        assert trend is not None
        # Should have data for each grade
        assert len(trend) >= 6
        # Heights should generally increase with grade
        heights = [g.get("average_height", 0) for g in trend if g.get("average_height")]
        if heights:
            # Heights should be in generally increasing order
            assert heights[-1] > heights[0]  # 六年级 should be taller than 一年级

    def test_statistical_calculations_accuracy(self, test_session):
        """
        Test the accuracy of statistical calculations.
        
        Expected: Calculations should match expected statistical values.
        """
        student_service = StudentService(test_session)
        stats_service = StatisticsService(test_session)
        
        # Create students with known heights for verification
        heights = [120, 120, 120, 120, 120]  # All same height
        for i, height in enumerate(heights):
            student_service.create_student({
                "student_id": 16001 + i,
                "name": f"准确学生{i}",
                "gender": "男",
                "grade": "一年级",
                "age": 7,
                "height_cm": height,
                "weight_kg": 25.0,
                "enrollment_date": date.today()
            })
        
        stats = stats_service.calculate_grade_statistics("一年级")
        
        # With all heights = 120, average and median should be 120, std dev = 0
        assert stats["average_height"] == pytest.approx(120.0, 0.1)
        assert stats["median_height"] == pytest.approx(120.0, 0.1)
        assert stats["height_standard_deviation"] == pytest.approx(0.0, 0.1)
        assert stats["min_height"] == pytest.approx(120.0, 0.1)
        assert stats["max_height"] == pytest.approx(120.0, 0.1)
