import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from matplotlib import font_manager
import os

# 设置中文字体 - 使用macOS系统自带的中文字体
# 按优先级尝试不同的中文字体
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
    print(f"使用中文字体: {selected_font}")
else:
    print("警告: 未找到合适的中文字体，中文可能显示为方框")

plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class HeightVisualizer:
    """身高数据可视化类"""

    def __init__(self, data_path, output_dir="../output"):
        """
        初始化可视化器

        参数:
            data_path: Excel数据文件路径
            output_dir: 图表输出目录
        """
        self.df = pd.read_excel(data_path)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_height_by_grade(self, save=True):
        """
        各年级平均身高柱状图
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        grade_means = self.df.groupby('年级')['身高(cm)'].mean().reindex(grade_order)

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        bars = ax.bar(grade_order, grade_means, color=colors, edgecolor='black', linewidth=1.2)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}cm',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_xlabel('年级', fontsize=12, fontweight='bold')
        ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_title('各年级学生平均身高分布', fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, max(grade_means) * 1.15)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/height_by_grade.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_by_grade.png")
        plt.show()

    def plot_height_by_gender(self, save=True):
        """
        男女身高对比图
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        gender_stats = self.df.groupby(['年级', '性别'])['身高(cm)'].mean().unstack()
        gender_stats = gender_stats.reindex(grade_order)

        x = np.arange(len(grade_order))
        width = 0.35

        bars1 = ax.bar(x - width/2, gender_stats['男'], width, label='男', color='#4A90E2', edgecolor='black')
        bars2 = ax.bar(x + width/2, gender_stats['女'], width, label='女', color='#E94B8A', edgecolor='black')

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
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
        plt.show()

    def plot_height_distribution(self, save=True):
        """
        身高分布直方图
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        bins = range(100, 170, 5)
        ax.hist(self.df['身高(cm)'], bins=bins, color='#5DADE2', edgecolor='black', alpha=0.7)

        ax.axvline(self.df['身高(cm)'].mean(), color='red', linestyle='--', linewidth=2, label=f'平均值: {self.df["身高(cm)"].mean():.1f}cm')
        ax.axvline(self.df['身高(cm)'].median(), color='green', linestyle='--', linewidth=2, label=f'中位数: {self.df["身高(cm)"].median():.1f}cm')

        ax.set_xlabel('身高 (cm)', fontsize=12, fontweight='bold')
        ax.set_ylabel('人数', fontsize=12, fontweight='bold')
        ax.set_title('学生身高分布直方图', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        if save:
            plt.savefig(f'{self.output_dir}/height_distribution.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_distribution.png")
        plt.show()

    def plot_boxplot_by_grade(self, save=True):
        """
        各年级身高箱线图
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        data_by_grade = [self.df[self.df['年级'] == grade]['身高(cm)'].values for grade in grade_order]

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
        plt.show()

    def plot_growth_trend(self, save=True):
        """
        生长趋势折线图
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']

        # 总体趋势
        overall_means = self.df.groupby('年级')['身高(cm)'].mean().reindex(grade_order)
        ax.plot(grade_order, overall_means, marker='o', linewidth=3, markersize=10,
                color='#2E86AB', label='总体平均', markerfacecolor='white', markeredgewidth=2)

        # 男生趋势
        male_means = self.df[self.df['性别'] == '男'].groupby('年级')['身高(cm)'].mean().reindex(grade_order)
        ax.plot(grade_order, male_means, marker='s', linewidth=2.5, markersize=8,
                color='#4A90E2', label='男生', linestyle='--')

        # 女生趋势
        female_means = self.df[self.df['性别'] == '女'].groupby('年级')['身高(cm)'].mean().reindex(grade_order)
        ax.plot(grade_order, female_means, marker='^', linewidth=2.5, markersize=8,
                color='#E94B8A', label='女生', linestyle='--')

        # 添加数值标签
        for i, (grade, height) in enumerate(zip(grade_order, overall_means)):
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
        plt.show()

    def plot_scatter_age_height(self, save=True):
        """
        年龄身高散点图
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = {'男': '#4A90E2', '女': '#E94B8A'}
        for gender in ['男', '女']:
            data = self.df[self.df['性别'] == gender]
            ax.scatter(data['年龄'], data['身高(cm)'], c=colors[gender],
                      alpha=0.6, s=50, label=gender, edgecolors='white', linewidth=0.5)

        # 添加趋势线
        z = np.polyfit(self.df['年龄'], self.df['身高(cm)'], 1)
        p = np.poly1d(z)
        ax.plot(sorted(self.df['年龄'].unique()),
                p(sorted(self.df['年龄'].unique())),
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
        plt.show()

    def plot_bmi_distribution(self, save=True):
        """
        BMI分布饼图
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 计算BMI
        self.df['BMI'] = self.df['体重(kg)'] / (self.df['身高(cm)'] / 100) ** 2

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

        # 饼图
        colors_pie = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
        explode = (0.05, 0, 0, 0)

        wedges, texts, autotexts = ax1.pie(bmi_counts, labels=bmi_counts.index, autopct='%1.1f%%',
                                           colors=colors_pie, explode=explode, shadow=True,
                                           startangle=90, textprops={'fontsize': 11})
        ax1.set_title('BMI分布比例', fontsize=14, fontweight='bold', pad=20)

        # 柱状图
        bmi_by_grade = pd.crosstab(self.df['年级'], self.df['BMI分类'])
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
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
        plt.show()

    def plot_height_heatmap(self, save=True):
        """
        身高热力图（年级vs性别）
        """
        fig, ax = plt.subplots(figsize=(8, 6))

        pivot_table = self.df.pivot_table(values='身高(cm)', index='年级', columns='性别', aggfunc='mean')
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        pivot_table = pivot_table.reindex(grade_order)

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
        if save:
            plt.savefig(f'{self.output_dir}/height_heatmap.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存: {self.output_dir}/height_heatmap.png")
        plt.show()

    def generate_all_plots(self):
        """
        生成所有图表
        """
        print("=" * 60)
        print("开始生成可视化图表...")
        print("=" * 60)

        self.plot_height_by_grade()
        self.plot_height_by_gender()
        self.plot_height_distribution()
        self.plot_boxplot_by_grade()
        self.plot_growth_trend()
        self.plot_scatter_age_height()
        self.plot_bmi_distribution()
        self.plot_height_heatmap()

        print("\n" + "=" * 60)
        print(f"所有图表已保存至: {self.output_dir}")
        print("=" * 60)


if __name__ == "__main__":
    # 测试可视化功能
    visualizer = HeightVisualizer("../data/student_height_data.xlsx")
    visualizer.generate_all_plots()
