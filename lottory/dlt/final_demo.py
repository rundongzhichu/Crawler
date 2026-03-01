#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透彩票分析系统最终演示
展示从数据获取到生成统一HTML报告的完整流程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_api_crawler import OfficialApiCrawler
from lottery_analyzer import LotteryAnalyzer
from predictor import LotteryPredictor
from dashboard import create_unified_dashboard
import pandas as pd

def main():
    """主演示函数"""
    print("🎯 大乐透彩票分析系统演示")
    print("="*60)
    
    # 1. 数据获取
    print("1. 🌐 从官方API获取数据...")
    crawler = OfficialApiCrawler()
    raw_data = crawler.fetch_all_history(max_pages=2)  # 获取2页数据(60条记录)
    
    if not raw_data:
        print("❌ 数据获取失败")
        return
    
    df = crawler.process_official_data(raw_data)
    print(f"✅ 成功获取 {len(df)} 期数据")
    print(f"   时间范围: {df['date'].min()} 到 {df['date'].max()}")
    
    # 2. 数据分析
    print("\n2. 📊 执行数据分析...")
    analyzer = LotteryAnalyzer(df)
    
    # 基础统计
    freq_data = analyzer.get_number_frequency()
    hot_cold = analyzer.find_hot_and_cold_numbers(30)
    sum_stats = analyzer.analyze_sum_statistics()
    
    print("   🔢 号码频率统计完成")
    print("   🔥 热门冷门号码分析完成")
    print("   🧮 和值分布分析完成")
    
    # 3. 预测生成
    print("\n3. 🔮 生成预测结果...")
    predictor = LotteryPredictor(df)
    predictor.train_prediction_models()
    predictions = predictor.generate_multiple_predictions(5)
    print("   ✅ 5种预测方案生成完成")
    
    # 4. 生成统一报告
    print("\n4. 🎨 生成统一HTML分析报告...")
    report_file = create_unified_dashboard(df, predictions, "final_dlt_report.html")
    print(f"   ✅ 报告已保存: {report_file}")
    
    # 5. 显示关键结果
    print("\n5. 📈 关键分析结果:")
    print(f"   最新期号: {df.iloc[0]['issue']}")
    print(f"   最新开奖: {df.iloc[0]['red_balls']} + {df.iloc[0]['blue_balls']}")
    print(f"   红球高频号码: {list(freq_data['red_frequency'].nlargest(5).index)}")
    print(f"   蓝球高频号码: {list(freq_data['blue_frequency'].nlargest(3).index)}")
    
    print("\n" + "="*60)
    print("🎉 演示完成!")
    print("💡 请在浏览器中打开 final_dlt_report.html 查看完整分析报告")
    print("💡 报告包含所有图表和分析结果的交互式展示")

if __name__ == "__main__":
    main()