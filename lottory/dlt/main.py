#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 大乐透彩票分析预测系统 - 统一主入口
 Lottery Analysis & Prediction System — Unified Entry Point
=============================================================================

 功能概述：
   1. 统一日志配置 → logs/lottery_YYYYMMDD.log
   2. 数据爬取    → data/YYYYMMDD/dlt_history.xlsx
   3. 数据分析    → analysis_results/YYYYMMDD/*.png
   4. 号码预测    → 多种策略综合预测
   5. 报告生成    → analysis_results/YYYYMMDD/dlt_unified_report.html

 使用方式：
   # 一键执行完整流程
   python main.py --pipeline --pages 5

   # 分步执行
   python main.py --crawl --pages 10
   python main.py --analyze
   python main.py --predict --eval
   python main.py --dashboard

   # 交互式菜单
   python main.py
=============================================================================
"""

import pandas as pd
import argparse
import logging
import sys
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# 路径初始化：确保当前目录在 sys.path 中，方便模块导入
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from official_api_crawler import OfficialApiCrawler
from lottery_analyzer import LotteryAnalyzer, create_analysis_visualizations
from predictor import LotteryPredictor, evaluate_prediction_accuracy
from dashboard import create_unified_dashboard


# ============================================================================
#  日志配置
# ============================================================================

def setup_logging(date_str: str = None, log_level: int = logging.INFO) -> str:
    """
    统一日志配置 —— 所有模块通过 logging.getLogger(__name__) 继承此配置。

    Args:
        date_str: 日期标识字符串，格式 YYYYMMDD，默认取当天日期
        log_level: 日志级别，默认 INFO

    Returns:
        str: 日志文件的完整路径
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    # 确保 logs 目录存在
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"lottery_{date_str}.log")

    # 获取 root logger 并清空已有 handler（避免重复配置）
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 配置格式和输出
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    return log_file


# ============================================================================
#  目录管理
# ============================================================================

def ensure_output_dirs(date_str: str = None) -> dict:
    """
    确保所有输出目录存在，返回路径字典。

    Args:
        date_str: 日期标识字符串，默认取当天日期

    Returns:
        dict: {
            'data_dir':         数据存储目录,
            'analysis_dir':     分析结果目录,
            'log_dir':          日志目录,
            'date_str':         日期字符串
        }
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    dirs = {
        'data_dir': os.path.join(base_dir, "data", date_str),
        'analysis_dir': os.path.join(base_dir, "analysis_results", date_str),
        'log_dir': os.path.join(base_dir, "logs"),
        'date_str': date_str,
    }

    for key in ['data_dir', 'analysis_dir', 'log_dir']:
        os.makedirs(dirs[key], exist_ok=True)

    return dirs


# ============================================================================
#  核心编排类
# ============================================================================

class LotteryPipeline:
    """
    大乐透分析流水线 —— 将爬取、分析、预测、报告串联为统一流程。

    使用示例:
        pipeline = LotteryPipeline(date_str="20260623")
        pipeline.run_full_pipeline(max_pages=5)
    """

    def __init__(self, date_str: str = None, data_file: str = None):
        """
        初始化流水线。

        Args:
            date_str: 日期标识字符串，用于目录隔离，默认当天
            data_file: 指定已有数据文件路径（可选，用于跳过爬取步骤）
        """
        self.date_str = date_str or datetime.now().strftime("%Y%m%d")
        self.dirs = ensure_output_dirs(self.date_str)

        # 数据文件路径
        if data_file:
            self.data_file = data_file
        else:
            self.data_file = os.path.join(
                self.dirs['data_dir'], "dlt_history.xlsx"
            )

        self.df = None           # 核心 DataFrame
        self.crawler = OfficialApiCrawler()
        self.analyzer = None     # LotteryAnalyzer 实例
        self.predictor = None    # LotteryPredictor 实例

        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    #  步骤 1: 数据加载
    # ------------------------------------------------------------------

    def load_existing_data(self) -> bool:
        """尝试从已有 Excel 文件加载数据。"""
        try:
            if os.path.exists(self.data_file):
                self.df = pd.read_excel(
                    self.data_file, sheet_name='lottery_data'
                )
                self.logger.info(
                    "成功加载 %d 条历史数据 ← %s", len(self.df), self.data_file
                )
                return True
            else:
                self.logger.info("数据文件不存在: %s，需要先爬取数据", self.data_file)
                return False
        except Exception as e:
            self.logger.error("加载数据文件失败: %s", str(e))
            return False

    # ------------------------------------------------------------------
    #  步骤 2: 数据爬取
    # ------------------------------------------------------------------

    def crawl_data(self, max_pages: int = None, force_update: bool = False) -> bool:
        """
        从官方 API 爬取大乐透历史数据。

        Args:
            max_pages: 爬取页数，None 表示获取全部
            force_update: 是否强制覆盖已有数据

        Returns:
            bool: 是否成功
        """
        self.logger.info("=" * 50)
        self.logger.info("▶ 步骤 1/4: 爬取大乐透数据")
        self.logger.info("=" * 50)

        try:
            raw_data = self.crawler.fetch_all_history(max_pages)
            if not raw_data:
                self.logger.error("未能获取到任何数据")
                return False

            new_df = self.crawler.process_official_data(raw_data)
            if new_df.empty:
                self.logger.error("数据处理后为空")
                return False

            # 合并或覆盖已有数据
            if self.df is not None and not force_update:
                combined_df = pd.concat([self.df, new_df])
                combined_df = combined_df.drop_duplicates(subset=['issue'])
                combined_df = combined_df.sort_values('issue').reset_index(drop=True)
                self.df = combined_df
            else:
                self.df = new_df

            # 保存到 data/{date}/ 目录
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            self.crawler.save_to_excel(self.df, self.data_file)
            self.logger.info(
                "✅ 成功获取 %d 条新数据，共 %d 条记录",
                len(new_df), len(self.df)
            )

            # 初始化下游组件
            self._init_components()
            return True

        except Exception as e:
            self.logger.error("数据爬取错误: %s", str(e))
            return False

    # ------------------------------------------------------------------
    #  步骤 3: 数据分析
    # ------------------------------------------------------------------

    def analyze_data(self, save_charts: bool = True) -> dict:
        """
        执行数据分析，生成统计结果和可视化图表。

        Args:
            save_charts: 是否保存 PNG 图表到 analysis_results/{date}/

        Returns:
            dict: 分析结果字典，包含 frequency, hot_cold, sum_stats 等
        """
        if self.analyzer is None:
            self.logger.error("分析器未初始化，请先加载或爬取数据")
            return None

        self.logger.info("=" * 50)
        self.logger.info("▶ 步骤 2/4: 执行数据分析")
        self.logger.info("=" * 50)

        try:
            # ---- 号码频率分析 ----
            freq_data = self.analyzer.get_number_frequency()
            hot_cold = self.analyzer.find_hot_and_cold_numbers(30)
            sum_stats = self.analyzer.analyze_sum_statistics()
            odd_even_df = self.analyzer.calculate_odd_even_ratio()
            avg_odd_ratio = odd_even_df['red_odd_ratio'].mean()

            # ---- 终端摘要输出 ----
            print("\n" + "=" * 50)
            print("📊 大乐透数据分析报告")
            print("=" * 50)
            print(f"\n📈 号码频率统计:")
            print(f"   红球最高频: {freq_data['red_frequency'].nlargest(5).to_dict()}")
            print(f"   蓝球最高频: {freq_data['blue_frequency'].nlargest(3).to_dict()}")
            print(f"\n🔥 近期热门号码: {dict(list(hot_cold['hot_numbers'].items())[:5])}")
            print(f"🧊 近期冷门号码: {dict(list(hot_cold['cold_numbers'].items())[:5])}")
            print(f"\n🧮 和值统计:")
            print(f"   红球和值平均: {sum_stats['red_sum_stats']['mean']:.1f}")
            print(f"   总和值平均:   {sum_stats['total_sum_stats']['mean']:.1f}")
            print(f"\n⚖️  红球平均奇数比例: {avg_odd_ratio:.2%}")

            # ---- 生成 PNG 图表 ----
            if save_charts:
                chart_dir = self.dirs['analysis_dir']
                self.logger.info("生成分析图表 → %s", chart_dir)
                create_analysis_visualizations(self.analyzer, chart_dir)
                print(f"\n📊 分析图表已保存到: {chart_dir}")

            results = {
                'frequency': freq_data,
                'hot_cold': hot_cold,
                'sum_stats': sum_stats,
                'odd_even_ratio': avg_odd_ratio
            }
            return results

        except Exception as e:
            self.logger.error("数据分析错误: %s", str(e))
            return None

    # ------------------------------------------------------------------
    #  步骤 4: 号码预测
    # ------------------------------------------------------------------

    def generate_predictions(self, count: int = 5, evaluate: bool = False) -> list:
        """
        使用多种策略生成预测号码。

        Args:
            count: 返回的预测方案数量 (1-5)
            evaluate: 是否进行回测评估

        Returns:
            list: 预测方案列表
        """
        if self.predictor is None:
            self.logger.error("预测器未初始化，请先加载或爬取数据")
            return None

        self.logger.info("=" * 50)
        self.logger.info("▶ 步骤 3/4: 生成预测结果")
        self.logger.info("=" * 50)

        try:
            self.predictor.train_prediction_models()
            predictions = self.predictor.generate_multiple_predictions(count)

            print("\n" + "=" * 50)
            print("🔮 大乐透预测结果")
            print("=" * 50)
            for i, pred in enumerate(predictions, 1):
                print(f"\n  方案 {i}: {pred['method']}")
                print(f"  红球: {sorted(pred['numbers']['red_balls'])}")
                print(f"  蓝球: {sorted(pred['numbers']['blue_balls'])}")

            if evaluate:
                self.logger.info("执行预测准确性回测...")
                evaluate_prediction_accuracy(self.predictor, test_periods=5)

            return predictions

        except Exception as e:
            self.logger.error("预测生成错误: %s", str(e))
            return None

    # ------------------------------------------------------------------
    #  步骤 5: 报告生成
    # ------------------------------------------------------------------

    def generate_report(self, predictions: list = None) -> str:
        """
        生成统一的 HTML 分析报告。

        Args:
            predictions: 预测结果（可选），来自 generate_predictions()

        Returns:
            str: 报告文件路径，失败返回 None
        """
        if self.df is None or self.df.empty:
            self.logger.error("没有数据可生成报告")
            return None

        self.logger.info("=" * 50)
        self.logger.info("▶ 步骤 4/4: 生成 HTML 分析报告")
        self.logger.info("=" * 50)

        try:
            report_path = os.path.join(
                self.dirs['analysis_dir'], "dlt_unified_report.html"
            )
            filename = create_unified_dashboard(
                self.df, predictions, report_path
            )
            print(f"\n📊 统一分析报告已生成: {filename}")
            return filename
        except Exception as e:
            self.logger.error("报告生成错误: %s", str(e))
            return None

    # ------------------------------------------------------------------
    #  一键流水线
    # ------------------------------------------------------------------

    def run_full_pipeline(
        self,
        max_pages: int = None,
        force_update: bool = False,
        prediction_count: int = 5,
        evaluate: bool = False,
    ) -> dict:
        """
        一键执行完整分析流水线：爬取 → 分析 → 预测 → 报告。

        Args:
            max_pages: 爬取页数
            force_update: 是否强制覆盖已有数据
            prediction_count: 预测方案数
            evaluate: 是否进行预测回测

        Returns:
            dict: {
                'analysis': 分析结果,
                'predictions': 预测结果,
                'report': 报告文件路径,
                'latest': 最新开奖结果
            }
        """
        print("\n" + "🎯" * 30)
        print("  大乐透彩票分析预测系统 — 全流程自动化")
        print("🎯" * 30)

        # 尝试加载已有数据
        self.load_existing_data()
        self._init_components()

        # Step 1: 爬取新数据（始终执行以获取最新）
        if not self.crawl_data(max_pages, force_update):
            if self.df is None or self.df.empty:
                print("❌ 无可用数据，流水线终止")
                return None
            print("⚠️  爬取失败，将使用已有数据继续...")

        # Step 2: 分析
        analysis = self.analyze_data(save_charts=True)

        # Step 3: 预测
        predictions = self.generate_predictions(prediction_count, evaluate)

        # Step 4: 报告
        report_path = self.generate_report(predictions)

        # 最新结果
        latest = self.get_latest_result()

        print("\n" + "=" * 60)
        print("🎉 全流程执行完成!")
        print(f"📁 数据目录:   {self.dirs['data_dir']}")
        print(f"📊 分析目录:   {self.dirs['analysis_dir']}")
        print(f"📝 日志文件:   logs/lottery_{self.date_str}.log")
        print("=" * 60)

        return {
            'analysis': analysis,
            'predictions': predictions,
            'report': report_path,
            'latest': latest,
        }

    # ------------------------------------------------------------------
    #  辅助方法
    # ------------------------------------------------------------------

    def _init_components(self):
        """初始化分析器和预测器。"""
        if self.df is not None and not self.df.empty:
            self.analyzer = LotteryAnalyzer(self.df)
            self.predictor = LotteryPredictor(self.df)
            self.logger.info("分析器和预测器初始化完成")
        else:
            self.logger.warning("暂无数据，分析器和预测器未初始化")

    def get_latest_result(self) -> dict:
        """获取最新一期开奖结果。"""
        if self.df is None or self.df.empty:
            return None
        latest = self.df.iloc[-1]
        return {
            'issue': latest['issue'],
            'date': latest['date'],
            'red_balls': [latest[col] for col in ['red1', 'red2', 'red3', 'red4', 'red5']],
            'blue_balls': [latest[col] for col in ['blue1', 'blue2']],
        }

    def export_text_report(self, filename: str = None) -> str:
        """
        导出纯文本分析报告。

        Args:
            filename: 报告文件路径，默认保存到 analysis_results/{date}/ 目录

        Returns:
            str: 报告文件路径
        """
        if filename is None:
            filename = os.path.join(
                self.dirs['analysis_dir'],
                f"analysis_report_{self.date_str}.txt"
            )

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("大乐透彩票分析报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据总量: {len(self.df) if self.df is not None else 0} 期\n\n")

                if self.df is not None and not self.df.empty:
                    latest = self.get_latest_result()
                    if latest:
                        f.write(f"最新期号: {latest['issue']}\n")
                        f.write(f"开奖日期: {latest['date']}\n")
                        f.write(f"红球号码: {latest['red_balls']}\n")
                        f.write(f"蓝球号码: {latest['blue_balls']}\n")

            self.logger.info("文本报告已导出 → %s", filename)
            return filename
        except Exception as e:
            self.logger.error("导出文本报告失败: %s", str(e))
            return None


# ============================================================================
#  CLI 入口
# ============================================================================

def build_argument_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description='大乐透彩票分析预测系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --pipeline --pages 5    一键执行完整流程
  python main.py --crawl --pages 10      仅爬取数据
  python main.py --analyze               仅分析数据
  python main.py --predict --eval        生成预测并回测
  python main.py --dashboard             生成HTML报告
  python main.py                         交互式菜单
        """
    )
    parser.add_argument(
        '--pipeline', action='store_true',
        help='一键执行完整流程: 爬取→分析→预测→报告'
    )
    parser.add_argument(
        '--crawl', action='store_true',
        help='爬取最新数据'
    )
    parser.add_argument(
        '--analyze', action='store_true',
        help='执行数据分析'
    )
    parser.add_argument(
        '--predict', action='store_true',
        help='生成预测结果'
    )
    parser.add_argument(
        '--dashboard', action='store_true',
        help='创建统一 HTML 可视化报告'
    )
    parser.add_argument(
        '--report', action='store_true',
        help='导出纯文本分析报告'
    )
    parser.add_argument(
        '--pages', type=int, default=None,
        help='爬取页数（默认获取全部）'
    )
    parser.add_argument(
        '--eval', action='store_true',
        help='评估预测准确性（回测）'
    )
    parser.add_argument(
        '--data-file', default=None,
        help='指定已有数据文件路径（跳过爬取步骤）'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='强制覆盖已有数据'
    )
    return parser


def show_interactive_menu(pipeline: LotteryPipeline):
    """
    交互式菜单 —— 当用户不带任何参数运行时显示。
    """
    while True:
        print("\n" + "=" * 60)
        print("🎰 大乐透彩票分析预测系统")
        print("=" * 60)
        print("  1. 🌐 爬取最新数据")
        print("  2. 📊 执行数据分析")
        print("  3. 🔮 生成预测结果")
        print("  4. 🎨 创建统一可视化报告")
        print("  5. 📄 导出文本分析报告")
        print("  6. ℹ️  查看最新开奖结果")
        print("  7. 🚀 一键执行完整流程")
        print("  0. 🚪 退出系统")
        print("=" * 60)

        choice = input("请选择操作 (0-7): ").strip()

        if choice == '1':
            pages = input("请输入爬取页数 (回车获取全部): ").strip()
            pages = int(pages) if pages.isdigit() else None
            pipeline.crawl_data(pages)

        elif choice == '2':
            pipeline.analyze_data()

        elif choice == '3':
            ev = input("是否进行预测准确性评估? (y/n): ").strip().lower()
            pipeline.generate_predictions(evaluate=(ev == 'y'))

        elif choice == '4':
            pipeline.generate_report()

        elif choice == '5':
            pipeline.export_text_report()

        elif choice == '6':
            latest = pipeline.get_latest_result()
            if latest:
                print(f"\n🎯 最新开奖结果:")
                print(f"   期号: {latest['issue']}")
                print(f"   日期: {latest['date']}")
                print(f"   红球: {sorted(latest['red_balls'])}")
                print(f"   蓝球: {sorted(latest['blue_balls'])}")
            else:
                print("暂无数据，请先爬取或加载数据")

        elif choice == '7':
            pages = input("请输入爬取页数 (回车获取全部): ").strip()
            pages = int(pages) if pages.isdigit() else None
            pipeline.run_full_pipeline(max_pages=pages)

        elif choice == '0':
            print("👋 感谢使用，再见!")
            break

        else:
            print("❌ 无效选择，请重新输入")


def main():
    """主程序入口 —— 解析命令行参数并调度对应功能。"""
    parser = build_argument_parser()
    args = parser.parse_args()

    # ---- 初始化日志和目录 ----
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = setup_logging(date_str)
    logger = logging.getLogger("main")

    logger.info("=" * 50)
    logger.info("大乐透分析系统启动 (日期: %s)", date_str)
    logger.info("日志文件: %s", log_file)

    # ---- 创建流水线实例 ----
    pipeline = LotteryPipeline(date_str=date_str, data_file=args.data_file)

    # 加载已有数据（供分析/预测/报告使用）
    pipeline.load_existing_data()
    pipeline._init_components()

    # ---- 路由到对应功能 ----

    # 一键流水线模式
    if args.pipeline:
        pipeline.run_full_pipeline(
            max_pages=args.pages,
            force_update=args.force,
            evaluate=args.eval,
        )
        return

    # 单步模式
    if args.crawl:
        print("🌐 正在爬取大乐透数据...")
        pipeline.crawl_data(args.pages, force_update=args.force)

    if args.analyze:
        print("📊 正在执行数据分析...")
        pipeline.analyze_data()

    predictions = None
    if args.predict:
        print("🔮 正在生成预测结果...")
        predictions = pipeline.generate_predictions(evaluate=args.eval)

    if args.dashboard:
        print("🎨 正在创建可视化仪表板...")
        pipeline.generate_report(predictions)

    if args.report:
        print("📄 正在导出分析报告...")
        pipeline.export_text_report()

    # 如果没有任何参数，显示交互式菜单
    if not any([
        args.pipeline, args.crawl, args.analyze,
        args.predict, args.dashboard, args.report
    ]):
        show_interactive_menu(pipeline)


if __name__ == "__main__":
    main()
