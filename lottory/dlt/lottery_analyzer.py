import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

class LotteryAnalyzer:
    """彩票数据分析器"""
    
    def __init__(self, data_df: pd.DataFrame):
        self.df = data_df.copy()
        self.red_ball_columns = ['red1', 'red2', 'red3', 'red4', 'red5']
        self.blue_ball_columns = ['blue1', 'blue2']
        
        # 确保数据按期号排序
        if 'issue' in self.df.columns:
            self.df = self.df.sort_values('issue').reset_index(drop=True)
    
    def get_number_frequency(self) -> Dict[str, pd.Series]:
        """统计各号码出现频率"""
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
        """统计近期号码频率"""
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
    
    def analyze_number_distribution(self) -> Dict:
        """分析号码分布特征"""
        analysis = {}
        
        # 红球分析
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
        
        # 蓝球分析
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
    
    def find_hot_and_cold_numbers(self, window_size: int = 30) -> Dict:
        """找出热门和冷门号码"""
        recent_df = self.df.tail(window_size)
        
        # 统计近期出现次数
        all_numbers = []
        for col in self.red_ball_columns + self.blue_ball_columns:
            all_numbers.extend(recent_df[col].dropna().astype(int).tolist())
        
        freq_counter = Counter(all_numbers)
        
        # 找出最热和最冷的号码
        sorted_freq = sorted(freq_counter.items(), key=lambda x: x[1], reverse=True)
        
        hot_numbers = dict(sorted_freq[:10])  # 前10个热门号码
        cold_numbers = dict(sorted_freq[-10:])  # 后10个冷门号码
        
        return {
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'frequency_analysis': freq_counter
        }
    
    def analyze_consecutive_patterns(self) -> Dict:
        """分析连号模式"""
        consecutive_patterns = {
            'red_consecutive': [],
            'blue_consecutive': []
        }
        
        # 分析红球连号
        for _, row in self.df.iterrows():
            red_balls = sorted([row[col] for col in self.red_ball_columns if pd.notna(row[col])])
            consecutive_count = 0
            
            for i in range(len(red_balls) - 1):
                if red_balls[i+1] - red_balls[i] == 1:
                    consecutive_count += 1
            
            consecutive_patterns['red_consecutive'].append(consecutive_count)
        
        # 分析蓝球连号
        for _, row in self.df.iterrows():
            blue_balls = sorted([row[col] for col in self.blue_ball_columns if pd.notna(row[col])])
            consecutive_count = 0
            
            if len(blue_balls) >= 2 and blue_balls[1] - blue_balls[0] == 1:
                consecutive_count = 1
            
            consecutive_patterns['blue_consecutive'].append(consecutive_count)
        
        return consecutive_patterns
    
    def calculate_odd_even_ratio(self) -> pd.DataFrame:
        """计算奇偶比"""
        ratios = []
        
        for _, row in self.df.iterrows():
            # 红球奇偶统计
            red_odds = sum(1 for col in self.red_ball_columns 
                          if pd.notna(row[col]) and int(row[col]) % 2 == 1)
            red_evens = 5 - red_odds
            
            # 蓝球奇偶统计
            blue_odds = sum(1 for col in self.blue_ball_columns 
                           if pd.notna(row[col]) and int(row[col]) % 2 == 1)
            blue_evens = 2 - blue_odds
            
            ratios.append({
                'red_odds': red_odds,
                'red_evens': red_evens,
                'blue_odds': blue_odds,
                'blue_evens': blue_evens,
                'red_odd_ratio': red_odds / 5,
                'blue_odd_ratio': blue_odds / 2
            })
        
        return pd.DataFrame(ratios)
    
    def analyze_sum_statistics(self) -> Dict:
        """分析和值统计"""
        # 红球和值
        red_sums = []
        for _, row in self.df.iterrows():
            red_sum = sum(row[col] for col in self.red_ball_columns if pd.notna(row[col]))
            red_sums.append(red_sum)
        
        # 蓝球和值
        blue_sums = []
        for _, row in self.df.iterrows():
            blue_sum = sum(row[col] for col in self.blue_ball_columns if pd.notna(row[col]))
            blue_sums.append(blue_sum)
        
        # 总和值
        total_sums = [r + b for r, b in zip(red_sums, blue_sums)]
        
        return {
            'red_sum_stats': {
                'mean': np.mean(red_sums),
                'std': np.std(red_sums),
                'min': np.min(red_sums),
                'max': np.max(red_sums),
                'median': np.median(red_sums)
            },
            'blue_sum_stats': {
                'mean': np.mean(blue_sums),
                'std': np.std(blue_sums),
                'min': np.min(blue_sums),
                'max': np.max(blue_sums),
                'median': np.median(blue_sums)
            },
            'total_sum_stats': {
                'mean': np.mean(total_sums),
                'std': np.std(total_sums),
                'min': np.min(total_sums),
                'max': np.max(total_sums),
                'median': np.median(total_sums)
            }
        }

