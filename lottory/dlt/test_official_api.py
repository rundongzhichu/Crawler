#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
官方API爬虫测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from official_api_crawler import OfficialApiCrawler
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_connection():
    """测试API连接"""
    print("🧪 测试官方API连接...")
    
    crawler = OfficialApiCrawler()
    
    # 测试单页获取
    print("\n1. 测试获取第1页数据...")
    page_data = crawler.fetch_single_page(1, 10)
    
    if page_data:
        print("✅ API连接成功!")
        print(f"   状态码: {page_data.get('success', 'N/A')}")
        print(f"   数据条数: {len(page_data.get('list', []))}")
        
        # 显示第一条数据结构
        if page_data.get('list'):
            first_item = page_data['list'][0]
            print(f"   数据结构示例: {list(first_item.keys())}")
            print(f"   示例期号: {first_item.get('lotteryDrawNum', 'N/A')}")
            print(f"   示例日期: {first_item.get('lotteryDrawTime', 'N/A')}")
            print(f"   示例号码: {first_item.get('lotteryDrawResult', 'N/A')}")
    else:
        print("❌ API连接失败!")
        return False
    
    return True

def test_data_processing():
    """测试数据处理"""
    print("\n2. 测试数据处理功能...")
    
    crawler = OfficialApiCrawler()
    
    # 获取少量数据进行测试
    raw_data = crawler.fetch_all_history(max_pages=2)
    
    if not raw_data:
        print("❌ 无法获取测试数据")
        return False
    
    print(f"   获取到 {len(raw_data)} 条原始数据")
    
    # 处理数据
    df = crawler.process_official_data(raw_data)
    
    if df.empty:
        print("❌ 数据处理失败")
        return False
    
    print("✅ 数据处理成功!")
    print(f"   处理后数据形状: {df.shape}")
    print(f"   包含列数: {len(df.columns)}")
    print(f"   列名: {list(df.columns)[:10]}...")  # 显示前10列
    
    # 显示数据预览
    print("\n📊 数据预览:")
    print(df[['issue', 'date', 'red_balls', 'blue_balls']].head(3).to_string(index=False))
    
    return True

def test_full_workflow():
    """测试完整工作流程"""
    print("\n3. 测试完整工作流程...")
    
    crawler = OfficialApiCrawler()
    
    try:
        # 获取数据
        print("   正在获取数据...")
        raw_data = crawler.fetch_all_history(max_pages=3)
        
        if not raw_data:
            print("❌ 数据获取失败")
            return False
        
        # 处理数据
        print("   正在处理数据...")
        df = crawler.process_official_data(raw_data)
        
        if df.empty:
            print("❌ 数据处理失败")
            return False
        
        # 保存数据
        print("   正在保存数据...")
        test_filename = "test_official_api_data.xlsx"
        crawler.save_to_excel(df, test_filename)
        
        # 显示摘要
        crawler.print_summary(df)
        
        print(f"✅ 完整流程测试成功! 数据已保存到 {test_filename}")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 启动官方API爬虫测试")
    print("="*50)
    
    tests = [
        ("API连接测试", test_api_connection),
        ("数据处理测试", test_data_processing),
        ("完整流程测试", test_full_workflow)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'-'*30}")
        print(f"执行: {test_name}")
        print('-'*30)
        
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {str(e)}")
    
    print("\n" + "="*50)
    print("🏁 测试完成")
    print(f"通过: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过! 官方API爬虫工作正常")
    else:
        print("⚠️  部分测试失败，请检查网络连接或API状态")

if __name__ == "__main__":
    main()