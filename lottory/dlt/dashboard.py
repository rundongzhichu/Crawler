import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
from lottery_analyzer import LotteryAnalyzer
warnings.filterwarnings('ignore')

# 设置英文字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class LotteryVisualizer:
    """彩票数据可视化仪表板"""
    
    def __init__(self, data_df: pd.DataFrame):
        self.df = data_df.copy()
        self.red_ball_columns = ['red1', 'red2', 'red3', 'red4', 'red5']
        self.blue_ball_columns = ['blue1', 'blue2']
        self.analyzer = LotteryAnalyzer(data_df)
        
        # 设置英文字体支持
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 设置绘图样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_dashboard_summary(self) -> go.Figure:
        """创建仪表板概览图"""
        # 计算关键统计数据
        total_draws = len(self.df)
        
        # 最新一期信息
        latest_issue = self.df.iloc[-1]['issue'] if 'issue' in self.df.columns else 'N/A'
        latest_date = self.df.iloc[-1]['date'] if 'date' in self.df.columns else 'N/A'
        
        # 号码范围统计
        red_min = min([self.df[col].min() for col in self.red_ball_columns])
        red_max = max([self.df[col].max() for col in self.red_ball_columns])
        blue_min = min([self.df[col].min() for col in self.blue_ball_columns])
        blue_max = max([self.df[col].max() for col in self.blue_ball_columns])
        
        # 创建仪表板
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('开奖期数统计', '号码范围分布', '最新开奖信息', '数据完整性'),
            specs=[[{"type": "indicator"}, {"type": "bar"}],
                   [{"type": "table"}, {"type": "indicator"}]]
        )
        
        # 总期数指标
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=total_draws,
                title={"text": "总开奖期数"},
                number={'font': {'size': 50}}
            ),
            row=1, col=1
        )
        
        # 号码范围柱状图
        fig.add_trace(
            go.Bar(
                x=['红球最小值', '红球最大值', '蓝球最小值', '蓝球最大值'],
                y=[red_min, red_max, blue_min, blue_max],
                marker_color=['red', 'red', 'blue', 'blue']
            ),
            row=1, col=2
        )
        
        # 最新开奖表格
        latest_data = self.df.iloc[-1:][['issue', 'date'] + self.red_ball_columns + self.blue_ball_columns]
        fig.add_trace(
            go.Table(
                header=dict(values=['期号', '日期'] + [f'红球{i+1}' for i in range(5)] + [f'蓝球{i+1}' for i in range(2)],
                           fill_color='paleturquoise',
                           align='left'),
                cells=dict(values=[latest_data[col] for col in latest_data.columns],
                          fill_color='lavender',
                          align='left')
            ),
            row=2, col=1
        )
        
        # 数据完整性指标
        completeness = (self.df.isnull().sum().sum() / (len(self.df) * len(self.df.columns))) * 100
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=100 - completeness,
                title={'text': "数据完整度 (%)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkgreen"},
                       'steps': [{'range': [0, 70], 'color': "lightgray"},
                                {'range': [70, 90], 'color': "gray"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75,
                                   'value': 95}}
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="大乐透数据分析仪表板")
        return fig
    
    def create_frequency_heatmap(self) -> plt.Figure:
        """创建号码频率热力图"""
        # 统计每个号码在各个位置的出现次数
        position_freq = {}
        
        # 红球位置频率
        for pos_idx, col in enumerate(self.red_ball_columns):
            freq_series = self.df[col].value_counts().sort_index()
            position_freq[f'红球位置{pos_idx+1}'] = freq_series
        
        # 蓝球位置频率
        for pos_idx, col in enumerate(self.blue_ball_columns):
            freq_series = self.df[col].value_counts().sort_index()
            position_freq[f'蓝球位置{pos_idx+1}'] = freq_series
        
        # 创建热力图数据
        all_numbers = range(1, 36)  # 红球1-35
        heatmap_data = []
        
        for pos_name in [f'红球位置{i}' for i in range(1, 6)] + [f'蓝球位置{i}' for i in range(1, 3)]:
            row_data = []
            freq_dict = position_freq.get(pos_name, {})
            for num in all_numbers:
                row_data.append(freq_dict.get(num, 0))
            heatmap_data.append(row_data)
        
        # 绘制热力图
        fig, ax = plt.subplots(figsize=(15, 8))
        
        im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
        
        # 设置标签
        ax.set_yticks(range(len(heatmap_data)))
        ax.set_yticklabels([f'红球位置{i}' for i in range(1, 6)] + [f'蓝球位置{i}' for i in range(1, 3)])
        ax.set_xticks(range(0, 35, 5))
        ax.set_xticklabels(range(1, 36, 5))
        
        # 添加数值标注
        for i in range(len(heatmap_data)):
            for j in range(len(heatmap_data[0])):
                if heatmap_data[i][j] > 0:
                    text = ax.text(j, i, heatmap_data[i][j],
                                 ha="center", va="center", color="black", fontsize=8)
        
        ax.set_title('各位置号码出现频率热力图', fontsize=16, pad=20)
        ax.set_xlabel('号码', fontsize=12)
        ax.set_ylabel('位置', fontsize=12)
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('出现次数', rotation=270, labelpad=20)
        
        plt.tight_layout()
        return fig
    
    def create_trend_analysis_plots(self) -> plt.Figure:
        """创建趋势分析图"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 红球和值趋势
        red_sums = []
        for _, row in self.df.iterrows():
            red_sum = sum(row[col] for col in self.red_ball_columns if pd.notna(row[col]))
            red_sums.append(red_sum)
        
        ax1.plot(range(len(red_sums)), red_sums, linewidth=1, alpha=0.7, color='red')
        ax1.set_title('红球和值变化趋势')
        ax1.set_xlabel('期数')
        ax1.set_ylabel('和值')
        ax1.grid(True, alpha=0.3)
        
        # 添加移动平均线
        if len(red_sums) > 10:
            moving_avg = pd.Series(red_sums).rolling(window=10).mean()
            ax1.plot(range(len(moving_avg)), moving_avg, color='darkred', linewidth=2, label='10期移动平均')
            ax1.legend()
        
        # 2. 蓝球和值趋势
        blue_sums = []
        for _, row in self.df.iterrows():
            blue_sum = sum(row[col] for col in self.blue_ball_columns if pd.notna(row[col]))
            blue_sums.append(blue_sum)
        
        ax2.plot(range(len(blue_sums)), blue_sums, linewidth=1, alpha=0.7, color='blue')
        ax2.set_title('蓝球和值变化趋势')
        ax2.set_xlabel('期数')
        ax2.set_ylabel('和值')
        ax2.grid(True, alpha=0.3)
        
        # 3. 奇偶比趋势
        odd_ratios = []
        for _, row in self.df.iterrows():
            red_odds = sum(1 for col in self.red_ball_columns 
                          if pd.notna(row[col]) and int(row[col]) % 2 == 1)
            odd_ratio = red_odds / 5
            odd_ratios.append(odd_ratio)
        
        ax3.plot(range(len(odd_ratios)), odd_ratios, linewidth=1, alpha=0.7, color='green')
        ax3.set_title('红球奇偶比趋势')
        ax3.set_xlabel('期数')
        ax3.set_ylabel('奇数比例')
        ax3.set_ylim(0, 1)
        ax3.grid(True, alpha=0.3)
        
        # 4. 连号数量趋势
        consecutive_counts = []
        for _, row in self.df.iterrows():
            red_balls = sorted([row[col] for col in self.red_ball_columns if pd.notna(row[col])])
            consecutive_count = 0
            for i in range(len(red_balls) - 1):
                if red_balls[i+1] - red_balls[i] == 1:
                    consecutive_count += 1
            consecutive_counts.append(consecutive_count)
        
        ax4.plot(range(len(consecutive_counts)), consecutive_counts, linewidth=1, alpha=0.7, color='orange')
        ax4.set_title('红球连号数量趋势')
        ax4.set_xlabel('期数')
        ax4.set_ylabel('连号数量')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_number_distribution_comparison(self) -> plt.Figure:
        """创建号码分布对比图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 红球分布
        all_red_numbers = []
        for col in self.red_ball_columns:
            all_red_numbers.extend(self.df[col].dropna().astype(int).tolist())
        
        # 按区间分组
        intervals = [(1, 12), (13, 24), (25, 35)]
        interval_labels = ['1-12', '13-24', '25-35']
        interval_counts = []
        
        for start, end in intervals:
            count = sum(1 for num in all_red_numbers if start <= num <= end)
            interval_counts.append(count)
        
        bars1 = ax1.bar(interval_labels, interval_counts, color=['lightcoral', 'lightsalmon', 'indianred'])
        ax1.set_title('红球号码区间分布')
        ax1.set_xlabel('号码区间')
        ax1.set_ylabel('出现次数')
        ax1.grid(True, alpha=0.3)
        
        # 添加数值标签
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 蓝球分布
        all_blue_numbers = []
        for col in self.blue_ball_columns:
            all_blue_numbers.extend(self.df[col].dropna().astype(int).tolist())
        
        blue_intervals = [(1, 6), (7, 12)]
        blue_labels = ['1-6', '7-12']
        blue_counts = []
        
        for start, end in blue_intervals:
            count = sum(1 for num in all_blue_numbers if start <= num <= end)
            blue_counts.append(count)
        
        bars2 = ax2.bar(blue_labels, blue_counts, color=['lightblue', 'steelblue'])
        ax2.set_title('蓝球号码区间分布')
        ax2.set_xlabel('号码区间')
        ax2.set_ylabel('出现次数')
        ax2.grid(True, alpha=0.3)
        
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        return fig
    
    def create_correlation_analysis(self) -> plt.Figure:
        """创建相关性分析图"""
        # 准备相关性数据
        correlation_data = self.df[self.red_ball_columns + self.blue_ball_columns].corr()
        
        # 创建热力图
        fig, ax = plt.subplots(figsize=(10, 8))
        mask = np.triu(np.ones_like(correlation_data, dtype=bool))
        
        sns.heatmap(correlation_data, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8}, ax=ax)
        
        ax.set_title('号码位置间相关性分析', fontsize=16, pad=20)
        plt.tight_layout()
        return fig
    
    def create_interactive_prediction_dashboard(self, predictions: list) -> go.Figure:
        """创建交互式预测仪表板"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('不同预测方法对比', '红球预测分布', '蓝球预测分布', '预测置信度'),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "pie"}, {"type": "indicator"}]]
        )
        
        # 收集所有预测结果
        all_red_predictions = []
        all_blue_predictions = []
        method_names = []
        
        for pred in predictions:
            all_red_predictions.extend(pred['numbers']['red_balls'])
            all_blue_predictions.extend(pred['numbers']['blue_balls'])
            method_names.extend([pred['method']] * 5)  # 每个方法5个红球
        
        # 1. 不同方法预测对比（只显示红球）
        from collections import Counter
        red_counter = Counter(all_red_predictions)
        top_red = red_counter.most_common(10)
        
        fig.add_trace(
            go.Bar(
                x=[str(num) for num, count in top_red],
                y=[count for num, count in top_red],
                name='红球预测次数',
                marker_color='red'
            ),
            row=1, col=1
        )
        
        # 2. 红球预测分布饼图
        fig.add_trace(
            go.Pie(
                labels=[str(num) for num, count in top_red],
                values=[count for num, count in top_red],
                name='红球分布',
                hole=0.3
            ),
            row=1, col=2
        )
        
        # 3. 蓝球预测分布
        blue_counter = Counter(all_blue_predictions)
        top_blue = blue_counter.most_common(5)
        
        fig.add_trace(
            go.Pie(
                labels=[str(num) for num, count in top_blue],
                values=[count for num, count in top_blue],
                name='蓝球分布',
                marker_colors=['blue', 'lightblue', 'royalblue', 'navy', 'skyblue']
            ),
            row=2, col=1
        )
        
        # 4. 预测置信度指标
        confidence_score = len(set(all_red_predictions)) / len(all_red_predictions) * 100
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=confidence_score,
                title={'text': "预测一致性 (%)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkgreen"}}
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False, 
                         title_text="彩票预测结果分析仪表板")
        return fig


def create_unified_dashboard(data_df: pd.DataFrame, predictions: list = None, filename: str = "dlt_analysis_report.html"):
    """创建统一的HTML分析报告"""
    import os
    
    visualizer = LotteryVisualizer(data_df)
    
    # 创建HTML内容
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DLT Analysis Report</title>
        <meta charset="UTF-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .section { margin: 30px 0; }
            .section-title { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
            .chart-container { width: 100%; height: 500px; margin: 20px 0; }
            .summary-table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .summary-table th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>🎯 DLT Lottery Analysis Report</h1>
        <div class="section">
            <h2 class="section-title">📊 Data Summary</h2>
    """
    
    # 添加数据摘要
    total_records = len(data_df)
    latest_issue = data_df.iloc[0]['issue'] if not data_df.empty else 'N/A'
    latest_date = data_df.iloc[0]['date'] if not data_df.empty else 'N/A'
    
    html_content += f"""
            <table class="summary-table">
                <tr><th>Total Records</th><td>{total_records}</td></tr>
                <tr><th>Latest Issue</th><td>{latest_issue}</td></tr>
                <tr><th>Latest Date</th><td>{latest_date}</td></tr>
            </table>
        </div>
    """
    
    # 1. 仪表板概览
    print("Generating dashboard overview...")
    dashboard_fig = visualizer.create_dashboard_summary()
    dashboard_json = dashboard_fig.to_json()
    
    html_content += """
        <div class="section">
            <h2 class="section-title">📈 Dashboard Overview</h2>
            <div id="dashboard-overview" class="chart-container"></div>
        </div>
    """
    
    # 2. 频率分析
    print("Generating frequency analysis...")
    freq_data = visualizer.analyzer.get_number_frequency()
    red_freq = freq_data['red_frequency']
    blue_freq = freq_data['blue_frequency']
    
    # 创建频率图表
    freq_fig = go.Figure()
    freq_fig.add_trace(go.Bar(x=red_freq.index, y=red_freq.values, name='Red Balls', marker_color='red'))
    freq_fig.add_trace(go.Bar(x=blue_freq.index, y=blue_freq.values, name='Blue Balls', marker_color='blue'))
    freq_fig.update_layout(title='Number Frequency Distribution', xaxis_title='Numbers', yaxis_title='Frequency')
    freq_json = freq_fig.to_json()
    
    html_content += """
        <div class="section">
            <h2 class="section-title">🔢 Number Frequency Analysis</h2>
            <div id="frequency-analysis" class="chart-container"></div>
        </div>
    """
    
    # 3. 热门冷门号码
    print("Generating hot/cold numbers analysis...")
    hot_cold_data = visualizer.analyzer.find_hot_and_cold_numbers(30)
    hot_nums = list(hot_cold_data['hot_numbers'].keys())[:10]
    hot_counts = list(hot_cold_data['hot_numbers'].values())[:10]
    cold_nums = list(hot_cold_data['cold_numbers'].keys())[:10]
    cold_counts = list(hot_cold_data['cold_numbers'].values())[:10]
    
    hot_cold_fig = make_subplots(rows=1, cols=2, subplot_titles=('Hot Numbers (Top 10)', 'Cold Numbers (Bottom 10)'))
    hot_cold_fig.add_trace(go.Bar(x=hot_nums, y=hot_counts, name='Hot Numbers', marker_color='red'), row=1, col=1)
    hot_cold_fig.add_trace(go.Bar(x=cold_nums, y=cold_counts, name='Cold Numbers', marker_color='blue'), row=1, col=2)
    hot_cold_fig.update_layout(title='Hot and Cold Numbers Analysis')
    hot_cold_json = hot_cold_fig.to_json()
    
    html_content += """
        <div class="section">
            <h2 class="section-title">🔥 Hot and Cold Numbers</h2>
            <div id="hot-cold-analysis" class="chart-container"></div>
        </div>
    """
    
    # 4. 和值分布
    print("Generating sum distribution...")
    sum_stats = visualizer.analyzer.analyze_sum_statistics()
    red_sums = []
    for _, row in data_df.iterrows():
        red_sum = sum(row[col] for col in visualizer.red_ball_columns if pd.notna(row[col]))
        red_sums.append(red_sum)
    
    sum_fig = go.Figure()
    sum_fig.add_trace(go.Histogram(x=red_sums, name='Red Ball Sums', nbinsx=30, marker_color='red'))
    sum_fig.add_vline(x=sum_stats['red_sum_stats']['mean'], line_dash="dash", line_color="red", 
                     annotation_text=f"Mean: {sum_stats['red_sum_stats']['mean']:.1f}")
    sum_fig.update_layout(title='Red Ball Sum Distribution', xaxis_title='Sum Values', yaxis_title='Frequency')
    sum_json = sum_fig.to_json()
    
    html_content += """
        <div class="section">
            <h2 class="section-title">🧮 Sum Distribution Analysis</h2>
            <div id="sum-distribution" class="chart-container"></div>
        </div>
    """
    
    # 5. 预测结果（如果有）
    if predictions:
        print("Generating prediction analysis...")
        pred_fig = visualizer.create_interactive_prediction_dashboard(predictions)
        pred_json = pred_fig.to_json()
        
        html_content += """
        <div class="section">
            <h2 class="section-title">🔮 Prediction Results</h2>
            <div id="prediction-analysis" class="chart-container"></div>
        </div>
        """
    else:
        pred_json = None
    
    # 添加JavaScript
    html_content += """
        <script>
            // Dashboard Overview
            Plotly.newPlot('dashboard-overview', 
                JSON.parse('""" + dashboard_json.replace('"', '\\"') + """')
            );
            
            // Frequency Analysis
            Plotly.newPlot('frequency-analysis',
                JSON.parse('""" + freq_json.replace('"', '\\"') + """')
            );
            
            // Hot/Cold Numbers
            Plotly.newPlot('hot-cold-analysis',
                JSON.parse('""" + hot_cold_json.replace('"', '\\"') + """')
            );
            
            // Sum Distribution
            Plotly.newPlot('sum-distribution',
                JSON.parse('""" + sum_json.replace('"', '\\"') + """')
            );
    """
    
    if pred_json:
        html_content += f"""
            // Prediction Analysis
            Plotly.newPlot('prediction-analysis',
                JSON.parse('""" + pred_json.replace('"', '\\"') + """')
            );
        """
    
    html_content += """
        </script>
    </body>
    </html>
    """
    
    # 保存HTML文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Unified dashboard saved to: {filename}")
    return filename

def main():
    """测试可视化功能"""
    try:
        # 读取数据
        df = pd.read_excel("super_lotto_history.xlsx", sheet_name='lottery_data')
        
        # 生成基础可视化
        create_comprehensive_dashboard(df)
        
        # 如果有预测模块，也可以生成预测可视化
        try:
            from predictor import LotteryPredictor
            predictor = LotteryPredictor(df)
            predictions = predictor.generate_multiple_predictions(3)
            create_comprehensive_dashboard(df, predictions)
        except ImportError:
            print("预测模块未找到，跳过预测可视化")
            
    except FileNotFoundError:
        print("数据文件未找到，请先运行爬虫获取数据")
    except Exception as e:
        print(f"可视化过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()