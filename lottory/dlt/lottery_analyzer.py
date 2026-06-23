#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 大乐透数据分析模块
 Lottery Analyzer — 号码频率、分布特征、冷热号、奇偶比、和值分析
=============================================================================

 功能列表:
   - get_number_frequency():      全量号码频率统计
   - get_recent_frequency():      近期号码频率统计
   - analyze_number_distribution(): 各位置号码分布特征
   - find_hot_and_cold_numbers():  热门/冷门号码识别
   - analyze_consecutive_patterns(): 连号模式分析
   - calculate_odd_even_ratio():   奇偶比统计
   - analyze_sum_statistics():     和值分布统计
   - create_analysis_visualizations(): 生成 PNG 分析图表

 使用示例:
   analyzer = LotteryAnalyzer(df)
   freq = analyzer.get_number_frequency()
   hot_cold = analyzer.find_hot_and_cold_numbers(30)
   create_analysis_visualizations(analyzer, "analysis_results/20260623")
=============================================================================
"""

import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# 使用统一日志配置（由 main.py 的 setup_logging() 初始化）
logger = logging.getLogger(__name__)


class LotteryAnalyzer:
    """
    大乐透数据分析器。

    提供全面的号码统计分析功能，包括频率统计、冷热号识别、
    和值分析、奇偶比、连号模式等。

    Attributes:
        df: 开奖数据 DataFrame
        red_ball_columns:  红球列名 ['red1'..'red5']
        blue_ball_columns: 蓝球列名 ['blue1', 'blue2']
    """

    def __init__(self, data_df: pd.DataFrame):
        """
        初始化分析器。

        Args:
            data_df: 包含开奖数据的 DataFrame
        """
        self.df = data_df.copy()
        self.red_ball_columns = ['red1', 'red2', 'red3', 'red4', 'red5']
        self.blue_ball_columns = ['blue1', 'blue2']

        # 按期号排序，确保时间顺序正确
        if 'issue' in self.df.columns:
            self.df = self.df.sort_values('issue').reset_index(drop=True)

    # ==================================================================
    #  频率分析
    # ==================================================================

    def get_number_frequency(self) -> Dict[str, pd.Series]:
        """
        统计各号码在全量历史数据中的出现频率。

        Returns:
            dict: {
                'red_frequency':  pd.Series (号码→出现次数),
                'blue_frequency': pd.Series (号码→出现次数)
            }
        """
        # 红球频率统计
        red_numbers = []
        for col in self.red_ball_columns:
            red_numbers.extend(self.df[col].dropna().astype(int).tolist())
        red_freq = pd.Series(Counter(red_numbers)).sort_index()

        # 蓝球频率统计
        blue_numbers = []
        for col in self.blue_ball_columns:
            blue_numbers.extend(self.df[col].dropna().astype(int).tolist())
        blue_freq = pd.Series(Counter(blue_numbers)).sort_index()

        return {
            'red_frequency': red_freq,
            'blue_frequency': blue_freq
        }

    def get_recent_frequency(self, recent_periods: int = 50) -> Dict[str, pd.Series]:
        """
        统计近期（最近 N 期）号码频率。

        Args:
            recent_periods: 最近期数，默认 50

        Returns:
            dict: {
                'recent_red_frequency':  pd.Series,
                'recent_blue_frequency': pd.Series
            }
        """
        recent_df = self.df.tail(recent_periods)

        # 近期红球频率
        red_numbers = []
        for col in self.red_ball_columns:
            red_numbers.extend(recent_df[col].dropna().astype(int).tolist())
        recent_red_freq = pd.Series(Counter(red_numbers)).sort_index()

        # 近期蓝球频率
        blue_numbers = []
        for col in self.blue_ball_columns:
            blue_numbers.extend(recent_df[col].dropna().astype(int).tolist())
        recent_blue_freq = pd.Series(Counter(blue_numbers)).sort_index()

        return {
            'recent_red_frequency': recent_red_freq,
            'recent_blue_frequency': recent_blue_freq
        }

    # ==================================================================
    #  分布特征分析
    # ==================================================================

    def analyze_number_distribution(self) -> Dict:
        """
        分析各号码位置的分布特征（均值、标准差、中位数等）。

        Returns:
            dict: {
                'red_ball_statistics': {position_N: {mean, std, ...}},
                'blue_ball_statistics': {position_N: {mean, std, ...}}
            }
        """
        analysis = {}

        # 红球各位置统计
        red_stats = {}
        for i, col in enumerate(self.red_ball_columns, 1):
            series = self.df[col].dropna().astype(int)
            red_stats[f'position_{i}'] = {
                'mean': series.mean(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'median': series.median()
            }

        # 蓝球各位置统计
        blue_stats = {}
        for i, col in enumerate(self.blue_ball_columns, 1):
            series = self.df[col].dropna().astype(int)
            blue_stats[f'position_{i}'] = {
                'mean': series.mean(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'median': series.median()
            }

        analysis['red_ball_statistics'] = red_stats
        analysis['blue_ball_statistics'] = blue_stats

        return analysis

    # ==================================================================
    #  热门 / 冷门号码
    # ==================================================================

    def find_hot_and_cold_numbers(self, window_size: int = 30) -> Dict:
        """
        基于最近 N 期数据识别热门和冷门号码。

        Args:
            window_size: 滑动窗口大小（期数），默认 30

        Returns:
            dict: {
                'hot_numbers':         {号码: 出现次数} top 10,
                'cold_numbers':        {号码: 出现次数} bottom 10,
                'frequency_analysis':  Counter 完整频率
            }
        """
        recent_df = self.df.tail(window_size)

        # 统计红球+蓝球全部号码的出现次数
        all_numbers = []
        for col in self.red_ball_columns + self.blue_ball_columns:
            all_numbers.extend(recent_df[col].dropna().astype(int).tolist())

        freq_counter = Counter(all_numbers)
        sorted_freq = sorted(freq_counter.items(), key=lambda x: x[1], reverse=True)

        hot_numbers = dict(sorted_freq[:10])    # 前 10 热门
        cold_numbers = dict(sorted_freq[-10:])  # 后 10 冷门

        return {
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'frequency_analysis': freq_counter
        }

    # ==================================================================
    #  连号模式
    # ==================================================================

    def analyze_consecutive_patterns(self) -> Dict:
        """
        分析每期开奖号码中的连号（相邻号码差值为 1）情况。

        Returns:
            dict: {
                'red_consecutive':  [每期红球连号数量],
                'blue_consecutive': [每期蓝球连号数量]
            }
        """
        consecutive_patterns = {
            'red_consecutive': [],
            'blue_consecutive': []
        }

        # 红球连号分析
        for _, row in self.df.iterrows():
            red_balls = sorted([
                row[col] for col in self.red_ball_columns
                if pd.notna(row[col])
            ])
            consecutive_count = sum(
                1 for i in range(len(red_balls) - 1)
                if red_balls[i + 1] - red_balls[i] == 1
            )
            consecutive_patterns['red_consecutive'].append(consecutive_count)

        # 蓝球连号分析
        for _, row in self.df.iterrows():
            blue_balls = sorted([
                row[col] for col in self.blue_ball_columns
                if pd.notna(row[col])
            ])
            consecutive_count = (
                1 if len(blue_balls) >= 2 and blue_balls[1] - blue_balls[0] == 1
                else 0
            )
            consecutive_patterns['blue_consecutive'].append(consecutive_count)

        return consecutive_patterns

    # ==================================================================
    #  奇偶比
    # ==================================================================

    def calculate_odd_even_ratio(self) -> pd.DataFrame:
        """
        计算每期的奇偶比。

        Returns:
            pd.DataFrame: 包含以下列:
                - red_odds, red_evens:   红球奇/偶数个数
                - blue_odds, blue_evens:  蓝球奇/偶数个数
                - red_odd_ratio:          红球奇数比例 (0~1)
                - blue_odd_ratio:         蓝球奇数比例 (0~1)
        """
        ratios = []

        for _, row in self.df.iterrows():
            red_odds = sum(
                1 for col in self.red_ball_columns
                if pd.notna(row[col]) and int(row[col]) % 2 == 1
            )
            blue_odds = sum(
                1 for col in self.blue_ball_columns
                if pd.notna(row[col]) and int(row[col]) % 2 == 1
            )

            ratios.append({
                'red_odds': red_odds,
                'red_evens': 5 - red_odds,
                'blue_odds': blue_odds,
                'blue_evens': 2 - blue_odds,
                'red_odd_ratio': red_odds / 5,
                'blue_odd_ratio': blue_odds / 2
            })

        return pd.DataFrame(ratios)

    # ==================================================================
    #  和值统计
    # ==================================================================

    def analyze_sum_statistics(self) -> Dict:
        """
        统计红球和值、蓝球和值、总和值的分布特征。

        Returns:
            dict: {
                'red_sum_stats':   {mean, std, min, max, median},
                'blue_sum_stats':  {mean, std, min, max, median},
                'total_sum_stats': {mean, std, min, max, median}
            }
        """
        # 红球和值
        red_sums = []
        for _, row in self.df.iterrows():
            r_sum = sum(
                row[col] for col in self.red_ball_columns
                if pd.notna(row[col])
            )
            red_sums.append(r_sum)

        # 蓝球和值
        blue_sums = []
        for _, row in self.df.iterrows():
            b_sum = sum(
                row[col] for col in self.blue_ball_columns
                if pd.notna(row[col])
            )
            blue_sums.append(b_sum)

        # 总和值 = 红球和值 + 蓝球和值
        total_sums = [r + b for r, b in zip(red_sums, blue_sums)]

        def _stats(arr):
            return {
                'mean': np.mean(arr),
                'std': np.std(arr),
                'min': np.min(arr),
                'max': np.max(arr),
                'median': np.median(arr)
            }

        return {
            'red_sum_stats': _stats(red_sums),
            'blue_sum_stats': _stats(blue_sums),
            'total_sum_stats': _stats(total_sums)
        }


# ============================================================================
#  可视化图表生成
# ============================================================================

def create_analysis_visualizations(
    analyzer: LotteryAnalyzer,
    save_path: str = None
):
    """
    生成分析可视化图表（PNG 格式）。

    生成图表:
        1. frequency_analysis.png  — 全量+近期红蓝球频率分布
        2. hot_cold_analysis.png   — 热门/冷门号码对比
        3. sum_distribution.png    — 和值分布直方图

    Args:
        analyzer: LotteryAnalyzer 实例
        save_path: 图片保存目录，默认 analysis_results/{当天日期}/
    """
    import os

    # 默认路径：按日期分目录
    if save_path is None:
        date_str = datetime.now().strftime("%Y%m%d")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(base_dir, "analysis_results", date_str)

    os.makedirs(save_path, exist_ok=True)

    # 设置中文字体（避免中文乱码）
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # ---- 图表 1: 号码频率分布 ----
    freq_data = analyzer.get_number_frequency()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # 红球全量频率
    red_freq = freq_data['red_frequency']
    ax1.bar(red_freq.index, red_freq.values, color='red', alpha=0.7)
    ax1.set_title('红球号码频率分布 (全量)')
    ax1.set_xlabel('号码')
    ax1.set_ylabel('出现次数')
    ax1.grid(True, alpha=0.3)

    # 蓝球全量频率
    blue_freq = freq_data['blue_frequency']
    ax2.bar(blue_freq.index, blue_freq.values, color='blue', alpha=0.7)
    ax2.set_title('蓝球号码频率分布 (全量)')
    ax2.set_xlabel('号码')
    ax2.set_ylabel('出现次数')
    ax2.grid(True, alpha=0.3)

    # 近期红球频率（最近 30 期）
    recent_freq = analyzer.get_recent_frequency(30)
    ax3.bar(
        recent_freq['recent_red_frequency'].index,
        recent_freq['recent_red_frequency'].values,
        color='orange', alpha=0.7
    )
    ax3.set_title('近期 (30期) 红球频率')
    ax3.set_xlabel('号码')
    ax3.set_ylabel('出现次数')
    ax3.grid(True, alpha=0.3)

    # 近期蓝球频率
    ax4.bar(
        recent_freq['recent_blue_frequency'].index,
        recent_freq['recent_blue_frequency'].values,
        color='lightblue', alpha=0.7
    )
    ax4.set_title('近期 (30期) 蓝球频率')
    ax4.set_xlabel('号码')
    ax4.set_ylabel('出现次数')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        os.path.join(save_path, "frequency_analysis.png"),
        dpi=300, bbox_inches='tight'
    )
    plt.close()

    # ---- 图表 2: 热门/冷门号码 ----
    hot_cold_data = analyzer.find_hot_and_cold_numbers(50)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # 热门号码 Top 10
    hot_nums = list(hot_cold_data['hot_numbers'].keys())
    hot_counts = list(hot_cold_data['hot_numbers'].values())
    ax1.bar(range(len(hot_nums)), hot_counts, color='red', alpha=0.7)
    ax1.set_title('热门号码 Top 10')
    ax1.set_xlabel('号码')
    ax1.set_ylabel('出现次数')
    ax1.set_xticks(range(len(hot_nums)))
    ax1.set_xticklabels(hot_nums)
    ax1.grid(True, alpha=0.3)

    # 冷门号码 Bottom 10
    cold_nums = list(hot_cold_data['cold_numbers'].keys())
    cold_counts = list(hot_cold_data['cold_numbers'].values())
    ax2.bar(range(len(cold_nums)), cold_counts, color='blue', alpha=0.7)
    ax2.set_title('冷门号码 Bottom 10')
    ax2.set_xlabel('号码')
    ax2.set_ylabel('出现次数')
    ax2.set_xticks(range(len(cold_nums)))
    ax2.set_xticklabels(cold_nums)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        os.path.join(save_path, "hot_cold_analysis.png"),
        dpi=300, bbox_inches='tight'
    )
    plt.close()

    # ---- 图表 3: 和值分布 ----
    sum_stats = analyzer.analyze_sum_statistics()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # 红球和值直方图
    red_sums = []
    for _, row in analyzer.df.iterrows():
        r_sum = sum(
            row[col] for col in analyzer.red_ball_columns
            if pd.notna(row[col])
        )
        red_sums.append(r_sum)

    ax1.hist(red_sums, bins=30, color='red', alpha=0.7, edgecolor='black')
    ax1.axvline(
        sum_stats['red_sum_stats']['mean'],
        color='red', linestyle='--',
        label=f"平均值: {sum_stats['red_sum_stats']['mean']:.1f}"
    )
    ax1.set_title('红球和值分布')
    ax1.set_xlabel('和值')
    ax1.set_ylabel('频次')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 总和值直方图
    total_sums = []
    for _, row in analyzer.df.iterrows():
        r_sum = sum(
            row[col] for col in analyzer.red_ball_columns
            if pd.notna(row[col])
        )
        b_sum = sum(
            row[col] for col in analyzer.blue_ball_columns
            if pd.notna(row[col])
        )
        total_sums.append(r_sum + b_sum)

    ax2.hist(total_sums, bins=30, color='purple', alpha=0.7, edgecolor='black')
    ax2.axvline(
        sum_stats['total_sum_stats']['mean'],
        color='purple', linestyle='--',
        label=f"平均值: {sum_stats['total_sum_stats']['mean']:.1f}"
    )
    ax2.set_title('总和值分布')
    ax2.set_xlabel('总和值')
    ax2.set_ylabel('频次')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        os.path.join(save_path, "sum_distribution.png"),
        dpi=300, bbox_inches='tight'
    )
    plt.close()

    logger.info("分析图表已保存 → %s", save_path)


# ============================================================================
#  独立运行入口
# ============================================================================

def main():
    """独立测试分析功能。"""
    try:
        df = pd.read_excel(
            "super_lotto_history.xlsx", sheet_name='lottery_data'
        )
        analyzer = LotteryAnalyzer(df)

        # 频率分析
        print("=== 号码频率分析 ===")
        freq_data = analyzer.get_number_frequency()
        print("红球频率前10:", freq_data['red_frequency'].nlargest(10).to_dict())
        print("蓝球频率前5:", freq_data['blue_frequency'].nlargest(5).to_dict())

        # 冷热号
        print("\n=== 热门冷门号码 ===")
        hot_cold = analyzer.find_hot_and_cold_numbers(30)
        print("热门号码:", hot_cold['hot_numbers'])
        print("冷门号码:", hot_cold['cold_numbers'])

        # 和值统计
        print("\n=== 和值统计 ===")
        sum_stats = analyzer.analyze_sum_statistics()
        print("红球和值:", sum_stats['red_sum_stats'])
        print("总和值:", sum_stats['total_sum_stats'])

        # 生成图表
        create_analysis_visualizations(analyzer)

    except FileNotFoundError:
        print("数据文件未找到，请先运行爬虫获取数据")
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main()
