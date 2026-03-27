"""
可视化服务模块

整合各种图表生成，提供统一的可视化接口。
"""

import os
from typing import List, Dict, Any, Optional

from src.visualization.charts import (
    HeightByGradeChart,
    HeightByGenderChart,
    HeightDistributionChart,
    BoxPlotByGradeChart,
    GrowthTrendChart,
    BMIDistributionChart,
    HeightHeatmapChart,
    ScatterAgeHeightChart,
)
from src.service.analysis_service import AnalysisService
from src.dao.student_dao import StudentDAO
from src.core.logger import get_logger
from src.core.exceptions import VisualizationException


class HeightVisualizer:
    """身高数据可视化器

    整合各种图表生成，提供统一的可视化接口。

    Attributes:
        _analysis_service: 分析服务
        _student_dao: 学生DAO
        _output_dir: 输出目录
        _logger: 日志记录器
    """

    def __init__(
        self,
        analysis_service: Optional[AnalysisService] = None,
        student_dao: Optional[StudentDAO] = None,
        output_dir: Optional[str] = None,
        session=None
    ) -> None:
        """初始化可视化器

        Args:
            analysis_service: 分析服务实例
            student_dao: 学生DAO实例
            output_dir: 输出目录
            session: 可选的数据库会话（用于测试）
        """
        if session is not None:
            self._analysis_service = AnalysisService(session=session)
            self._student_dao = StudentDAO(session)
        else:
            self._analysis_service = analysis_service or AnalysisService()
            self._student_dao = student_dao or StudentDAO()
        self._output_dir = output_dir
        self._logger = get_logger(self.__class__.__name__)

        # 初始化图表生成器
        self._charts = {
            'height_by_grade': HeightByGradeChart(output_dir=output_dir),
            'height_by_gender': HeightByGenderChart(output_dir=output_dir),
            'height_distribution': HeightDistributionChart(output_dir=output_dir),
            'boxplot_by_grade': BoxPlotByGradeChart(output_dir=output_dir),
            'growth_trend': GrowthTrendChart(output_dir=output_dir),
            'bmi_distribution': BMIDistributionChart(output_dir=output_dir),
            'height_heatmap': HeightHeatmapChart(output_dir=output_dir),
            'scatter_age_height': ScatterAgeHeightChart(output_dir=output_dir),
        }

    def generate_height_by_grade_chart(self) -> str:
        """生成各年级平均身高柱状图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成各年级平均身高柱状图")

            data = self._analysis_service.get_grade_statistics()
            fig = self._charts['height_by_grade'].create(data)
            filepath = self._charts['height_by_grade'].save(fig, 'height_by_grade.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成各年级平均身高柱状图失败: {e}")
            raise VisualizationException(
                message=f"生成各年级平均身高柱状图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_height_by_gender_chart(self) -> str:
        """生成男女身高对比图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成男女身高对比图")

            data = self._analysis_service.get_gender_statistics()
            fig = self._charts['height_by_gender'].create(data)
            filepath = self._charts['height_by_gender'].save(fig, 'height_by_gender.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成男女身高对比图失败: {e}")
            raise VisualizationException(
                message=f"生成男女身高对比图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_height_distribution_chart(self) -> str:
        """生成身高分布直方图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成身高分布直方图")

            data = self._analysis_service.get_height_distribution()
            fig = self._charts['height_distribution'].create(data)
            filepath = self._charts['height_distribution'].save(fig, 'height_distribution.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成身高分布直方图失败: {e}")
            raise VisualizationException(
                message=f"生成身高分布直方图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_boxplot_by_grade_chart(self) -> str:
        """生成各年级身高箱线图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成各年级身高箱线图")

            # 获取原始学生数据
            students = self._student_dao.get_all()
            data = [
                {
                    'grade': s.grade,
                    'height': s.height,
                    'gender': s.gender
                }
                for s in students
            ]

            fig = self._charts['boxplot_by_grade'].create(data)
            filepath = self._charts['boxplot_by_grade'].save(fig, 'boxplot_by_grade.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成各年级身高箱线图失败: {e}")
            raise VisualizationException(
                message=f"生成各年级身高箱线图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_growth_trend_chart(self) -> str:
        """生成生长趋势折线图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成生长趋势折线图")

            data = self._analysis_service.get_growth_trend()
            fig = self._charts['growth_trend'].create(data)
            filepath = self._charts['growth_trend'].save(fig, 'growth_trend.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成生长趋势折线图失败: {e}")
            raise VisualizationException(
                message=f"生成生长趋势折线图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_bmi_distribution_chart(self) -> str:
        """生成BMI分布图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成BMI分布图")

            data = self._analysis_service.get_bmi_statistics()
            fig = self._charts['bmi_distribution'].create(data)
            filepath = self._charts['bmi_distribution'].save(fig, 'bmi_distribution.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成BMI分布图失败: {e}")
            raise VisualizationException(
                message=f"生成BMI分布图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_height_heatmap_chart(self) -> str:
        """生成身高热力图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成身高热力图")

            data = self._analysis_service.get_gender_statistics()
            fig = self._charts['height_heatmap'].create(data)
            filepath = self._charts['height_heatmap'].save(fig, 'height_heatmap.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成身高热力图失败: {e}")
            raise VisualizationException(
                message=f"生成身高热力图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_scatter_age_height_chart(self) -> str:
        """生成年龄身高散点图

        Returns:
            生成的图表文件路径
        """
        try:
            self._logger.debug("生成年龄身高散点图")

            # 获取原始学生数据
            students = self._student_dao.get_all()
            data = [
                {
                    'age': s.age,
                    'height': s.height,
                    'gender': s.gender
                }
                for s in students
            ]

            fig = self._charts['scatter_age_height'].create(data)
            filepath = self._charts['scatter_age_height'].save(fig, 'scatter_age_height.png')

            self._logger.info(f"生成图表: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"生成年龄身高散点图失败: {e}")
            raise VisualizationException(
                message=f"生成年龄身高散点图失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )

    def generate_all_charts(self) -> List[str]:
        """生成所有图表

        Returns:
            生成的图表文件路径列表
        """
        self._logger.info("开始生成所有图表")

        chart_files = []

        try:
            chart_files.append(self.generate_height_by_grade_chart())
            chart_files.append(self.generate_height_by_gender_chart())
            chart_files.append(self.generate_height_distribution_chart())
            chart_files.append(self.generate_boxplot_by_grade_chart())
            chart_files.append(self.generate_growth_trend_chart())
            chart_files.append(self.generate_bmi_distribution_chart())
            chart_files.append(self.generate_height_heatmap_chart())
            chart_files.append(self.generate_scatter_age_height_chart())

            self._logger.info(f"成功生成 {len(chart_files)} 个图表")
            return chart_files

        except Exception as e:
            self._logger.error(f"生成图表过程中出错: {e}")
            raise VisualizationException(
                message=f"生成图表失败: {str(e)}",
                error_code="CHART_GENERATION_ERROR"
            )
