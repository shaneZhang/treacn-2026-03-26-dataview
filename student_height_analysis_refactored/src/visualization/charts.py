"""
图表生成模块

实现各种数据可视化图表的生成。
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import font_manager
import pandas as pd
import numpy as np

from config.settings import get_settings
from src.core.logger import get_logger
from src.core.exceptions import VisualizationException


class ChartBase(ABC):
    """图表基类
    
    所有图表的抽象基类，定义通用接口。
    
    Attributes:
        _figsize: 图表尺寸
        _dpi: 图表DPI
        _output_dir: 输出目录
        _logger: 日志记录器
    """
    
    def __init__(
        self,
        figsize: Tuple[int, int] = (10, 6),
        dpi: int = 300,
        output_dir: Optional[str] = None
    ) -> None:
        """初始化图表基类
        
        Args:
            figsize: 图表尺寸
            dpi: 图表DPI
            output_dir: 输出目录
        """
        self._figsize = figsize
        self._dpi = dpi
        self._output_dir = output_dir or get_settings().output_path
        self._logger = get_logger(self.__class__.__name__)
        
        # 确保输出目录存在
        os.makedirs(self._output_dir, exist_ok=True)
        
        # 设置中文字体
        self._setup_chinese_font()
    
    def _setup_chinese_font(self) -> None:
        """设置中文字体"""
        # macOS系统自带的中文字体
        chinese_fonts = ['Heiti TC', 'STHeiti', 'PingFang HK', 'Arial Unicode MS', 'Noto Sans CJK SC']
        
        # 获取系统可用的字体
        available_fonts = [f.name for f in font_manager.fontManager.ttflist]
        
        # 找到第一个可用的中文字体
        selected_font = None
        for font in chinese_fonts:
            if font in available_fonts:
                selected_font = font
                break
        
        if selected_font:
            plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
            self._logger.debug(f"使用中文字体: {selected_font}")
        else:
            self._logger.warning("未找到合适的中文字体，中文可能显示为方框")
        
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    @abstractmethod
    def create(self, data: Any) -> plt.Figure:
        """创建图表
        
        Args:
            data: 图表数据
            
        Returns:
            matplotlib图表对象
        """
        pass
    
    def save(self, fig: plt.Figure, filename: str) -> str:
        """保存图表
        
        Args:
            fig: 图表对象
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        filepath = os.path.join(self._output_dir, filename)
        fig.savefig(filepath, dpi=self._dpi, bbox_inches='tight')
        plt.close(fig)
        self._logger.debug(f"图表已保存: {filepath}")
        return filepath


class HeightByGradeChart(ChartBase):
    """各年级平均身高柱状图"""
    
    def create(self, data: List[Dict[str, Any]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 年级统计数据列表
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=self._figsize)
        
        # 按年级顺序排序
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        data_dict = {d['grade']: d for d in data}
        grades = [g for g in grade_order if g in data_dict]
        heights = [data_dict[g]['avg_height'] for g in grades]
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        bars = ax.bar(grades, heights, color=colors, edgecolor='black', linewidth=1.2)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}cm',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级学生平均身高分布', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, max(heights) * 1.15 if heights else 150)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig


