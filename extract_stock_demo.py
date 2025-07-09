#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据提取工具 - 使用示例
快速提取个股数据用于测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.stock_data_extractor import StockDataExtractor


def quick_extract_demo():
    """快速提取示例"""
    print("🚀 股票数据提取工具 - 快速使用示例")
    print("=" * 50)
    
    # 数据文件路径
    data_file = "core/test_processed_data_0624.json"
    
    # 检查文件是否存在
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    # 初始化提取器
    try:
        extractor = StockDataExtractor(data_file)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    print("\n" + "="*50)
    print("💡 使用方法示例:")
    print("="*50)
    
    # 示例1: 提取红太阳数据
    print("\n📌 示例1: 提取红太阳数据")
    stock_data = extractor.extract_stock_by_name("红太阳")
    if stock_data:
        print(f"✅ 找到股票: {stock_data['name']} ({stock_data['ts_code']})")
        print(f"   涨跌幅: {stock_data['basic_info']['pct_change']}")
        print(f"   净流入: {stock_data['basic_info']['net_amount']}")
        
        # 保存数据
        output_path = extractor.save_stock_data(stock_data)
        print(f"💾 数据已保存到: {output_path}")
    else:
        print("❌ 未找到红太阳")
    
    # 示例2: 模糊搜索
    print("\n📌 示例2: 模糊搜索包含'太阳'的股票")
    matches = extractor.search_stock("太阳")
    if matches:
        print(f"🎯 找到 {len(matches)} 个匹配结果:")
        for stock in matches:
            print(f"   - {stock['name']} ({stock['ts_code']}) {stock['basic_info']['pct_change']}")
    
    # 示例3: 根据代码提取
    print("\n📌 示例3: 根据股票代码提取数据")
    stock_data = extractor.extract_stock_by_code("000525.SZ")
    if stock_data:
        print(f"✅ 找到股票: {stock_data['name']} ({stock_data['ts_code']})")
    
    print("\n" + "="*50)
    print("🎮 交互式模式:")
    print("="*50)
    print("运行以下命令启动交互式模式:")
    print(f"python utils/stock_data_extractor.py {data_file} -i")
    print("")
    print("或者直接提取特定股票:")
    print(f"python utils/stock_data_extractor.py {data_file} -s 红太阳")
    print("")
    print("列出所有股票:")
    print(f"python utils/stock_data_extractor.py {data_file} -l")


def batch_extract_demo():
    """批量提取示例"""
    print("\n🔄 批量提取示例")
    print("=" * 30)
    
    # 要提取的股票列表
    target_stocks = ["红太阳", "泰山石油", "厦门信达"]
    
    data_file = "core/test_processed_data_0624.json"
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    extractor = StockDataExtractor(data_file)
    
    extracted_files = []
    for stock_name in target_stocks:
        print(f"\n📤 正在提取: {stock_name}")
        stock_data = extractor.extract_stock_by_name(stock_name)
        
        if stock_data:
            filepath = extractor.save_stock_data(stock_data)
            extracted_files.append(filepath)
            print(f"✅ {stock_name} 提取成功")
        else:
            print(f"❌ 未找到 {stock_name}")
    
    print(f"\n🎉 批量提取完成! 共提取 {len(extracted_files)} 个文件:")
    for filepath in extracted_files:
        print(f"   📁 {filepath}")


if __name__ == "__main__":
    # 运行快速示例
    quick_extract_demo()
    
    # 询问是否运行批量提取示例
    print("\n" + "="*50)
    choice = input("🤔 是否运行批量提取示例? (y/N): ").strip().lower()
    if choice in ['y', 'yes']:
        batch_extract_demo()
    
    print("\n👋 示例演示完成！") 