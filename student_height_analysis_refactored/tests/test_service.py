"""
业务逻辑层单元测试
"""
import pytest
from datetime import date
from pathlib import Path
import pandas as pd

from core.service import StudentService, DataAnalysisService, DataImportExportService
from core.dao import StudentDAO, HeightRecordDAO


class TestStudentService:
    """学生服务测试类"""
    
    def test_create_student(self, test_db):
        """测试创建学生"""
        service = StudentService()
        service.student_dao = StudentDAO(session=test_db.get_session())
        service.record_dao = HeightRecordDAO(session=test_db.get_session())
        
        student = service.create_student(
            student_number='10001',
            name='张三',
            gender='男',
            grade='三年级',
            age=9,
            enrollment_date=date(2022, 9, 1)
        )
        
        assert student.id is not None
        assert student.student_id == '10001'
    
    def test_add_height_record(self, test_db):
        """测试添加身高记录"""
        student_service = StudentService()
        student_service.student_dao = StudentDAO(session=test_db.get_session())
        student_service.record_dao = HeightRecordDAO(session=test_db.get_session())
        
        student = student_service.create_student(
            student_number='10001',
            name='张三',
            gender='男',
            grade='三年级',
            age=9,
            enrollment_date=date(2022, 9, 1)
        )
        
        record = student_service.add_height_record(
            student_id=student.id,
            record_date=date.today(),
            height=130.5,
            weight=28.0
        )
        
        assert record.id is not None
        assert record.height == 130.5
        assert record.bmi > 0
        assert record.bmi_category in ['偏瘦', '正常', '超重', '肥胖']


class TestDataAnalysisService:
    """数据分析服务测试类"""
    
    def test_get_basic_statistics(self, test_db):
        """测试获取基础统计"""
        student_dao = StudentDAO(session=test_db.get_session())
        record_dao = HeightRecordDAO(session=test_db.get_session())
        
        for i in range(10):
            student = student_dao.create({
                'student_id': f'1000{i}',
                'name': f'学生{i}',
                'gender': '男' if i % 2 == 0 else '女',
                'grade': '三年级',
                'age': 9,
                'enrollment_date': date.today()
            })
            
            record_dao.create({
                'student_id': student.id,
                'record_date': date.today(),
                'height': 130.0 + i,
                'weight': 28.0 + i * 0.5,
                'age_at_record': 9,
                'grade_at_record': '三年级'
            })
        
        service = DataAnalysisService()
        service.student_dao = student_dao
        service.record_dao = record_dao
        
        stats = service.get_basic_statistics()
        
        assert stats['total_students'] == 10
        assert stats['total_records'] == 10
        assert stats['avg_height'] > 0
    
    def test_get_grade_statistics(self, test_db):
        """测试获取年级统计"""
        student_dao = StudentDAO(session=test_db.get_session())
        record_dao = HeightRecordDAO(session=test_db.get_session())
        
        for i in range(6):
            student = student_dao.create({
                'student_id': f'1000{i}',
                'name': f'学生{i}',
                'gender': '男',
                'grade': f'{i+1}年级',
                'age': 6 + i,
                'enrollment_date': date.today()
            })
            
            record_dao.create({
                'student_id': student.id,
                'record_date': date.today(),
                'height': 120.0 + i * 5,
                'weight': 25.0 + i * 2,
                'age_at_record': 6 + i,
                'grade_at_record': f'{i+1}年级'
            })
        
        service = DataAnalysisService()
        service.student_dao = student_dao
        service.record_dao = record_dao
        
        df = service.get_grade_statistics()
        
        assert not df.empty
        assert '平均身高' in df.columns


class TestDataImportExportService:
    """数据导入导出服务测试类"""
    
    def test_export_to_excel(self, test_db, tmp_path):
        """测试导出到Excel"""
        student_dao = StudentDAO(session=test_db.get_session())
        record_dao = HeightRecordDAO(session=test_db.get_session())
        
        student = student_dao.create({
            'student_id': '10001',
            'name': '张三',
            'gender': '男',
            'grade': '三年级',
            'age': 9,
            'enrollment_date': date.today()
        })
        
        record_dao.create({
            'student_id': student.id,
            'record_date': date.today(),
            'height': 130.5,
            'weight': 28.0,
            'age_at_record': 9,
            'grade_at_record': '三年级'
        })
        
        service = DataImportExportService()
        service.student_dao = student_dao
        service.record_dao = record_dao
        
        output_path = str(tmp_path / 'test_export.xlsx')
        result = service.export_to_excel(output_path)
        
        assert Path(result).exists()
        
        df = pd.read_excel(result)
        assert len(df) == 1
        assert df.iloc[0]['姓名'] == '张三'
