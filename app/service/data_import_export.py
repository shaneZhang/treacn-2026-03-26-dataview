"""
Data Import/Export service for Excel ↔ Database synchronization.

This module provides functionality to import data from Excel files
to the database and export data from the database to Excel files.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
import pandas as pd
from sqlalchemy.orm import Session

from app.service.base_service import BaseService
from app.service.student_service import StudentService
from app.utils.observer import EventType
from app.utils.logger import get_logger
from app.utils.exceptions import (
    ImportError,
    ExportError,
    FileProcessingError,
    InvalidDataError
)

logger = get_logger(__name__)


class DataImportExportService(BaseService):
    """
    Service class for data import and export operations.

    This class provides methods to synchronize data between Excel files
    and the database, supporting both import and export operations.
    """

    # Mapping from Excel column names (Chinese) to database field names
    EXCEL_COLUMN_MAPPING = {
        '学生ID': 'student_id',
        '姓名': 'name',
        '性别': 'gender',
        '年级': 'grade',
        '年龄': 'age',
        '身高(cm)': 'height_cm',
        '体重(kg)': 'weight_kg',
        '入学日期': 'enrollment_date'
    }

    # Reverse mapping for export
    DB_COLUMN_MAPPING = {v: k for k, v in EXCEL_COLUMN_MAPPING.items()}

    # Expected columns in Excel files
    EXPECTED_COLUMNS = list(EXCEL_COLUMN_MAPPING.keys())

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the import/export service.

        Args:
            session: Optional SQLAlchemy database session.
        """
        super().__init__(session)
        self._student_service = StudentService(session)

    def validate_excel_file(self, file_path: str) -> Tuple[bool, List[str], pd.DataFrame]:
        """
        Validate an Excel file before import.

        Args:
            file_path: Path to the Excel file.

        Returns:
            Tuple[bool, List[str], pd.DataFrame]: (is_valid, errors, DataFrame)

        Raises:
            FileProcessingError: If the file cannot be read.
        """
        errors = []

        # Check if file exists
        if not os.path.exists(file_path):
            raise FileProcessingError(
                message=f"File not found: {file_path}",
                details={"file_path": file_path}
            )

        # Check file extension
        if not file_path.lower().endswith(('.xlsx', '.xls')):
            errors.append(f"Invalid file format. Expected Excel file (.xlsx or .xls), got: {file_path}")
            return False, errors, pd.DataFrame()

        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
        except Exception as e:
            raise FileProcessingError(
                message=f"Failed to read Excel file: {e}",
                details={"file_path": file_path, "error": str(e)}
            ) from e

        # Check for empty file
        if df.empty:
            errors.append("Excel file is empty")
            return False, errors, df

        # Check for required columns (support both Chinese and English column names)
        # First, try to map English columns to Chinese if needed
        df = self._normalize_column_names(df)
        
        # Check that at least the essential columns are present
        essential_columns = ['学生ID', '姓名', '性别', '年级', '身高(cm)', '体重(kg)']
        missing_essential = []
        for col in essential_columns:
            if col not in df.columns:
                missing_essential.append(col)

        if missing_essential:
            errors.append(f"Missing essential columns: {', '.join(missing_essential)}")
            errors.append(f"Expected columns: {', '.join(self.EXPECTED_COLUMNS)}")
            errors.append(f"Found columns: {', '.join(df.columns.tolist())}")

        return len(errors) == 0, errors, df

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to support both Chinese and English column names.
        
        Args:
            df: Input DataFrame.
            
        Returns:
            pd.DataFrame: DataFrame with normalized column names.
        """
        # Create a reverse mapping for English to Chinese column names
        english_to_chinese = {
            'student_id': '学生ID',
            'name': '姓名',
            'gender': '性别',
            'grade': '年级',
            'age': '年龄',
            'height_cm': '身高(cm)',
            'weight_kg': '体重(kg)',
            'enrollment_date': '入学日期'
        }
        
        # Rename columns if they match English names
        column_mapping = {}
        for col in df.columns:
            if col in english_to_chinese:
                column_mapping[col] = english_to_chinese[col]
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        return df

    def preprocess_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Preprocess the DataFrame for database import.

        Args:
            df: Input DataFrame from Excel.

        Returns:
            Tuple[pd.DataFrame, List[Dict[str, Any]]]: (processed DataFrame, errors)
        """
        errors = []
        processed_df = df.copy()

        # Rename columns to match database fields
        processed_df = processed_df.rename(columns=self.EXCEL_COLUMN_MAPPING)

        # Translate gender values (English to Chinese)
        if 'gender' in processed_df.columns:
            gender_translation = {
                'Male': '男',
                'Female': '女',
                'male': '男',
                'female': '女',
                'M': '男',
                'F': '女'
            }
            processed_df['gender'] = processed_df['gender'].apply(
                lambda x: gender_translation.get(x, x) if pd.notna(x) else x
            )

        # Translate grade values (English to Chinese)
        if 'grade' in processed_df.columns:
            grade_translation = {
                'Grade 1': '一年级',
                'Grade 2': '二年级',
                'Grade 3': '三年级',
                'Grade 4': '四年级',
                'Grade 5': '五年级',
                'Grade 6': '六年级',
                'grade 1': '一年级',
                'grade 2': '二年级',
                'grade 3': '三年级',
                'grade 4': '四年级',
                'grade 5': '五年级',
                'grade 6': '六年级'
            }
            processed_df['grade'] = processed_df['grade'].apply(
                lambda x: grade_translation.get(x, x) if pd.notna(x) else x
            )

        # Convert enrollment_date to datetime if present
        if 'enrollment_date' in processed_df.columns:
            try:
                processed_df['enrollment_date'] = pd.to_datetime(
                    processed_df['enrollment_date'],
                    errors='coerce'
                ).dt.date
            except Exception as e:
                errors.append({
                    'row': 'N/A',
                    'column': '入学日期',
                    'error': f"Failed to parse enrollment dates: {e}"
                })

        return processed_df, errors

    def import_from_excel(
        self,
        file_path: str,
        overwrite: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Import data from an Excel file to the database.

        Args:
            file_path: Path to the Excel file.
            overwrite: If True, overwrite existing records (by student_id).
            validate_only: If True, only validate without importing.

        Returns:
            Dict[str, Any]: Import results.

        Raises:
            ImportError: If import fails.
        """
        logger.info(f"Starting import from Excel file: {file_path}")

        # Validate the Excel file
        is_valid, validation_errors, df = self.validate_excel_file(file_path)
        if not is_valid:
            error_msg = "; ".join(validation_errors)
            logger.error(f"Excel validation failed: {error_msg}")
            
            # Handle empty file gracefully (return result instead of raising)
            if "Excel file is empty" in error_msg:
                return {
                    'success': True,
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'errors': validation_errors,
                    'total_records': 0,
                    'message': 'Excel file is empty'
                }
            
            raise ImportError(
                message="Excel file validation failed",
                details={"errors": validation_errors}
            )

        # Preprocess the DataFrame
        processed_df, preprocess_errors = self.preprocess_dataframe(df)
        if preprocess_errors:
            logger.warning(f"Preprocessing warnings: {preprocess_errors}")

        if validate_only:
            return {
                'success': True,
                'message': 'Validation successful',
                'total_records': len(processed_df),
                'preprocess_warnings': preprocess_errors
            }

        # Convert DataFrame to list of dictionaries
        records = processed_df.to_dict('records')

        # Validate each record and check for duplicates
        validated_records = []
        row_errors = []
        duplicates_found = 0

        for i, record in enumerate(records, start=2):  # Excel rows start at 1, header at 1
            try:
                # Clean NaN values
                cleaned_record = {k: v for k, v in record.items() if pd.notna(v)}

                # Validate using student service
                is_valid, errors = self._student_service.validate_student_data(cleaned_record)
                if not is_valid:
                    row_errors.append({
                        'row': i,
                        'record': cleaned_record,
                        'errors': errors
                    })
                    continue

                # Check for existing student with same student_id
                existing = self.dao.student.get_by_student_id(cleaned_record['student_id'])
                if existing:
                    if overwrite:
                        # Update existing record
                        validated_records.append({
                            'action': 'update',
                            'id': existing.id,
                            'data': cleaned_record
                        })
                    else:
                        # Skip duplicate (don't treat as error)
                        duplicates_found += 1
                        continue
                else:
                    validated_records.append({
                        'action': 'create',
                        'data': cleaned_record
                    })

            except Exception as e:
                row_errors.append({
                    'row': i,
                    'record': record,
                    'error': str(e)
                })

        # If there are errors but we have some valid records, continue with valid ones
        # Only raise if all records have errors and no valid records to process
        if row_errors and not validated_records and not overwrite:
            logger.error(f"Found {len(row_errors)} errors during import validation with no valid records")
            raise ImportError(
                message=f"Import validation failed with {len(row_errors)} errors",
                details={
                    'errors': row_errors[:10],  # Show first 10 errors
                    'total_errors': len(row_errors),
                    'duplicates_found': duplicates_found
                }
            )

        # Perform the import
        created_count = 0
        updated_count = 0

        try:
            with self.transaction():
                for record in validated_records:
                    if record['action'] == 'create':
                        self.dao.student.create(**record['data'])
                        created_count += 1
                    elif record['action'] == 'update':
                        self.dao.student.update(record['id'], **record['data'])
                        updated_count += 1

                self.emit_event(
                    EventType.DATA_IMPORTED,
                    data={
                        'file_path': file_path,
                        'created': created_count,
                        'updated': updated_count
                    },
                    source="DataImportExportService.import_from_excel"
                )

        except Exception as e:
            logger.error(f"Database import failed: {e}")
            raise ImportError(
                message="Failed to import data to database",
                details={"error": str(e)}
            ) from e

        result = {
            'success': True,
            'total_records': len(df),
            'created': created_count,
            'updated': updated_count,
            'skipped': len(row_errors) + duplicates_found,
            'errors': row_errors,
            'preprocess_warnings': preprocess_errors,
            'message': f"Import completed: {created_count} created, {updated_count} updated, {len(row_errors) + duplicates_found} skipped"
        }

        logger.info(result['message'])
        return result

    def export_to_excel(
        self,
        file_path: str,
        grade: Optional[str] = None,
        include_headers: bool = True,
        sheet_name: str = "学生数据",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export data from the database to an Excel file.

        Args:
            file_path: Path where the Excel file will be saved.
            grade: Optional grade filter (export only this grade).
            include_headers: Include column headers in the export.
            sheet_name: Name of the Excel sheet.
            filters: Optional dictionary of filters (for backward compatibility).

        Returns:
            Dict[str, Any]: Export results.

        Raises:
            ExportError: If export fails.
        """
        logger.info(f"Starting export to Excel file: {file_path}")

        try:
            # Handle filters parameter for backward compatibility
            if filters and 'grade' in filters:
                grade = filters.get('grade')

            # Get data from database
            if grade:
                students = self.dao.student.get_by_grade(grade)
            else:
                students = self.dao.student.get_all()

            if not students:
                logger.warning("No student data found for export")
                return {
                    'success': True,
                    'message': 'No data to export',
                    'exported_count': 0,
                    'file_path': file_path
                }

            # Convert to DataFrame
            data = []
            for student in students:
                student_dict = student.to_dict()
                # Convert datetime to string
                if student_dict.get('enrollment_date'):
                    student_dict['enrollment_date'] = str(student_dict['enrollment_date'])
                data.append(student_dict)

            df = pd.DataFrame(data)

            # Keep only the columns that should be exported
            export_columns = list(self.DB_COLUMN_MAPPING.keys())
            df = df[export_columns]

            # Rename columns to Chinese for export
            df = df.rename(columns=self.DB_COLUMN_MAPPING)

            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

            # Write to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                    header=include_headers
                )

            self.emit_event(
                EventType.DATA_EXPORTED,
                data={
                    'file_path': file_path,
                    'exported_count': len(students),
                    'grade': grade
                },
                source="DataImportExportService.export_to_excel"
            )

            result = {
                'success': True,
                'exported_count': len(students),
                'exported': len(students),  # For backward compatibility
                'file_path': file_path,
                'grade': grade,
                'message': f"Export completed: {len(students)} records exported to {file_path}"
            }

            logger.info(result['message'])
            return result

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ExportError(
                message="Failed to export data to Excel",
                details={"error": str(e), "file_path": file_path}
            ) from e

    def export_statistics_to_excel(
        self,
        file_path: str,
        include_grade_stats: bool = True,
        include_gender_stats: bool = True,
        include_bmi_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Export statistics to an Excel file with multiple sheets.

        Args:
            file_path: Path where the Excel file will be saved.
            include_grade_stats: Include grade-wise statistics.
            include_gender_stats: Include gender-wise statistics.
            include_bmi_stats: Include BMI statistics.

        Returns:
            Dict[str, Any]: Export results.
        """
        from app.service.student_service import StudentService

        student_service = StudentService(self.session)
        sheets = {}

        # Basic statistics
        basic_stats = student_service.calculate_basic_statistics()
        sheets['基本统计'] = pd.DataFrame([basic_stats])

        # Grade statistics
        if include_grade_stats:
            grade_stats_list = []
            for grade in StudentService.GRADE_ORDER:
                grade_stats = student_service.calculate_grade_statistics(grade)
                grade_stats_list.append(grade_stats)
            sheets['年级统计'] = pd.DataFrame(grade_stats_list)

        # Gender statistics
        if include_gender_stats:
            gender_stats = student_service.calculate_gender_statistics()
            # Flatten the nested structure for Excel
            flattened = {
                '性别': ['男', '女'],
                '人数': [gender_stats['male']['count'], gender_stats['female']['count']],
                '平均身高': [gender_stats['male']['avg_height'], gender_stats['female']['avg_height']],
                '平均体重': [gender_stats['male']['avg_weight'], gender_stats['female']['avg_weight']]
            }
            sheets['性别统计'] = pd.DataFrame(flattened)

        # BMI statistics
        if include_bmi_stats:
            bmi_stats = student_service.calculate_bmi_distribution()
            sheets['BMI统计'] = pd.DataFrame([bmi_stats['categories']])

        try:
            # Write all sheets to Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            result = {
                'success': True,
                'sheets_exported': list(sheets.keys()),
                'statistics_sheets': list(sheets.keys()),  # For backward compatibility
                'exported': len(sheets),  # For backward compatibility
                'file_path': file_path,
                'message': f"Statistics exported successfully to {file_path}"
            }

            logger.info(result['message'])
            return result

        except Exception as e:
            logger.error(f"Statistics export failed: {e}")
            raise ExportError(
                message="Failed to export statistics to Excel",
                details={"error": str(e), "file_path": file_path}
            ) from e

    def export_statistics_report(
        self,
        file_path: str,
        include_grade_stats: bool = True,
        include_gender_stats: bool = True,
        include_bmi_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Alias for export_statistics_to_excel for backward compatibility.
        """
        return self.export_statistics_to_excel(
            file_path=file_path,
            include_grade_stats=include_grade_stats,
            include_gender_stats=include_gender_stats,
            include_bmi_stats=include_bmi_stats
        )

    def sync_excel_to_database(
        self,
        file_path: str,
        sync_mode: str = 'upsert'  # 'upsert', 'append', or 'replace'
    ) -> Dict[str, Any]:
        """
        Synchronize an Excel file with the database.

        Args:
            file_path: Path to the Excel file.
            sync_mode: Synchronization mode:
                - 'upsert': Update existing records, insert new ones
                - 'append': Only insert new records, skip duplicates
                - 'replace': Clear the table and insert all records

        Returns:
            Dict[str, Any]: Synchronization results.
        """
        if sync_mode not in ['upsert', 'append', 'replace']:
            raise ValueError(
                f"Invalid sync_mode: {sync_mode}. Must be 'upsert', 'append', or 'replace'."
            )

        logger.info(f"Starting Excel to database sync with mode: {sync_mode}")

        if sync_mode == 'replace':
            # Clear the students table first
            try:
                with self.transaction():
                    # Note: This is a simplified approach. In production,
                    # you might want to use TRUNCATE or batch delete.
                    students = self.dao.student.get_all()
                    for student in students:
                        self.dao.student.delete(student.id, commit=False)
                    logger.info(f"Cleared {len(students)} existing student records")
            except Exception as e:
                logger.error(f"Failed to clear students table: {e}")
                raise ImportError(
                    message="Failed to clear students table for replace sync",
                    details={"error": str(e)}
                ) from e

        # Import with appropriate settings
        return self.import_from_excel(
            file_path,
            overwrite=(sync_mode == 'upsert' or sync_mode == 'replace')
        )
