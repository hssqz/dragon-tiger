#!/usr/bin/env python3
"""
龙虎榜资金博弈分析系统 - 火山引擎版本
基于PRD Gemini方案实现的模块化LLM分析流水线
使用火山引擎DeepSeek接口
"""

import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入火山引擎DeepSeek接口
try:
    from core.huoshan_deepseek_interface import HuoshanDeepSeekInterface
except ImportError:
    try:
        from huoshan_deepseek_interface import HuoshanDeepSeekInterface
    except ImportError:
        # 尝试导入文件名带括号的版本
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "huoshan_deepseek_interface", 
            os.path.join(os.path.dirname(__file__), "deepseek_interface(huoshan).py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        HuoshanDeepSeekInterface = module.HuoshanDeepSeekInterface

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('funding_battle_analyzer_huoshan')


class FundingBattleAnalyzerHuoshan:
    """
    龙虎榜资金博弈分析器 - 火山引擎版本
    实现优化的5模块分析流水线（合并模块一+二，模块四+五）
    """
    
    def __init__(self):
        """初始化分析器"""
        self.deepseek = HuoshanDeepSeekInterface()
        logger.info("龙虎榜资金博弈分析器（火山引擎版本）初始化完成")
    
    def load_seat_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        加载龙虎榜数据
        
        参数:
            file_path: 数据文件路径
            
        返回:
            解析后的JSON数据，失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # 如果数据包含stocks数组，提取第一个股票数据
            if 'stocks' in raw_data and len(raw_data['stocks']) > 0:
                data = raw_data['stocks'][0]
            else:
                data = raw_data
                
            logger.info(f"成功加载龙虎榜数据: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载数据文件失败: {e}")
            return None
    
    def module_1_2_combined(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        合并模块一和二：上榜原因解读 + 战局总览
        通过一次API调用完成两个模块的分析，节约token和调用次数
        """
        try:
            # 提取上榜原因数据
            reasons = data.get('basic_info', {}).get('reasons', [])
            reasons_text = ", ".join(reasons) if reasons else "无"
            
            # 提取基本信息数据
            basic_info = data.get('basic_info', {})
            basic_info_json = json.dumps(basic_info, ensure_ascii=False, indent=2)
            
            prompt = f"""你是一位A股龙虎榜分析专家。请同时完成两个分析任务：

**任务一：上榜原因解读**
上榜原因列表: {reasons_text}

请分析：
1. 这些原因说明了什么？
2. 它们反映了当前市场对这只股票怎样的情绪和博弈状态？（例如：是强烈的多头共识，还是剧烈的多空分歧？）

**任务二：战局总览**
基于以下JSON格式的龙虎榜核心摘要数据，进行三维度综合评估：

1. **战局定性**: 给出多空胜负的最终判断
2. **市场情绪评估**: 基于`pct_change`和`turnover_rate`，评估市场的真实情绪是亢奋、分歧还是恐慌
3. **资金对抗评估**: 基于所有资金相关数据（如`l_buy`, `l_sell`, `net_amount`等），评估主力资金的控盘力度和多空对抗的激烈程度
4. **核心结论**: 用一句话点出今天战局的核心看点

**重要提示**: 请确保你的分析是数据驱动的。例如，同样的净买入额，对于小盘股（`float_values`低）的影响力远大于大盘股。

**核心摘要数据 (JSON):**
{basic_info_json}

请按照以下JSON格式输出分析结果："""

            json_schema = """{
  "listing_reason_analysis": {
    "reasons": ["string"],
    "interpretation": "string"
  },
  "overall_assessment": {
    "verdict": "string",
    "confidence_score": "float",
    "market_sentiment": {
      "level": "string, must be one of ['亢奋', '乐观', '分歧', '博弈', '观望', '悲观', '恐慌', '退潮']",
      "interpretation": "string"
    },
    "capital_confrontation": {
      "level": "string, must be one of ['亢奋', '乐观', '分歧', '博弈', '观望', '悲观', '恐慌', '退潮']",
      "interpretation": "string"
    },
    "key_takeaway": "string"
  }
}"""
            
            result = self.deepseek.generate_json_output(prompt, json_schema)
            logger.info("合并模块一+二：上榜原因解读 + 战局总览 - 完成")
            return result
            
        except Exception as e:
            logger.error(f"合并模块一+二分析失败: {e}")
            return None
    
    def module_3_key_forces_analysis(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        模块三：核心力量分析
        """
        try:
            seat_data = data.get('seat_data', {})
            buy_seats = seat_data.get('buy_seats', [])
            sell_seats = seat_data.get('sell_seats', [])
            
            buy_seats_json = json.dumps(buy_seats, ensure_ascii=False, indent=2)
            sell_seats_json = json.dumps(sell_seats, ensure_ascii=False, indent=2)
            
            prompt = f"""你是一位精通识别游资和机构手法的专家。请基于以下龙虎榜席位数据，识别出买卖双方阵营中的核心力量（优先选择知名游资、机构等）。

对于每个核心力量，请进行深入的风格画像分析：
1.  **行为解读**: 他们今天具体做了什么？（例如：主封、接力、做T、出货）
2.  **风格画像 (Style Profile)**: 输出一个结构化的风格评估：
    *   如果 `player_info.style` 信息不全，请深入分析 `player_info.description` (长段文字描述) 来推断
    *   **核心概述**: 结合其风格和今日行为，一针见血地阐述他们的意图和后市可能的剧本。
    *   如果没有深入分析，不需要硬要分析，空着即可

如果一个席位没有特殊的`player_info`，则可以不进行风格分析。

买方席位: {buy_seats_json}
卖方席位: {sell_seats_json}"""

            json_schema = """{
  "key_forces": {
    "buying_force": [
      {
        "seat_name": "string",
        "player_type": "string",
        "player_name": "string",
        "buy_amount": "string",
        "sell_amount": "string",
        "net_amount": "string",
        "buy_rate": "string",
        "sell_rate": "string",
        "action_interpretation": "string",
        "style_profile": {
          "summary": "string",
          "time_horizon": "string",
          "preferred_setup": "string",
          "typical_exit": "string"
        }
      }
    ],
    "selling_force": [
      {
        "seat_name": "string",
        "player_type": "string",
        "player_name": "string",
        "buy_amount": "string",
        "sell_amount": "string",
        "net_amount": "string",
        "buy_rate": "string",
        "sell_rate": "string",
        "action_interpretation": "string",
        "style_profile": {
          "summary": "string",
          "time_horizon": "string",
          "preferred_setup": "string",
          "typical_exit": "string"
        }
      }
    ]
  }
}"""
            
            result = self.deepseek.generate_json_output(prompt, json_schema)
            logger.info("模块三：核心力量分析 - 完成")
            return result
            
        except Exception as e:
            logger.error(f"模块三分析失败: {e}")
            return None
    
    def module_4_5_combined(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        合并模块四和五：买方结构与协同性 + 卖方压力与意图
        """
        try:
            seat_data = data.get('seat_data', {})
            buy_seats = seat_data.get('buy_seats', [])
            sell_seats = seat_data.get('sell_seats', [])
            
            buy_seats_json = json.dumps(buy_seats, ensure_ascii=False, indent=2)
            sell_seats_json = json.dumps(sell_seats, ensure_ascii=False, indent=2)
            
            prompt = f"""请基于以下龙虎榜席位数据，同时完成买方结构和卖方压力的双重分析：


请分析买方的集中度（是"高度集中"还是"相对分散"），并分析是否存在协同作战的迹象（比如多个知名游资同时上榜）。

请分析卖方席位数据，判断卖压的来源和性质，是来自特定主力的"集中出货"，还是普遍的"获利了结"？

**数据输入:**
买方席位: {buy_seats_json}

卖方席位: {sell_seats_json}

请按照以下JSON格式输出分析结果："""

            json_schema = """{
  "buyer_analysis": {
    "concentration_level": "string",
    "concentration_desc": "string",
    "synergy_analysis": "string"
  },
  "seller_analysis": {
    "pressure_level": "string", 
    "pressure_desc": "string"
  }
}"""
            
            result = self.deepseek.generate_json_output(prompt, json_schema)
            logger.info("合并模块四+五：买方结构 + 卖方压力分析 - 完成")
            return result
            
        except Exception as e:
            logger.error(f"合并模块四+五分析失败: {e}")
            return None
    
    def module_6_historical_context(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        模块六：历史趋势与行为定性
        """
        try:
            historical_data = data.get('historical_data', {})
            historical_json = json.dumps(historical_data, ensure_ascii=False, indent=2)
            
            prompt = f"""你是一位精通"量价时空"的K线分析专家。你的任务是基于该股近期的日K线数据，分析龙虎榜当天（即数据中的最后一天）的上榜行为。

**分析要求:**

1.  **行为定性 (behavior_type):** 对本次上榜行为给出一个清晰、简洁的定性判断。

2.  **趋势解读 (trend_interpretation):** 详细解读你的判断依据。  
    *   **要点:**
        *   **当前阶段:** 说明当前股价处于整个短期趋势的哪个阶段（例如：上涨初期、主升浪、上涨末期、下跌通道、筑底阶段等）。
        *   **量价关系:** 结合上榜日及前几日的成交量变化，分析量价配合情况（例如：放量上涨、缩量上涨、价涨量缩、放量下跌等）。
        *   **关键信号:** 指出是否存在关键的K线形态（如大阳线、长上影、十字星等）或技术信号（如突破关键均线、平台整理等）。

**数据输入:**

*   **龙虎榜日期:** K线数据的最后一天。
*   **近期K线数据:** 
{historical_json}

请严格按照下面的JSON格式输出你的分析结果。"""

            json_schema = """{
  "trend_analysis": {
    "behavior_type": "string",
    "trend_interpretation": "string"
  }
}"""
            
            result = self.deepseek.generate_json_output(prompt, json_schema)
            logger.info("模块六：历史趋势与行为定性 - 完成")
            return result
            
        except Exception as e:
            logger.error(f"模块六分析失败: {e}")
            return None
    
    def module_7_final_verdict(self, module_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        模块七：后市策略与风险展望
        """
        try:
            # 将前6个模块的结果转为JSON字符串
            modules_json = json.dumps(module_results, ensure_ascii=False, indent=2)
            
            prompt = f"""你是一位经验丰富的投资顾问，擅长为散户提供清晰的交易策略。请综合以下所有分析模块的结论，给出一个完整的后市展望、具体的操作策略建议和明确的风险提示。

分析模块结果: {modules_json}"""

            json_schema = """{
  "final_verdict": {
    "outlook": "string",
    "strategy": "string",
    "risk_warning": "string"
  }
}"""
            
            result = self.deepseek.generate_json_output(prompt, json_schema)
            logger.info("模块七：后市策略与风险展望 - 完成")
            return result
            
        except Exception as e:
            logger.error(f"模块七分析失败: {e}")
            return None
    
    def analyze_complete_report(self, data_file_path: str, output_path: str = None) -> Optional[Dict[str, Any]]:
        """
        执行完整的龙虎榜分析流水线（优化版：5次API调用）
        
        参数:
            data_file_path: 输入数据文件路径
            output_path: 输出文件路径，为None时不保存文件
            
        返回:
            完整的分析报告JSON
        """
        logger.info("开始执行龙虎榜资金博弈分析流水线（火山引擎优化合并模式）")
        
        # 加载数据
        data = self.load_seat_data(data_file_path)
        if not data:
            return None
        
        # 提取基本信息
        basic_info = data.get('basic_info', {})
        stock_code = data.get('ts_code', 'Unknown')
        stock_name = data.get('name', 'Unknown') 
        trade_date = data.get('trade_date', 'Unknown')
        
        # 执行各模块分析
        analysis_results = {}
        
        # 合并模块1+2：上榜原因解读 + 战局总览
        module_1_2_result = self.module_1_2_combined(data)
        if module_1_2_result:
            analysis_results.update(module_1_2_result)
        
        # 模块3：核心力量分析
        module_3_result = self.module_3_key_forces_analysis(data)
        if module_3_result:
            analysis_results.update(module_3_result)
        
        # 合并模块4+5：买方结构 + 卖方压力分析  
        module_4_5_result = self.module_4_5_combined(data)
        if module_4_5_result:
            analysis_results.update(module_4_5_result)
        
        # 模块6：历史趋势与行为定性
        module_6_result = self.module_6_historical_context(data)
        if module_6_result:
            analysis_results.update(module_6_result)
        
        # 模块7：后市策略与风险展望
        module_7_result = self.module_7_final_verdict(analysis_results)
        if module_7_result:
            analysis_results.update(module_7_result)
        
        # 构建最终报告
        final_report = {
            "stock_info": {
                "ts_code": stock_code,
                "name": stock_name,
                "trade_date": trade_date
            },
            "analysis_report": analysis_results,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_provider": "huoshan_deepseek"
        }
        
        # 保存结果
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(final_report, f, ensure_ascii=False, indent=2)
                logger.info(f"分析报告已保存至: {output_path}")
            except Exception as e:
                logger.error(f"保存报告失败: {e}")
        
        logger.info("龙虎榜资金博弈分析流水线（火山引擎版本）执行完成，共调用5次API")
        return final_report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='龙虎榜资金博弈分析系统（火山引擎优化版）')
    parser.add_argument('input_file', help='输入的龙虎榜数据文件路径')
    parser.add_argument('-o', '--output', help='输出分析报告文件路径', default=None)
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 初始化分析器
    analyzer = FundingBattleAnalyzerHuoshan()
    
    # 执行分析
    result = analyzer.analyze_complete_report(args.input_file, args.output)
    
    if result:
        print("="*60)
        print("龙虎榜资金博弈分析报告（火山引擎版本）")
        print("="*60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("分析失败，请检查日志信息")


if __name__ == "__main__":
    main()