class HeightByGenderChart(ChartBase):
    """男女身高对比图"""
    
    def create(self, data: List[Dict[str, Any]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 性别统计数据列表
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 按年级和性别组织数据
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        
        male_heights = []
        female_heights = []
        
        for grade in grade_order:
            male_data = next((d for d in data if d['grade'] == grade and d['gender'] == '男'), None)
            female_data = next((d for d in data if d['grade'] == grade and d['gender'] == '女'), None)
            
            male_heights.append(male_data['avg_height'] if male_data else 0)
            female_heights.append(female_data['avg_height'] if female_data else 0)
        
        x = np.arange(len(grade_order))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, male_heights, width, label='男', color='#4A90E2', edgecolor='black')
        bars2 = ax.bar(x + width/2, female_heights, width, label='女', color='#E94B8A', edgecolor='black')
        
        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级男女生平均身高对比', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(grade_order)
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig


class HeightDistributionChart(ChartBase):
    """身高分布直方图"""
    
    def create(self, data: Dict[str, int]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 身高分布数据
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 按顺序排列
        labels = ['<110cm', '110-120cm', '120-130cm', '130-140cm', '140-150cm', '150-160cm', '>160cm']
        values = [data.get(label, 0) for label in labels]
        
        bars = ax.bar(labels, values, color='#5DADE2', edgecolor='black', alpha=0.7)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('身高段', fontsize=12, fontweight='bold')
        ax.set_ylabel('人数', fontsize=12, fontweight='bold')
        ax.set_title('学生身高分布直方图', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig


class BoxPlotByGradeChart(ChartBase):
    """各年级身高箱线图"""
    
    def create(self, data: List[Dict[str, Any]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 包含学生身高数据的列表
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 按年级组织数据
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        data_by_grade = []
        
        for grade in grade_order:
            grade_data = [d['height'] for d in data if d.get('grade') == grade]
            data_by_grade.append(grade_data if grade_data else [0])
        
        box_plot = ax.boxplot(data_by_grade, labels=grade_order, patch_artist=True)
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax.set_ylabel('身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级学生身高分布箱线图', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig


class GrowthTrendChart(ChartBase):
    """生长趋势折线图"""
    
    def create(self, data: List[Dict[str, Any]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 生长趋势数据列表
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 提取数据
        grade_ranges = [d['grade_range'] for d in data]
        growth_values = [d['height_growth'] for d in data]
        
        # 绘制折线
        ax.plot(grade_ranges, growth_values, marker='o', linewidth=3, markersize=10,
                color='#2E86AB', markerfacecolor='white', markeredgewidth=2)
        
        # 添加数值标签
        for i, (grade_range, growth) in enumerate(zip(grade_ranges, growth_values)):
            ax.annotate(f'{growth:.1f}cm',
                       (i, growth),
                       textcoords="offset points",
                       xytext=(0, 10),
                       ha='center',
                       fontsize=9,
                       fontweight='bold')
        
        ax.set_xlabel('年级段', fontsize=12, fontweight='bold')
        ax.set_ylabel('身高增长 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级段身高增长趋势', fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig


class BMIDistributionChart(ChartBase):
    """BMI分布图"""
    
    def create(self, data: Tuple[Dict[str, int], List[Dict[str, Any]]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: (BMI分布, 各年级BMI分布)元组
            
        Returns:
            图表对象
        """
        bmi_dist, bmi_by_grade = data
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 饼图
        colors_pie = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
        categories = list(bmi_dist.keys())
        values = list(bmi_dist.values())
        
        explode = (0.05,) + (0,) * (len(categories) - 1)
        
        wedges, texts, autotexts = ax1.pie(
            values,
            labels=categories,
            autopct='%1.1f%%',
            colors=colors_pie[:len(categories)],
            explode=explode[:len(categories)],
            shadow=True,
            startangle=90,
            textprops={'fontsize': 11}
        )
        ax1.set_title('BMI分布比例', fontsize=14, fontweight='bold', pad=20)
        
        # 柱状图
        if bmi_by_grade:
            # 转换为DataFrame便于绘图
            df = pd.DataFrame(bmi_by_grade)
            pivot_df = df.pivot(index='grade', columns='bmi_category', values='count').fillna(0)
            
            grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
            pivot_df = pivot_df.reindex([g for g in grade_order if g in pivot_df.index])
            
            pivot_df.plot(kind='bar', ax=ax2, color=colors_pie, width=0.8)
            ax2.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax2.set_ylabel('人数', fontsize=12, fontweight='bold')
            ax2.set_title('各年级BMI分布', fontsize=14, fontweight='bold', pad=20)
            ax2.legend(title='BMI分类', fontsize=9)
            ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
            ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig


class HeightHeatmapChart(ChartBase):
    """身高热力图"""
    
    def create(self, data: List[Dict[str, Any]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 性别统计数据列表
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 构建透视表
        df = pd.DataFrame(data)
        if not df.empty:
            pivot_table = df.pivot(index='grade', columns='gender', values='avg_height')
            
            grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
            pivot_table = pivot_table.reindex([g for g in grade_order if g in pivot_table.index])
            
            im = ax.imshow(pivot_table.values, cmap='YlOrRd', aspect='auto')
            
            # 设置刻度
            ax.set_xticks(np.arange(len(pivot_table.columns)))
            ax.set_yticks(np.arange(len(pivot_table.index)))
            ax.set_xticklabels(pivot_table.columns)
            ax.set_yticklabels(pivot_table.index)
            
            # 添加数值标签
            for i in range(len(pivot_table.index)):
                for j in range(len(pivot_table.columns)):
                    text = ax.text(j, i, f'{pivot_table.iloc[i, j]:.1f}',
                                 ha="center", va="center", color="black", fontweight='bold')
            
            ax.set_title('各年级男女生平均身高热力图', fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('性别', fontsize=12, fontweight='bold')
            ax.set_ylabel('年级', fontsize=12, fontweight='bold')
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('身高 (cm)', fontsize=11)
        
        plt.tight_layout()
        return fig


class ScatterAgeHeightChart(ChartBase):
    """年龄身高散点图"""
    
    def create(self, data: List[Dict[str, Any]]) -> plt.Figure:
        """创建图表
        
        Args:
            data: 学生数据列表，包含年龄、身高、性别
            
        Returns:
            图表对象
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 按性别分组
        df = pd.DataFrame(data)
        
        if not df.empty:
            colors = {'男': '#4A90E2', '女': '#E94B8A'}
            
            for gender in ['男', '女']:
                gender_data = df[df['gender'] == gender]
                if not gender_data.empty:
                    ax.scatter(gender_data['age'], gender_data['height'],
                              c=colors.get(gender, '#333333'),
                              alpha=0.6, s=50, label=gender,
                              edgecolors='white', linewidth=0.5)
            
            # 添加趋势线
            if not df.empty:
                z = np.polyfit(df['age'], df['height'], 1)
                p = np.poly1d(z)
                ages = sorted(df['age'].unique())
                ax.plot(ages, p(ages), "r--", alpha=0.8, linewidth=2, label='趋势线')
            
            ax.set_xlabel('年龄 (岁)', fontsize=12, fontweight='bold')
            ax.set_ylabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('年龄与身高关系散点图', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        return fig
