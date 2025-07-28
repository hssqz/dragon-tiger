import os
import json
from collections import Counter
import pprint

def aggregate_summary_stats(directory_path: str) -> dict:
    """
    遍历指定目录下的所有 *_analysis.json 文件，
    聚合生成增强版的 summary_stats。
    """
    if not os.path.isdir(directory_path):
        print(f"错误: 目录不存在 -> {directory_path}")
        return {}

    # 初始化所有统计项的计数器和列表
    verdict_counter = Counter()
    kline_behavior_counter = Counter()
    market_sentiment_counter = Counter()
    capital_confrontation_counter = Counter()
    listing_reason_counter = Counter()
    
    player_buy_side_counter = Counter()
    player_sell_side_counter = Counter()
    
    confidence_scores = []
    analyzed_files_count = 0

    print(f"正在扫描目录: {directory_path}\n")

    # 遍历目录中的所有文件
    for filename in os.listdir(directory_path):
        if filename.endswith("_analysis.json"):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                analyzed_files_count += 1
                report = data.get("analysis_report", {})
                if not report:
                    continue

                # --- 聚合数据 ---

                # 1. verdict_distribution & average_confidence
                assessment = report.get("overall_assessment", {})
                if assessment.get("verdict"):
                    verdict_counter[assessment["verdict"]] += 1
                if assessment.get("confidence_score"):
                    confidence_scores.append(float(assessment["confidence_score"]))

                # 2. kline_behavior_distribution
                kline_behavior = report.get("kline_behavior_analysis", {}).get("behavior_type")
                if kline_behavior:
                    kline_behavior_counter[kline_behavior] += 1

                # 3. market_sentiment_distribution
                sentiment = assessment.get("market_sentiment", {}).get("level")
                if sentiment:
                    market_sentiment_counter[sentiment] += 1

                # 4. capital_confrontation_distribution
                confrontation = assessment.get("capital_confrontation", {}).get("level")
                if confrontation:
                    capital_confrontation_counter[confrontation] += 1
                
                # 5. player_activity_summary
                key_forces = report.get("key_forces", {})
                # 使用 set 来确保每只股票只对一个玩家类型计数一次
                buy_player_types = {p.get("player_type") for p in key_forces.get("buying_force", []) if p.get("player_type")}
                sell_player_types = {p.get("player_type") for p in key_forces.get("selling_force", []) if p.get("player_type")}
                
                for p_type in buy_player_types:
                    player_buy_side_counter[p_type] += 1
                for p_type in sell_player_types:
                    player_sell_side_counter[p_type] += 1

                # 6. listing_reason_distribution
                reasons = report.get("listing_reason_analysis", {}).get("reasons", [])
                for reason in reasons:
                    listing_reason_counter[reason] += 1
            
            except json.JSONDecodeError:
                print(f"警告: JSON解码错误，跳过文件 -> {filename}")
            except Exception as e:
                print(f"警告: 处理文件时发生未知错误 -> {filename}, 错误: {e}")

    # --- 组装最终结果 ---
    
    # 计算平均置信度
    average_confidence = round(sum(confidence_scores) / len(confidence_scores), 2) if confidence_scores else 0

    summary_stats = {
        "verdict_distribution": dict(verdict_counter),
        "average_confidence": average_confidence,
        "kline_behavior_distribution": dict(kline_behavior_counter),
        "market_sentiment_distribution": dict(market_sentiment_counter),
        "capital_confrontation_distribution": dict(capital_confrontation_counter),
        "player_activity_summary": {
            "buy_side_appearances": dict(player_buy_side_counter),
            "sell_side_appearances": dict(player_sell_side_counter)
        },
        "listing_reason_distribution": dict(listing_reason_counter)
    }

    print(f"--- 聚合结果 (共处理 {analyzed_files_count} 个文件) ---")
    pprint.pprint(summary_stats)
    
    return summary_stats

if __name__ == "__main__":
    # 指定要测试的目录
    TEST_DIRECTORY = "data/analyzed/20250703"
    
    # 运行聚合函数
    aggregate_summary_stats(TEST_DIRECTORY) 