def create_analysis_visualizations(analyzer: LotteryAnalyzer, save_path: str = "analysis_plots"):
    """创建分析可视化图表"""
    import os
    import matplotlib.font_manager as fm
    
    # 创建保存目录
    os.makedirs(save_path, exist_ok=True)
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 1. 号码频率分布图
    freq_data = analyzer.get_number_frequency()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 红球频率
    red_freq = freq_data['red_frequency']
    ax1.bar(red_freq.index, red_freq.values, color='red', alpha=0.7)
    ax1.set_title('红球号码频率分布')
    ax1.set_xlabel('号码')
    ax1.set_ylabel('出现次数')
    ax1.grid(True, alpha=0.3)
    
    # 蓝球频率
    blue_freq = freq_data['blue_frequency']
    ax2.bar(blue_freq.index, blue_freq.values, color='blue', alpha=0.7)
    ax2.set_title('蓝球号码频率分布')
    ax2.set_xlabel('号码')
    ax2.set_ylabel('出现次数')
    ax2.grid(True, alpha=0.3)
    
    # 近期频率对比
    recent_freq = analyzer.get_recent_frequency(30)
    ax3.bar(recent_freq['recent_red_frequency'].index, 
            recent_freq['recent_red_frequency'].values, 
            color='orange', alpha=0.7)
    ax3.set_title('近期(30期)红球频率')
    ax3.set_xlabel('号码')
    ax3.set_ylabel('出现次数')
    ax3.grid(True, alpha=0.3)
    
    ax4.bar(recent_freq['recent_blue_frequency'].index, 
            recent_freq['recent_blue_frequency'].values, 
            color='lightblue', alpha=0.7)
    ax4.set_title('近期(30期)蓝球频率')
    ax4.set_xlabel('号码')
    ax4.set_ylabel('出现次数')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{save_path}/frequency_analysis.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2. 热门冷门号码分析
    hot_cold_data = analyzer.find_hot_and_cold_numbers(50)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 热门号码
    hot_nums = list(hot_cold_data['hot_numbers'].keys())
    hot_counts = list(hot_cold_data['hot_numbers'].values())
    bars1 = ax1.bar(range(len(hot_nums)), hot_counts, color='red', alpha=0.7)
    ax1.set_title('热门号码 Top 10')
    ax1.set_xlabel('号码')
    ax1.set_ylabel('出现次数')
    ax1.set_xticks(range(len(hot_nums)))
    ax1.set_xticklabels(hot_nums)
    ax1.grid(True, alpha=0.3)
    
    # 冷门号码
    cold_nums = list(hot_cold_data['cold_numbers'].keys())
    cold_counts = list(hot_cold_data['cold_numbers'].values())
    bars2 = ax2.bar(range(len(cold_nums)), cold_counts, color='blue', alpha=0.7)
    ax2.set_title('冷门号码 Bottom 10')
    ax2.set_xlabel('号码')
    ax2.set_ylabel('出现次数')
    ax2.set_xticks(range(len(cold_nums)))
    ax2.set_xticklabels(cold_nums)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{save_path}/hot_cold_analysis.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3. 和值分布图
    sum_stats = analyzer.analyze_sum_statistics()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 红球和值分布
    red_sums = []
    for _, row in analyzer.df.iterrows():
        red_sum = sum(row[col] for col in analyzer.red_ball_columns if pd.notna(row[col]))
        red_sums.append(red_sum)
    
    ax1.hist(red_sums, bins=30, color='red', alpha=0.7, edgecolor='black')
    ax1.axvline(sum_stats['red_sum_stats']['mean'], color='red', linestyle='--', 
                label=f"平均值: {sum_stats['red_sum_stats']['mean']:.1f}")
    ax1.set_title('红球和值分布')
    ax1.set_xlabel('和值')
    ax1.set_ylabel('频次')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 总和值分布
    total_sums = []
    for _, row in analyzer.df.iterrows():
        red_sum = sum(row[col] for col in analyzer.red_ball_columns if pd.notna(row[col]))
        blue_sum = sum(row[col] for col in analyzer.blue_ball_columns if pd.notna(row[col]))
        total_sums.append(red_sum + blue_sum)
    
    ax2.hist(total_sums, bins=30, color='purple', alpha=0.7, edgecolor='black')
    ax2.axvline(sum_stats['total_sum_stats']['mean'], color='purple', linestyle='--',
                label=f"平均值: {sum_stats['total_sum_stats']['mean']:.1f}")
    ax2.set_title('总和值分布')
    ax2.set_xlabel('总和值')
    ax2.set_ylabel('频次')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{save_path}/sum_distribution.png", dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """测试分析功能"""
    # 读取数据进行测试
    try:
        df = pd.read_excel("super_lotto_history.xlsx", sheet_name='lottery_data')
        analyzer = LotteryAnalyzer(df)
        
        # 执行各种分析
        print("=== 号码频率分析 ===")
        freq_data = analyzer.get_number_frequency()
        print("红球频率前10:", freq_data['red_frequency'].nlargest(10))
        print("蓝球频率前5:", freq_data['blue_frequency'].nlargest(5))
        
        print("\n=== 热门冷门号码 ===")
        hot_cold = analyzer.find_hot_and_cold_numbers(30)
        print("热门号码:", hot_cold['hot_numbers'])
        print("冷门号码:", hot_cold['cold_numbers'])
        
        print("\n=== 和值统计 ===")
        sum_stats = analyzer.analyze_sum_statistics()
        print("红球和值统计:", sum_stats['red_sum_stats'])
        print("总和值统计:", sum_stats['total_sum_stats'])
        
        # 创建可视化图表
        create_analysis_visualizations(analyzer)
        
    except FileNotFoundError:
        print("数据文件未找到，请先运行爬虫获取数据")
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()