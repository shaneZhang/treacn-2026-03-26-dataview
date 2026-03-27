"""
业务逻辑层（Service）

实现数据分析、数据导入导出等业务逻辑
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
import pandas as pd
import numpy as np
from pathlib import Path

from models import Student, HeightRecord, StandardHeight
from core.dao import StudentDAO, HeightRecordDAO, ClassDAO, StandardHeightDAO
from core.database import DatabaseFactory
from core.observer import EventManager, EventType
from utils import (
    AnalysisException,
    ImportExportException,
    FileNotFoundException,
    InvalidDataException,
    get_logger
)
from config import Config


class StudentService:
    """
    学生业务逻辑服务
    
    提供学生相关的业务逻辑处理
    
    Example:
        >>> service = StudentService()
        >>> student = service.create_student(student_data)
    """
    
    def __init__(self) -> None:
        """初始化学生服务"""
        self.logger = get_logger(__name__)
        self.student_dao = StudentDAO()
        self.record_dao = HeightRecordDAO()
        self.event_manager = EventManager.get_instance()
    
    def create_student(
        self,
        student_number: str,
        name: str,
        gender: str,
        grade: str,
        age: int,
        enrollment_date: date,
        class_id: Optional[int] = None
    ) -> Student:
        """
        创建学生
        
        Args:
            student_number: 学号
            name: 姓名
            gender: 性别
            grade: 年级
            age: 年龄
            enrollment_date: 入学日期
            class_id: 班级ID
        
        Returns:
            Student: 学生对象
        
        Example:
            >>> student = service.create_student(
            ...     '10001', '张三', '男', '三年级', 9, date(2022, 9, 1)
            ... )
        """
        student_data = {
            'student_id': student_number,
            'name': name,
            'gender': gender,
            'grade': grade,
            'age': age,
            'enrollment_date': enrollment_date,
            'class_id': class_id
        }
        
        return self.student_dao.create(student_data)
    
    def get_student(self, student_id: int) -> Dict[str, Any]:
        """
        获取学生信息（包含最新身高记录）
        
        Args:
            student_id: 学生ID
        
        Returns:
            Dict[str, Any]: 学生信息字典
        
        Example:
            >>> info = service.get_student(1)
        """
        student = self.student_dao.get_by_id(student_id)
        latest_record = self.record_dao.get_latest_by_student(student_id)
        
        result = student.to_dict()
        if latest_record:
            result['latest_height'] = latest_record.height
            result['latest_weight'] = latest_record.weight
            result['latest_bmi'] = latest_record.bmi
            result['bmi_category'] = latest_record.bmi_category
            result['record_date'] = latest_record.record_date.isoformat()
        
        return result
    
    def add_height_record(
        self,
        student_id: int,
        record_date: date,
        height: float,
        weight: float,
        notes: Optional[str] = None
    ) -> HeightRecord:
        """
        为学生添加身高记录
        
        Args:
            student_id: 学生ID
            record_date: 记录日期
            height: 身高(cm)
            weight: 体重(kg)
            notes: 备注
        
        Returns:
            HeightRecord: 身高记录对象
        
        Example:
            >>> record = service.add_height_record(
            ...     1, date.today(), 130.5, 28.0
            ... )
        """
        student = self.student_dao.get_by_id(student_id)
        
        record_data = {
            'student_id': student_id,
            'record_date': record_date,
            'height': height,
            'weight': weight,
            'age_at_record': student.age,
            'grade_at_record': student.grade,
            'notes': notes
        }
        
        return self.record_dao.create(record_data)
    
    def get_students_by_grade(self, grade: str) -> List[Dict[str, Any]]:
        """
        获取指定年级的所有学生
        
        Args:
            grade: 年级
        
        Returns:
            List[Dict[str, Any]]: 学生信息列表
        
        Example:
            >>> students = service.get_students_by_grade('三年级')
        """
        students = self.student_dao.get_all(grade=grade, limit=1000)
        return [s.to_dict() for s in students]


class DataAnalysisService:
    """
    数据分析业务逻辑服务
    
    提供数据分析相关的业务逻辑处理
    
    Example:
        >>> service = DataAnalysisService()
        >>> stats = service.get_basic_statistics()
    """
    
    GRADE_ORDER = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
    
    def __init__(self) -> None:
        """初始化数据分析服务"""
        self.logger = get_logger(__name__)
        self.student_dao = StudentDAO()
        self.record_dao = HeightRecordDAO()
        self.standard_dao = StandardHeightDAO()
        self.event_manager = EventManager.get_instance()
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """
        获取基础统计数据
        
        Returns:
            Dict[str, Any]: 基础统计数据字典
        
        Example:
            >>> stats = service.get_basic_statistics()
        """
        try:
            with DatabaseFactory.get_instance().session_scope() as session:
                total_count = session.query(Student).count()
                male_count = session.query(Student).filter(
                    Student.gender == '男'
                ).count()
                female_count = session.query(Student).filter(
                    Student.gender == '女'
                ).count()
                
                records = session.query(HeightRecord).all()
                
                if records:
                    heights = [r.height for r in records]
                    weights = [r.weight for r in records]
                    
                    stats = {
                        'total_students': total_count,
                        'male_count': male_count,
                        'female_count': female_count,
                        'total_records': len(records),
                        'avg_height': round(np.mean(heights), 2),
                        'std_height': round(np.std(heights), 2),
                        'min_height': round(min(heights), 1),
                        'max_height': round(max(heights), 1),
                        'median_height': round(np.median(heights), 1),
                        'avg_weight': round(np.mean(weights), 2),
                        'std_weight': round(np.std(weights), 2),
                    }
                else:
                    stats = {
                        'total_students': total_count,
                        'male_count': male_count,
                        'female_count': female_count,
                        'total_records': 0,
                        'avg_height': 0,
                        'std_height': 0,
                        'min_height': 0,
                        'max_height': 0,
                        'median_height': 0,
                        'avg_weight': 0,
                        'std_weight': 0,
                    }
                
                self.event_manager.emit(
                    EventType.ANALYSIS_COMPLETED,
                    {'analysis_type': 'basic_statistics'},
                    source='DataAnalysisService'
                )
                
                return stats
                
        except Exception as e:
            self.logger.error(f"获取基础统计数据失败: {e}")
            raise AnalysisException(f"获取基础统计数据失败: {e}")
    
    def get_grade_statistics(self) -> pd.DataFrame:
        """
        获取年级统计数据
        
        Returns:
            pd.DataFrame: 年级统计数据
        
        Example:
            >>> df = service.get_grade_statistics()
        """
        try:
            with DatabaseFactory.get_instance().session_scope() as session:
                records = session.query(HeightRecord).all()
                
                if not records:
                    return pd.DataFrame()
                
                data = [{
                    'grade': r.grade_at_record,
                    'height': r.height,
                    'weight': r.weight
                } for r in records]
                
                df = pd.DataFrame(data)
                
                grade_stats = df.groupby('grade').agg({
                    'height': ['count', 'mean', 'std', 'min', 'max'],
                    'weight': ['mean', 'std']
                }).round(2)
                
                grade_stats.columns = [
                    '人数', '平均身高', '身高标准差', '最矮身高', '最高身高',
                    '平均体重', '体重标准差'
                ]
                
                grade_stats = grade_stats.reindex(self.GRADE_ORDER)
                
                return grade_stats
                
        except Exception as e:
            self.logger.error(f"获取年级统计数据失败: {e}")
            raise AnalysisException(f"获取年级统计数据失败: {e}")
    
    def get_gender_statistics(self) -> pd.DataFrame:
        """
        获取性别统计数据
        
        Returns:
            pd.DataFrame: 性别统计数据
        
        Example:
            >>> df = service.get_gender_statistics()
        """
        try:
            with DatabaseFactory.get_instance().session_scope() as session:
                records = session.query(HeightRecord).all()
                
                if not records:
                    return pd.DataFrame()
                
                data = [{
                    'grade': r.grade_at_record,
                    'gender': session.query(Student).get(r.student_id).gender,
                    'height': r.height
                } for r in records]
                
                df = pd.DataFrame(data)
                
                gender_stats = df.groupby(['grade', 'gender'])['height'].agg([
                    'count', 'mean', 'std'
                ]).round(2)
                
                gender_stats.columns = ['人数', '平均身高', '标准差']
                
                return gender_stats
                
        except Exception as e:
            self.logger.error(f"获取性别统计数据失败: {e}")
            raise AnalysisException(f"获取性别统计数据失败: {e}")
    
    def get_growth_analysis(self) -> pd.DataFrame:
        """
        获取生长趋势分析
        
        Returns:
            pd.DataFrame: 生长趋势数据
        
        Example:
            >>> df = service.get_growth_analysis()
        """
        try:
            grade_stats = self.get_grade_statistics()
            
            if grade_stats.empty:
                return pd.DataFrame()
            
            growth_data = []
            for i in range(1, len(self.GRADE_ORDER)):
                prev_grade = self.GRADE_ORDER[i-1]
                curr_grade = self.GRADE_ORDER[i]
                
                if prev_grade in grade_stats.index and curr_grade in grade_stats.index:
                    prev_height = grade_stats.loc[prev_grade, '平均身高']
                    curr_height = grade_stats.loc[curr_grade, '平均身高']
                    growth = curr_height - prev_height
                    growth_rate = (growth / prev_height * 100) if prev_height > 0 else 0
                    
                    growth_data.append({
                        '年级段': f"{prev_grade}到{curr_grade}",
                        '身高增长(cm)': round(growth, 2),
                        '增长率(%)': round(growth_rate, 2)
                    })
            
            return pd.DataFrame(growth_data)
            
        except Exception as e:
            self.logger.error(f"获取生长趋势分析失败: {e}")
            raise AnalysisException(f"获取生长趋势分析失败: {e}")
    
    def get_percentile_analysis(self) -> pd.DataFrame:
        """
        获取百分位数分析
        
        Returns:
            pd.DataFrame: 百分位数数据
        
        Example:
            >>> df = service.get_percentile_analysis()
        """
        try:
            with DatabaseFactory.get_instance().session_scope() as session:
                records = session.query(HeightRecord).all()
                
                if not records:
                    return pd.DataFrame()
                
                data = [{
                    'grade': r.grade_at_record,
                    'height': r.height
                } for r in records]
                
                df = pd.DataFrame(data)
                
                percentiles = [3, 10, 25, 50, 75, 90, 97]
                percentile_data = []
                
                for grade in self.GRADE_ORDER:
                    grade_data = df[df['grade'] == grade]['height']
                    if len(grade_data) > 0:
                        row = {'年级': grade}
                        for p in percentiles:
                            row[f'P{p}'] = round(np.percentile(grade_data, p), 1)
                        percentile_data.append(row)
                
                return pd.DataFrame(percentile_data)
                
        except Exception as e:
            self.logger.error(f"获取百分位数分析失败: {e}")
            raise AnalysisException(f"获取百分位数分析失败: {e}")
    
    def get_bmi_statistics(self) -> Tuple[Dict[str, int], pd.DataFrame]:
        """
        获取BMI统计数据
        
        Returns:
            Tuple[Dict[str, int], pd.DataFrame]: BMI分布和按年级的BMI分类
        
        Example:
            >>> bmi_dist, bmi_by_grade = service.get_bmi_statistics()
        """
        try:
            with DatabaseFactory.get_instance().session_scope() as session:
                records = session.query(HeightRecord).all()
                
                if not records:
                    return {}, pd.DataFrame()
                
                data = [{
                    'grade': r.grade_at_record,
                    'bmi_category': r.bmi_category
                } for r in records]
                
                df = pd.DataFrame(data)
                
                bmi_dist = df['bmi_category'].value_counts().to_dict()
                
                bmi_by_grade = pd.crosstab(
                    df['grade'], 
                    df['bmi_category']
                ).reindex(self.GRADE_ORDER)
                
                return bmi_dist, bmi_by_grade
                
        except Exception as e:
            self.logger.error(f"获取BMI统计数据失败: {e}")
            raise AnalysisException(f"获取BMI统计数据失败: {e}")
    
    def compare_with_standard(self) -> pd.DataFrame:
        """
        与标准身高对比
        
        Returns:
            pd.DataFrame: 对比数据
        
        Example:
            >>> df = service.compare_with_standard()
        """
        try:
            grade_stats = self.get_grade_statistics()
            standards = self.standard_dao.get_all()
            
            if grade_stats.empty or not standards:
                return pd.DataFrame()
            
            standard_dict = {
                (s.grade, s.gender): s.standard_height 
                for s in standards
            }
            
            comparison_data = []
            for grade in self.GRADE_ORDER:
                if grade in grade_stats.index:
                    actual_height = grade_stats.loc[grade, '平均身高']
                    
                    male_std = standard_dict.get((grade, '男'), 0)
                    female_std = standard_dict.get((grade, '女'), 0)
                    avg_std = (male_std + female_std) / 2
                    
                    diff = actual_height - avg_std
                    diff_pct = (diff / avg_std * 100) if avg_std > 0 else 0
                    
                    comparison_data.append({
                        '年级': grade,
                        '实际平均身高(cm)': round(actual_height, 1),
                        '标准身高(cm)': round(avg_std, 1),
                        '差异(cm)': round(diff, 1),
                        '差异率(%)': round(diff_pct, 2)
                    })
            
            return pd.DataFrame(comparison_data)
            
        except Exception as e:
            self.logger.error(f"与标准身高对比失败: {e}")
            raise AnalysisException(f"与标准身高对比失败: {e}")


class DataImportExportService:
    """
    数据导入导出业务逻辑服务
    
    提供数据导入导出相关的业务逻辑处理
    
    Example:
        >>> service = DataImportExportService()
        >>> service.import_from_excel('data.xlsx')
    """
    
    def __init__(self) -> None:
        """初始化数据导入导出服务"""
        self.logger = get_logger(__name__)
        self.student_dao = StudentDAO()
        self.record_dao = HeightRecordDAO()
        self.event_manager = EventManager.get_instance()
        self.config = Config.get_instance()
    
    def import_from_excel(
        self, 
        file_path: str,
        create_records: bool = True
    ) -> Dict[str, Any]:
        """
        从Excel导入数据
        
        Args:
            file_path: Excel文件路径
            create_records: 是否自动创建身高记录
        
        Returns:
            Dict[str, Any]: 导入结果统计
        
        Raises:
            FileNotFoundException: 文件不存在
            ImportExportException: 导入失败
        
        Example:
            >>> result = service.import_from_excel('students.xlsx')
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundException(f"文件不存在: {file_path}")
            
            df = pd.read_excel(file_path)
            
            required_columns = ['学生ID', '姓名', '性别', '年级', '年龄', '身高(cm)', '体重(kg)', '入学日期']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise InvalidDataException(
                    f"Excel文件缺少必需列: {', '.join(missing_columns)}"
                )
            
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    student_data = {
                        'student_id': str(row['学生ID']),
                        'name': str(row['姓名']),
                        'gender': str(row['性别']),
                        'grade': str(row['年级']),
                        'age': int(row['年龄']),
                        'enrollment_date': pd.to_datetime(row['入学日期']).date()
                    }
                    
                    student = self.student_dao.create(student_data)
                    
                    if create_records:
                        record_data = {
                            'student_id': student.id,
                            'record_date': date.today(),
                            'height': float(row['身高(cm)']),
                            'weight': float(row['体重(kg)']),
                            'age_at_record': student.age,
                            'grade_at_record': student.grade
                        }
                        self.record_dao.create(record_data)
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{idx+1}行: {str(e)}")
                    self.logger.warning(f"导入第{idx+1}行失败: {e}")
            
            result = {
                'total': len(df),
                'success': success_count,
                'failed': error_count,
                'errors': errors[:10]
            }
            
            self.event_manager.emit(
                EventType.DATA_IMPORTED,
                result,
                source='DataImportExportService'
            )
            
            self.logger.info(
                f"数据导入完成: 成功{success_count}条, 失败{error_count}条"
            )
            
            return result
            
        except (FileNotFoundException, InvalidDataException):
            raise
        except Exception as e:
            self.logger.error(f"从Excel导入数据失败: {e}")
            raise ImportExportException(f"从Excel导入数据失败: {e}")
    
    def export_to_excel(
        self,
        output_path: str,
        include_records: bool = True
    ) -> str:
        """
        导出数据到Excel
        
        Args:
            output_path: 输出文件路径
            include_records: 是否包含身高记录
        
        Returns:
            str: 导出文件路径
        
        Raises:
            ImportExportException: 导出失败
        
        Example:
            >>> path = service.export_to_excel('output.xlsx')
        """
        try:
            with DatabaseFactory.get_instance().session_scope() as session:
                students = session.query(Student).all()
                
                student_data = []
                for student in students:
                    row = {
                        '学生ID': student.student_id,
                        '姓名': student.name,
                        '性别': student.gender,
                        '年级': student.grade,
                        '年龄': student.age,
                        '入学日期': student.enrollment_date
                    }
                    
                    if include_records and student.height_records:
                        latest = student.height_records[0]
                        row['身高(cm)'] = latest.height
                        row['体重(kg)'] = latest.weight
                        row['BMI'] = latest.bmi
                        row['BMI分类'] = latest.bmi_category
                    
                    student_data.append(row)
                
                df = pd.DataFrame(student_data)
                
                output_dir = Path(output_path).parent
                output_dir.mkdir(parents=True, exist_ok=True)
                
                df.to_excel(output_path, index=False, engine='openpyxl')
                
                self.event_manager.emit(
                    EventType.DATA_EXPORTED,
                    {'file_path': output_path, 'count': len(df)},
                    source='DataImportExportService'
                )
                
                self.logger.info(f"数据导出成功: {output_path}, 共{len(df)}条记录")
                
                return output_path
                
        except Exception as e:
            self.logger.error(f"导出数据到Excel失败: {e}")
            raise ImportExportException(f"导出数据到Excel失败: {e}")
    
    def export_statistics_report(
        self,
        output_path: str
    ) -> str:
        """
        导出统计分析报告
        
        Args:
            output_path: 输出文件路径
        
        Returns:
            str: 导出文件路径
        
        Example:
            >>> path = service.export_statistics_report('report.xlsx')
        """
        try:
            analysis_service = DataAnalysisService()
            
            basic_stats = analysis_service.get_basic_statistics()
            grade_stats = analysis_service.get_grade_statistics()
            growth_analysis = analysis_service.get_growth_analysis()
            percentile_analysis = analysis_service.get_percentile_analysis()
            bmi_dist, bmi_by_grade = analysis_service.get_bmi_statistics()
            
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                pd.DataFrame([basic_stats]).to_excel(
                    writer, sheet_name='基础统计', index=False
                )
                
                if not grade_stats.empty:
                    grade_stats.to_excel(writer, sheet_name='年级统计')
                
                if not growth_analysis.empty:
                    growth_analysis.to_excel(
                        writer, sheet_name='生长趋势', index=False
                    )
                
                if not percentile_analysis.empty:
                    percentile_analysis.to_excel(
                        writer, sheet_name='百分位数', index=False
                    )
                
                if not bmi_by_grade.empty:
                    bmi_by_grade.to_excel(writer, sheet_name='BMI统计')
            
            self.logger.info(f"统计分析报告导出成功: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"导出统计分析报告失败: {e}")
            raise ImportExportException(f"导出统计分析报告失败: {e}")
