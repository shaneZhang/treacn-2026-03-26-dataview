"""
Height data visualization module.

This module provides the HeightVisualizer class for creating various
visualizations of student height data from Excel files or databases.

Note: This is a legacy module maintained for backward compatibility.
For new development, please use the app.service.visualization_service module instead.
"""

import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from matplotlib import font_manager
import os
import warnings

# Import new architecture for compatibility
try:
    from app.service import VisualizationService as NewVisualizationService
    from app.config.database import get_db_pool
    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError:
    NEW_ARCHITECTURE_AVAILABLE = False

# Configure Chinese fonts for matplotlib
chinese_fonts = ['Heiti TC', 'STHeiti', 'PingFang HK', 'Arial Unicode MS', 'Noto Sans CJK SC',
                 'Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei']
available_fonts = [f.name for f in font_manager.fontManager.ttflist]
selected_font = None

for font in chinese_fonts:
    if font in available_fonts:
        selected_font = font
        break

if selected_font:
    plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
else:
    print("Warning: Suitable Chinese font not found, Chinese characters may display as squares")

plt.rcParams['axes.unicode_minus'] = False  # Fix negative sign display


class HeightVisualizer:
    """
    Height data visualizer class.

    This class provides methods for creating various visualizations of student
    height data, supporting both Excel files and database sources.

    Attributes:
        df (pandas.DataFrame): The student data
        output_dir (str): Directory to save generated plots

    Note: For new development, use app.service.VisualizationService instead.
    """

    def __init__(self, data_path=None, output_dir="../output", use_database=False):
        """
        Initialize the visualizer with a data source.

        Args:
            data_path: Path to Excel data file (for file-based mode)
            output_dir: Directory to save generated plots
            use_database: Whether to use the database for data access
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._use_database = use_database
        self._viz_service = None

        if use_database:
            if NEW_ARCHITECTURE_AVAILABLE:
                self._init_from_database()
            else:
                warnings.warn(
                    "New architecture not available. Falling back to Excel-based mode. "
                    "Please provide a data_path.",
                    UserWarning
                )
                if data_path:
                    self.df = pd.read_excel(data_path)
                else:
                    raise ValueError("Either data_path must be provided or new architecture must be available")
        elif data_path:
            self.df = pd.read_excel(data_path)
        else:
            raise ValueError("Either data_path or use_database=True must be provided")

    def _init_from_database(self):
        """Initialize data from the database using the new architecture."""
        pool = get_db_pool()
        session = pool.get_session()
        self._viz_service = NewVisualizationService(session, output_dir=self.output_dir)
        self.df = self._viz_service._student_service.get_students_dataframe()

    def _get_column_names(self):
        """Get column names, handling both old and new formats."""
        if 'height_cm' in self.df.columns:
            return {
                'grade': 'grade',
                'gender': 'gender',
                'height': 'height_cm',
                'weight': 'weight_kg',
                'age': 'age'
            }
        else:
            return {
                'grade': '年级',
                'gender': '性别',
                'height': '身高(cm)',
                'weight': '体重(kg)',
                'age': '年龄'
            }

    def plot_height_by_grade(self, save=True, show=False):
        """
        Plot average height by grade as a bar chart.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_height_by_grade(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(10, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        grade_means = self.df.groupby(cols['grade'])[cols['height']].mean().reindex(grade_order)

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        bars = ax.bar(grade_order, grade_means, color=colors, edgecolor='black', linewidth=1.2)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}cm',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级学生平均身高分布', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, max(grade_means) * 1.15 if max(grade_means) > 0 else 1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/height_by_grade.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_by_grade.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_height_by_gender(self, save=True, show=False):
        """
        Plot height comparison by gender across grades.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_height_by_gender(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(12, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        gender_stats = self.df.groupby([cols['grade'], cols['gender']])[cols['height']].mean().unstack()
        gender_stats = gender_stats.reindex(grade_order)

        x = np.arange(len(grade_order))
        width = 0.35

        if '男' in gender_stats.columns:
            bars1 = ax.bar(x - width/2, gender_stats['男'], width, label='男', color='#4A90E2', edgecolor='black')
        if '女' in gender_stats.columns:
            bars2 = ax.bar(x + width/2, gender_stats['女'], width, label='女', color='#E94B8A', edgecolor='black')

        # Add value labels
        for bars in [bars1, bars2] if '男' in gender_stats.columns and '女' in gender_stats.columns else [bars1] if '男' in gender_stats.columns else [bars2]:
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
        if save:
            plt.savefig(f'{self.output_dir}/height_by_gender.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_by_gender.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_height_distribution(self, save=True, show=False):
        """
        Plot height distribution as a histogram.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_height_distribution(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(12, 6))

        bins = range(100, 170, 5)
        ax.hist(self.df[cols['height']], bins=bins, color='#5DADE2', edgecolor='black', alpha=0.7)

        mean_height = self.df[cols['height']].mean()
        median_height = self.df[cols['height']].median()

        ax.axvline(mean_height, color='red', linestyle='--', linewidth=2, label=f'平均值: {mean_height:.1f}cm')
        ax.axvline(median_height, color='green', linestyle='--', linewidth=2, label=f'中位数: {median_height:.1f}cm')

        ax.set_xlabel('身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_ylabel('人数', fontsize=12, fontweight='bold')
        ax.set_title('学生身高分布直方图', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/height_distribution.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_distribution.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_boxplot_by_grade(self, save=True, show=False):
        """
        Plot height distribution by grade as boxplots.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_boxplot_by_grade(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(12, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        data_by_grade = [self.df[self.df[cols['grade']] == grade][cols['height']].values for grade in grade_order]

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
        if save:
            plt.savefig(f'{self.output_dir}/boxplot_by_grade.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/boxplot_by_grade.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_growth_trend(self, save=True, show=False):
        """
        Plot height growth trend across grades as a line chart.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_growth_trend(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(12, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']

        # Overall trend
        overall_means = self.df.groupby(cols['grade'])[cols['height']].mean().reindex(grade_order)
        ax.plot(grade_order, overall_means, marker='o', linewidth=3, markersize=10,
                color='#2E86AB', label='总体平均', markerfacecolor='white', markeredgewidth=2)

        # Male trend
        if '男' in self.df[cols['gender']].values:
            male_means = self.df[self.df[cols['gender']] == '男'].groupby(cols['grade'])[cols['height']].mean().reindex(grade_order)
            ax.plot(grade_order, male_means, marker='s', linewidth=2.5, markersize=8,
                    color='#4A90E2', label='男生', linestyle='--')

        # Female trend
        if '女' in self.df[cols['gender']].values:
            female_means = self.df[self.df[cols['gender']] == '女'].groupby(cols['grade'])[cols['height']].mean().reindex(grade_order)
            ax.plot(grade_order, female_means, marker='^', linewidth=2.5, markersize=8,
                    color='#E94B8A', label='女生', linestyle='--')

        # Add value labels for overall means
        for i, (grade, height) in enumerate(zip(grade_order, overall_means)):
            if height > 0:
                ax.annotate(f'{height:.1f}cm', (i, height), textcoords="offset points",
                           xytext=(0, 10), ha='center', fontsize=9, fontweight='bold')

        ax.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级身高生长趋势', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=11, loc='upper left')
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/growth_trend.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/growth_trend.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_scatter_age_height(self, save=True, show=False):
        """
        Plot scatter plot of age vs height.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_scatter_age_height(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = {'男': '#4A90E2', '女': '#E94B8A'}
        for gender in ['男', '女']:
            data = self.df[self.df[cols['gender']] == gender]
            if not data.empty:
                ax.scatter(data[cols['age']], data[cols['height']], c=colors[gender],
                          alpha=0.6, s=50, label=gender, edgecolors='white', linewidth=0.5)

        # Add trend line
        z = np.polyfit(self.df[cols['age']], self.df[cols['height']], 1)
        p = np.poly1d(z)
        ax.plot(sorted(self.df[cols['age']].unique()),
                p(sorted(self.df[cols['age']].unique())),
                "r--", alpha=0.8, linewidth=2, label='趋势线')

        ax.set_xlabel('年龄 (岁)', fontsize=12, fontweight='bold')
        ax.set_ylabel('身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('年龄与身高关系散点图', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/scatter_age_height.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/scatter_age_height.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_bmi_distribution(self, save=True, show=False):
        """
        Plot BMI distribution as pie and bar charts.

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_bmi_distribution(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Calculate BMI
        self.df['BMI'] = self.df[cols['weight']] / (self.df[cols['height']] / 100) ** 2

        def classify_bmi(bmi):
            if bmi < 14:
                return '偏瘦'
            elif bmi < 18:
                return '正常'
            elif bmi < 21:
                return '超重'
            else:
                return '肥胖'

        self.df['BMI分类'] = self.df['BMI'].apply(classify_bmi)
        bmi_counts = self.df['BMI分类'].value_counts()

        # Pie chart
        colors_pie = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
        explode = (0.05, 0, 0, 0)

        wedges, texts, autotexts = ax1.pie(bmi_counts, labels=bmi_counts.index, autopct='%1.1f%%',
                                           colors=colors_pie, explode=explode, shadow=True,
                                           startangle=90, textprops={'fontsize': 11})
        ax1.set_title('BMI分布比例', fontsize=14, fontweight='bold', pad=20)

        # Bar chart by grade
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        bmi_by_grade = pd.crosstab(self.df[cols['grade']], self.df['BMI分类'])
        bmi_by_grade = bmi_by_grade.reindex(grade_order)

        bmi_by_grade.plot(kind='bar', ax=ax2, color=colors_pie, width=0.8)
        ax2.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax2.set_ylabel('人数', fontsize=12, fontweight='bold')
        ax2.set_title('各年级BMI分布', fontsize=14, fontweight='bold', pad=20)
        ax2.legend(title='BMI分类', fontsize=9)
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/bmi_distribution.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/bmi_distribution.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def plot_height_heatmap(self, save=True, show=False):
        """
        Plot height heatmap (grade vs gender).

        Args:
            save: Whether to save the plot to a file
            show: Whether to display the plot
        """
        if self._viz_service is not None:
            self._viz_service.plot_height_heatmap(save=save, show=show)
            return

        cols = self._get_column_names()
        fig, ax = plt.subplots(figsize=(8, 6))

        pivot_table = self.df.pivot_table(values=cols['height'], index=cols['grade'], columns=cols['gender'], aggfunc='mean')
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        pivot_table = pivot_table.reindex(grade_order)

        im = ax.imshow(pivot_table.values, cmap='YlOrRd', aspect='auto')

        # Set ticks
        ax.set_xticks(np.arange(len(pivot_table.columns)))
        ax.set_yticks(np.arange(len(pivot_table.index)))
        ax.set_xticklabels(pivot_table.columns)
        ax.set_yticklabels(pivot_table.index)

        # Add value labels
        for i in range(len(pivot_table.index)):
            for j in range(len(pivot_table.columns)):
                text = ax.text(j, i, f'{pivot_table.iloc[i, j]:.1f}',
                             ha="center", va="center", color="black", fontweight='bold')

        ax.set_title('各年级男女生平均身高热力图', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('性别', fontsize=12, fontweight='bold')
        ax.set_ylabel('年级', fontsize=12, fontweight='bold')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('身高 (cm)', fontsize=11)

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/height_heatmap.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_heatmap.png")
        if show:
            plt.show()
        else:
            plt.close(fig)

    def generate_all_plots(self, show=False):
        """
        Generate all available visualizations.

        Args:
            show: Whether to display each plot after generation
        """
        if self._viz_service is not None:
            self._viz_service.generate_all_plots(show=show)
            return

        print("=" * 60)
        print("开始生成可视化图表...")
        print("=" * 60)

        self.plot_height_by_grade(show=show)
        self.plot_height_by_gender(show=show)
        self.plot_height_distribution(show=show)
        self.plot_boxplot_by_grade(show=show)
        self.plot_growth_trend(show=show)
        self.plot_scatter_age_height(show=show)
        self.plot_bmi_distribution(show=show)
        self.plot_height_heatmap(show=show)

        print("\n" + "=" * 60)
        print(f"所有图表已保存至: {self.output_dir}")
        print("=" * 60)


if __name__ == "__main__":
    # Test the visualizer
    visualizer = HeightVisualizer("../data/student_height_data.xlsx")
    visualizer.generate_all_plots()
