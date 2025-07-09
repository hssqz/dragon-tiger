"""
Gushen AI - DataFetcher 模块
负责从各种数据源获取原始数据（调取tushare API）

Version: 1.0
Author: AI
Date: 2024-07-25
"""

import tushare as ts
import pandas as pd
import os
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataFetcher:
    """
    数据获取器类
    负责从Tushare API获取龙虎榜相关数据
    """
    
    def __init__(self, tushare_token=None):
        """
        初始化DataFetcher
        
        Args:
            tushare_token (str): Tushare API token，如果为None则尝试从环境变量获取
        """
        if tushare_token is None:
            # 默认使用notebook中的token，生产环境建议从环境变量获取
            tushare_token = '3dd89b70c03a8b595c64686dbde181a4c68f1c8dedbb5c98f8b11d42'
        
        self.token = tushare_token
        self.pro = ts.pro_api(self.token)
        logger.info("DataFetcher初始化完成")
    
    def fetch_top_list(self, trade_date=None, save_to_csv=True, file_path='top_list.csv'):
        """
        获取龙虎榜每日列表数据
        
        Args:
            trade_date (str): 交易日期，格式YYYYMMDD，默认为最近交易日
            save_to_csv (bool): 是否保存为CSV文件
            file_path (str): CSV文件保存路径
            
        Returns:
            pd.DataFrame: 龙虎榜列表数据
        """
        try:
            # 如果未指定日期，使用最近交易日
            if trade_date is None:
                trade_date = self._get_latest_trade_date()
            
            logger.info(f"正在获取{trade_date}的龙虎榜列表数据...")
            
            # 调用Tushare API获取数据
            df = self.pro.top_list(trade_date=trade_date)
            
            if df.empty:
                logger.warning(f"日期{trade_date}没有龙虎榜数据")
                return df
            
            logger.info(f"成功获取{len(df)}条龙虎榜数据")
            
            # 数据质量检查
            self._validate_top_list_data(df)
            
            # 保存到CSV
            if save_to_csv:
                df.to_csv(file_path, index=False, encoding='utf-8')
                logger.info(f"数据已保存到: {file_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取龙虎榜列表数据失败: {str(e)}")
            raise
    
    def _get_latest_trade_date(self):
        """
        获取最近的交易日期（简单实现，实际应该考虑节假日）
        
        Returns:
            str: 交易日期字符串，格式YYYYMMDD
        """
        today = datetime.now()
        # 简单处理：如果是周末，回溯到周五
        if today.weekday() == 5:  # 周六
            today = today - timedelta(days=1)
        elif today.weekday() == 6:  # 周日
            today = today - timedelta(days=2)
        
        return today.strftime('%Y%m%d')
    
    def _validate_top_list_data(self, df):
        """
        验证top_list数据的完整性
        
        Args:
            df (pd.DataFrame): 待验证的数据
        """
        required_columns = [
            'trade_date', 'ts_code', 'name', 'close', 'pct_change',
            'turnover_rate', 'amount', 'l_sell', 'l_buy', 'l_amount',
            'net_amount', 'net_rate', 'amount_rate', 'float_values', 'reason'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必要字段: {missing_columns}")
        
        # 检查是否有空值
        critical_columns = ['trade_date', 'ts_code', 'name', 'close']
        for col in critical_columns:
            if df[col].isnull().any():
                logger.warning(f"关键字段{col}存在空值")
        
        logger.info("数据质量检查通过")
    
    def fetch_top_data(self, trade_date=None, save_to_csv=True, file_path='top_data.csv'):
        """
        获取个股席位数据（龙虎榜详细交易数据）
        
        Args:
            trade_date (str): 交易日期，格式YYYYMMDD，默认为最近交易日
            save_to_csv (bool): 是否保存为CSV文件
            file_path (str): CSV文件保存路径
            
        Returns:
            pd.DataFrame: 个股席位数据
        """
        try:
            # 如果未指定日期，使用最近交易日
            if trade_date is None:
                trade_date = self._get_latest_trade_date()
            
            logger.info(f"正在获取{trade_date}的个股席位数据...")
            
            # 调用Tushare API获取数据
            df = self.pro.top_inst(trade_date=trade_date)
            
            if df.empty:
                logger.warning(f"日期{trade_date}没有个股席位数据")
                return df
            
            logger.info(f"成功获取{len(df)}条个股席位数据")
            
            # 数据质量检查
            self._validate_top_data(df)
            
            # 保存到CSV
            if save_to_csv:
                df.to_csv(file_path, index=False, encoding='utf-8')
                logger.info(f"数据已保存到: {file_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取个股席位数据失败: {str(e)}")
            raise
    
    def _validate_top_data(self, df):
        """
        验证top_data数据的完整性
        
        Args:
            df (pd.DataFrame): 待验证的数据
        """
        required_columns = [
            'trade_date', 'ts_code', 'exalter', 'buy', 'buy_rate',
            'sell', 'sell_rate', 'net_buy', 'side', 'reason'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必要字段: {missing_columns}")
        
        # 检查是否有空值
        critical_columns = ['trade_date', 'ts_code', 'exalter']
        for col in critical_columns:
            if df[col].isnull().any():
                logger.warning(f"关键字段{col}存在空值")
        
        logger.info("个股席位数据质量检查通过")

    def fetch_daily_data(self, ts_codes=None, start_date=None, end_date=None, save_to_csv=True, file_path='daily_data.csv'):
        """
        获取股票日K线数据
        
        Args:
            ts_codes (str or list): 股票代码，可以是单个代码或代码列表，如果为None则从龙虎榜获取
            start_date (str): 开始日期，格式YYYYMMDD
            end_date (str): 结束日期，格式YYYYMMDD  
            save_to_csv (bool): 是否保存为CSV文件
            file_path (str): CSV文件保存路径
            
        Returns:
            pd.DataFrame: 日K线数据
        """
        try:
            # 如果未指定股票代码，从最新龙虎榜获取
            if ts_codes is None:
                if end_date is None:
                    end_date = self._get_latest_trade_date()
                top_list_df = self.fetch_top_list(trade_date=end_date, save_to_csv=False)
                if not top_list_df.empty:
                    ts_codes = top_list_df['ts_code'].unique().tolist()
                else:
                    raise ValueError("无法获取股票代码列表")
            
            # 处理股票代码格式
            if isinstance(ts_codes, str):
                ts_codes = [ts_codes]
            elif isinstance(ts_codes, list):
                pass
            else:
                raise ValueError("ts_codes参数格式错误")
            
            # 如果未指定日期范围，默认获取最近10个交易日
            if end_date is None:
                end_date = self._get_latest_trade_date()
            if start_date is None:
                # 简单计算：往前推14天（考虑周末）
                from datetime import datetime, timedelta
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                start_dt = end_dt - timedelta(days=14)
                start_date = start_dt.strftime('%Y%m%d')
            
            logger.info(f"正在获取{len(ts_codes)}只股票从{start_date}到{end_date}的日K线数据...")
            
            # 批量获取数据
            all_data = []
            for ts_code in ts_codes:
                try:
                    df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                    if not df.empty:
                        all_data.append(df)
                except Exception as e:
                    logger.warning(f"获取{ts_code}的数据失败: {str(e)}")
                    continue
            
            if not all_data:
                logger.warning("没有获取到任何日K线数据")
                return pd.DataFrame()
            
            # 合并所有数据
            combined_df = pd.concat(all_data, ignore_index=True)
            
            logger.info(f"成功获取{len(combined_df)}条日K线数据，覆盖{combined_df['ts_code'].nunique()}只股票")
            
            # 数据质量检查
            self._validate_daily_data(combined_df)
            
            # 保存到CSV
            if save_to_csv:
                combined_df.to_csv(file_path, index=False, encoding='utf-8')
                logger.info(f"数据已保存到: {file_path}")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"获取日K线数据失败: {str(e)}")
            raise
    
    def _validate_daily_data(self, df):
        """
        验证daily_data数据的完整性
        
        Args:
            df (pd.DataFrame): 待验证的数据
        """
        required_columns = [
            'ts_code', 'trade_date', 'open', 'high', 'low', 'close',
            'pre_close', 'change', 'pct_chg', 'vol', 'amount'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必要字段: {missing_columns}")
        
        # 检查是否有空值
        critical_columns = ['ts_code', 'trade_date', 'close']
        for col in critical_columns:
            if df[col].isnull().any():
                logger.warning(f"关键字段{col}存在空值")
        
        logger.info("日K线数据质量检查通过")

    def fetch_hm_list(self, save_to_csv=True, file_path='hm_list.csv'):
        """
        获取游资名人录数据
        
        Args:
            save_to_csv (bool): 是否保存为CSV文件
            file_path (str): CSV文件保存路径
            
        Returns:
            pd.DataFrame: 游资名人录数据
        """
        try:
            logger.info("正在获取游资名人录数据...")
            
            # 调用Tushare API获取数据
            df = self.pro.hm_list()
            
            if df.empty:
                logger.warning("没有获取到游资名人录数据")
                return df
            
            logger.info(f"成功获取{len(df)}条游资名人录数据")
            
            # 数据质量检查
            self._validate_hm_list_data(df)
            
            # 保存到CSV
            if save_to_csv:
                df.to_csv(file_path, index=False, encoding='utf-8')
                logger.info(f"数据已保存到: {file_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取游资名人录数据失败: {str(e)}")
            raise
    
    def _validate_hm_list_data(self, df):
        """
        验证hm_list数据的完整性
        
        Args:
            df (pd.DataFrame): 待验证的数据
        """
        required_columns = ['name', 'desc', 'orgs']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必要字段: {missing_columns}")
        
        # 检查是否有空值
        critical_columns = ['name']
        for col in critical_columns:
            if df[col].isnull().any():
                logger.warning(f"关键字段{col}存在空值")
        
        logger.info("游资名人录数据质量检查通过")

    def get_data_summary(self, trade_date=None):
        """
        获取指定日期的龙虎榜数据概况
        
        Args:
            trade_date (str): 交易日期，格式YYYYMMDD
            
        Returns:
            dict: 数据概况信息
        """
        df = self.fetch_top_list(trade_date, save_to_csv=False)
        
        if df.empty:
            return {"error": "无数据"}
        
        summary = {
            "date": trade_date or self._get_latest_trade_date(),
            "total_stocks": len(df),
            "total_amount": df['l_amount'].sum(),
            "avg_pct_change": df['pct_change'].mean(),
            "top_reasons": df['reason'].value_counts().head(3).to_dict()
        }
        
        return summary


def main():
    """
    测试函数
    """
    # 初始化DataFetcher
    fetcher = DataFetcher()
    
    # 获取最新龙虎榜数据
    print("=== 测试DataFetcher ===")
    
    # 测试1：获取龙虎榜列表数据
    test_date = '20250617'
    df_list = fetcher.fetch_top_list(trade_date=test_date, file_path='test_top_list.csv')
    print(f"获取{test_date}龙虎榜列表数据：{len(df_list)}条记录")
    print(df_list.head())
    
    # 测试2：获取个股席位数据
    df_data = fetcher.fetch_top_data(trade_date=test_date, file_path='test_top_data.csv')
    print(f"\n获取{test_date}个股席位数据：{len(df_data)}条记录")
    print(df_data.head())
    
    # 测试3：获取日K线数据（测试指定股票代码）
    test_codes = ['000525.SZ', '000554.SZ']
    df_daily = fetcher.fetch_daily_data(
        ts_codes=test_codes, 
        start_date='20250604', 
        end_date='20250617',
        file_path='test_daily_data.csv'
    )
    print(f"\n获取{test_codes}从20250604到20250617的日K线数据：{len(df_daily)}条记录")
    print(df_daily.head())
    
    # 测试4：获取游资名人录数据
    df_hm = fetcher.fetch_hm_list(file_path='test_hm_list.csv')
    print(f"\n获取游资名人录数据：{len(df_hm)}条记录")
    print(df_hm.head())
    
    # 测试5：获取数据概况
    summary = fetcher.get_data_summary(test_date)
    print(f"\n数据概况：{summary}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main() 