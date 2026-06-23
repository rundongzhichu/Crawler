#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 官方 API 爬虫使用示例
=============================================================================

 展示如何单独使用官方 API 爬虫获取和分析大乐透数据。
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from official_api_crawler import OfficialApiCrawler
from lottery_analyzer import LotteryAnalyzer
import pandas as pd
from datetime import datetime


def main():
    """主示例函数。"""
    print("🎯 官方 API 大乐透数据获取示例")
    print("=" * 50)

    # 1. 创建爬虫实例
    crawler = OfficialApiCrawler()

    # 2. 获取数据
    print("2. 从官方 API 获取数据...")
    raw_data = crawler.fetch_all_history(max_pages=1)

    if not raw_data:
        print("❌ 无法获取数据，请检查网络连接")
        return

    print(f"✅ 成功获取 {len(raw_data)} 条记录")

    # 3. 处理数据
    print("3. 处理和格式化数据...")
    df = crawler.process_official_data(raw_data)

    if df.empty:
        print("❌ 数据处理失败")
        return

    print(f"✅ 数据处理完成，共 {len(df)} 期数据")

    # 4. 显示数据摘要
    print("4. 数据摘要:")
    print(f"   时间范围: {df['date'].min()} 到 {df['date'].max()}")
    print(f"   期号范围: {df['issue'].min()} 到 {df['issue'].max()}")

    # 5. 最新几期数据
    print("\n5. 最新 5 期开奖数据:")
    display_cols = ['issue', 'date', 'red_balls', 'blue_balls']
    print(df[display_cols].head().to_string(index=False))

    # 6. 基础统计
    print("\n6. 基础统计分析:")
    red_cols = ['red1', 'red2', 'red3', 'red4', 'red5']
    blue_cols = ['blue1', 'blue2']

    all_red_numbers = []
    all_blue_numbers = []
    for _, row in df.iterrows():
        for col in red_cols:
            if pd.notna(row[col]):
                all_red_numbers.append(int(row[col]))
        for col in blue_cols:
            if pd.notna(row[col]):
                all_blue_numbers.append(int(row[col]))

    red_freq = pd.Series(all_red_numbers).value_counts().sort_values(ascending=False)
    print(f"   红球最频繁号码: {dict(red_freq.head(5))}")

    blue_freq = pd.Series(all_blue_numbers).value_counts().sort_values(ascending=False)
    print(f"   蓝球最频繁号码: {dict(blue_freq.head(3))}")

    # 7. 保存数据（使用日期目录）
    date_str = datetime.now().strftime("%Y%m%d")
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", date_str)
    os.makedirs(data_dir, exist_ok=True)
    filename = os.path.join(data_dir, "dlt_example_data.xlsx")
    crawler.save_to_excel(df, filename)
    print(f"\n✅ 数据已保存到 {filename}")

    # 8. 深度分析
    print("\n8. 使用专业分析器进行深度分析...")
    try:
        analyzer = LotteryAnalyzer(df)
        hot_cold = analyzer.find_hot_and_cold_numbers(20)
        print(f"   近期热门红球: {dict(list(hot_cold['hot_numbers'].items())[:5])}")
        print(f"   近期冷门红球: {dict(list(hot_cold['cold_numbers'].items())[:5])}")

        odd_even_df = analyzer.calculate_odd_even_ratio()
        avg_odd_ratio = odd_even_df['red_odd_ratio'].mean()
        print(f"   红球平均奇数比例: {avg_odd_ratio:.2%}")
    except Exception as e:
        print(f"⚠️  深度分析遇到问题: {str(e)}")

    print("\n" + "=" * 50)
    print("🎉 示例执行完成!")
    print("💡 提示: 可修改 max_pages 参数获取更多历史数据")
    print("💡 提示: 运行 python main.py --pipeline 一键执行完整流程")


if __name__ == "__main__":
    main()
