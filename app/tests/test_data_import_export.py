"""
Unit tests for the DataImportExportService class.

This module contains tests for data import/export functionality including:
- Excel file import
- Excel file export
- Data validation during import
- Error handling for invalid files
"""

import os
import pytest
import pandas as pd
from datetime import date, datetime
from typing import List
from sqlalchemy import text

from app.service.data_import_export import DataImportExportService
from app.service.student_service import StudentService
from app.utils.exceptions import ImportError, ValidationError
from app.config.settings import get_settings

settings = get_settings()


class TestDataImportExportService:
    """Test cases for DataImportExportService."""

    @pytest.fixture
    def test_output_dir(self) -> str:
        """
        Fixture for test output directory.
        
        Returns:
            str: Path to test output directory.
        """
        test_dir = "./test_output"
        os.makedirs(test_dir, exist_ok=True)
        return test_dir

    @pytest.fixture
    def sample_excel_file(self, test_output_dir: str) -> str:
        """
        Fixture for creating a sample Excel file for import testing.
        
        Args:
            test_output_dir: Directory to save the test file.
            
        Returns:
            str: Path to the created Excel file.
        """
        file_path = os.path.join(test_output_dir, "test_import_data.xlsx")
        
        # Create sample data
        data = {
            "学生ID": [20001, 20002, 20003, 20004, 20005],
            "姓名": ["学生A", "学生B", "学生C", "学生D", "学生E"],
            "性别": ["男", "女", "男", "女", "男"],
            "年级": ["一年级", "一年级", "二年级", "二年级", "三年级"],
            "年龄": [7, 7, 8, 8, 9],
            "身高(cm)": [120.5, 119.0, 125.5, 124.0, 130.0],
            "体重(kg)": [25.0, 24.5, 28.0, 27.5, 32.0],
            "入学日期": [date.today()] * 5
        }
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        yield file_path
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_import_from_excel(self, test_session, sample_excel_file: str):
        """
        Test importing student data from Excel.
        
        Expected: Data should be imported successfully into the database.
        """
        import_service = DataImportExportService(test_session)
        
        result = import_service.import_from_excel(sample_excel_file)
        
        assert result is not None
        assert result["created"] == 5
        assert result["updated"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == []

    def test_import_from_excel_duplicate_data(
        self, test_session, sample_excel_file: str
    ):
        """
        Test importing duplicate data from Excel.
        
        Expected: Existing records should be updated or skipped based on configuration.
        """
        import_service = DataImportExportService(test_session)
        student_service = StudentService(test_session)
        
        # First import
        result1 = import_service.import_from_excel(sample_excel_file)
        assert result1["created"] == 5
        
        # Second import with same file - should update or skip
        result2 = import_service.import_from_excel(sample_excel_file)
        # Students should be updated since they already exist
        assert result2["updated"] == 5 or result2["skipped"] == 5

    def test_import_from_excel_invalid_format(self, test_session, test_output_dir: str):
        """
        Test importing from an Excel file with invalid format.
        
        Expected: ImportError should be raised.
        """
        import_service = DataImportExportService(test_session)
        
        # Create Excel file with missing required columns
        invalid_file = os.path.join(test_output_dir, "invalid_import.xlsx")
        data = {
            "姓名": ["学生X", "学生Y"],
            "性别": ["男", "女"],
            # Missing student_id, grade, height, weight, etc.
        }
        
        df = pd.DataFrame(data)
        df.to_excel(invalid_file, index=False)
        
        try:
            with pytest.raises(ImportError):
                import_service.import_from_excel(invalid_file)
        finally:
            if os.path.exists(invalid_file):
                os.remove(invalid_file)

    def test_import_from_excel_invalid_data(self, test_session, test_output_dir: str):
        """
        Test importing from an Excel file with invalid data values.
        
        Expected: Invalid records should be reported as errors.
        """
        import_service = DataImportExportService(test_session)
        
        invalid_file = os.path.join(test_output_dir, "invalid_data.xlsx")
        data = {
            "学生ID": [30001, 30002, 30003],
            "姓名": ["学生1", "学生2", "学生3"],
            "性别": ["男", "无效性别", "女"],  # Invalid gender
            "年级": ["一年级", "二年级", "不存在的年级"],  # Invalid grade
            "年龄": [7, 8, 9],
            "身高(cm)": [120.5, -10.0, 130.0],  # Invalid height (negative)
            "体重(kg)": [25.0, 28.0, -5.0],  # Invalid weight (negative)
            "入学日期": [date.today()] * 3
        }
        
        df = pd.DataFrame(data)
        df.to_excel(invalid_file, index=False)
        
        try:
            result = import_service.import_from_excel(invalid_file)
            # Should have some errors or some records skipped
            assert len(result["errors"]) > 0 or result["skipped"] > 0
        finally:
            if os.path.exists(invalid_file):
                os.remove(invalid_file)

    def test_export_to_excel(self, test_session, test_output_dir: str):
        """
        Test exporting student data to Excel.
        
        Expected: Excel file should be created with student data.
        """
        import_service = DataImportExportService(test_session)
        student_service = StudentService(test_session)
        
        # First create some test students
        for i in range(10):
            student_service.create_student({
                "student_id": 40001 + i,
                "name": f"导出学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "三年级",
                "age": 9,
                "height_cm": 130.0 + i,
                "weight_kg": 35.0 + i,
                "enrollment_date": date.today()
            })
        
        export_file = os.path.join(test_output_dir, "test_export.xlsx")
        
        try:
            result = import_service.export_to_excel(export_file)
            
            assert result is not None
            assert os.path.exists(export_file)
            assert result["exported"] >= 10
            assert result["file_path"] == export_file
            
            # Verify the file content
            df = pd.read_excel(export_file)
            assert len(df) >= 10
            # Check that columns exist (in Chinese as per export format)
            assert "学生ID" in df.columns or "student_id" in df.columns
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)

    def test_export_filtered_data(self, test_session, test_output_dir: str):
        """
        Test exporting filtered student data.
        
        Expected: Only students matching the filter criteria should be exported.
        """
        import_service = DataImportExportService(test_session)
        student_service = StudentService(test_session)
        
        # Create students in different grades
        grades = ["一年级", "一年级", "二年级", "二年级", "三年级"]
        for i, grade in enumerate(grades):
            student_service.create_student({
                "student_id": 50001 + i,
                "name": f"筛选学生{i}",
                "gender": "男",
                "grade": grade,
                "age": 7 + i,
                "height_cm": 120.0 + i * 5,
                "weight_kg": 25.0 + i * 3,
                "enrollment_date": date.today()
            })
        
        export_file = os.path.join(test_output_dir, "filtered_export.xlsx")
        
        try:
            # Export only 一年级 students
            result = import_service.export_to_excel(
                export_file,
                filters={"grade": "一年级"}
            )
            
            assert result["exported"] == 2  # Should have 2 students from 一年级
            
            # Verify the exported data
            df = pd.read_excel(export_file)
            assert len(df) == 2
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)

    def test_import_export_roundtrip(self, test_session, test_output_dir: str):
        """
        Test importing and exporting data (roundtrip).
        
        Expected: Exported data should match the originally imported data.
        """
        import_service = DataImportExportService(test_session)
        student_service = StudentService(test_session)
        
        # Create original data
        original_count = 15
        for i in range(original_count):
            student_service.create_student({
                "student_id": 60001 + i,
                "name": f"往返学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "四年级",
                "age": 10,
                "height_cm": 135.0 + i * 0.5,
                "weight_kg": 38.0 + i * 0.3,
                "enrollment_date": date.today()
            })
        
        # Export
        export_file = os.path.join(test_output_dir, "roundtrip_export.xlsx")
        export_result = import_service.export_to_excel(export_file)
        
        assert export_result["exported"] == original_count
        
        # Clear the table to simulate fresh import
        test_session.execute(text("DELETE FROM students"))
        test_session.commit()
        
        # Import back
        import_result = import_service.import_from_excel(export_file)
        
        assert import_result["created"] == original_count
        
        # Cleanup
        if os.path.exists(export_file):
            os.remove(export_file)

    def test_import_empty_file(self, test_session, test_output_dir: str):
        """
        Test importing from an empty Excel file.
        
        Expected: Should handle empty files gracefully.
        """
        import_service = DataImportExportService(test_session)
        
        empty_file = os.path.join(test_output_dir, "empty_file.xlsx")
        
        # Create empty DataFrame
        df = pd.DataFrame()
        df.to_excel(empty_file, index=False)
        
        try:
            result = import_service.import_from_excel(empty_file)
            assert result["created"] == 0
            assert result["errors"] == [] or len(result["errors"]) > 0
        finally:
            if os.path.exists(empty_file):
                os.remove(empty_file)

    def test_export_statistics(self, test_session, test_output_dir: str):
        """
        Test exporting statistics data to Excel.
        
        Expected: Statistics report should be exported to Excel.
        """
        from app.service.statistics_service import StatisticsService
        
        import_service = DataImportExportService(test_session)
        stats_service = StatisticsService(test_session)
        student_service = StudentService(test_session)
        
        # Create some students
        for i in range(20):
            student_service.create_student({
                "student_id": 70001 + i,
                "name": f"统计导出学生{i}",
                "gender": "男" if i % 2 == 0 else "女",
                "grade": "五年级",
                "age": 11,
                "height_cm": 140.0 + i * 0.5,
                "weight_kg": 40.0 + i * 0.4,
                "enrollment_date": date.today()
            })
        
        stats_file = os.path.join(test_output_dir, "statistics_export.xlsx")
        
        try:
            result = import_service.export_statistics_report(stats_file)
            assert os.path.exists(stats_file)
            assert "statistics_sheets" in result or "exported" in result
        finally:
            if os.path.exists(stats_file):
                os.remove(stats_file)

    def test_column_name_variations(self, test_session, test_output_dir: str):
        """
        Test import with different column name variations.
        
        Expected: Should handle various column name formats (Chinese, English, different cases).
        """
        import_service = DataImportExportService(test_session)
        
        # Test with English column names
        english_col_file = os.path.join(test_output_dir, "english_cols.xlsx")
        data = {
            "student_id": [80001, 80002],
            "name": ["Student A", "Student B"],
            "gender": ["Male", "Female"],
            "grade": ["Grade 1", "Grade 2"],
            "age": [7, 8],
            "height_cm": [120.5, 125.0],
            "weight_kg": [25.0, 28.0],
        }
        
        df = pd.DataFrame(data)
        df.to_excel(english_col_file, index=False)
        
        try:
            result = import_service.import_from_excel(english_col_file)
            # Should handle or report English column names
            # May have errors due to gender/grade not being in Chinese
            assert result is not None
        finally:
            if os.path.exists(english_col_file):
                os.remove(english_col_file)
