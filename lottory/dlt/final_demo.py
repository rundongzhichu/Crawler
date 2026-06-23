#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 大乐透彩票分析系统 - 完整流程演示
=============================================================================

 展示从数据获取到生成统一 HTML 报告的完整流程。
 推荐用法: 直接运行 main.py --pipeline
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import LotteryPipeline, setup_logging, ensure_output_dirs
from datetime import datetime


def main():
    """主演示函数 —— 调用 main.py 的流水线能力。"""
    print("🎯 大乐透彩票分析系统演示")
    print("=" * 60)

    # 初始化日志和目录
    date_str = datetime.now().strftime("%Y%m%d")
    setup_logging(date_str)

    # 创建流水线并执行
    pipeline = LotteryPipeline(date_str=date_str)
    result = pipeline.run_full_pipeline(max_pages=2)

    if result is None:
        print("❌ 演示失败")
        return

    # 展示关键结果
    print("\n5. 📈 关键分析结果:")
    if result.get('latest'):
        latest = result['latest']
        print(f"   最新期号: {latest['issue']}")
        print(f"   最新开奖: {latest['red_balls']} + {latest['blue_balls']}")

    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print(f"💡 请在浏览器中打开 {result.get('report', '报告文件')} 查看完整分析报告")


if __name__ == "__main__":
    main()
