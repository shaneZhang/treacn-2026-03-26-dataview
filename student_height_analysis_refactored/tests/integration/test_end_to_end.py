"""
端到端集成测试
"""

import os
import pytest

from src.service.data_generator import DataGeneratorService
from src.service.analysis_service import AnalysisService
from src.visualization.visualizer import HeightVisualizer


class TestEndToEndWorkflow:
    """测试端到端工作流"""

    def test_full_pipeline(self, db_session, tmp_path):
        """测试完整流程"""
        # 设置输出目录
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # 1. 生成数据
        generator = DataGeneratorService(session=db_session)
        student_data = generator.generate_student_data(n=50)
        assert len(student_data) == 50

        # 2. 导入数据
        from src.dao.student_dao import StudentDAO
        dao = StudentDAO(db_session)
        entities = dao.create_many(student_data)
        assert len(entities) == 50

        # 3. 数据分析
        analysis_service = AnalysisService(session=db_session)
        stats = analysis_service.get_basic_statistics()
        assert stats['total_count'] == 50

        # 4. 生成图表
        visualizer = HeightVisualizer(output_dir=str(output_dir), session=db_session)
        chart_files = visualizer.generate_all_charts()
        assert len(chart_files) == 8

        # 验证图表文件存在
        for filepath in chart_files:
            assert os.path.exists(filepath)

    def test_data_import_export(self, db_session, tmp_path):
        """测试数据导入导出"""
        # 生成测试数据
        generator = DataGeneratorService(session=db_session)
        student_data = generator.generate_student_data(n=20)

        from src.dao.student_dao import StudentDAO
        dao = StudentDAO(db_session)
        dao.create_many(student_data)

        # 导出到Excel
        export_path = tmp_path / "export.xlsx"
        export_file = generator.export_to_excel(str(export_path))
        assert os.path.exists(export_file)

        # 验证导出文件
        import pandas as pd
        df = pd.read_excel(export_file)
        assert len(df) == 20


class TestDataConsistency:
    """测试数据一致性"""

    def test_bmi_calculation_consistency(self, db_session):
        """测试BMI计算一致性"""
        from src.dao.student_dao import StudentDAO

        dao = StudentDAO(db_session)

        # 创建学生
        student_data = {
            'student_id': 'BMI001',
            'name': 'BMI测试',
            'gender': '男',
            'grade': '一年级',
            'age': 7,
            'height': 120.0,
            'weight': 24.0,
            'bmi': 0,  # 稍后计算
            'bmi_category': ''
        }

        # 手动计算BMI
        expected_bmi = round(24.0 / ((120.0 / 100) ** 2), 2)

        student_data['bmi'] = expected_bmi
        if expected_bmi < 14:
            student_data['bmi_category'] = '偏瘦'
        elif expected_bmi < 18:
            student_data['bmi_category'] = '正常'
        elif expected_bmi < 21:
            student_data['bmi_category'] = '超重'
        else:
            student_data['bmi_category'] = '肥胖'

        created = dao.create(student_data)

        # 验证BMI
        assert created.bmi == expected_bmi

    def test_statistics_accuracy(self, db_session):
        """测试统计准确性"""
        from src.dao.student_dao import StudentDAO
        from src.service.analysis_service import AnalysisService

        dao = StudentDAO(db_session)

        # 创建已知数据
        test_data = [
            {'student_id': 'S001', 'name': 'A', 'gender': '男', 'grade': '一年级', 'age': 7, 'height': 100.0, 'weight': 20.0, 'bmi': 20.0, 'bmi_category': '正常'},
            {'student_id': 'S002', 'name': 'B', 'gender': '女', 'grade': '一年级', 'age': 7, 'height': 110.0, 'weight': 22.0, 'bmi': 18.2, 'bmi_category': '正常'},
            {'student_id': 'S003', 'name': 'C', 'gender': '男', 'grade': '一年级', 'age': 7, 'height': 120.0, 'weight': 25.0, 'bmi': 17.4, 'bmi_category': '正常'},
        ]

        for data in test_data:
            dao.create(data)

        # 验证统计
        service = AnalysisService(session=db_session)
        stats = service.get_basic_statistics()

        assert stats['total_count'] == 3
        assert stats['avg_height'] == 110.0  # (100 + 110 + 120) / 3
        assert stats['min_height'] == 100.0
        assert stats['max_height'] == 120.0
