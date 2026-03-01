#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        from super_lotto_crawler import SuperLottoCrawler
        print("✅ Crawler module imported successfully")
    except Exception as e:
        print(f"❌ Crawler import failed: {e}")
        return False
    
    try:
        from lottory.dlt.lottery_analyzer import LotteryAnalyzer
        print("✅ Analyzer module imported successfully")
    except Exception as e:
        print(f"❌ Analyzer import failed: {e}")
        return False
    
    try:
        from lottory.dlt.predictor import LotteryPredictor
        print("✅ Predictor module imported successfully")
    except Exception as e:
        print(f"❌ Predictor import failed: {e}")
        return False
    
    try:
        from lottory.dlt.dashboard import LotteryVisualizer
        print("✅ Dashboard module imported successfully")
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return False
    
    try:
        from lottory.dlt.main_system import LotterySystem
        print("✅ Main system module imported successfully")
    except Exception as e:
        print(f"❌ Main system import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")
    
    try:
        from super_lotto_crawler import SuperLottoCrawler
        crawler = SuperLottoCrawler()
        print("✅ Crawler instantiated successfully")
        
        # 测试数据处理功能
        sample_data = [{
            'code': '2024001',
            'date': '2024-01-01',
            'red': '01,02,03,04,05',
            'blue': '01,02'
        }]
        
        processed_df = crawler.process_super_lotto_data(sample_data)
        if not processed_df.empty:
            print("✅ Data processing works correctly")
        else:
            print("❌ Data processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False
    
    return True

def test_analysis_components():
    """测试分析组件"""
    print("\n🧪 测试分析组件...")
    
    try:
        import pandas as pd
        from lottory.dlt.lottery_analyzer import LotteryAnalyzer
        from lottory.dlt.predictor import LotteryPredictor
        
        # 创建测试数据
        test_data = {
            'issue': ['2024001', '2024002', '2024003'],
            'date': ['2024-01-01', '2024-01-03', '2024-01-05'],
            'red1': [1, 2, 3], 'red2': [11, 12, 13], 'red3': [21, 22, 23],
            'red4': [26, 27, 28], 'red5': [31, 32, 33],
            'blue1': [1, 2, 3], 'blue2': [7, 8, 9]
        }
        
        df = pd.DataFrame(test_data)
        analyzer = LotteryAnalyzer(df)
        
        # 测试频率分析
        freq_data = analyzer.get_number_frequency()
        if 'red_frequency' in freq_data and 'blue_frequency' in freq_data:
            print("✅ Frequency analysis works")
        else:
            print("❌ Frequency analysis failed")
            return False
            
        # 测试预测器
        predictor = LotteryPredictor(df)
        print("✅ Predictor instantiated successfully")
        
    except Exception as e:
        print(f"❌ Analysis components test failed: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 大乐透彩票分析系统测试")
    print("="*50)
    
    # 运行各项测试
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_basic_functionality():
        tests_passed += 1
        
    if test_analysis_components():
        tests_passed += 1
    
    print("\n" + "="*50)
    print(f"📊 测试结果: {tests_passed}/{total_tests} 项测试通过")
    
    if tests_passed == total_tests:
        print("🎉 所有测试通过！系统可以正常使用")
        print("\n💡 使用说明:")
        print("   1. 运行 'python main_system.py --help' 查看帮助")
        print("   2. 运行 'python main_system.py --crawl' 获取数据")
        print("   3. 运行 'python main_system.py' 进入交互模式")
    else:
        print("⚠️  部分测试失败，请检查环境配置")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)