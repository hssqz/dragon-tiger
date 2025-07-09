"""
龙虎榜资金博弈分析 - 主流程控制器
整合三个阶段的处理流程：代码预处理 -> LLM增强 -> 叙事生成
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# 智能导入处理
try:
    from core.funding_battle_builder import FundingBattleBuilder
    from core.funding_battle_enricher import FundingBattleEnricher
    from core.Fund_build_V1.post_generator import PostGenerator
    from core.deepseek_interface import DeepSeekInterface
except ImportError:
    from funding_battle_builder import FundingBattleBuilder
    from funding_battle_enricher import FundingBattleEnricher
    from core.Fund_build_V1.post_generator import PostGenerator
    from deepseek_interface import DeepSeekInterface

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('funding_battle_pipeline')

class FundingBattlePipeline:
    """
    龙虎榜资金博弈分析流水线
    整合三个阶段：事实层 -> 洞察层 -> 叙事层
    """
    
    def __init__(self, deepseek_interface: Optional[DeepSeekInterface] = None):
        """
        初始化分析流水线
        
        参数:
            deepseek_interface: DeepSeek接口实例，如果不提供则自动创建
        """
        logger.info("初始化龙虎榜资金博弈分析流水线")
        
        # 初始化三个阶段的处理器
        self.builder = FundingBattleBuilder()
        self.enricher = FundingBattleEnricher(deepseek_interface)
        self.generator = PostGenerator(deepseek_interface)
        
        # 创建输出目录
        self.ensure_output_directories()
    
    def ensure_output_directories(self):
        """确保输出目录存在"""
        directories = [
            "data/processed",
            "data/output/posts",
            "data/output/summaries"
        ]
        
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"确保目录存在: {dir_path}")
    
    def generate_file_names(self, stock_name: str, ts_code: str) -> Dict[str, str]:
        """
        生成各阶段输出文件名
        
        参数:
            stock_name(str): 股票名称
            ts_code(str): 股票代码
            
        返回:
            Dict[str, str]: 各阶段文件路径
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 清理股票名称，移除特殊字符
        clean_name = "".join(c for c in stock_name if c.isalnum() or c in "._-")
        clean_code = ts_code.replace(".", "_")
        
        base_name = f"{timestamp}_{clean_name}_{clean_code}"
        
        return {
            "structured_facts": f"data/processed/{base_name}_structured_facts.json",
            "funding_summary": f"data/processed/{base_name}_funding_summary.json",
            "analysis_report": f"data/output/posts/{base_name}_analysis_report.md",
            "summary_copy": f"data/output/summaries/{base_name}_summary.json"
        }
    
    def run_stage1_facts_extraction(self, input_path: str, output_path: str) -> bool:
        """
        运行第一阶段：事实提取（代码预处理）
        
        参数:
            input_path(str): 原始数据路径
            output_path(str): 结构化事实输出路径
            
        返回:
            bool: 是否成功
        """
        logger.info("🔄 开始第一阶段：事实提取（代码预处理）")
        
        success = self.builder.process_file(input_path, output_path)
        
        if success:
            logger.info("✅ 第一阶段完成：结构化事实数据已生成")
        else:
            logger.error("❌ 第一阶段失败：事实提取失败")
        
        return success
    
    def run_stage2_llm_enhancement(self, input_path: str, output_path: str) -> bool:
        """
        运行第二阶段：LLM洞察增强
        
        参数:
            input_path(str): 结构化事实数据路径
            output_path(str): 增强摘要输出路径
            
        返回:
            bool: 是否成功
        """
        logger.info("🔄 开始第二阶段：LLM洞察增强")
        
        success = self.enricher.process_file(input_path, output_path)
        
        if success:
            logger.info("✅ 第二阶段完成：LLM增强分析已完成")
        else:
            logger.error("❌ 第二阶段失败：LLM增强失败")
        
        return success
    
    def run_stage3_narrative_generation(self, input_path: str, output_path: str) -> bool:
        """
        运行第三阶段：叙事生成
        
        参数:
            input_path(str): 增强摘要数据路径
            output_path(str): 分析报告输出路径
            
        返回:
            bool: 是否成功
        """
        logger.info("🔄 开始第三阶段：叙事生成")
        
        success = self.generator.process_file(input_path, output_path)
        
        if success:
            logger.info("✅ 第三阶段完成：分析报告已生成")
        else:
            logger.error("❌ 第三阶段失败：报告生成失败")
        
        return success
    
    def run_full_pipeline(self, input_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        运行完整的三阶段分析流水线
        
        参数:
            input_path(str): 原始龙虎榜数据路径
            output_dir(str): 输出目录，默认使用配置的目录
            
        返回:
            Dict[str, Any]: 运行结果和输出文件路径
        """
        logger.info("🚀 开始运行完整的龙虎榜资金博弈分析流水线")
        logger.info(f"📁 输入文件: {input_path}")
        
        result = {
            "success": False,
            "stages_completed": 0,
            "output_files": {},
            "error_message": "",
            "processing_time": 0
        }
        
        start_time = datetime.now()
        
        try:
            # 读取原始数据获取股票信息
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            stocks = raw_data.get("stocks", [])
            if not stocks:
                result["error_message"] = "原始数据中未找到股票信息"
                return result
            
            stock_data = stocks[0]
            stock_name = stock_data.get("name", "未知股票")
            ts_code = stock_data.get("ts_code", "UNKNOWN")
            
            logger.info(f"📊 分析目标: {stock_name} ({ts_code})")
            
            # 生成输出文件路径
            file_paths = self.generate_file_names(stock_name, ts_code)
            result["output_files"] = file_paths
            
            # 第一阶段：事实提取
            stage1_success = self.run_stage1_facts_extraction(
                input_path, 
                file_paths["structured_facts"]
            )
            
            if not stage1_success:
                result["error_message"] = "第一阶段事实提取失败"
                return result
            
            result["stages_completed"] = 1
            
            # 第二阶段：LLM增强
            stage2_success = self.run_stage2_llm_enhancement(
                file_paths["structured_facts"],
                file_paths["funding_summary"]
            )
            
            if not stage2_success:
                result["error_message"] = "第二阶段LLM增强失败"
                return result
            
            result["stages_completed"] = 2
            
            # 第三阶段：叙事生成
            stage3_success = self.run_stage3_narrative_generation(
                file_paths["funding_summary"],
                file_paths["analysis_report"]
            )
            
            if not stage3_success:
                result["error_message"] = "第三阶段叙事生成失败"
                return result
            
            result["stages_completed"] = 3
            
            # 复制摘要到输出目录
            self.copy_summary_to_output(
                file_paths["funding_summary"],
                file_paths["summary_copy"]
            )
            
            result["success"] = True
            
            end_time = datetime.now()
            result["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info("🎉 完整流水线运行成功！")
            logger.info(f"⏱️ 总耗时: {result['processing_time']:.1f}秒")
            
        except Exception as e:
            result["error_message"] = f"流水线运行异常: {str(e)}"
            logger.error(f"❌ 流水线运行异常: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def copy_summary_to_output(self, source_path: str, target_path: str):
        """
        复制摘要文件到输出目录
        
        参数:
            source_path(str): 源文件路径
            target_path(str): 目标文件路径
        """
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            logger.info(f"摘要文件已复制到输出目录: {target_path}")
            
        except Exception as e:
            logger.warning(f"复制摘要文件失败: {e}")
    
    def print_result_summary(self, result: Dict[str, Any]):
        """
        打印运行结果摘要
        
        参数:
            result(Dict): 运行结果
        """
        print("\n" + "="*60)
        print("🎯 龙虎榜资金博弈分析流水线 - 运行结果")
        print("="*60)
        
        if result["success"]:
            print("✅ 状态: 运行成功")
            print(f"⚡ 完成阶段: {result['stages_completed']}/3")
            print(f"⏱️ 总耗时: {result['processing_time']:.1f}秒")
            
            print("\n📁 输出文件:")
            for file_type, file_path in result["output_files"].items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"  ✓ {file_type}: {file_path} ({file_size} bytes)")
                else:
                    print(f"  ✗ {file_type}: {file_path} (文件不存在)")
            
        else:
            print("❌ 状态: 运行失败")
            print(f"⚡ 完成阶段: {result['stages_completed']}/3")
            print(f"💥 错误信息: {result['error_message']}")
        
        print("="*60 + "\n")


# ====== 主程序入口 ======
def main():
    """主程序入口"""
    # 创建流水线
    pipeline = FundingBattlePipeline()
    
    # 默认输入文件
    default_input = "core/test-seat.json"
    
    print("🚀 龙虎榜资金博弈分析流水线")
    print(f"📁 使用默认输入文件: {default_input}")
    
    # 检查输入文件是否存在
    if not os.path.exists(default_input):
        print(f"❌ 输入文件不存在: {default_input}")
        return
    
    # 运行完整流水线
    result = pipeline.run_full_pipeline(default_input)
    
    # 打印结果摘要
    pipeline.print_result_summary(result)
    
    # 如果成功，尝试显示报告预览
    if result["success"] and "analysis_report" in result["output_files"]:
        report_path = result["output_files"]["analysis_report"]
        if os.path.exists(report_path):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print("📄 分析报告预览（前800字符）:")
                print("-" * 60)
                print(content[:800] + "..." if len(content) > 800 else content)
                print("-" * 60)
                
            except Exception as e:
                print(f"❌ 读取报告预览失败: {e}")


if __name__ == "__main__":
    main() 