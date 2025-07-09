#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据提取工具
用于从完整的龙虎榜数据中提取指定个股的数据，便于测试使用
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class StockDataExtractor:
    """股票数据提取器"""
    
    def __init__(self, data_file_path: str):
        """
        初始化提取器
        
        Args:
            data_file_path: JSON数据文件路径
        """
        self.data_file_path = data_file_path
        self.data = None
        self.load_data()
    
    def load_data(self):
        """加载JSON数据"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ 成功加载数据文件: {self.data_file_path}")
            print(f"📊 数据包含 {self.data['meta']['stock_count']} 只股票")
            print(f"📅 交易日期: {self.data['meta']['trade_date_display']}")
        except FileNotFoundError:
            print(f"❌ 错误: 找不到数据文件 {self.data_file_path}")
            raise
        except json.JSONDecodeError:
            print(f"❌ 错误: JSON文件格式错误 {self.data_file_path}")
            raise
    
    def list_all_stocks(self) -> List[Dict]:
        """列出所有股票的基本信息"""
        if not self.data:
            return []
        
        stocks_info = []
        for stock in self.data['stocks']:
            stocks_info.append({
                'name': stock['name'],
                'ts_code': stock['ts_code'],
                'close': stock['basic_info']['close'],
                'pct_change': stock['basic_info']['pct_change'],
                'net_amount': stock['basic_info']['net_amount']
            })
        
        return stocks_info
    
    def search_stock(self, query: str) -> List[Dict]:
        """
        搜索股票（支持名称和代码模糊匹配）
        
        Args:
            query: 搜索关键词（股票名称或代码）
            
        Returns:
            匹配的股票列表
        """
        if not self.data:
            return []
        
        query = query.strip().upper()
        matches = []
        
        for stock in self.data['stocks']:
            # 匹配股票名称
            if query in stock['name']:
                matches.append(stock)
            # 匹配股票代码
            elif query in stock['ts_code'].upper():
                matches.append(stock)
        
        return matches
    
    def extract_stock_by_name(self, stock_name: str) -> Optional[Dict]:
        """
        根据股票名称提取数据（精确匹配）
        
        Args:
            stock_name: 股票名称
            
        Returns:
            股票数据，如果未找到返回None
        """
        if not self.data:
            return None
        
        for stock in self.data['stocks']:
            if stock['name'] == stock_name:
                return stock
        
        return None
    
    def extract_stock_by_code(self, ts_code: str) -> Optional[Dict]:
        """
        根据股票代码提取数据
        
        Args:
            ts_code: 股票代码（如：000525.SZ）
            
        Returns:
            股票数据，如果未找到返回None
        """
        if not self.data:
            return None
        
        ts_code = ts_code.upper()
        for stock in self.data['stocks']:
            if stock['ts_code'] == ts_code:
                return stock
        
        return None
    
    def save_stock_data(self, stock_data: Dict, output_dir: str = "data/extracted") -> str:
        """
        保存个股数据到JSON文件
        
        Args:
            stock_data: 股票数据
            output_dir: 输出目录
            
        Returns:
            保存的文件路径
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 构建文件名
        stock_name = stock_data['name']
        ts_code = stock_data['ts_code'].replace('.', '_')
        trade_date = stock_data['trade_date']
        timestamp = datetime.now().strftime("%H%M%S")
        
        filename = f"{trade_date}_{timestamp}_{stock_name}_{ts_code}_extracted.json"
        filepath = os.path.join(output_dir, filename)
        
        # 构建完整的数据结构（包含meta信息）
        extracted_data = {
            "meta": {
                "trade_date": self.data['meta']['trade_date'],
                "trade_date_display": self.data['meta']['trade_date_display'],
                "processing_time": datetime.now().isoformat(),
                "stock_count": 1,
                "data_quality": "extracted_single_stock",
                "source_file": os.path.basename(self.data_file_path),
                "extracted_stock": {
                    "name": stock_name,
                    "ts_code": stock_data['ts_code']
                }
            },
            "stocks": [stock_data]
        }
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已保存 {stock_name} 的数据到: {filepath}")
        return filepath
    
    def interactive_extract(self):
        """交互式提取工具"""
        print("\n🎯 股票数据提取工具")
        print("=" * 50)
        
        while True:
            print("\n请选择操作:")
            print("1. 列出所有股票")
            print("2. 搜索股票")
            print("3. 提取股票数据")
            print("4. 退出")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == "1":
                self._list_stocks_interactive()
            elif choice == "2":
                self._search_stocks_interactive()
            elif choice == "3":
                self._extract_stock_interactive()
            elif choice == "4":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选项，请重新选择")
    
    def _list_stocks_interactive(self):
        """交互式列出所有股票"""
        stocks = self.list_all_stocks()
        print(f"\n📊 共有 {len(stocks)} 只股票:")
        print("-" * 80)
        print(f"{'序号':<4} {'股票名称':<10} {'股票代码':<12} {'收盘价':<8} {'涨跌幅':<10} {'净流入':<12}")
        print("-" * 80)
        
        for i, stock in enumerate(stocks, 1):
            print(f"{i:<4} {stock['name']:<10} {stock['ts_code']:<12} {stock['close']:<8} {stock['pct_change']:<10} {stock['net_amount']:<12}")
    
    def _search_stocks_interactive(self):
        """交互式搜索股票"""
        query = input("\n🔍 请输入搜索关键词（股票名称或代码）: ").strip()
        if not query:
            print("❌ 搜索关键词不能为空")
            return
        
        matches = self.search_stock(query)
        if not matches:
            print(f"❌ 未找到包含 '{query}' 的股票")
            return
        
        print(f"\n🎯 找到 {len(matches)} 个匹配结果:")
        print("-" * 60)
        
        for i, stock in enumerate(matches, 1):
            print(f"{i}. {stock['name']} ({stock['ts_code']}) - {stock['basic_info']['pct_change']}")
    
    def _extract_stock_interactive(self):
        """交互式提取股票数据"""
        query = input("\n📤 请输入要提取的股票名称或代码: ").strip()
        if not query:
            print("❌ 股票名称/代码不能为空")
            return
        
        # 先尝试精确匹配
        stock_data = self.extract_stock_by_name(query)
        if not stock_data:
            stock_data = self.extract_stock_by_code(query)
        
        # 如果精确匹配失败，尝试模糊搜索
        if not stock_data:
            matches = self.search_stock(query)
            if not matches:
                print(f"❌ 未找到股票: {query}")
                return
            elif len(matches) == 1:
                stock_data = matches[0]
            else:
                print(f"\n🎯 找到多个匹配结果，请选择:")
                for i, stock in enumerate(matches, 1):
                    print(f"{i}. {stock['name']} ({stock['ts_code']})")
                
                try:
                    choice = int(input("\n请输入选项: ")) - 1
                    if 0 <= choice < len(matches):
                        stock_data = matches[choice]
                    else:
                        print("❌ 无效选项")
                        return
                except ValueError:
                    print("❌ 请输入有效数字")
                    return
        
        # 保存数据
        if stock_data:
            print(f"\n📋 股票信息:")
            print(f"名称: {stock_data['name']}")
            print(f"代码: {stock_data['ts_code']}")
            print(f"涨跌幅: {stock_data['basic_info']['pct_change']}")
            print(f"净流入: {stock_data['basic_info']['net_amount']}")
            
            confirm = input("\n确认提取此股票数据？(y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                filepath = self.save_stock_data(stock_data)
                print(f"✅ 数据已成功提取并保存!")
                return filepath
            else:
                print("❌ 已取消提取")


def main():
    """主函数 - 命令行工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description="股票数据提取工具")
    parser.add_argument("data_file", help="数据文件路径")
    parser.add_argument("-s", "--stock", help="股票名称或代码")
    parser.add_argument("-o", "--output", default="data/extracted", help="输出目录")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互式模式")
    parser.add_argument("-l", "--list", action="store_true", help="列出所有股票")
    
    args = parser.parse_args()
    
    # 初始化提取器
    extractor = StockDataExtractor(args.data_file)
    
    if args.interactive:
        # 交互式模式
        extractor.interactive_extract()
    elif args.list:
        # 列出所有股票
        stocks = extractor.list_all_stocks()
        print(f"共有 {len(stocks)} 只股票:")
        for stock in stocks:
            print(f"{stock['name']} ({stock['ts_code']}) - {stock['pct_change']}")
    elif args.stock:
        # 提取指定股票
        stock_data = extractor.extract_stock_by_name(args.stock)
        if not stock_data:
            stock_data = extractor.extract_stock_by_code(args.stock)
        
        if stock_data:
            filepath = extractor.save_stock_data(stock_data, args.output)
            print(f"✅ 已提取 {stock_data['name']} 的数据")
        else:
            print(f"❌ 未找到股票: {args.stock}")
    else:
        print("请指定操作选项，使用 -h 查看帮助")


if __name__ == "__main__":
    main() 