"""
服务层单元测试
"""

import pytest
import pandas as pd
from src.service.data_generator import DataGeneratorService
from src.service.analysis_service import AnalysisService


class TestDataGeneratorService:
    """测试数据生成服务"""

    def test_generate_name(self):
        """测试生成姓名"""
        service = DataGeneratorService()
        name = service._generate_name()

        assert len(name) >= 2
        assert isinstance(name, str)

    def test_generate_student_data(self):
        """测试生成学生数据"""
        service = DataGeneratorService()
        data = service.generate_student_data(n=10)

        assert len(data) == 10
        for student in data:
            assert 'student_id' in student
            assert 'name' in student
            assert 'gender' in student
            assert 'grade' in student
            assert 'height' in student
            assert 'weight' in student
            assert 'bmi' in student

    def test_calculate_bmi(self):
        """测试BMI计算"""
        service = DataGeneratorService()

        # 正常BMI
        bmi, category = service._calculate_bmi(120, 22)
        assert bmi > 0
        assert category in ['偏瘦', '正常', '超重', '肥胖']

        # 边界情况
        bmi, category = service._calculate_bmi(0, 22)
        assert bmi == 0.0


class TestAnalysisService:
    """测试分析服务"""

    def test_get_basic_statistics(self, db_session, sample_student_data):
        """测试基础统计"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        for data in sample_student_data:
            dao.create(data)

        service = AnalysisService(session=db_session)
        stats = service.get_basic_statistics()

        assert 'total_count' in stats
        assert stats['total_count'] == 3
        assert 'avg_height' in stats

    def test_get_grade_statistics(self, db_session, sample_student_data):
        """测试年级统计"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        for data in sample_student_data:
            dao.create(data)

        service = AnalysisService(session=db_session)
        stats = service.get_grade_statistics()

        assert len(stats) > 0
        assert 'grade' in stats[0]
        assert 'avg_height' in stats[0]

    def test_get_height_distribution(self, db_session, sample_student_data):
        """测试身高分布"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        for data in sample_student_data:
            dao.create(data)

        service = AnalysisService(session=db_session)
        distribution = service.get_height_distribution()

        assert isinstance(distribution, dict)
        # 总数量应该等于学生数量
        total = sum(distribution.values())
        assert total == 3

    def test_compare_with_standard(self, db_session, sample_student_data):
        """测试与标准身高对比"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        for data in sample_student_data:
            dao.create(data)

        service = AnalysisService(session=db_session)
        comparison = service.compare_with_standard()

        assert len(comparison) > 0
        assert 'actual_height' in comparison[0]
        assert 'standard_height' in comparison[0]
        assert 'difference' in comparison[0]

    def test_generate_report(self, db_session, sample_student_data):
        """测试生成报告"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)
        for data in sample_student_data:
            dao.create(data)

        service = AnalysisService(session=db_session)
        report = service.generate_report()

        assert isinstance(report, str)
        assert '小学生身高数据分析报告' in report
        assert '基础统计' in report
