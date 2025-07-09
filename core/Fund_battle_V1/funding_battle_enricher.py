"""
龙虎榜资金博弈分析 - 第二阶段：LLM洞察生成模块 (V4)
将StructuredFacts数据通过LLM分析生成FundingBattleInsights（纯洞察）
"""

import json
import logging
from typing import Dict, List, Any, Optional

# 智能导入处理
try:
    from core.deepseek_interface import DeepSeekInterface
except ImportError:
    from deepseek_interface import DeepSeekInterface

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('funding_battle_enricher')

class FundingBattleEnricher:
    """
    龙虎榜资金博弈增强器 - V4洞察生成版
    负责调用LLM生成FundingBattleInsights（纯洞察），不包含数据拼接
    """
    
    def __init__(self, deepseek_interface: Optional[DeepSeekInterface] = None):
        """
        初始化增强器
        
        参数:
            deepseek_interface: DeepSeek接口实例，如果不提供则自动创建
        """
        logger.info("初始化龙虎榜资金博弈增强器 (V4 - 洞察生成)")
        self.llm = deepseek_interface or DeepSeekInterface()
    
    def create_insights_prompt(self, structured_facts: Dict[str, Any]) -> str:
        """
        创建LLM洞察分析提示词 (V4.1 - 游资聚焦版)
        
        参数:
            structured_facts(Dict): 结构化事实数据
            
        返回:
            str: 洞察分析提示词
        """
        prompt = f"""# 游资博弈专项解读与战局评估任务 (V4.1)

你是一位顶级的A股龙虎榜分析师，擅长通过席位操作行为"辨意图"。现有经代码预处理的`StructuredFacts`，请你基于此进行深度分析，**只输出纯粹的洞察部分**，格式为`FundingBattleInsights`。

**核心使命：穿透数据迷雾，精准锁定并深度解读"知名游资"的核心战术，并对整场战局的性质、走向和关键博弈点做出专业评估。**

**重要原则：游资是主角，普通席位是背景。**

## 战报事实 (StructuredFacts)
```json
{json.dumps(structured_facts, ensure_ascii=False, indent=2)}
```

## 分析框架与输出要求

请严格按照`FundingBattleInsights`的JSON格式，但将你的分析焦点进行如下调整：

1.  **不要复述或格式化任何输入数据**：例如，不要在你的输出中包含`total_amount_wan`或`concentration_metrics`等字段。你的任务是创造新信息（洞察），而不是转述旧信息。

2.  **阵营洞察 (`long_side_insights` / `short_side_insights`)**:
    *   在`long_side_facts.players`中，挑选出最重要的1-2名核心主力，填充到`core_players`。
    *   为核心主力打上`role_tags`（如："主攻手"、"锁仓主力"、"砸盘元凶"）和`reasons`。
    *   **核心玩家意图分析 (`analysis`)**: 这是关键。
        *   `actions`: 阐述其操作行为。
        *   `intention_tags`: 从总结出你认为的1-3个标签：
        *   `intention`: 用一段话总结其战术意图。**你的推断必须结合其在`StructuredFacts`中的"行为"、"净额"和"风格"进行解释**。

3.  **核心玩家意图分析逻辑（重点）**
    *   **看净额**：大幅净买入 -> `坚决做多`；大幅净卖出 -> `坚决做空`；买卖均衡 -> `做T套利`。
    *   **看风格** (结合`long_side_facts.players[...].description` 和 `style`):
        *   "打板"风格 + 大额净买入 -> `尝试拉升`。
        *   "砸盘"风格 + 大额净卖出 -> `派发砸盘`。
        *   "锁仓"风格 + 大额净买入 -> `锁仓看好`。
    *   **综合判断**: 将净额和风格结合，形成最终结论。

4.  **阵营总结 (`summary`)**:
    *   `style_tags`: 从所有玩家风格中提炼出该阵营的整体风格。
    *   `conclusion`: 用一句话总结该阵营的战术意图和构成。

5.  **战局评估 (`battle_assessment`)**:
    *   `long_strength_score` / `short_strength_score`: 结合资金量、玩家质量、资金集中度，给出一个0-100的实力评分。
    *   `battle_tags`: 结合`battle_facts`中的指标，生成最能体现战局本质的标签（例如："游资闪电战", "机构与游资的对决"）。
    *   `key_takeaway`: 一段话，给出整场战局最核心的结论。

**重要约束：**
*   你的所有分析都必须严格基于以上提供的`StructuredFacts`数据。
*   禁止猜测任何`StructuredFacts`中未给出的信息（如历史K线、技术指标等）。
*   **你的输出必须是严格的、不含任何额外注释的`FundingBattleInsights` JSON对象。**

**请严格按照指定的JSON Schema输出最终结果。**"""

        return prompt
    
    def create_insights_schema_example(self) -> str:
        """
        创建FundingBattleInsights JSON输出格式示例
        
        返回:
            str: JSON格式示例
        """
        return """{
  "long_side_insights": {
    "core_players": [
      {
        "seat_name": "中信证券股份有限公司浙江分公司",
        "player_type": "普通席位",
        "role_tags": ["主导多头", "锁仓主力"],
        "reasons": ["净买入金额最大"],
        "analysis": {
          "actions": "净买入0.61亿元，是多方绝对主力。",
          "intention_tags": ["坚决做多", "锁仓看好"],
          "intention": "基于其巨大的净买入额，并无卖出行为，判断其意图为利用资金优势强力拉升并锁仓。"
        }
      },
      {
        "seat_name": "国泰君安证券股份有限公司成都北一环路证券营业部",
        "player_name": "成都系",
        "style_tags": ["短线", "打板"],
        "reasons": ["知名游资参与"],
        "analysis": {
          "actions": "净买入0.41亿元，是多方核心力量之一。",
          "intention_tags": ["打板突击", "寻求次日溢价"],
          "intention": "基于其'打板'风格和坚决的净买入行为，推断其核心意图是制造涨停，引导市场情绪，并博取次日的高开溢价。"
        }
      }
    ],
    "summary": {
      "style_tags": ["打板", "短线突击"],
      "conclusion": "由普通席位主导，知名游资'成都系'积极参与，形成合力猛攻。"
    }
  },
  "short_side_insights": {
    "core_players": [
      {
        "seat_name": "国元证券股份有限公司宁波分公司",
        "player_type": "普通席位",
        "role_tags": ["主力砸盘"],
        "reasons": ["卖出金额最大"],
        "analysis": {
          "actions": "净卖出0.35亿元，是空方主力。",
          "intention_tags": ["坚决做空"],
          "intention": "基于其大额净卖出行为，判断其意图为获利了结或看空后市。"
        }
      }
    ],
    "summary": {
      "style_tags": ["短线交易", "获利了结"],
      "conclusion": "多名席位分散抛售，缺乏统一战术。"
    }
  },
  "battle_assessment": {
    "long_strength_score": 85,
    "short_strength_score": 52,
    "battle_tags": ["游资主导局", "多头强攻", "高位换手"],
    "key_takeaway": "多方凭借核心力量的压倒性优势，牢牢控制战局，空方抵抗分散且力度不足。"
  }
}"""
    
    def generate_insights(self, structured_facts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        调用LLM生成FundingBattleInsights（纯洞察）
        
        参数:
            structured_facts(Dict): 结构化事实数据
            
        返回:
            Optional[Dict]: FundingBattleInsights，失败时返回None
        """
        logger.info(f"开始LLM洞察生成: {structured_facts.get('name')} ({structured_facts.get('ts_code')})")
        
        # 创建洞察分析提示词
        prompt = self.create_insights_prompt(structured_facts)
        
        # 创建JSON格式示例
        json_schema = self.create_insights_schema_example()
        
        # 调用LLM进行JSON格式分析
        insights = self.llm.generate_json_output_with_validation(
            prompt=prompt,
            json_schema_example=json_schema,
            required_fields=["long_side_insights", "short_side_insights", "battle_assessment"],
            max_tokens=65536,
            temperature=1.0,
            timeout=120
        )
        
        if insights is None:
            logger.error("LLM洞察生成失败")
            return None
            
        logger.info("LLM洞察生成完成")
        return insights
    
    def save_insights(self, insights: Dict[str, Any], output_path: str) -> bool:
        """
        保存FundingBattleInsights到文件
        
        参数:
            insights(Dict): FundingBattleInsights数据
            output_path(str): 输出文件路径
            
        返回:
            bool: 是否保存成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(insights, f, ensure_ascii=False, indent=2)
            
            logger.info(f"FundingBattleInsights已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存FundingBattleInsights失败: {e}")
            return False
    
    def load_structured_facts(self, input_path: str) -> Optional[Dict[str, Any]]:
        """
        加载结构化事实数据
        
        参数:
            input_path(str): 输入文件路径
            
        返回:
            Optional[Dict]: 结构化事实数据，失败时返回None
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                structured_facts = json.load(f)
            
            logger.info(f"成功加载结构化事实数据: {input_path}")
            return structured_facts
            
        except Exception as e:
            logger.error(f"加载结构化事实数据失败: {e}")
            return None
    
    def process_file(self, input_path: str, output_path: str) -> bool:
        """
        处理单个文件：从StructuredFacts到FundingBattleInsights
        
        参数:
            input_path(str): 输入文件路径（StructuredFacts）
            output_path(str): 输出文件路径（FundingBattleInsights）
            
        返回:
            bool: 是否处理成功
        """
        logger.info(f"开始洞察生成处理: {input_path} -> {output_path}")
        
        # 加载结构化事实数据
        structured_facts = self.load_structured_facts(input_path)
        if structured_facts is None:
            return False
        
        # 生成洞察
        insights = self.generate_insights(structured_facts)
        if insights is None:
            return False
        
        # 保存洞察结果
        return self.save_insights(insights, output_path)


# ====== 测试代码 ======
if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # 智能路径解析：找到项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent if current_dir.name == 'core' else current_dir
    
    # 测试FundingBattleEnricher (V4洞察生成版)
    enricher = FundingBattleEnricher()
    
    # 测试文件路径（相对于项目根目录）
    input_file = project_root / "data/processed/test_structured_facts.json"
    output_file = project_root / "data/processed/test_funding_battle_insights.json"
    
    # 处理文件
    success = enricher.process_file(input_file, output_file)
    
    if success:
        print(f"✅ 洞察生成处理成功！")
        print(f"📁 输入文件: {input_file}")
        print(f"📁 输出文件: {output_file}")
        
        # 显示处理结果摘要
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            print(f"\n📊 洞察生成结果摘要:")
            print(f"多方实力评分: {result['battle_assessment']['long_strength_score']}")
            print(f"空方实力评分: {result['battle_assessment']['short_strength_score']}")
            print(f"战局标签: {', '.join(result['battle_assessment']['battle_tags'])}")
            print(f"核心结论: {result['battle_assessment']['key_takeaway']}")
            
        except Exception as e:
            print(f"❌ 读取结果文件失败: {e}")
    else:
        print(f"❌ 洞察生成处理失败！") 