"""
数据分析服务模块

实现学生身高数据的分析功能。
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import numpy as np

from src.dao.student_dao import StudentDAO
from src.dao.models import Student
from src.core.logger import get_logger
from src.core.exceptions import DataValidationException


@dataclass
class StatisticsResult:
    """统计结果数据类
    
    Attributes:
        metric_name: 指标名称
        value: 指标值
        unit: 单位
        description: 描述
        timestamp: 计算时间
    """
    metric_name: str
    value: Any
    unit: str = ""
    description: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AnalysisService:
    """数据分析服务
    
    提供学生身高数据的统计分析功能。
    
    Attributes:
        _student_dao: 学生DAO
        _logger: 日志记录器
        _results: 分析结果缓存
    """
    
    # 中国儿童身高标准（2023年）
    STANDARD_HEIGHTS = {
        '一年级': {'男': 120.0, '女': 119.0},
        '二年级': {'男': 125.0, '女': 124.0},
        '三年级': {'男': 130.0, '女': 129.0},
        '四年级': {'男': 135.0, '女': 134.0},
        '五年级': {'男': 140.0, '女': 140.0},
        '六年级': {'男': 147.0, '女': 148.0},
    }
    
    def __init__(self, student_dao: Optional[StudentDAO] = None, session=None) -> None:
        """初始化分析服务
        
        Args:
            student_dao: 学生DAO实例
            session: 可选的数据库会话（用于测试）
        """
        if session is not None:
            self._student_dao = StudentDAO(session)
        else:
            self._student_dao = student_dao or StudentDAO()
        self._logger = get_logger(self.__class__.__name__)
        self._results: Dict[str, Any] = {}
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """获取基础统计信息
        
        Returns:
            基础统计信息字典
        """
        self._logger.debug("计算基础统计信息")
        
        total_count = self._student_dao.count()
        
        if total_count == 0:
            return {
                'total_count': 0,
                'male_count': 0,
                'female_count': 0,
                'avg_height': 0.0,
                'std_height': 0.0,
                'min_height': 0.0,
                'max_height': 0.0,
                'median_height': 0.0,
            }
        
        # 获取所有学生
        students = self._student_dao.get_all()
        heights = [s.height for s in students]
        
        male_count = len([s for s in students if s.gender == '男'])
        female_count = len([s for s in students if s.gender == '女'])
        
        stats = {
            'total_count': total_count,
            'male_count': male_count,
            'female_count': female_count,
            'avg_height': round(np.mean(heights), 2),
            'std_height': round(np.std(heights), 2),
            'min_height': round(min(heights), 2),
            'max_height': round(max(heights), 2),
            'median_height': round(np.median(heights), 2),
        }
        
        self._results['basic'] = stats
        return stats
    
    def get_grade_statistics(self) -> List[Dict[str, Any]]:
        """获取各年级统计信息
        
        Returns:
            各年级统计信息列表
        """
        self._logger.debug("计算各年级统计信息")
        
        stats = self._student_dao.get_statistics_by_grade()
        self._results['grade'] = stats
        return stats
    
    def get_gender_statistics(self) -> List[Dict[str, Any]]:
        """获取按性别统计信息
        
        Returns:
            按性别统计信息列表
        """
        self._logger.debug("计算性别统计信息")
        
        stats = self._student_dao.get_statistics_by_gender()
        self._results['gender'] = stats
        return stats
    
    def get_height_distribution(self) -> Dict[str, int]:
        """获取身高分布
        
        Returns:
            身高段到人数的映射
        """
        self._logger.debug("计算身高分布")
        
        students = self._student_dao.get_all()
        heights = [s.height for s in students]
        
        # 定义身高段
        bins = [0, 110, 120, 130, 140, 150, 160, 200]
        labels = ['<110cm', '110-120cm', '120-130cm', '130-140cm', '140-150cm', '150-160cm', '>160cm']
        
        # 使用pandas进行分组
        series = pd.Series(heights)
        distribution = pd.cut(series, bins=bins, labels=labels, right=False).value_counts().sort_index()
        
        result = {str(k): int(v) for k, v in distribution.items()}
        self._results['height_distribution'] = result
        return result
    
    def get_bmi_statistics(self) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """获取BMI统计信息
        
        Returns:
            (BMI分布, 各年级BMI分布)元组
        """
        self._logger.debug("计算BMI统计信息")
        
        bmi_distribution = self._student_dao.get_bmi_distribution()
        bmi_by_grade = self._student_dao.get_bmi_distribution_by_grade()
        
        self._results['bmi_distribution'] = bmi_distribution
        self._results['bmi_by_grade'] = bmi_by_grade
        
        return bmi_distribution, bmi_by_grade
    
    def get_growth_trend(self) -> List[Dict[str, Any]]:
        """获取生长趋势
        
        Returns:
            生长趋势数据列表
        """
        self._logger.debug("计算生长趋势")
        
        trend = self._student_dao.get_growth_trend()
        self._results['growth_trend'] = trend
        return trend
    
    def get_percentile_analysis(self, percentiles: List[int] = None) -> List[Dict[str, Any]]:
        """获取百分位数分析
        
        Args:
            percentiles: 百分位数列表
            
        Returns:
            各年级百分位数数据
        """
        self._logger.debug("计算百分位数")
        
        if percentiles is None:
            percentiles = [3, 10, 25, 50, 75, 90, 97]
        
        result = self._student_dao.get_height_percentiles(percentiles)
        self._results['percentiles'] = result
        return result
    
    def compare_with_standard(self) -> List[Dict[str, Any]]:
        """与标准身高对比
        
        Returns:
            与标准身高对比结果
        """
        self._logger.debug("对比标准身高")
        
        gender_stats = self._student_dao.get_statistics_by_gender()
        
        comparison = []
        for stat in gender_stats:
            grade = stat['grade']
            gender = stat['gender']
            actual_height = stat['avg_height']
            
            standard_height = self.STANDARD_HEIGHTS.get(grade, {}).get(gender, 0)
            diff = actual_height - standard_height
            diff_percent = (diff / standard_height * 100) if standard_height > 0 else 0
            
            comparison.append({
                'grade': grade,
                'gender': gender,
                'actual_height': actual_height,
                'standard_height': standard_height,
                'difference': round(diff, 2),
                'difference_percent': round(diff_percent, 2),
            })
        
        self._results['standard_comparison'] = comparison
        return comparison
    
    def get_age_statistics(self) -> List[Dict[str, Any]]:
        """获取按年龄统计信息
        
        Returns:
            各年龄统计信息列表
        """
        self._logger.debug("计算年龄统计信息")
        
        students = self._student_dao.get_all()
        
        # 按年龄分组
        age_groups = {}
        for student in students:
            age = student.age
            if age not in age_groups:
                age_groups[age] = []
            age_groups[age].append(student.height)
        
        stats = []
        for age in sorted(age_groups.keys()):
            heights = age_groups[age]
            stats.append({
                'age': age,
                'count': len(heights),
                'avg_height': round(np.mean(heights), 2),
                'std_height': round(np.std(heights), 2),
                'min_height': round(min(heights), 2),
                'max_height': round(max(heights), 2),
            })
        
        self._results['age'] = stats
        return stats
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """运行完整分析
        
        Returns:
            所有分析结果
        """
        self._logger.info("开始完整数据分析")
        
        results = {
            'basic': self.get_basic_statistics(),
            'grade': self.get_grade_statistics(),
            'gender': self.get_gender_statistics(),
            'height_distribution': self.get_height_distribution(),
            'bmi': self.get_bmi_statistics(),
            'growth_trend': self.get_growth_trend(),
            'percentiles': self.get_percentile_analysis(),
            'standard_comparison': self.compare_with_standard(),
            'age': self.get_age_statistics(),
        }
        
        self._logger.info("完整数据分析完成")
        return results
    
    def generate_report(self) -> str:
        """生成分析报告
        
        Returns:
            报告文本
        """
        results = self.run_full_analysis()
        
        lines = []
        lines.append("=" * 60)
        lines.append("小学生身高数据分析报告")
        lines.append("=" * 60)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 基础统计
        lines.append("【一、基础统计】")
        basic = results['basic']
        for key, value in basic.items():
            lines.append(f"  {key}: {value}")
        lines.append("")
        
        # 年级统计
        lines.append("【二、年级统计】")
        for stat in results['grade']:
            lines.append(f"  {stat['grade']}: 人数={stat['count']}, 平均身高={stat['avg_height']}cm")
        lines.append("")
        
        # 性别统计
        lines.append("【三、性别统计】")
        for stat in results['gender']:
            lines.append(f"  {stat['grade']} {stat['gender']}: 人数={stat['count']}, 平均身高={stat['avg_height']}cm")
        lines.append("")
        
        # BMI统计
        lines.append("【四、BMI分布】")
        bmi_dist = results['bmi'][0]
        for category, count in bmi_dist.items():
            lines.append(f"  {category}: {count}人")
        lines.append("")
        
        # 生长趋势
        lines.append("【五、生长趋势】")
        for trend in results['growth_trend']:
            lines.append(f"  {trend['grade_range']}: 增长{trend['height_growth']}cm ({trend['growth_rate']}%)")
        lines.append("")
        
        # 标准对比
        lines.append("【六、与标准身高对比】")
        for comp in results['standard_comparison'][:6]:  # 只显示前6条
            lines.append(f"  {comp['grade']} {comp['gender']}: 实际{comp['actual_height']}cm, "
                        f"标准{comp['standard_height']}cm, 差异{comp['difference']}cm")
        lines.append("")
        
        lines.append("=" * 60)
        lines.append("报告生成完成")
        lines.append("=" * 60)
        
        return "\n".join(lines)
