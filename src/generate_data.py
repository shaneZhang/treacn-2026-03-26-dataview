import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta


def generate_student_data(n=1000, random_seed=42):
    """
    生成小学生身高模拟数据

    参数:
        n: 生成数据条数，默认1000
        random_seed: 随机种子，保证可重复性

    返回:
        DataFrame: 包含学生信息的DataFrame
    """
    np.random.seed(random_seed)
    random.seed(random_seed)

    # 姓氏和名字库
    surnames = ['王', '李', '张', '刘', '陈', '杨', '黄', '赵', '吴', '周',
                '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高',
                '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹']

    names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军',
             '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞',
             '平', '刚', '桂英', '文', '辉', '鑫', '宇', '博', '浩', '然',
             '梓', '涵', '轩', '怡', '欣', '雨', '晨', '曦', '阳', '昊',
             '思', '琪', '佳', '雪', '梦', '瑶', '琳', '婉', '清', '悦']

    # 年级和对应年龄范围
    grades = {
        '一年级': (6, 7),
        '二年级': (7, 8),
        '三年级': (8, 9),
        '四年级': (9, 10),
        '五年级': (10, 11),
        '六年级': (11, 12)
    }

    # 年级到数字的映射
    grade_to_num = {
        '一年级': 1, '二年级': 2, '三年级': 3,
        '四年级': 4, '五年级': 5, '六年级': 6
    }

    # 各年级男女生的平均身高和标准差（基于中国儿童生长标准）
    height_stats = {
        '一年级': {'男': (120, 5.5), '女': (119, 5.3)},
        '二年级': {'男': (125, 5.8), '女': (124, 5.5)},
        '三年级': {'男': (130, 6.0), '女': (129, 5.8)},
        '四年级': {'男': (135, 6.2), '女': (134, 6.0)},
        '五年级': {'男': (140, 6.5), '女': (140, 6.3)},
        '六年级': {'男': (147, 7.0), '女': (148, 6.8)},
    }

    data = []
    student_id = 10001

    for _ in range(n):
        # 随机选择年级
        grade = random.choice(list(grades.keys()))
        age_range = grades[grade]
        age = random.randint(age_range[0], age_range[1])

        # 随机性别
        gender = random.choice(['男', '女'])

        # 生成身高（基于正态分布）
        mean, std = height_stats[grade][gender]
        height = np.random.normal(mean, std)
        height = round(height, 1)

        # 生成体重（与身高相关）
        bmi_base = 16 if age < 9 else 17
        weight = (height / 100) ** 2 * np.random.normal(bmi_base, 1.5)
        weight = round(weight, 1)

        # 生成姓名
        name = random.choice(surnames) + random.choice(names)

        # 生成入学日期
        grade_num = grade_to_num[grade]
        year = 2024 - (grade_num - 1)
        month = random.randint(9, 12) if grade_num == 1 else random.randint(1, 12)
        day = random.randint(1, 28)
        enrollment_date = f"{year}-{month:02d}-{day:02d}"

        data.append({
            '学生ID': student_id,
            '姓名': name,
            '性别': gender,
            '年级': grade,
            '年龄': age,
            '身高(cm)': height,
            '体重(kg)': weight,
            '入学日期': enrollment_date
        })

        student_id += 1

    return pd.DataFrame(data)


def save_to_excel(df, filepath):
    """
    将数据保存为Excel文件

    参数:
        df: DataFrame数据
        filepath: 保存路径
    """
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"数据已保存至: {filepath}")


if __name__ == "__main__":
    # 生成数据
    df = generate_student_data(n=1000)

    # 保存数据
    output_path = "../data/student_height_data.xlsx"
    save_to_excel(df, output_path)

    # 显示数据预览
    print("\n数据预览（前10条）:")
    print(df.head(10))
    print(f"\n数据总量: {len(df)} 条")
    print(f"\n数据统计:")
    print(df.describe())
