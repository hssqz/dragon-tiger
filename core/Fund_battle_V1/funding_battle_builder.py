"""
龙虎榜资金博弈分析 - 第一阶段：代码预处理模块 (事实层)
将原始龙虎榜数据转换为结构化的StructuredFacts数据
"""

import json
import logging
from typing import Dict, List, Any, Tuple
from decimal import Decimal, InvalidOperation

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('funding_battle_builder')

class FundingBattleBuilder:
    """
    龙虎榜资金博弈构建器 - 事实层处理
    负责所有确定性的计算和数据结构化，确保100%的准确性
    """
    
    def __init__(self):
        """初始化构建器"""
        logger.info("初始化龙虎榜资金博弈构建器")
    
    def parse_amount_to_wan(self, amount_str: str) -> float:
        """
        解析金额字符串为万元数值
        
        参数:
            amount_str(str): 金额字符串，如"0.65亿元"、"456.11万元"
            
        返回:
            float: 万元数值
        """
        try:
            if not amount_str or amount_str.strip() == "":
                return 0.0
                
            # 移除空格和"元"字
            clean_str = amount_str.replace(" ", "").replace("元", "").replace(",", "")
            
            # 处理亿元
            if "亿" in clean_str:
                num_str = clean_str.replace("亿", "")
                return float(num_str) * 10000.0
            
            # 处理万元
            if "万" in clean_str:
                num_str = clean_str.replace("万", "")
                return float(num_str)
            
            # 处理纯数字（假设为万元）
            return float(clean_str)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"金额解析失败: {amount_str}, 错误: {e}")
            return 0.0
    
    def parse_percentage(self, pct_str: str) -> float:
        """
        解析百分比字符串为数值
        
        参数:
            pct_str(str): 百分比字符串，如"4.46%"
            
        返回:
            float: 百分比数值
        """
        try:
            if not pct_str or pct_str.strip() == "":
                return 0.0
            
            # 移除%符号
            clean_str = pct_str.replace("%", "").strip()
            return float(clean_str)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"百分比解析失败: {pct_str}, 错误: {e}")
            return 0.0
    
    def calculate_concentration_metrics(self, amounts: List[float]) -> Dict[str, float]:
        """
        计算资金集中度指标
        
        参数:
            amounts(List[float]): 金额列表（万元）
            
        返回:
            Dict[str, float]: 集中度指标
        """
        if not amounts:
            return {"top1_pct": 0.0, "top2_pct": 0.0, "top5_pct": 0.0}
        
        # 按金额排序（降序）
        sorted_amounts = sorted(amounts, reverse=True)
        total = sum(amounts)
        
        if total == 0:
            return {"top1_pct": 0.0, "top2_pct": 0.0, "top5_pct": 0.0}
        
        # 计算前N大占比
        top1_pct = (sorted_amounts[0] / total * 100) if len(sorted_amounts) >= 1 else 0.0
        top2_sum = sum(sorted_amounts[:2]) if len(sorted_amounts) >= 2 else sum(sorted_amounts)
        top2_pct = top2_sum / total * 100
        top5_sum = sum(sorted_amounts[:5]) if len(sorted_amounts) >= 5 else sum(sorted_amounts)
        top5_pct = top5_sum / total * 100
        
        return {
            "top1_pct": round(top1_pct, 1),
            "top2_pct": round(top2_pct, 1), 
            "top5_pct": round(top5_pct, 1)
        }
    
    def analyze_side_data(self, seats: List[Dict[str, Any]], side_type: str) -> Dict[str, Any]:
        """
        分析单个阵营（多方或空方）的数据
        
        参数:
            seats(List[Dict]): 席位数据列表
            side_type(str): 阵营类型，"buy"或"sell"
            
        返回:
            Dict[str, Any]: 阵营分析数据
        """
        if not seats:
            return {
                "total_amount_wan": 0.0,
                "player_count": 0,
                "famous_player_count": 0,
                "concentration_metrics": {"top1_pct": 0.0, "top2_pct": 0.0, "top5_pct": 0.0},
                "contribution_by_type": {},
                "players": []
            }
        
        # 解析席位数据
        processed_players = []
        amounts = []
        famous_count = 0
        contribution_by_type = {}
        
        for seat in seats:
            # 获取净买入/卖出金额
            if side_type == "buy":
                amount_str = seat.get("net_amount", "0万元")
            else:
                # 对于卖出方，净金额通常是负数，我们取绝对值
                amount_str = seat.get("net_amount", "0万元")
                if amount_str.startswith("-"):
                    amount_str = amount_str[1:]  # 移除负号
            
            amount_wan = self.parse_amount_to_wan(amount_str)
            amounts.append(amount_wan)
            
            # 获取玩家信息
            player_info = seat.get("player_info", {})
            player_type = player_info.get("type", "普通席位")
            
            # 统计知名游资数量
            if player_type == "知名游资":
                famous_count += 1
            
            # 按类型统计贡献
            if player_type not in contribution_by_type:
                contribution_by_type[player_type] = 0.0
            contribution_by_type[player_type] += amount_wan
            
            # 构建标准化的玩家数据（保持原始格式）
            player_data = {
                "seat_name": seat.get("seat_name", ""),
                "net_amount": seat.get("net_amount", "0万元"),
                "buy": seat.get("buy_amount", "0万元"),
                "sell": seat.get("sell_amount", "0万元"),
                "buy_rate": seat.get("buy_rate", "0.00%"),
                "sell_rate": seat.get("sell_rate", "0.00%"),
                "net_rate": f"{amount_wan/10000:.2f}%" if amount_wan > 0 else "0.00%",  # 简单估算
                "type": player_type,
                "name": player_info.get("name", player_type),
                "description": player_info.get("description", "暂无相关信息"),
                "style": player_info.get("style", ["风格未明"])
            }
            processed_players.append(player_data)
        
        # 计算集中度指标
        concentration_metrics = self.calculate_concentration_metrics(amounts)
        
        # 格式化按类型贡献（转换为万元）
        formatted_contribution = {}
        for ptype, amount in contribution_by_type.items():
            key = f"{ptype}_net_wan"
            formatted_contribution[key] = round(amount, 1)
        
        return {
            "total_amount_wan": round(sum(amounts), 1),
            "player_count": len(seats),
            "famous_player_count": famous_count,
            "concentration_metrics": concentration_metrics,
            "contribution_by_type": formatted_contribution,
            "players": processed_players
        }
    
    def calculate_battle_metrics(self, long_side: Dict[str, Any], short_side: Dict[str, Any], 
                                basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算资金博弈指标
        
        参数:
            long_side(Dict): 多方数据
            short_side(Dict): 空方数据  
            basic_info(Dict): 基础信息
            
        返回:
            Dict[str, Any]: 博弈指标
        """
        long_amount = long_side.get("total_amount_wan", 0.0)
        short_amount = short_side.get("total_amount_wan", 0.0)
        
        # 计算净优势
        net_advantage_wan = long_amount - short_amount
        
        # 判断获胜方
        winner = "多方" if net_advantage_wan > 0 else "空方" if net_advantage_wan < 0 else "平局"
        
        # 计算净优势百分比
        total_amount = long_amount + short_amount
        net_advantage_pct = (abs(net_advantage_wan) / total_amount * 100) if total_amount > 0 else 0.0
        
        # 获取龙虎榜总成交占比
        amount_rate_str = basic_info.get("amount_rate", "0.00%")
        on_list_turnover_pct = self.parse_percentage(amount_rate_str)
        
        return {
            "net_advantage_wan": round(net_advantage_wan, 1),
            "winner": winner,
            "net_advantage_pct": round(net_advantage_pct, 1),
            "on_list_turnover_pct": round(on_list_turnover_pct, 1)
        }
    
    def build_structured_facts(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建结构化事实数据
        
        参数:
            raw_data(Dict): 原始龙虎榜数据
            
        返回:
            Dict[str, Any]: StructuredFacts数据
        """
        logger.info("开始构建结构化事实数据")
        
        # 获取股票数据（假设只有一只股票）
        stocks = raw_data.get("stocks", [])
        if not stocks:
            logger.error("未找到股票数据")
            return {}
        
        stock_data = stocks[0]  # 取第一只股票
        ts_code = stock_data.get("ts_code", "")
        name = stock_data.get("name", "")
        basic_info = stock_data.get("basic_info", {})
        seat_data = stock_data.get("seat_data", {})
        
        logger.info(f"处理股票: {name} ({ts_code})")
        
        # 分析买方（多方）
        buy_seats = seat_data.get("buy_seats", [])
        long_side_facts = self.analyze_side_data(buy_seats, "buy")
        
        # 分析卖方（空方）
        sell_seats = seat_data.get("sell_seats", [])
        short_side_facts = self.analyze_side_data(sell_seats, "sell")
        
        # 计算博弈指标
        battle_facts = self.calculate_battle_metrics(long_side_facts, short_side_facts, basic_info)
        
        # 构建最终的StructuredFacts
        structured_facts = {
            "ts_code": ts_code,
            "name": name,
            "raw_basic_info": basic_info,
            "long_side_facts": long_side_facts,
            "short_side_facts": short_side_facts,
            "battle_facts": battle_facts
        }
        
        logger.info("结构化事实数据构建完成")
        logger.info(f"多方资金: {long_side_facts['total_amount_wan']}万元, "
                   f"空方资金: {short_side_facts['total_amount_wan']}万元, "
                   f"净优势: {battle_facts['net_advantage_wan']}万元, "
                   f"获胜方: {battle_facts['winner']}")
        
        return structured_facts
    
    def save_structured_facts(self, structured_facts: Dict[str, Any], output_path: str) -> bool:
        """
        保存结构化事实数据到文件
        
        参数:
            structured_facts(Dict): 结构化事实数据
            output_path(str): 输出文件路径
            
        返回:
            bool: 是否保存成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(structured_facts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结构化事实数据已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存结构化事实数据失败: {e}")
            return False
    
    def load_raw_data(self, input_path: str) -> Dict[str, Any]:
        """
        加载原始龙虎榜数据
        
        参数:
            input_path(str): 输入文件路径
            
        返回:
            Dict[str, Any]: 原始数据
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            logger.info(f"成功加载原始数据: {input_path}")
            return raw_data
            
        except Exception as e:
            logger.error(f"加载原始数据失败: {e}")
            return {}
    
    def process_file(self, input_path: str, output_path: str) -> bool:
        """
        处理单个文件：从原始数据到结构化事实
        
        参数:
            input_path(str): 输入文件路径
            output_path(str): 输出文件路径
            
        返回:
            bool: 是否处理成功
        """
        logger.info(f"开始处理文件: {input_path} -> {output_path}")
        
        # 加载原始数据
        raw_data = self.load_raw_data(input_path)
        if not raw_data:
            return False
        
        # 构建结构化事实
        structured_facts = self.build_structured_facts(raw_data)
        if not structured_facts:
            return False
        
        # 保存结果
        return self.save_structured_facts(structured_facts, output_path)


# ====== 测试代码 ======
if __name__ == "__main__":
    import os
    from pathlib import Path
    
    # 智能路径解析：找到项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent if current_dir.name == 'core' else current_dir
    
    # 测试FundingBattleBuilder
    builder = FundingBattleBuilder()
    
    # 测试文件路径（相对于项目根目录）
    input_file = project_root / "core/test-seat.json"
    output_file = project_root / "data/processed/test_structured_facts.json"
    
    # 处理文件
    success = builder.process_file(input_file, output_file)
    
    if success:
        print(f"✅ 文件处理成功！")
        print(f"📁 输入文件: {input_file}")
        print(f"📁 输出文件: {output_file}")
        
        # 显示处理结果摘要
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            print(f"\n📊 处理结果摘要:")
            print(f"股票: {result.get('name')} ({result.get('ts_code')})")
            print(f"多方资金: {result['long_side_facts']['total_amount_wan']}万元")
            print(f"空方资金: {result['short_side_facts']['total_amount_wan']}万元") 
            print(f"净优势: {result['battle_facts']['net_advantage_wan']}万元")
            print(f"获胜方: {result['battle_facts']['winner']}")
            print(f"龙虎榜成交占比: {result['battle_facts']['on_list_turnover_pct']}%")
            
        except Exception as e:
            print(f"❌ 读取结果文件失败: {e}")
    else:
        print(f"❌ 文件处理失败！")