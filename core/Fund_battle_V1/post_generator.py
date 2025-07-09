"""
龙虎榜资金博弈分析 - 第三阶段：叙事生成模块 (叙事层)
将FundingBattleSummary数据生成图文并茂的用户可读分析报告
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 智能导入处理
try:
    from core.deepseek_interface import DeepSeekInterface
except ImportError:
    from deepseek_interface import DeepSeekInterface

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('post_generator')

class PostGenerator:
    """
    龙虎榜分析报告生成器 - 叙事层处理
    负责将高密度的FundingBattleSummary转换为用户友好的分析报告
    """
    
    def __init__(self, deepseek_interface: Optional[DeepSeekInterface] = None):
        """
        初始化报告生成器
        
        参数:
            deepseek_interface: DeepSeek接口实例，如果不提供则自动创建
        """
        logger.info("初始化龙虎榜分析报告生成器")
        self.llm = deepseek_interface or DeepSeekInterface()
    
    def create_post_prompt(self, funding_battle_summary: Dict[str, Any]) -> str:
        """
        创建报告生成提示词
        
        参数:
            funding_battle_summary(Dict): FundingBattleSummary数据
            
        返回:
            str: 报告生成提示词
        """
        prompt = f"""# 龙虎榜资金博弈分析报告生成任务

你是一位资深的A股分析师和内容创作专家。现在需要基于高质量的"资金博弈概要(FundingBattleSummary)"，创作一篇专业且易读的龙虎榜分析报告。

## 资金博弈概要 (FundingBattleSummary)
```json
{json.dumps(funding_battle_summary, ensure_ascii=False, indent=2)}
```

## 报告创作要求

请创作一篇结构完整、信息丰富的龙虎榜分析报告，具体要求：

### 1. 报告结构
- **标题**: 吸引人的标题，体现股票名称和核心看点
- **核心摘要**: 3-4句话概括战局本质和关键结论
- **多方阵营分析**: 详细分析买方力量构成和战术特点
- **空方阵营分析**: 详细分析卖方力量构成和战术特点  
- **战局评估**: 综合评估资金博弈结果和市场影响
- **操作启示**: 给投资者的实用建议和风险提示

### 2. 内容要求
- **数据准确**: 所有数据必须与FundingBattleSummary完全一致
- **逻辑清晰**: 从数据到分析到结论，逻辑链条完整
- **专业深度**: 体现专业的游资分析和市场洞察
- **通俗易懂**: 复杂概念用通俗语言解释，便于散户理解
- **实用性强**: 提供具体可操作的投资建议

### 3. 写作风格
- **客观理性**: 基于数据分析，避免主观臆测
- **生动形象**: 用生动的比喻和描述增强可读性
- **重点突出**: 用**加粗**、`代码块`等格式突出关键信息
- **结构清晰**: 使用标题、列表、分段等增强阅读体验

### 4. 特别要求
- **游资画像**: 如果涉及知名游资，要深入分析其操作特点和意图
- **风险提示**: 必须包含风险提示，提醒投资者理性决策
- **后市展望**: 基于当前战局给出合理的后市展望
- **不得编造**: 严格基于提供的数据，不得编造任何信息

请生成一篇完整的Markdown格式分析报告。"""

        return prompt
    
    def generate_post(self, funding_battle_summary: Dict[str, Any]) -> Optional[str]:
        """
        生成分析报告
        
        参数:
            funding_battle_summary(Dict): FundingBattleSummary数据
            
        返回:
            Optional[str]: 生成的报告内容，失败时返回None
        """
        stock_name = funding_battle_summary.get('name', '未知股票')
        ts_code = funding_battle_summary.get('ts_code', '')
        
        logger.info(f"开始生成分析报告: {stock_name} ({ts_code})")
        
        # 创建报告生成提示词
        prompt = self.create_post_prompt(funding_battle_summary)
        
        # 调用LLM生成报告
        report_content, thinking_process = self.llm.generate_text_with_thinking(
            prompt=prompt,
            max_tokens=16384,
            temperature=0.8,
            timeout=120
        )
        
        if report_content.startswith("生成失败"):
            logger.error(f"报告生成失败: {report_content}")
            return None
            
        logger.info("分析报告生成完成")
        return report_content
    
    def add_metadata_header(self, content: str, funding_battle_summary: Dict[str, Any]) -> str:
        """
        为报告添加元数据头部
        
        参数:
            content(str): 报告内容
            funding_battle_summary(Dict): FundingBattleSummary数据
            
        返回:
            str: 添加元数据后的报告
        """
        basic_info = funding_battle_summary.get('basic_info', {})
        battle_assessment = funding_battle_summary.get('battle_assessment', {})
        
        metadata = f"""---
stock_code: {funding_battle_summary.get('ts_code', '')}
stock_name: {funding_battle_summary.get('name', '')}
close_price: {basic_info.get('close', 0)}
pct_change: {basic_info.get('pct_change', '0%')}
turnover_rate: {basic_info.get('turnover_rate', '0%')}
net_amount: {basic_info.get('net_amount', '0元')}
winner: {battle_assessment.get('winner', '未知')}
battle_tags: {', '.join(battle_assessment.get('battle_tags', []))}
generation_time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

"""
        return metadata + content
    
    def save_post(self, content: str, output_path: str) -> bool:
        """
        保存分析报告到文件
        
        参数:
            content(str): 报告内容
            output_path(str): 输出文件路径
            
        返回:
            bool: 是否保存成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"分析报告已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存分析报告失败: {e}")
            return False
    
    def load_funding_battle_summary(self, input_path: str) -> Optional[Dict[str, Any]]:
        """
        加载FundingBattleSummary数据
        
        参数:
            input_path(str): 输入文件路径
            
        返回:
            Optional[Dict]: FundingBattleSummary数据，失败时返回None
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
            
            logger.info(f"成功加载FundingBattleSummary: {input_path}")
            return summary
            
        except Exception as e:
            logger.error(f"加载FundingBattleSummary失败: {e}")
            return None
    
    def process_file(self, input_path: str, output_path: str) -> bool:
        """
        处理单个文件：从FundingBattleSummary到分析报告
        
        参数:
            input_path(str): 输入文件路径（FundingBattleSummary）
            output_path(str): 输出文件路径（Markdown报告）
            
        返回:
            bool: 是否处理成功
        """
        logger.info(f"开始生成分析报告: {input_path} -> {output_path}")
        
        # 加载FundingBattleSummary数据
        summary = self.load_funding_battle_summary(input_path)
        if summary is None:
            return False
        
        # 生成报告内容
        content = self.generate_post(summary)
        if content is None:
            return False
        
        # 添加元数据头部
        final_content = self.add_metadata_header(content, summary)
        
        # 保存报告
        return self.save_post(final_content, output_path)


# ====== 测试代码 ======
if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # 智能路径解析：找到项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent if current_dir.name == 'core' else current_dir
    
    # 测试PostGenerator
    generator = PostGenerator()
    
    # 测试文件路径（相对于项目根目录）
    input_file = project_root / "data/processed/test_funding_battle_summary.json"
    output_file = project_root / "data/output/posts/test_analysis_report.md"
    
    # 处理文件
    success = generator.process_file(input_file, output_file)
    
    if success:
        print(f"✅ 分析报告生成成功！")
        print(f"📁 输入文件: {input_file}")
        print(f"📁 输出文件: {output_file}")
        
        # 显示报告预览
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📄 报告预览（前500字符）:")
            print("-" * 50)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ 读取报告文件失败: {e}")
    else:
        print(f"❌ 分析报告生成失败！") 