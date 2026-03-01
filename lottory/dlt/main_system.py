#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透彩票分析预测系统
Lottery Analysis and Prediction System for Super Lotto
"""

import pandas as pd
import argparse
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_api_crawler import OfficialApiCrawler
from lottery_analyzer import LotteryAnalyzer, create_analysis_visualizations
from predictor import LotteryPredictor, evaluate_prediction_accuracy
from dashboard import create_unified_dashboard

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lottery_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LotterySystem:
    """大乐透彩票分析系统主类"""
    
    def __init__(self, data_file: str = "dlt_history.xlsx"):
        self.data_file = data_file
        self.df = None
        self.crawler = OfficialApiCrawler()
        self.analyzer = None
        self.predictor = None
        
    def initialize_system(self):
        """初始化系统组件"""
        logger.info("初始化彩票分析系统...")
        
        # 尝试加载现有数据
        self.load_existing_data()
        
        # 初始化各组件
        if self.df is not None and not self.df.empty:
            self.analyzer = LotteryAnalyzer(self.df)
            self.predictor = LotteryPredictor(self.df)
            logger.info("系统初始化完成")
        else:
            logger.warning("未找到历史数据，部分功能可能受限")
    
    def load_existing_data(self):
        """加载现有数据文件"""
        try:
            if os.path.exists(self.data_file):
                self.df = pd.read_excel(self.data_file, sheet_name='lottery_data')
                logger.info(f"成功加载 {len(self.df)} 条历史数据")
            else:
                logger.info("数据文件不存在，需要先获取数据")
        except Exception as e:
            logger.error(f"加载数据文件失败: {str(e)}")
            self.df = None
    
    def crawl_new_data(self, max_pages: int = None, force_update: bool = False):
        """爬取新的彩票数据"""
        logger.info("开始爬取大乐透数据...")
        
        try:
            # 获取数据
            raw_data = self.crawler.fetch_all_history(max_pages)
            
            if not raw_data:
                logger.error("未能获取到任何数据")
                return False
            
            # 处理数据
            new_df = self.crawler.process_official_data(raw_data)
            
            if new_df.empty:
                logger.error("数据处理后为空")
                return False
            
            # 合并或更新数据
            if self.df is not None and not force_update:
                # 合并新旧数据，去重
                combined_df = pd.concat([self.df, new_df]).drop_duplicates(subset=['issue'])
                combined_df = combined_df.sort_values('issue').reset_index(drop=True)
                self.df = combined_df
            else:
                self.df = new_df
            
            # 保存数据
            self.crawler.save_to_excel(self.df, self.data_file)
            logger.info(f"成功获取并保存 {len(new_df)} 条新数据")
            
            # 重新初始化分析组件
            self.initialize_system()
            return True
            
        except Exception as e:
            logger.error(f"数据爬取过程中出现错误: {str(e)}")
            return False
    
    def perform_analysis(self, save_visualizations: bool = True):
        """执行数据分析"""
        if self.analyzer is None:
            logger.error("分析器未初始化，请先加载数据")
            return None
        
        logger.info("开始执行数据分析...")
        
        try:
            # 基础统计分析
            print("\n" + "="*50)
            print("📊 大乐透数据分析报告")
            print("="*50)
            
            # 号码频率分析
            freq_data = self.analyzer.get_number_frequency()
            print(f"\n📈 号码频率统计:")
            print(f"红球最频繁号码: {freq_data['red_frequency'].nlargest(5).to_dict()}")
            print(f"蓝球最频繁号码: {freq_data['blue_frequency'].nlargest(3).to_dict()}")
            
            # 热门冷门号码
            hot_cold = self.analyzer.find_hot_and_cold_numbers(30)
            print(f"\n🔥 近期热门号码: {dict(list(hot_cold['hot_numbers'].items())[:5])}")
            print(f"🧊 近期冷门号码: {dict(list(hot_cold['cold_numbers'].items())[:5])}")
            
            # 和值统计
            sum_stats = self.analyzer.analyze_sum_statistics()
            print(f"\n🧮 和值统计:")
            print(f"红球和值平均: {sum_stats['red_sum_stats']['mean']:.1f}")
            print(f"总和值平均: {sum_stats['total_sum_stats']['mean']:.1f}")
            
            # 奇偶比分析
            odd_even_df = self.analyzer.calculate_odd_even_ratio()
            avg_odd_ratio = odd_even_df['red_odd_ratio'].mean()
            print(f"\n⚖️  奇偶比分析:")
            print(f"红球平均奇数比例: {avg_odd_ratio:.2%}")
            
            # 生成可视化图表
            if save_visualizations:
                logger.info("生成分析可视化图表...")
                create_analysis_visualizations(self.analyzer, "analysis_results")
                print(f"\n📊 分析图表已保存到 analysis_results 目录")
            
            return {
                'frequency': freq_data,
                'hot_cold': hot_cold,
                'sum_stats': sum_stats,
                'odd_even_ratio': avg_odd_ratio
            }
            
        except Exception as e:
            logger.error(f"数据分析过程中出现错误: {str(e)}")
            return None
    
    def generate_predictions(self, prediction_count: int = 5, evaluate_accuracy: bool = False):
        """生成预测结果"""
        if self.predictor is None:
            logger.error("预测器未初始化，请先加载数据")
            return None
        
        logger.info("开始生成预测结果...")
        
        try:
            # 训练预测模型
            logger.info("训练预测模型...")
            self.predictor.train_prediction_models()
            
            # 生成多种预测方案
            predictions = self.predictor.generate_multiple_predictions(prediction_count)
            
            print("\n" + "="*50)
            print("🔮 大乐透预测结果")
            print("="*50)
            
            for i, pred in enumerate(predictions, 1):
                print(f"\n方案 {i}: {pred['method']}")
                print(f"红球: {sorted(pred['numbers']['red_balls'])}")
                print(f"蓝球: {sorted(pred['numbers']['blue_balls'])}")
            
            # 预测评估（可选）
            if evaluate_accuracy:
                logger.info("进行预测准确性评估...")
                evaluate_prediction_accuracy(self.predictor, test_periods=5)
            
            return predictions
            
        except Exception as e:
            logger.error(f"预测生成过程中出现错误: {str(e)}")
            return None
    
    def create_dashboard(self, predictions: list = None):
        """创建统一可视化报告"""
        if self.df is None or self.df.empty:
            logger.error("没有数据可用于创建报告")
            return False
        
        try:
            logger.info("创建统一HTML分析报告...")
            filename = create_unified_dashboard(self.df, predictions, "dlt_unified_report.html")
            print(f"\n📊 统一分析报告已生成: {filename}")
            return True
        except Exception as e:
            logger.error(f"报告创建过程中出现错误: {str(e)}")
            return False
    
    def get_latest_result(self):
        """获取最新开奖结果"""
        if self.df is None or self.df.empty:
            return None
        
        latest = self.df.iloc[-1]
        return {
            'issue': latest['issue'],
            'date': latest['date'],
            'red_balls': [latest[col] for col in ['red1', 'red2', 'red3', 'red4', 'red5']],
            'blue_balls': [latest[col] for col in ['blue1', 'blue2']]
        }
    
    def export_report(self, filename: str = None):
        """导出分析报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lottery_analysis_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("大乐透彩票分析报告\n")
                f.write("="*50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据总量: {len(self.df) if self.df is not None else 0} 期\n\n")
                
                if self.df is not None and not self.df.empty:
                    latest = self.get_latest_result()
                    f.write(f"最新期号: {latest['issue']}\n")
                    f.write(f"开奖日期: {latest['date']}\n")
                    f.write(f"红球号码: {latest['red_balls']}\n")
                    f.write(f"蓝球号码: {latest['blue_balls']}\n\n")
                    
                    # 基本统计
                    analysis = self.perform_analysis(save_visualizations=False)
                    if analysis:
                        f.write("主要分析结果:\n")
                        f.write("-"*30 + "\n")
                        f.write(f"红球最高频号码: {max(analysis['frequency']['red_frequency'].items(), key=lambda x: x[1])}\n")
                        f.write(f"蓝球最高频号码: {max(analysis['frequency']['blue_frequency'].items(), key=lambda x: x[1])}\n")
                        f.write(f"红球和值平均: {analysis['sum_stats']['red_sum_stats']['mean']:.1f}\n")
                
            logger.info(f"分析报告已导出到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"报告导出失败: {str(e)}")
            return None

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='大乐透彩票分析预测系统')
    parser.add_argument('--crawl', action='store_true', help='爬取最新数据')
    parser.add_argument('--analyze', action='store_true', help='执行数据分析')
    parser.add_argument('--predict', action='store_true', help='生成预测结果')
    parser.add_argument('--dashboard', action='store_true', help='创建统一可视化报告')
    parser.add_argument('--report', action='store_true', help='导出分析报告')
    parser.add_argument('--pages', type=int, default=5, help='爬取页数 (默认: 5)')
    parser.add_argument('--eval', action='store_true', help='评估预测准确性')
    parser.add_argument('--data-file', default='dlt_history.xlsx', help='数据文件路径')
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = LotterySystem(args.data_file)
    system.initialize_system()
    
    # 根据参数执行相应功能
    if args.crawl:
        print("🌐 正在爬取大乐透数据...")
        if not system.crawl_new_data(args.pages):
            print("❌ 数据爬取失败")
            return
    
    if args.analyze or not any([args.crawl, args.predict, args.dashboard, args.report]):
        print("📊 正在执行数据分析...")
        system.perform_analysis()
    
    predictions = None
    if args.predict:
        print("🔮 正在生成预测结果...")
        predictions = system.generate_predictions(evaluate_accuracy=args.eval)
    
    if args.dashboard:
        print("🎨 正在创建可视化仪表板...")
        system.create_dashboard(predictions)
    
    if args.report:
        print("📄 正在导出分析报告...")
        system.export_report()
    
    # 如果没有任何参数，显示菜单
    if not any([args.crawl, args.analyze, args.predict, args.dashboard, args.report]):
        show_interactive_menu(system)

def show_interactive_menu(system):
    """显示交互式菜单"""
    while True:
        print("\n" + "="*60)
        print("🎰 大乐透彩票分析预测系统")
        print("="*60)
        print("1. 🌐 爬取最新数据")
        print("2. 📊 执行数据分析")
        print("3. 🔮 生成预测结果")
        print("4. 🎨 创建统一可视化报告")
        print("5. 📄 导出分析报告")
        print("6. ℹ️  查看最新开奖结果")
        print("0. 🚪 退出系统")
        print("="*60)
        
        choice = input("请选择操作 (0-6): ").strip()
        
        if choice == '1':
            pages = input("请输入要爬取的页数 (默认5): ").strip()
            pages = int(pages) if pages.isdigit() else 5
            system.crawl_new_data(pages)
            
        elif choice == '2':
            system.perform_analysis()
            
        elif choice == '3':
            eval_choice = input("是否进行预测准确性评估? (y/n): ").strip().lower()
            predictions = system.generate_predictions(evaluate_accuracy=(eval_choice == 'y'))
            
        elif choice == '4':
            system.create_dashboard()
            
        elif choice == '5':
            filename = input("请输入报告文件名 (回车使用默认): ").strip()
            system.export_report(filename if filename else None)
            
        elif choice == '6':
            latest = system.get_latest_result()
            if latest:
                print(f"\n🎯 最新开奖结果:")
                print(f"期号: {latest['issue']}")
                print(f"日期: {latest['date']}")
                print(f"红球: {sorted(latest['red_balls'])}")
                print(f"蓝球: {sorted(latest['blue_balls'])}")
            else:
                print("暂无数据")
                
        elif choice == '0':
            print("👋 感谢使用，再见!")
            break
            
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main()