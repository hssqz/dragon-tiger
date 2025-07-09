# -*- coding: utf-8 -*-
"""
FundingBattleLLMBuilder
使用LLM (DeepSeek) 生成资金博弈概要 (FundingBattleSummary)
与 funding_battle_builder.py 的代码版本进行效果对比

运行：
    python core/funding_battle_llm_builder.py      # 默认读取 core/test-seat.json 做示例
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from deepseek_interface import DeepSeekInterface

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FundingBattleLLMBuilder")


class FundingBattleLLMBuilder:
    def __init__(self):
        """初始化LLM构建器"""
        try:
            self.llm = DeepSeekInterface()
            logger.info("DeepSeek接口初始化成功")
        except Exception as e:
            logger.error(f"DeepSeek接口初始化失败: {e}")
            raise

    def build_summary(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM分析原始seat_data，生成FundingBattleSummary
        """
        # 构建提示词
        prompt = self._build_prompt(stock)
        
        # JSON输出格式示例
        json_schema = self._get_json_schema()
        
        # 调用LLM生成JSON
        logger.info(f"开始分析股票 {stock.get('name', '')}({stock.get('ts_code', '')})")
        
        result = self.llm.generate_json_output(
            prompt=prompt,
            json_schema_example=json_schema,
            max_tokens=16384,
            temperature=1.0, 
            timeout=120,
            max_retries=3
        )
        
        if result is None:
            logger.error("LLM生成失败，返回默认结构")
            return self._get_fallback_result(stock)
        
        logger.info("LLM分析完成")
        return result

    def _build_prompt(self, stock: Dict[str, Any]) -> str:
        """构建给LLM的分析提示词"""
        
        basic_info = stock.get("basic_info", {})
        seat_data = stock.get("seat_data", {})
        buy_seats = seat_data.get("buy_seats", [])
        sell_seats = seat_data.get("sell_seats", [])
        
        prompt = f"""
# 龙虎榜资金博弈分析任务

请基于以下原始龙虎榜数据，生成一份结构化的**资金博弈概要 (FundingBattleSummary)**。

## 股票基本信息
- 股票代码：{stock.get('ts_code', '')}
- 股票名称：{stock.get('name', '')}
- 交易日期：{basic_info.get('trade_date_display', '')}
- 收盘价：{basic_info.get('close', 0)}
- 涨跌幅：{basic_info.get('pct_change', '')}
- 换手率：{basic_info.get('turnover_rate', '')}
- 成交额：{basic_info.get('amount', '')}
- 龙虎榜买入总额：{basic_info.get('l_buy', '')}
- 龙虎榜卖出总额：{basic_info.get('l_sell', '')}
- 净买入额：{basic_info.get('net_amount', '')}

## 买方席位数据
"""
        
        # 添加买方席位详情
        for i, seat in enumerate(buy_seats, 1):
            player_info = seat.get('player_info', {})
            prompt += f"""
**买方席位{i}**：
- 席位名称：{seat.get('seat_name', '')}
- 买入金额：{seat.get('buy_amount', '')}
- 卖出金额：{seat.get('sell_amount', '')}
- 净额：{seat.get('net_amount', '')}
- 玩家类型：{player_info.get('type', '普通席位')}
- 玩家名称：{player_info.get('name', '普通席位')}
- 玩家描述：{player_info.get('description', '')}
- 操作风格：{', '.join(player_info.get('style', []))}
"""

        prompt += "\n## 卖方席位数据\n"
        
        # 添加卖方席位详情
        for i, seat in enumerate(sell_seats, 1):
            player_info = seat.get('player_info', {})
            prompt += f"""
**卖方席位{i}**：
- 席位名称：{seat.get('seat_name', '')}
- 买入金额：{seat.get('buy_amount', '')}
- 卖出金额：{seat.get('sell_amount', '')}
- 净额：{seat.get('net_amount', '')}
- 玩家类型：{player_info.get('type', '普通席位')}
- 玩家名称：{player_info.get('name', '普通席位')}
- 玩家描述：{player_info.get('description', '')}
- 操作风格：{', '.join(player_info.get('style', []))}
"""

        prompt += f"""

## 分析要求

请根据上述数据，按照以下要求进行深度分析：

### 1. 多方阵营分析 (long_side)
- 统计买方的总金额、席位数量、知名游资数量
- 识别核心主力（按净买入金额排序，取前2名）
- 为每个核心主力标注角色标签和成为主力的原因
- 生成多方的风格标签和一句话战术总结

### 2. 空方阵营分析 (short_side)  
- 统计卖方的总金额、席位数量、知名游资数量
- 识别核心主力（按净卖出金额排序，取前2名）
- 为每个核心主力标注角色标签和成为主力的原因
- 生成空方的风格标签和一句话战术总结

### 3. 协同小组识别 (synergy_groups)
- 识别同一游资名称的多个席位（如"T王"出现在多个席位）
- 计算小组的总买入、总卖出、净额
- 判断小组属于多方还是空方

### 4. 战局评估 (battle_assessment)
- 判断胜负方（基于净买入额）
- 计算双方实力评分（可基于金额大小、玩家质量等）
- 生成战局标签，如：游资主导局、机构出逃局、多空胶着、强力锁仓等
- 给出关键要点总结

### 5. 重要提示
- 所有金额保持原格式（如"0.65亿元"、"456.11万元"）
- 角色标签要具体明确（如"主导多头"、"核心游资"、"助攻力量"等）
- 战局评估要客观理性，基于数据说话
- 关注游资的历史风格和操作特点

请严格按照JSON格式输出分析结果。
"""
        
        return prompt

    def _get_json_schema(self) -> str:
        """返回期望的JSON输出格式示例"""
        return """{
    "ts_code": "000525.SZ",
    "name": "红太阳", 
    "basic_info": {
        "close": 9.03,
        "pct_change": "9.99%",
        "turnover_rate": "16.46%",
        "amount": "14.59亿元",
        "l_sell": "1.09亿元",
        "l_buy": "2.37亿元",
        "net_amount": "1.28亿元",
        "trade_date_display": "2025-06-17"
    },
    "long_side": {
        "total_amount_on_list": "2.37亿元",
        "player_count": 5,
        "famous_player_count": 1,
        "core_players": [
            {
                "seat_name": "中信证券股份有限公司浙江分公司",
                "buy_amount": "0.65亿元",
                "sell_amount": "456.11万元",
                "player_type": "普通席位",
                "role_tags": ["主导多头"],
                "reasons": ["买入金额第一", "净买入金额最大"]
            },
            {
                "seat_name": "国泰海通证券股份有限公司成都北一环路证券营业部",
                "buy_amount": "0.41亿元", 
                "sell_amount": "0.54万元",
                "player_type": "知名游资",
                "role_tags": ["核心游资", "成都系"],
                "reasons": ["知名游资参与", "买入金额第三"]
            }
        ],
        "other_players": [],
        "summary": {
            "concentration": "44.7%",
            "style_tags": ["打板", "短线交易"],
            "conclusion": "由普通席位和知名游资'成都系'联手主导进攻"
        }
    },
    "short_side": {
        "total_amount_on_list": "1.09亿元",
        "player_count": 5,
        "famous_player_count": 3,
        "core_players": [
            {
                "seat_name": "国元证券股份有限公司宁波分公司",
                "buy_amount": "0.00万元",
                "sell_amount": "0.30亿元", 
                "player_type": "普通席位",
                "role_tags": ["主导空头"],
                "reasons": ["卖出金额第一"]
            }
        ],
        "other_players": [],
        "summary": {
            "concentration": "27.5%",
            "style_tags": ["短线交易", "做T"], 
            "conclusion": "空方以T王等游资为主，呈现分散撤退态势"
        }
    },
    "synergy_groups": [
        {
            "group_name": "T王",
            "type": "知名游资",
            "side": "short",
            "seats_involved": [
                "东方财富证券股份有限公司拉萨团结路第二证券营业部",
                "东方财富证券股份有限公司拉萨团结路第一证券营业部"
            ],
            "total_buy_amount": "1707.59万元",
            "total_sell_amount": "3300万元",
            "net_amount": "-1592.41万元"
        }
    ],
    "battle_assessment": {
        "winner": "多方",
        "net_advantage": "1.28亿元",
        "long_strength_score": 85,
        "short_strength_score": 52,
        "battle_tags": ["游资主导局", "强力锁仓"],
        "key_takeaway": "多方在资金总量和核心力量上均占优势，知名游资积极介入；空方虽有游资出逃，但力量相对分散，多方胜算较大"
    }
}"""

    def _get_fallback_result(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """LLM失败时的备用结果"""
        basic_info = stock.get("basic_info", {})
        return {
            "ts_code": stock.get("ts_code", ""),
            "name": stock.get("name", ""),
            "basic_info": basic_info,
            "long_side": {
                "total_amount_on_list": basic_info.get("l_buy", "0万元"),
                "player_count": len(stock.get("seat_data", {}).get("buy_seats", [])),
                "famous_player_count": 0,
                "core_players": [],
                "other_players": [],
                "summary": {
                    "conclusion": "LLM分析失败，需要重新处理"
                }
            },
            "short_side": {
                "total_amount_on_list": basic_info.get("l_sell", "0万元"),
                "player_count": len(stock.get("seat_data", {}).get("sell_seats", [])),
                "famous_player_count": 0,
                "core_players": [],
                "other_players": [],
                "summary": {
                    "conclusion": "LLM分析失败，需要重新处理"
                }
            },
            "synergy_groups": [],
            "battle_assessment": {
                "winner": "未知",
                "net_advantage": "0万元",
                "long_strength_score": 50,
                "short_strength_score": 50,
                "battle_tags": ["分析失败"],
                "key_takeaway": "LLM分析失败，建议使用代码版本重新分析"
            }
        }


# -------------------- CLI -------------------- #
def _run_demo(input_path: Path):
    """运行LLM版本的演示"""
    try:
        builder = FundingBattleLLMBuilder()
        
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        summaries = []
        for stock in data.get("stocks", []):
            summary = builder.build_summary(stock)
            summaries.append(summary)

        # 保存结果
        output_path = input_path.parent / "test_funding_summary_llm.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)

        logger.info(f"🎉 LLM版本 FundingBattleSummary 已生成: {output_path}")
        
        # 显示结果
        print("=" * 60)
        print("LLM版本分析结果:")
        print("=" * 60)
        print(json.dumps(summaries, ensure_ascii=False, indent=2))
        
    except Exception as e:
        logger.error(f"LLM版本运行失败: {e}")
        raise


if __name__ == "__main__":
    default_input = Path(__file__).parent / "test-seat.json"
    _run_demo(default_input) 