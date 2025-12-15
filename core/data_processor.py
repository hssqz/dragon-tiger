"""
Gushen AI - DataProcessor 模块
负责对原始数据进行清洗、格式化、合并

Version: 2.1
Author: AI
Date: 2024-07-25
Updated: 2025-01-XX - 完善字段单位标识规范，百分比加"%"，成交量改为"万手"
"""

import pandas as pd
import numpy as np
import json
import logging
import re
import os
from datetime import datetime, timedelta
from data_fetcher import DataFetcher

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    数据处理器类
    负责清洗、合并和预处理龙虎榜相关数据
    """
    
    def __init__(self, data_fetcher=None):
        """
        初始化DataProcessor
        
        Args:
            data_fetcher (DataFetcher): 数据获取器实例，如果为None则创建新实例
        """
        self.fetcher = data_fetcher if data_fetcher else DataFetcher()
        # 加载游资画像数据
        self.player_profiles = self._load_player_profiles()
        logger.info("DataProcessor初始化完成")
    
    def _load_player_profiles(self):
        """
        加载游资画像数据
        
        Returns:
            dict: 游资名称 -> 画像信息的映射
        """
        player_profiles = {}
        
        try:
            # 获取当前文件的目录，然后构建相对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            profile_file = os.path.join(current_dir, '..', 'docs', '游资风格画像分析.md')
            
            if not os.path.exists(profile_file):
                logger.warning(f"游资画像文件不存在: {profile_file}")
                return player_profiles
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析markdown表格
            lines = content.strip().split('\n')
            
            # 找到表格数据行（跳过标题和分隔符）
            data_lines = []
            in_table = False
            for line in lines:
                if line.startswith('|') and '游资名称' in line:
                    in_table = True
                    continue
                elif line.startswith('|') and ':---' in line:
                    continue
                elif line.startswith('|') and in_table:
                    data_lines.append(line)
            
            # 解析每一行数据
            for line in data_lines:
                if not line.strip():
                    continue
                
                # 分割表格列
                columns = [col.strip() for col in line.split('|')[1:-1]]  # 去掉首尾空元素
                
                if len(columns) >= 5:
                    player_name = columns[0].replace('**', '').strip()  # 去掉markdown加粗符号
                    profile = columns[1].strip()
                    preference = columns[2].strip()
                    code = columns[3].strip()
                    reputation = columns[4].strip()
                    
                    # 构建完整的画像信息
                    player_profiles[player_name] = {
                        "profile": profile if profile != '-' else '',
                        "preference": preference if preference != '-' else '',
                        "code": code if code != '-' else '',
                        "reputation": reputation if reputation != '-' else ''
                    }
            
            logger.info(f"成功加载{len(player_profiles)}个游资画像")
            
        except Exception as e:
            logger.error(f"加载游资画像数据失败: {str(e)}")
        
        return player_profiles
    
    # ==================== 数据清洗辅助方法 ====================
    
    def _format_amount(self, amount):
        """
        金额单位转换：元 -> 万元/亿元，直接返回格式化字符串
        """
        if pd.isna(amount) or amount == 0:
            return "0.00万元"
        
        if amount < 10000000:  # < 1000万元 -> 万元显示
            amount_wan = amount / 10000
            return f"{amount_wan:,.2f}万元"
        else:  # >= 1000万元 -> 亿元显示
            amount_yi = amount / 100000000
            return f"{amount_yi:,.2f}亿元"
    
    def _format_percentage(self, percentage):
        """
        百分比格式化，保留两位小数并添加%符号
        
        Args:
            percentage (float): 百分比数值
            
        Returns:
            str: 格式化后的百分比字符串
        """
        if pd.isna(percentage):
            return "0.00%"
        return f"{round(float(percentage), 2):.2f}%"
    
    def _format_volume(self, volume):
        """
        成交量格式化，转换为万手并保留两位小数
        
        Args:
            volume (float): 成交量数值（手）
            
        Returns:
            str: 格式化后的成交量字符串（万手）
        """
        if pd.isna(volume):
            return "0.00万手"
        volume_wan = float(volume) / 10000  # 手转万手
        return f"{volume_wan:,.2f}万手"
    
    def _format_price(self, price):
        """
        价格格式化，保留两位小数
        
        Args:
            price (float): 价格数值
            
        Returns:
            float: 格式化后的价格
        """
        if pd.isna(price):
            return 0.00
        return round(float(price), 2)
    
    def _format_date_display(self, date_str):
        """
        日期格式化：YYYYMMDD -> YYYY-MM-DD
        
        Args:
            date_str (str): 输入日期字符串 (YYYYMMDD)
            
        Returns:
            str: 格式化后的日期字符串 (YYYY-MM-DD)
        """
        if not date_str or pd.isna(date_str):
            return ""
        
        try:
            # 确保是字符串格式
            date_str = str(date_str)
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                return date_str
        except Exception:
            return str(date_str)
    
    # ==================== 原有方法（已更新清洗逻辑）====================

    def process_single_date_data(self, trade_date, days_back=10):
        """
        处理单个交易日的完整数据（核心方法）
        
        Args:
            trade_date (str): 交易日期，格式YYYYMMDD
            days_back (int): 向前获取历史数据的天数
            
        Returns:
            dict: 处理后的结构化数据
        """
        try:
            logger.info(f"开始处理{trade_date}的完整数据...")
            
            # 1. 获取基础数据
            top_list_df = self.fetcher.fetch_top_list(trade_date=trade_date, save_to_csv=False)
            top_data_df = self.fetcher.fetch_top_data(trade_date=trade_date, save_to_csv=False)
            hm_list_df = self.fetcher.fetch_hm_list(save_to_csv=False)
            
            if top_list_df.empty:
                logger.warning(f"日期{trade_date}没有龙虎榜数据")
                return {"error": f"日期{trade_date}没有龙虎榜数据"}
            
            # 2. 获取历史K线数据
            ts_codes = top_list_df['ts_code'].unique().tolist()
            # 过滤掉可转债（通常以1开头且以.SZ/.SH结尾）
            stock_codes = [code for code in ts_codes if not self._is_convertible_bond(code)]
            
            if stock_codes:
                start_date = self._calculate_start_date(trade_date, days_back)
                daily_df = self.fetcher.fetch_daily_data(
                    ts_codes=stock_codes, 
                    start_date=start_date, 
                    end_date=trade_date,
                    save_to_csv=False
                )
            else:
                daily_df = pd.DataFrame()  # 空DataFrame
            
            # 3. 数据清洗和预处理
            processed_data = {
                "meta": {
                    "trade_date": trade_date,
                    "trade_date_display": self._format_date_display(trade_date),
                    "processing_time": datetime.now().isoformat(),
                    "stock_count": len(ts_codes),
                    "data_quality": "good"
                },
                "stocks": self._process_stock_data(top_list_df, top_data_df, daily_df, hm_list_df)
            }
            
            logger.info(f"数据处理完成，包含{len(processed_data['stocks'])}只股票")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理{trade_date}数据失败: {str(e)}")
            raise
    
    def _process_stock_data(self, top_list_df, top_data_df, daily_df, hm_list_df):
        """
        处理每只股票的完整数据，避免重复处理
        
        Returns:
            list: 处理后的股票数据列表
        """
        stocks_data = []
        
        # 获取唯一的股票代码，避免重复处理
        unique_stocks = top_list_df.drop_duplicates(subset=['ts_code'])
        
        for _, stock_row in unique_stocks.iterrows():
            ts_code = stock_row['ts_code']
            
            # 获取该股票的所有上榜记录（可能有多个原因）
            stock_records = top_list_df[top_list_df['ts_code'] == ts_code]
            
            # 合并多个上榜记录的信息
            merged_info = self._merge_stock_records(stock_records)
            
            # 基础信息
            stock_info = {
                "ts_code": ts_code,
                "name": stock_row['name'],
                "trade_date": stock_row['trade_date'],
                "basic_info": merged_info,
                "seat_data": self._process_seat_data(ts_code, top_data_df, hm_list_df),
                "historical_data": self._process_historical_data(ts_code, daily_df)
            }
            
            stocks_data.append(stock_info)
        
        return stocks_data
    
    def _merge_stock_records(self, stock_records):
        """
        合并同一只股票的多个上榜记录
        
        Args:
            stock_records (pd.DataFrame): 同一只股票的所有上榜记录
            
        Returns:
            dict: 合并后的基础信息
        """
        def safe_float(value, default=0.0):
            """安全转换为float，处理NaN值"""
            try:
                if pd.isna(value):
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # 取第一条记录作为基础
        first_record = stock_records.iloc[0]
        
        # 对于数值字段，取最大值（代表该股票当日的最大交易情况）
        # 应用数据清洗规范
        merged_data = {
            "close": self._format_price(first_record['close']),
            "pct_change": self._format_percentage(first_record['pct_change']),
            "turnover_rate": self._format_percentage(stock_records['turnover_rate'].max()),
            "amount": self._format_amount(safe_float(stock_records['amount'].max())),
            "l_sell": self._format_amount(safe_float(stock_records['l_sell'].max())),
            "l_buy": self._format_amount(safe_float(stock_records['l_buy'].max())),
            "l_amount": self._format_amount(safe_float(stock_records['l_amount'].max())),
            "net_amount": self._format_amount(safe_float(stock_records['net_amount'].max())),
            "net_rate": self._format_percentage(stock_records['net_rate'].max()),
            "amount_rate": self._format_percentage(stock_records['amount_rate'].max()),
            "float_values": self._format_amount(safe_float(first_record['float_values'])),
            "reasons": list(stock_records['reason'].drop_duplicates()),  # 去重后保存所有上榜原因
            "trade_date_display": self._format_date_display(first_record['trade_date'])  # 添加格式化日期
        }
        
        return merged_data
    
    def _extract_basic_info(self, stock_row):
        """
        提取股票基础信息，处理NaN值，应用数据清洗规范
        """
        def safe_float(value, default=0.0):
            """安全转换为float，处理NaN值"""
            try:
                if pd.isna(value):
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        return {
            "close": self._format_price(stock_row['close']),
            "pct_change": self._format_percentage(stock_row['pct_change']),
            "turnover_rate": self._format_percentage(stock_row['turnover_rate']),
            "amount": self._format_amount(safe_float(stock_row['amount'])),
            "l_sell": self._format_amount(safe_float(stock_row['l_sell'])),
            "l_buy": self._format_amount(safe_float(stock_row['l_buy'])),
            "l_amount": self._format_amount(safe_float(stock_row['l_amount'])),
            "net_amount": self._format_amount(safe_float(stock_row['net_amount'])),
            "net_rate": self._format_percentage(stock_row['net_rate']),
            "amount_rate": self._format_percentage(stock_row['amount_rate']),
            "float_values": self._format_amount(safe_float(stock_row['float_values'])),
            "reason": stock_row['reason'],
            "trade_date_display": self._format_date_display(stock_row['trade_date'])  # 添加格式化日期
        }
    
    def _process_seat_data(self, ts_code, top_data_df, hm_list_df):
        """
        处理席位数据，包括游资身份识别和去重
        正确处理重复：只去除因多个上榜原因导致的完全重复记录，保留所有不同的席位
        """
        # 筛选当前股票的席位数据
        stock_seats = top_data_df[top_data_df['ts_code'] == ts_code].copy()
        
        if stock_seats.empty:
            return {"buy_seats": [], "sell_seats": [], "buy_total": "0.00万元", "sell_total": "0.00万元"}
        
        # 关键修复：去除因多个上榜原因导致的完全重复记录
        # 按(席位名称, 买入金额, 卖出金额, 净买入, 买入比例, 卖出比例)去重
        # 保留相同名称但不同金额的席位（这些是不同的席位）
        stock_seats_dedup = stock_seats.drop_duplicates(
            subset=['exalter', 'buy', 'sell', 'net_buy', 'buy_rate', 'sell_rate']
        ).copy()
        
        logger.debug(f"股票{ts_code}: 原始席位记录{len(stock_seats)}条，去重后{len(stock_seats_dedup)}条")
        
        # 不再按席位名称分组求和，直接处理每个不同的席位
        buy_seats = []
        sell_seats = []
        
        # 先按净买入排序，再格式化
        stock_seats_sorted = stock_seats_dedup.sort_values('net_buy', ascending=False)
        
        for _, seat_row in stock_seats_sorted.iterrows():
            # 应用数据清洗规范
            seat_info = {
                "seat_name": seat_row['exalter'],
                "buy_amount": self._format_amount(max(0, float(seat_row['buy']))),
                "sell_amount": self._format_amount(max(0, float(seat_row['sell']))),
                "net_amount": self._format_amount(float(seat_row['net_buy'])),
                "buy_rate": self._format_percentage(max(0, float(seat_row['buy_rate']))),
                "sell_rate": self._format_percentage(max(0, float(seat_row['sell_rate']))),
                "player_info": self._identify_player(seat_row['exalter'], hm_list_df)
            }
            
            # 根据净买入方向分类
            if float(seat_row['net_buy']) > 0:
                buy_seats.append(seat_info)
            else:
                sell_seats.append(seat_info)
        
        # 计算总金额
        buy_total_raw = sum([max(0, float(seat_row['buy'])) for _, seat_row in stock_seats_sorted.iterrows()])
        sell_total_raw = sum([max(0, float(seat_row['sell'])) for _, seat_row in stock_seats_sorted.iterrows()])
        
        return {
            "buy_seats": buy_seats,
            "sell_seats": sell_seats,
            "buy_total": self._format_amount(buy_total_raw),
            "sell_total": self._format_amount(sell_total_raw)
        }
    
    def _identify_player(self, seat_name, hm_list_df):
        """
        识别席位背后的玩家身份
        支持游资/量化/机构三种类型的识别
        """
        # 默认玩家信息
        player_info = {
            "name": "普通席位",
            "type": "机构专用" if "机构专用" in seat_name else "普通席位",
            "description": "暂无相关信息",
            "style": ["风格未明"]
        }
        
        # 遍历游资名人录进行匹配
        for _, hm_row in hm_list_df.iterrows():
            try:
                # 解析orgs字段（JSON格式）
                orgs = json.loads(hm_row['orgs'].replace("'", '"')) if hm_row['orgs'] != '[]' else []
                
                # 检查是否匹配
                for org in orgs:
                    if org in seat_name or seat_name in org:
                        # 确定玩家类型：量化 > 知名游资 > 知名机构
                        player_type = self._determine_player_type(hm_row['name'], hm_row['desc'])
                        
                        player_info = {
                            "name": hm_row['name'],
                            "type": player_type,
                            "description": hm_row['desc'],
                            "style": self._get_player_style_from_profile(hm_row['name'])
                        }
                        break
                
                if player_info['type'] not in ["普通席位", "机构专用"]:
                    break
                    
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return player_info
    
    def _determine_player_type(self, name, description):
        """
        根据名称精确匹配确定玩家类型
        
        Args:
            name (str): 玩家名称
            description (str): 玩家描述
            
        Returns:
            str: 玩家类型（量化/机构/知名游资）
        """
        # 量化类型（精确匹配名称）
        quant_names = [
            "量化抢筹",
            "量化打扮", 
            "量化基金",
            "竞价抢筹"
        ]
        
        # 机构类型（精确匹配名称）
        institution_names = [
            "深股通专用",
            "沪股通专用",
            "机构专用",
            "境外机构",
            "中信总部"
        ]
        
        # 优先级：量化 > 机构 > 游资
        # 精确匹配量化名称
        if name in quant_names:
            return "量化"
        # 精确匹配机构名称
        elif name in institution_names:
            return "机构"
        # 默认为知名游资
        else:
            return "知名游资"
    
    def _get_player_style_from_profile(self, player_name):
        """
        从游资画像数据中获取完整的风格信息
        
        Args:
            player_name (str): 游资名称
            
        Returns:
            dict: 完整的游资画像信息
        """
        # 精确匹配游资名称
        if player_name in self.player_profiles:
            profile_data = self.player_profiles[player_name]
            
            # 构建完整的风格画像信息
            style_info = {
                "核心交易档案": profile_data.get("profile", ""),
                "标的选择偏好": profile_data.get("preference", ""), 
                "盘中操盘密码": profile_data.get("code", ""),
                "软实力与市场标签": profile_data.get("reputation", "")
            }
            
            # 过滤掉空值
            style_info = {k: v for k, v in style_info.items() if v}
            
            return style_info if style_info else {"风格画像": "暂无详细信息"}
        
        # 如果没有找到精确匹配，返回默认信息
        return {"风格画像": "暂无详细信息"}
    
    def _process_historical_data(self, ts_code, daily_df):
        """
        处理历史K线数据
        """
        # 如果是可转债，返回特殊标记
        if self._is_convertible_bond(ts_code):
            return {
                "chart_data": [], 
                "summary": {"note": "可转债暂不提供历史K线数据"}
            }
        
        # 筛选当前股票的历史数据
        stock_daily = daily_df[daily_df['ts_code'] == ts_code].copy()
        
        if stock_daily.empty:
            return {"chart_data": [], "summary": {}}
        
        # 按日期排序
        stock_daily = stock_daily.sort_values('trade_date')
        
        # 构建图表数据，应用数据清洗规范
        chart_data = []
        for _, row in stock_daily.iterrows():
            chart_data.append({
                "date": row['trade_date'],  # 保持原始格式用于计算
                "date_display": self._format_date_display(row['trade_date']),  # 添加显示格式
                "open": self._format_price(row['open']),
                "high": self._format_price(row['high']),
                "low": self._format_price(row['low']),
                "close": self._format_price(row['close']),
                "volume": self._format_volume(row['vol']),  # 成交量格式化
                "amount": self._format_amount(float(row['amount']) * 1000),  # 千元转元后格式化
                "pct_change": self._format_percentage(row['pct_chg'])
            })
        
        # 计算历史统计，应用数据清洗规范
        summary = {
            "days_count": len(chart_data),
            "max_price": self._format_price(stock_daily['high'].max()),
            "min_price": self._format_price(stock_daily['low'].min()),
            "avg_volume": self._format_volume(stock_daily['vol'].mean()),
            "volatility": self._format_percentage(stock_daily['pct_chg'].std())
        }
        
        return {
            "chart_data": chart_data,
            "summary": summary
        }
    
    def _is_convertible_bond(self, ts_code):
        """
        判断是否为可转债
        可转债代码通常以1开头（如123xxx.SZ, 113xxx.SH等）
        """
        if pd.isna(ts_code) or not isinstance(ts_code, str):
            return False
        
        code_part = ts_code.split('.')[0]
        return code_part.startswith('1') and len(code_part) == 6
    
    def _calculate_start_date(self, end_date, days_back):
        """
        计算开始日期
        """
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        start_dt = end_dt - timedelta(days=days_back * 2)  # 考虑周末，多取一些天数
        return start_dt.strftime('%Y%m%d')
    
    def save_processed_data(self, processed_data, file_path='processed_data.json'):
        """
        保存处理后的数据到JSON文件
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"处理后的数据已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            raise


def main():
    """
    测试函数
    """
    print("=== 测试DataProcessor ===")
    
    # 初始化DataProcessor
    processor = DataProcessor()
    
    # 测试处理单个交易日数据
    test_date = '20250805'
    processed_data = processor.process_single_date_data(test_date, days_back=10)
    
    print(f"处理{test_date}数据完成")
    print(f"包含股票数量: {processed_data['meta']['stock_count']}")
    print(f"第一只股票示例: {processed_data['stocks'][0]['name']}")
    
    # 保存处理后的数据
    processor.save_processed_data(processed_data, 'test_processed_data_0624.json')
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main() 