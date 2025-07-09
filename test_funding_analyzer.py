#!/usr/bin/env python3
"""
龙虎榜资金博弈分析系统测试脚本
"""

import os
import sys
from core.funding_battle_analyzer import FundingBattleAnalyzer

def test_analyzer():
    """测试分析器功能"""
    print("正在初始化龙虎榜资金博弈分析器...")
    
    # 初始化分析器
    analyzer = FundingBattleAnalyzer()
    
    # 测试数据文件路径
    test_data_file = "core/test-seat-4.json"
    
    # 检查测试数据文件是否存在
    if not os.path.exists(test_data_file):
        print(f"警告：测试数据文件 {test_data_file} 不存在")
        print("请确保该文件存在并包含正确的龙虎榜数据格式")
        return
    
    # 输出文件路径
    output_file = "data/output/funding_battle_analysis_report-6.json"
    os.makedirs("data/output", exist_ok=True)
    
    print(f"正在分析文件: {test_data_file}")
    print("这可能需要几分钟时间，因为需要调用5个LLM模块...")
    
    # 执行完整分析
    result = analyzer.analyze_complete_report(test_data_file, output_file)
    
    if result:
        print("\n" + "="*80)
        print("🎉 分析完成！")
        print("="*80)
        print(f"📊 股票代码: {result['stock_info']['ts_code']}")
        print(f"📈 股票名称: {result['stock_info']['name']}")
        print(f"📅 交易日期: {result['stock_info']['trade_date']}")
        print(f"💾 报告已保存至: {output_file}")
        print("\n📋 分析摘要:")
        
        # 显示关键结论
        analysis = result.get('analysis_report', {})
        
        # 上榜原因
        if 'listing_reason_analysis' in analysis:
            reason_analysis = analysis['listing_reason_analysis']
            print(f"🎯 上榜信号强度: {reason_analysis.get('signal_strength', '未知')}")
            print(f"📝 上榜解读: {reason_analysis.get('interpretation', '无')}")
        
        # 战局总览
        if 'overall_assessment' in analysis:
            overall = analysis['overall_assessment']
            print(f"⚔️  战局定性: {overall.get('verdict', '未知')}")
            print(f"🔥 核心看点: {overall.get('key_takeaway', '无')}")
        
        # 后市展望
        if 'final_verdict' in analysis:
            final = analysis['final_verdict']
            print(f"🔮 后市展望: {final.get('outlook', '未知')}")
            print(f"💡 操作策略: {final.get('strategy', '无')}")
            print(f"⚠️  风险提示: {final.get('risk_warning', '无')}")
        
    else:
        print("❌ 分析失败，请检查:")
        print("1. DeepSeek API密钥是否正确配置")
        print("2. 网络连接是否正常")
        print("3. 输入数据格式是否正确")


if __name__ == "__main__":
    test_analyzer() 