#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gushen AI - 龙虎榜数据处理完整流水线
串联数据获取、处理、提取和LLM分析的完整workflow

Version: 1.0
Author: AI  
Date: 2025-01-XX
"""

import os
import sys
import json
import logging
import argparse
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

# 添加core目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from core.data_fetcher import DataFetcher
from core.data_processor import DataProcessor  
from utils.stock_data_extractor import StockDataExtractor
from core.funding_battle_analyzer import FundingBattleAnalyzer
from core.post_generator_v2 import PostGeneratorV2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dragon_tiger_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('dragon_tiger_pipeline')


class DragonTigerPipeline:
    """
    龙虎榜数据处理完整流水线
    将数据获取、处理、提取和LLM分析串联起来
    """
    
    def __init__(self, tushare_token: str = None, max_workers: int = 16, api_delay: float = 0.1, enable_post_generation: bool = False):
        """
        初始化流水线
        
        Args:
            tushare_token: Tushare API token，如果为None则使用默认值
            max_workers: 最大并行工作线程数（DeepSeek无限制，可以激进设置）
            api_delay: API调用间隔（秒），由于无限制可以设置很小
            enable_post_generation: 是否启用帖子生成功能
        """
        logger.info("初始化龙虎榜数据处理流水线（高并发版本+帖子生成）...")
        
        # 初始化各个组件
        self.data_fetcher = DataFetcher(tushare_token)
        self.data_processor = DataProcessor(self.data_fetcher)
        
        # 帖子生成配置
        self.enable_post_generation = enable_post_generation
        if enable_post_generation:
            self.post_generator = PostGeneratorV2()
            logger.info("✅ 帖子生成功能已启用")
        
        # 高并发配置
        self.max_workers = max_workers
        self.api_delay = api_delay
        
        # 线程安全锁
        self.progress_lock = Lock()
        self.result_lock = Lock()
        
        # 创建必要的目录
        self._ensure_directories()
        
        logger.info(f"流水线初始化完成，高并发模式: {max_workers}线程, API延迟: {api_delay}秒")
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            'data/processed',
            'data/extracted', 
            'data/analyzed',
            'data/output/posts',  # 帖子输出根目录
            'logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _ensure_post_date_directory(self, trade_date: str):
        """确保指定日期的帖子目录存在"""
        post_date_dir = f"data/output/posts/{trade_date}"
        os.makedirs(post_date_dir, exist_ok=True)
        return post_date_dir
    
    def _ensure_date_directory(self, trade_date: str):
        """确保指定日期的目录存在"""
        date_dir = f"data/analyzed/{trade_date}"
        os.makedirs(date_dir, exist_ok=True)
        return date_dir
    
    def process_date(self, trade_date: str, skip_existing: bool = True) -> Dict[str, Any]:
        """
        处理指定日期的完整龙虎榜数据
        
        Args:
            trade_date: 交易日期，格式YYYYMMDD
            skip_existing: 是否跳过已存在的分析结果
            
        Returns:
            包含所有股票分析结果的字典
        """
        logger.info(f"开始处理{trade_date}的龙虎榜数据")
        
        # 步骤1：数据获取和处理
        processed_data = self._step1_fetch_and_process(trade_date)
        if not processed_data:
            return {"error": "数据获取或处理失败"}
        
        # 步骤2：提取和分析每只股票（根据模式选择并行或串行）
        if hasattr(self, '_force_serial') and self._force_serial:
            analysis_results = self._step2_analyze_stocks_serial(processed_data, trade_date, skip_existing)
        else:
            analysis_results = self._step2_analyze_stocks_parallel(processed_data, trade_date, skip_existing)
        
        # 步骤3：生成帖子（如果启用）
        if self.enable_post_generation and analysis_results:
            if hasattr(self, '_force_serial') and self._force_serial:
                post_results = self._step3_generate_posts_serial(analysis_results, trade_date, skip_existing)
            else:
                post_results = self._step3_generate_posts_parallel(analysis_results, trade_date, skip_existing)
        else:
            post_results = []
        
        # 步骤4：汇总结果
        summary_result = self._step4_generate_summary(analysis_results, post_results, trade_date)
        
        logger.info(f"完成{trade_date}的龙虎榜数据处理")
        return summary_result
    
    def _step1_fetch_and_process(self, trade_date: str) -> Optional[Dict[str, Any]]:
        """
        步骤1：获取原始数据并进行预处理
        """
        try:
            logger.info("步骤1: 获取和处理原始数据")
            
            # 检查是否已有处理后的数据
            processed_file = f"data/processed/{trade_date}_processed_data.json"
            if os.path.exists(processed_file):
                logger.info(f"发现已处理的数据文件: {processed_file}")
                with open(processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 获取和处理数据
            processed_data = self.data_processor.process_single_date_data(
                trade_date=trade_date,
                days_back=10
            )
            
            if not processed_data or 'error' in processed_data:
                logger.error(f"数据处理失败: {processed_data}")
                return None
            
            # 保存处理后的数据
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据处理完成，包含{processed_data['meta']['stock_count']}只股票")
            return processed_data
            
        except Exception as e:
            logger.error(f"步骤1失败: {e}")
            return None
    
    def _step2_analyze_stocks_serial(self, processed_data: Dict[str, Any], trade_date: str, skip_existing: bool) -> List[Dict[str, Any]]:
        """
        步骤2：提取并分析每只股票
        """
        logger.info("步骤2: 分析各只股票")
        
        # 确保日期目录存在
        date_dir = self._ensure_date_directory(trade_date)
        
        stocks = processed_data.get('stocks', [])
        analysis_results = []
        
        # 使用进度条显示处理进度
        with tqdm(total=len(stocks), desc="分析股票") as pbar:
            for i, stock_data in enumerate(stocks):
                stock_name = stock_data.get('name', 'Unknown')
                ts_code = stock_data.get('ts_code', 'Unknown')
                
                pbar.set_description(f"分析 {stock_name}")
                
                try:
                    # 构建分析结果文件路径（放在日期目录下）
                    analysis_file = os.path.join(date_dir, f"{stock_name}_{ts_code.replace('.', '_')}_analysis.json")
                    
                    if skip_existing and os.path.exists(analysis_file):
                        logger.info(f"跳过已分析的股票: {stock_name}")
                        # 加载已有结果
                        with open(analysis_file, 'r', encoding='utf-8') as f:
                            existing_result = json.load(f)
                            analysis_results.append(existing_result)
                        pbar.update(1)
                        continue
                    
                    # 提取单股数据
                    extracted_data = self._extract_single_stock(processed_data, stock_data, trade_date)
                    if not extracted_data:
                        logger.warning(f"提取{stock_name}数据失败")
                        pbar.update(1)
                        continue
                    
                    # LLM分析
                    analysis_result = self._analyze_single_stock(extracted_data, stock_name, ts_code)
                    if analysis_result:
                        # 保存分析结果到日期目录下
                        with open(analysis_file, 'w', encoding='utf-8') as f:
                            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                        
                        analysis_results.append(analysis_result)
                        logger.info(f"完成{stock_name}分析，保存至: {analysis_file}")
                    else:
                        logger.warning(f"分析{stock_name}失败")
                
                except Exception as e:
                    logger.error(f"处理{stock_name}时出错: {e}")
                
                pbar.update(1)
        
        return analysis_results
    
    def _step2_analyze_stocks_parallel(self, processed_data: Dict[str, Any], trade_date: str, skip_existing: bool) -> List[Dict[str, Any]]:
        """
        步骤2：并行提取并分析每只股票（高并发版本）
        """
        logger.info(f"步骤2: 高并发分析各只股票（{self.max_workers}线程）")
        
        # 确保日期目录存在
        date_dir = self._ensure_date_directory(trade_date)
        
        stocks = processed_data.get('stocks', [])
        analysis_results = []
        
        # 准备任务参数
        tasks = [(stock_data, trade_date, date_dir, skip_existing, processed_data) for stock_data in stocks]
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(self._analyze_single_stock_worker, task): task[0]['name'] 
                for task in tasks
            }
            
            # 使用进度条显示处理进度
            with tqdm(total=len(stocks), desc="🚀 高并发分析中") as pbar:
                for future in as_completed(future_to_stock):
                    stock_name = future_to_stock[future]
                    try:
                        result = future.result()
                        if result:
                            with self.result_lock:
                                analysis_results.append(result)
                    except Exception as e:
                        logger.error(f"分析{stock_name}时出现异常: {e}")
                    
                    with self.progress_lock:
                        pbar.update(1)
                        pbar.set_description(f"🚀 已完成 {len(analysis_results)} 只股票")
        
        logger.info(f"高并发分析完成，成功分析 {len(analysis_results)}/{len(stocks)} 只股票")
        return analysis_results
    
    def _analyze_single_stock_worker(self, args: Tuple[Dict[str, Any], str, str, bool, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        单只股票分析的工作函数（线程工作单元）
        
        Args:
            args: (stock_data, trade_date, date_dir, skip_existing, processed_data)
            
        Returns:
            分析结果或None
        """
        stock_data, trade_date, date_dir, skip_existing, processed_data = args
        
        stock_name = stock_data.get('name', 'Unknown')
        ts_code = stock_data.get('ts_code', 'Unknown')
        thread_id = threading.current_thread().ident
        
        try:
            # 构建分析结果文件路径
            analysis_file = os.path.join(date_dir, f"{stock_name}_{ts_code.replace('.', '_')}_analysis.json")
            
            # 检查是否已有分析结果
            if skip_existing and os.path.exists(analysis_file):
                logger.debug(f"[线程{thread_id}] 跳过已分析的股票: {stock_name}")
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 提取单股数据（线程安全版本）
            extracted_file = self._extract_single_stock_for_thread(stock_data, trade_date, thread_id, processed_data)
            if not extracted_file:
                logger.warning(f"[线程{thread_id}] 提取{stock_name}数据失败")
                return None
            
            # 轻微的API调用延迟（防止过度并发）
            if self.api_delay > 0:
                time.sleep(self.api_delay)
            
            # 创建线程专用的分析器实例
            funding_analyzer = FundingBattleAnalyzer()
            
            # LLM分析
            analysis_result = funding_analyzer.analyze_complete_report(
                data_file_path=extracted_file,
                output_path=None
            )
            
            # 清理临时文件
            if os.path.exists(extracted_file):
                os.remove(extracted_file)
            
            if analysis_result:
                # 保存分析结果
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                
                analysis_result['processed_at'] = datetime.now().isoformat()
                logger.debug(f"[线程{thread_id}] 完成{stock_name}分析")
                return analysis_result
            else:
                logger.warning(f"[线程{thread_id}] 分析{stock_name}失败")
                return None
                
        except Exception as e:
            logger.error(f"[线程{thread_id}] 处理{stock_name}时出错: {e}")
            return None
    
    def _extract_single_stock_for_thread(self, stock_data: Dict[str, Any], trade_date: str, thread_id: int, processed_data: Dict[str, Any]) -> Optional[str]:
        """
        为线程提取单只股票的数据（线程安全版本）
        """
        try:
            # 创建临时的完整数据结构
            temp_data = {
                "meta": processed_data["meta"],
                "stocks": [stock_data]
            }
            
            # 保存临时文件（包含线程ID避免冲突）
            temp_file = f"data/extracted/temp_{trade_date}_{stock_data['name']}_{stock_data['ts_code'].replace('.', '_')}_thread{thread_id}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)
            
            return temp_file
            
        except Exception as e:
            logger.error(f"[线程{thread_id}] 提取单股数据失败: {e}")
            return None
    
    def _step3_generate_posts_parallel(self, analysis_results: List[Dict[str, Any]], trade_date: str, skip_existing: bool) -> List[Dict[str, Any]]:
        """
        步骤3：并行生成帖子（高并发版本）
        """
        if not self.enable_post_generation:
            logger.info("帖子生成功能未启用，跳过")
            return []
        
        logger.info(f"步骤3: 高并发生成帖子（{self.max_workers}线程）")
        
        # 确保日期目录存在
        date_dir = self._ensure_date_directory(trade_date)
        post_date_dir = self._ensure_post_date_directory(trade_date)
        
        # 过滤有效的分析结果
        valid_results = [r for r in analysis_results if r and 'analysis_report' in r]
        post_results = []
        
        # 准备任务参数
        tasks = [(result, trade_date, date_dir, post_date_dir, skip_existing) for result in valid_results]
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(self._generate_single_post_worker, task): task[0].get('stock_info', {}).get('name', 'Unknown')
                for task in tasks
            }
            
            # 使用进度条显示处理进度
            with tqdm(total=len(valid_results), desc="📝 高并发生成帖子") as pbar:
                for future in as_completed(future_to_stock):
                    stock_name = future_to_stock[future]
                    try:
                        result = future.result()
                        if result:
                            with self.result_lock:
                                post_results.append(result)
                    except Exception as e:
                        logger.error(f"生成{stock_name}帖子时出现异常: {e}")
                    
                    with self.progress_lock:
                        pbar.update(1)
                        pbar.set_description(f"📝 已生成 {len(post_results)} 篇帖子")
        
        logger.info(f"高并发帖子生成完成，成功生成 {len(post_results)}/{len(valid_results)} 篇帖子")
        return post_results
    
    def _step3_generate_posts_serial(self, analysis_results: List[Dict[str, Any]], trade_date: str, skip_existing: bool) -> List[Dict[str, Any]]:
        """
        步骤3：串行生成帖子
        """
        if not self.enable_post_generation:
            logger.info("帖子生成功能未启用，跳过")
            return []
        
        logger.info("步骤3: 串行生成帖子")
        
        # 确保日期目录存在
        date_dir = self._ensure_date_directory(trade_date)
        post_date_dir = self._ensure_post_date_directory(trade_date)
        
        # 过滤有效的分析结果
        valid_results = [r for r in analysis_results if r and 'analysis_report' in r]
        post_results = []
        
        # 使用进度条显示处理进度
        with tqdm(total=len(valid_results), desc="📝 生成帖子") as pbar:
            for result in valid_results:
                stock_name = result.get('stock_info', {}).get('name', 'Unknown')
                pbar.set_description(f"生成 {stock_name} 帖子")
                
                try:
                    post_result = self._generate_single_post_worker((result, trade_date, date_dir, post_date_dir, skip_existing))
                    if post_result:
                        post_results.append(post_result)
                        logger.info(f"完成{stock_name}帖子生成")
                    else:
                        logger.warning(f"生成{stock_name}帖子失败")
                
                except Exception as e:
                    logger.error(f"处理{stock_name}帖子时出错: {e}")
                
                pbar.update(1)
        
        return post_results
    
    def _generate_single_post_worker(self, args: Tuple[Dict[str, Any], str, str, str, bool]) -> Optional[Dict[str, Any]]:
        """
        单个帖子生成的工作函数（线程工作单元）
        
        Args:
            args: (analysis_result, trade_date, date_dir, post_date_dir, skip_existing)
            
        Returns:
            帖子生成结果或None
        """
        analysis_result, trade_date, date_dir, post_date_dir, skip_existing = args
        
        stock_info = analysis_result.get('stock_info', {})
        stock_name = stock_info.get('name', 'Unknown')
        ts_code = stock_info.get('ts_code', 'Unknown')
        thread_id = threading.current_thread().ident
        
        try:
            # 检查是否已有帖子
            if skip_existing:
                # 检查是否存在类似名称的帖子文件
                if os.path.exists(post_date_dir):
                    existing_files = [f for f in os.listdir(post_date_dir) 
                                    if f.startswith(f"{trade_date}_{stock_name}_gushen_post")]
                    if existing_files:
                        logger.debug(f"[线程{thread_id}] 跳过已生成的帖子: {stock_name}")
                        return {
                            "stock_name": stock_name,
                            "ts_code": ts_code,
                            "post_file": os.path.join(post_date_dir, existing_files[0]),
                            "status": "skipped",
                            "generated_at": None
                        }
            
            # 保存临时分析结果文件（用于帖子生成）
            temp_analysis_file = os.path.join(date_dir, f"{stock_name}_{ts_code.replace('.', '_')}_analysis.json")
            
            if not os.path.exists(temp_analysis_file):
                logger.warning(f"[线程{thread_id}] 分析结果文件不存在: {temp_analysis_file}")
                return None
            
            # 轻微的API调用延迟（防止过度并发）
            if self.api_delay > 0:
                time.sleep(self.api_delay)
            
            # 创建线程专用的帖子生成器实例
            post_generator = PostGeneratorV2()
            
            # 生成帖子内容
            try:
                # 1. 加载数据
                analysis_data = post_generator.load_analysis_data(temp_analysis_file)
                
                # 2. 生成阶段一内容
                stage1_content, thinking1 = post_generator.generate_stage1_content(analysis_data)
                
                # 3. 生成阶段二内容
                stage2_content, thinking2 = post_generator.generate_stage2_content(analysis_data, stage1_content)
                
                # 4. 合并内容
                final_content = post_generator.combine_content(stage1_content, stage2_content)
                
                # 5. 保存完整帖子到指定的日期目录
                post_filepath = post_generator.save_post(
                    final_content, 
                    analysis_data,
                    stage1_thinking=thinking1,
                    stage2_json_data=thinking2,
                    output_dir=post_date_dir  # 使用日期目录
                )
                
                post_result = {
                    "success": True,
                    "post_filepath": post_filepath,
                    "final_content": final_content
                }
                
            except Exception as e:
                logger.error(f"[线程{thread_id}] 帖子生成过程失败: {e}")
                post_result = {
                    "success": False,
                    "error": str(e)
                }
            
            if post_result and post_result["success"]:
                result_info = {
                    "stock_name": stock_name,
                    "ts_code": ts_code,
                    "post_file": post_result["post_filepath"],
                    "status": "success",
                    "generated_at": datetime.now().isoformat()
                }
                logger.debug(f"[线程{thread_id}] 完成{stock_name}帖子生成")
                return result_info
            else:
                error_msg = post_result.get("error", "未知错误") if post_result else "帖子生成器返回None"
                logger.warning(f"[线程{thread_id}] 生成{stock_name}帖子失败: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"[线程{thread_id}] 处理{stock_name}帖子时出错: {e}")
            return None

    def _extract_single_stock(self, processed_data: Dict[str, Any], stock_data: Dict[str, Any], trade_date: str) -> Optional[str]:
        """
        提取单只股票的数据
        """
        try:
            # 创建临时的完整数据结构
            temp_data = {
                "meta": processed_data["meta"],
                "stocks": [stock_data]
            }
            
            # 保存临时文件
            temp_file = f"data/extracted/temp_{trade_date}_{stock_data['name']}_{stock_data['ts_code'].replace('.', '_')}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)
            
            return temp_file
            
        except Exception as e:
            logger.error(f"提取单股数据失败: {e}")
            return None
    
    def _analyze_single_stock(self, extracted_file: str, stock_name: str, ts_code: str) -> Optional[Dict[str, Any]]:
        """
        使用LLM分析单只股票（已弃用，保留兼容性）
        """
        try:
            # 创建分析器实例
            funding_analyzer = FundingBattleAnalyzer()
            
            # 执行资金博弈分析
            analysis_result = funding_analyzer.analyze_complete_report(
                data_file_path=extracted_file,
                output_path=None  # 不额外保存，由上层统一管理
            )
            
            # 清理临时文件
            if os.path.exists(extracted_file):
                os.remove(extracted_file)
            
            if analysis_result:
                # 添加处理时间戳
                analysis_result['processed_at'] = datetime.now().isoformat()
                return analysis_result
            
            return None
            
        except Exception as e:
            logger.error(f"LLM分析{stock_name}失败: {e}")
            return None
    
    def _step4_generate_summary(self, analysis_results: List[Dict[str, Any]], post_results: List[Dict[str, Any]], trade_date: str) -> Dict[str, Any]:
        """
        步骤4：生成汇总报告
        """
        logger.info("步骤4: 生成汇总报告")
        
        # 确保日期目录存在
        date_dir = self._ensure_date_directory(trade_date)
        
        # 统计信息
        total_stocks = len(analysis_results)
        successful_analysis = len([r for r in analysis_results if r and 'analysis_report' in r])
        
        # 帖子生成统计
        total_posts = len(post_results)
        successful_posts = len([r for r in post_results if r and r.get('status') == 'success'])
        skipped_posts = len([r for r in post_results if r and r.get('status') == 'skipped'])
        
        # 构建轻量级汇总结果（不包含完整的股票分析数据，只包含统计信息）
        summary = {
            "meta": {
                "trade_date": trade_date,
                "trade_date_display": self._format_date_display(trade_date),
                "total_stocks": total_stocks,
                "successful_analysis": successful_analysis,
                "analysis_success_rate": f"{(successful_analysis/total_stocks*100):.1f}%" if total_stocks > 0 else "0%",
                "post_generation_enabled": self.enable_post_generation,
                "total_posts": total_posts,
                "successful_posts": successful_posts,
                "skipped_posts": skipped_posts,
                "post_success_rate": f"{(successful_posts/total_posts*100):.1f}%" if total_posts > 0 else "0%",
                "generated_at": datetime.now().isoformat(),
                "processing_mode": "high_concurrency_parallel" if not hasattr(self, '_force_serial') or not self._force_serial else "serial",
                "max_workers": self.max_workers,
                "api_delay": self.api_delay
            },
            "stock_list": [
                {
                    "name": result.get('stock_info', {}).get('name', 'Unknown'),
                    "ts_code": result.get('stock_info', {}).get('ts_code', 'Unknown'),
                    "analysis_status": "success" if result and 'analysis_report' in result else "failed",
                    "post_status": self._get_post_status(result.get('stock_info', {}).get('name', 'Unknown'), post_results),
                    "post_file": self._get_post_file(result.get('stock_info', {}).get('name', 'Unknown'), post_results)
                }
                for result in analysis_results
            ],
            "summary_stats": self._calculate_summary_stats(analysis_results)
        }
        
        # 保存汇总报告到日期目录下
        summary_file = os.path.join(date_dir, "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"汇总报告已保存: {summary_file}")
        logger.info(f"成功分析 {successful_analysis}/{total_stocks} 只股票")
        if self.enable_post_generation:
            logger.info(f"成功生成 {successful_posts}/{total_posts} 篇帖子")
            if skipped_posts > 0:
                logger.info(f"跳过已存在 {skipped_posts} 篇帖子")
        logger.info(f"所有结果已保存到目录: {date_dir}")
        
        return summary
    
    def _get_post_status(self, stock_name: str, post_results: List[Dict[str, Any]]) -> str:
        """获取指定股票的帖子状态"""
        if not self.enable_post_generation:
            return "disabled"
        
        for post_result in post_results:
            if post_result.get('stock_name') == stock_name:
                return post_result.get('status', 'unknown')
        
        return "not_generated"
    
    def _get_post_file(self, stock_name: str, post_results: List[Dict[str, Any]]) -> Optional[str]:
        """获取指定股票的帖子文件路径"""
        if not self.enable_post_generation:
            return None
        
        for post_result in post_results:
            if post_result.get('stock_name') == stock_name:
                return post_result.get('post_file')
        
        return None
    
    def _format_date_display(self, date_str: str) -> str:
        """格式化日期显示"""
        try:
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return date_str
        except:
            return date_str
    
    def _calculate_summary_stats(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算汇总统计信息"""
        if not analysis_results:
            return {}
        
        try:
            # 提取有效的分析结果
            valid_results = [r for r in analysis_results if r and 'analysis_report' in r]
            
            if not valid_results:
                return {"note": "没有有效的分析结果"}
            
            # 统计战局总览信息
            verdicts = []
            confidence_scores = []
            
            for result in valid_results:
                overall_assessment = result.get('analysis_report', {}).get('overall_assessment', {})
                if 'verdict' in overall_assessment:
                    verdicts.append(overall_assessment['verdict'])
                if 'confidence_score' in overall_assessment:
                    try:
                        confidence_scores.append(float(overall_assessment['confidence_score']))
                    except (ValueError, TypeError):
                        pass
            
            stats = {
                "verdict_distribution": self._count_items(verdicts),
                "average_confidence": round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"计算汇总统计失败: {e}")
            return {"error": "统计计算失败"}
    
    def _count_items(self, items: List[str]) -> Dict[str, int]:
        """统计项目出现次数"""
        count_dict = {}
        for item in items:
            count_dict[item] = count_dict.get(item, 0) + 1
        return count_dict
    
    def batch_process_dates(self, date_list: List[str], skip_existing: bool = True) -> Dict[str, Any]:
        """
        批量处理多个日期
        
        Args:
            date_list: 日期列表
            skip_existing: 是否跳过已存在的结果
            
        Returns:
            批量处理结果汇总
        """
        logger.info(f"开始批量处理{len(date_list)}个日期")
        
        batch_results = {}
        
        for trade_date in date_list:
            logger.info(f"处理日期: {trade_date}")
            try:
                result = self.process_date(trade_date, skip_existing)
                batch_results[trade_date] = result
            except Exception as e:
                logger.error(f"处理日期{trade_date}失败: {e}")
                batch_results[trade_date] = {"error": str(e)}
        
        # 保存批量结果
        batch_summary_file = f"data/analyzed/batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_summary_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"批量处理完成，结果已保存: {batch_summary_file}")
        return batch_results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='龙虎榜数据处理完整流水线（高并发版本）')
    parser.add_argument('trade_date', help='交易日期 (YYYYMMDD格式)')
    parser.add_argument('--token', help='Tushare API token (可选)')
    parser.add_argument('--skip-existing', action='store_true', default=True, 
                       help='跳过已存在的分析结果 (默认: True)')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--batch', help='批量处理，传入包含日期列表的文件路径')
    parser.add_argument('--workers', type=int, default=16, help='最大并行线程数 (默认: 16，适合DeepSeek无限制)')
    parser.add_argument('--delay', type=float, default=0.1, help='API调用间隔秒数 (默认: 0.1，可以很小)')
    parser.add_argument('--serial', action='store_true', help='使用串行模式（调试用）')
    parser.add_argument('--enable-posts', action='store_true', help='启用帖子生成功能')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 初始化流水线
    pipeline = DragonTigerPipeline(
        tushare_token=args.token,
        max_workers=args.workers,
        api_delay=args.delay,
        enable_post_generation=args.enable_posts
    )
    
    # 设置串行模式（如果指定）
    if args.serial:
        pipeline._force_serial = True
        logger.info("强制使用串行模式")
    
    try:
        if args.batch:
            # 批量处理模式
            with open(args.batch, 'r', encoding='utf-8') as f:
                date_list = [line.strip() for line in f if line.strip()]
            
            result = pipeline.batch_process_dates(date_list, args.skip_existing)
            print("批量处理完成")
        else:
            # 单日处理模式
            result = pipeline.process_date(args.trade_date, args.skip_existing)
            
            if 'error' in result:
                print(f"处理失败: {result['error']}")
            else:
                print("="*60)
                print(f"🚀 龙虎榜数据处理完成 - {args.trade_date}")
                print("="*60)
                print(f"📊 总股票数: {result['meta']['total_stocks']}")
                print(f"✅ 成功分析: {result['meta']['successful_analysis']}")
                print(f"📈 分析成功率: {result['meta']['analysis_success_rate']}")
                
                # 帖子生成统计
                if result['meta']['post_generation_enabled']:
                    print(f"📝 帖子生成: 启用")
                    print(f"📄 成功生成: {result['meta']['successful_posts']}")
                    print(f"⏭️  跳过已存在: {result['meta']['skipped_posts']}")
                    print(f"📊 帖子成功率: {result['meta']['post_success_rate']}")
                else:
                    print(f"📝 帖子生成: 未启用")
                
                print(f"⚡ 处理模式: {result['meta']['processing_mode']}")
                print(f"🔥 并行线程: {result['meta']['max_workers']}")
                print(f"⏱️  API延迟: {result['meta']['api_delay']}秒")
                print(f"📁 结果目录: data/analyzed/{args.trade_date}/")
                
                print("📂 文件结构:")
                print(f"  ├── summary.json  (汇总统计)")
                print(f"  ├── 股票名称1_代码_analysis.json")
                print(f"  ├── 股票名称2_代码_analysis.json")
                print(f"  └── ...")
                
                if result['meta']['post_generation_enabled']:
                    print(f"📄 帖子文件: data/output/posts/{args.trade_date}/")
                    print(f"  ├── {args.trade_date}_股票名称1_gushen_post_v2.1_HHMMSS.md")
                    print(f"  ├── {args.trade_date}_股票名称2_gushen_post_v2.1_HHMMSS.md")
                    print(f"  └── ...")
                
                print(f"\n🎯 使用高并发处理，大幅提升效率！")
                if result['meta']['post_generation_enabled']:
                    print(f"💡 现在支持一键生成投资帖子！")
    
    except KeyboardInterrupt:
        logger.info("用户中断处理")
        print("\n处理已中断")
    except Exception as e:
        logger.error(f"处理过程中出现错误: {e}")
        print(f"错误: {e}")


if __name__ == "__main__":
    main() 