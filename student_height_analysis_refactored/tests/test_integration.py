"""
集成测试
"""
import pytest
from datetime import date
from pathlib import Path

from core.database import DatabaseFactory
from core.dao import StudentDAO, HeightRecordDAO
from core.service import StudentService, DataAnalysisService
from utils import DataGenerator


class TestIntegration:
    """集成测试类"""
    
    def test_full_workflow(self, test_db):
        """测试完整工作流程"""
        student_dao = StudentDAO(session=test_db.get_session())
        record_dao = HeightRecordDAO(session=test_db.get_session())
        
        student = student_dao.create({
            'student_id': '10001',
            'name': '张三',
            'gender': '男',
            'grade': '三年级',
            'age': 9,
            'enrollment_date': date(2022, 9, 1)
        })
        
        record = record_dao.create({
            'student_id': student.id,
            'record_date': date.today(),
            'height': 130.5,
            'weight': 28.0,
            'age_at_record': 9,
            'grade_at_record': '三年级'
        })
        
        found_student = student_dao.get_by_id(student.id)
        assert found_student.name == '张三'
        
        records = record_dao.get_by_student_id(student.id)
        assert len(records) == 1
        assert records[0].height == 130.5
        
        student_dao.update(student.id, {'age': 10, 'grade': '四年级'})
        updated = student_dao.get_by_id(student.id)
        assert updated.age == 10
        
        student_dao.delete(student.id)
        
        with pytest.raises(Exception):
            student_dao.get_by_id(student.id)
    
    def test_data_generator_integration(self, test_db):
        """测试数据生成器集成"""
        generator = DataGenerator(random_seed=42)
        
        generator.generate_standard_heights()
        
        count = generator.generate_and_save(n=10)
        
        assert count == 10
        
        student_dao = StudentDAO(session=test_db.get_session())
        students = student_dao.get_all(limit=20)
        
        assert len(students) == 10
    
    def test_analysis_integration(self, test_db):
        """测试数据分析集成"""
        generator = DataGenerator(random_seed=42)
        generator.generate_standard_heights()
        generator.generate_and_save(n=100)
        
        analysis_service = DataAnalysisService()
        
        basic_stats = analysis_service.get_basic_statistics()
        assert basic_stats['total_students'] == 100
        assert basic_stats['total_records'] == 100
        
        grade_stats = analysis_service.get_grade_statistics()
        assert not grade_stats.empty
        
        growth_analysis = analysis_service.get_growth_analysis()
        assert not growth_analysis.empty
        
        percentile_analysis = analysis_service.get_percentile_analysis()
        assert not percentile_analysis.empty
        
        bmi_dist, bmi_by_grade = analysis_service.get_bmi_statistics()
        assert len(bmi_dist) > 0
        assert not bmi_by_grade.empty
    
    def test_observer_pattern_integration(self, test_db):
        """测试观察者模式集成"""
        from core.observer import (
            EventManager, LogObserver, CacheObserver, EventType
        )
        
        event_manager = EventManager.get_instance()
        
        log_observer = LogObserver()
        cache_observer = CacheObserver()
        
        event_manager.attach(log_observer)
        event_manager.attach(cache_observer)
        
        student_dao = StudentDAO(session=test_db.get_session())
        student = student_dao.create({
            'student_id': '10001',
            'name': '张三',
            'gender': '男',
            'grade': '三年级',
            'age': 9,
            'enrollment_date': date.today()
        })
        
        event_manager.emit(
            EventType.STUDENT_CREATED,
            {'student_id': student.id},
            source='test'
        )
        
        event_manager.detach(log_observer)
        event_manager.detach(cache_observer)
        
        EventManager.reset()
