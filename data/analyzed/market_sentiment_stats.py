#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gushen AI 龙虎榜每日分析汇总报告生成器
=================================

功能特点：
- 📅 按日期分组统计个股情绪水平分布
- 📊 生成美观的控制台报告展示
- 💾 输出结构化的每日分析报告Markdown文件
- 🎯 提供个股情绪洞察和风险评估
- 👥 识别核心参与者（机构vs知名游资动向）
- 📈 K线形态分析（高位出货、低位吸筹等技术形态）

分析维度：
- 亢奋：个股情绪高涨，多头氛围浓厚
- 恐慌：个股恐慌情绪，空头压制明显  
- 分歧：多空博弈激烈，个股分歧严重

作者：Gushen AI Team
版本：v2.0
更新：2025-07-27
"""

import json
import os
from collections import defaultdict
from datetime import datetime


def generate_stock_title(stock_name, level, verdict, behavior_type, core_players, ts_code):
    """生成个股分析标题"""
    emoji_map = {
        '亢奋': '🚀',
        '恐慌': '😰',
        '分歧': '🤔'
    }
    
    # 获取情绪emoji
    emotion_emoji = emoji_map.get(level, '📊')
    
    # 基于核心参与者生成标题差异化
    players_summary = core_players.get('summary', '普通散户')
    
    # 根据不同情况生成标题模板
    if '机构' in players_summary and any(trader in players_summary for trader in ['买', '卖', '博弈']):
        # 机构+游资博弈
        title = f"{emotion_emoji} {stock_name}：机构游资激烈博弈，{behavior_type}态势明确"
    elif '机构' in players_summary:
        # 纯机构参与
        if '买' in players_summary:
            title = f"{emotion_emoji} {stock_name}：机构重金抄底，{behavior_type}信号强烈"
        else:
            title = f"{emotion_emoji} {stock_name}：机构大举减仓，{behavior_type}趋势确立"
    elif any(famous_trader in players_summary for famous_trader in ['佛山', '淮海', '东莞', '华鑫', '光大']):
        # 知名游资参与
        if '博弈' in players_summary:
            title = f"{emotion_emoji} {stock_name}：知名游资对决升级，{behavior_type}成关键"
        elif '买' in players_summary:
            title = f"{emotion_emoji} {stock_name}：游资大佬重仓出击，{behavior_type}爆发在即"
        else:
            title = f"{emotion_emoji} {stock_name}：游资高位派发，{behavior_type}风险加剧"
    else:
        # 普通散户或其他情况
        if level == '亢奋':
            title = f"{emotion_emoji} {stock_name}：散户情绪高涨，{behavior_type}值得关注"
        elif level == '恐慌':
            title = f"{emotion_emoji} {stock_name}：恐慌抛售加剧，{behavior_type}底部显现"
        else:
            title = f"{emotion_emoji} {stock_name}：多空分歧严重，{behavior_type}方向待定"
    
    # 生成文件链接（基于ts_code）
    link_url = f"./analysis/{ts_code}_analysis.html"
    
    # 返回Markdown链接格式
    return f"[{title}]({link_url})"


def analyze_core_players(buying_force, selling_force):
    """分析核心参与者，重点关注知名游资"""
    players = {
        'institutions': {'buy': False, 'sell': False},
        'famous_traders': {'buy': [], 'sell': []},
        'summary': ''
    }
    
    # 分析买方力量
    for player in buying_force:
        player_type = player.get('player_type', '')
        player_name = player.get('player_name', '')
        
        if player_type == '机构':
            players['institutions']['buy'] = True
        elif player_type == '知名游资' and player_name:
            players['famous_traders']['buy'].append(player_name)
    
    # 分析卖方力量
    for player in selling_force:
        player_type = player.get('player_type', '')
        player_name = player.get('player_name', '')
        
        if player_type == '机构':
            players['institutions']['sell'] = True
        elif player_type == '知名游资' and player_name:
            players['famous_traders']['sell'].append(player_name)
    
    # 生成摘要
    summary_parts = []
    
    # 机构参与情况
    if players['institutions']['buy'] and players['institutions']['sell']:
        summary_parts.append("机构(买卖)")
    elif players['institutions']['buy']:
        summary_parts.append("机构(买)")
    elif players['institutions']['sell']:
        summary_parts.append("机构(卖)")
    
    # 知名游资参与情况
    buy_traders = list(set(players['famous_traders']['buy']))  # 去重
    sell_traders = list(set(players['famous_traders']['sell']))  # 去重
    
    if buy_traders and sell_traders:
        # 同时有买卖的知名游资
        all_traders = list(set(buy_traders + sell_traders))
        if len(all_traders) == 1:
            summary_parts.append(f"{all_traders[0]}(做T)")
        else:
            # 显示所有参与博弈的游资名字
            trader_names = ",".join(all_traders)
            summary_parts.append(f"{trader_names}(博弈)")
    elif buy_traders:
        if len(buy_traders) == 1:
            summary_parts.append(f"{buy_traders[0]}(买)")
        else:
            # 显示所有买入的游资名字
            trader_names = ",".join(buy_traders)
            summary_parts.append(f"{trader_names}(买)")
    elif sell_traders:
        if len(sell_traders) == 1:
            summary_parts.append(f"{sell_traders[0]}(卖)")
        else:
            # 显示所有卖出的游资名字
            trader_names = ",".join(sell_traders)
            summary_parts.append(f"{trader_names}(卖)")
    
    players['summary'] = " vs ".join(summary_parts) if summary_parts else "普通散户"
    
    return players


def scan_market_sentiment_levels():
    """扫描所有分析文件，按日期统计个股情绪水平分布"""
    # 获取当前脚本所在目录（应该是analyzed目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 用于存储统计结果，按日期分组
    daily_stats = defaultdict(lambda: defaultdict(list))  # {date: {level: [stock_list]}}
    total_stocks = 0
    error_files = []
    
    print("🔍 开始扫描个股情绪水平按日期统计...")
    print(f"📁 扫描目录: {current_dir}")
    print("-" * 80)
    
    # 遍历所有日期目录，但只处理20250702
    date_dirs = [item for item in os.listdir(current_dir) 
                 if os.path.isdir(os.path.join(current_dir, item)) and item.isdigit() and len(item) == 8]
    date_dirs.sort()  # 按日期排序
    
    # 只处理7月2号的数据
    target_date = "20250702"
    filtered_date_dirs = [date for date in date_dirs if date == target_date]
    
    for date_item in filtered_date_dirs:
        date_dir = os.path.join(current_dir, date_item)
        print(f"📅 处理日期: {date_item}")
        
        # 遍历该日期目录下的所有json文件
        json_files = [f for f in os.listdir(date_dir) if f.endswith('_analysis.json')]
        print(f"   📄 找到{len(json_files)}个分析文件")
        
        daily_stock_count = 0
        for json_file in json_files:
            file_path = os.path.join(date_dir, json_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取股票基本信息
                stock_info = data.get('stock_info', {})
                stock_name = stock_info.get('name', 'Unknown')
                ts_code = stock_info.get('ts_code', 'Unknown')
                trade_date = stock_info.get('trade_date', date_item)
                
                # 提取market_sentiment.level和interpretation
                analysis_report = data.get('analysis_report', {})
                overall_assessment = analysis_report.get('overall_assessment', {})
                market_sentiment = overall_assessment.get('market_sentiment', {})
                level = market_sentiment.get('level', 'Unknown')
                interpretation = market_sentiment.get('interpretation', '')
                
                # 提取更多信息用于展示
                verdict = overall_assessment.get('verdict', 'Unknown')
                confidence_score = overall_assessment.get('confidence_score', 0)
                
                # 提取K线行为类型
                kline_behavior_analysis = analysis_report.get('kline_behavior_analysis', {})
                behavior_type = kline_behavior_analysis.get('behavior_type', 'Unknown')
                
                # 提取核心参与者信息
                key_forces = analysis_report.get('key_forces', {})
                buying_force = key_forces.get('buying_force', [])
                selling_force = key_forces.get('selling_force', [])
                
                # 分析核心参与者
                core_players = analyze_core_players(buying_force, selling_force)
                
                # 生成个股分析标题
                stock_title = generate_stock_title(stock_name, level, verdict, behavior_type, core_players, ts_code)
                
                # 添加到统计中
                stock_entry = {
                    'name': stock_name,
                    'ts_code': ts_code,
                    'trade_date': trade_date,
                    'file': json_file,
                    'verdict': verdict,
                    'confidence_score': confidence_score,
                    'interpretation': interpretation,
                    'behavior_type': behavior_type,
                    'core_players': core_players,
                    'title': stock_title  # 新增题目字段
                }
                
                daily_stats[date_item][level].append(stock_entry)
                total_stocks += 1
                daily_stock_count += 1
                
            except Exception as e:
                error_files.append({
                    'file': file_path,
                    'error': str(e)
                })
                print(f"   ❌ 处理文件错误: {json_file} - {e}")
        
        print(f"   ✅ 成功处理{daily_stock_count}个股票")
        print()
    
    return daily_stats, total_stocks, error_files


def display_statistics(daily_stats, total_stocks, error_files):
    """显示按日期分组的统计结果"""
    print("\n" + "=" * 100)
    print("📊 龙虎榜每日分析汇总报告")
    print("=" * 100)
    
    print(f"📈 总计处理个股: {total_stocks}")
    print(f"📅 统计日期数量: {len(daily_stats)}")
    print(f"❌ 错误文件数量: {len(error_files)}")
    print()
    
    # 按日期顺序展示
    for date in sorted(daily_stats.keys()):
        date_stats = daily_stats[date]
        daily_total = sum(len(stocks) for stocks in date_stats.values())
        
        # 格式化日期显示
        formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        
        print("┌" + "─" * 98 + "┐")
        print(f"│ 📅 {formatted_date} 龙虎榜分析汇总 (共{daily_total}只股票)" + " " * (98 - len(f" {formatted_date} 龙虎榜分析汇总 (共{daily_total}只股票)") - 3) + "│")
        print("├" + "─" * 98 + "┤")
        
        # 按个股数量排序情绪级别
        sorted_levels = sorted(date_stats.items(), key=lambda x: len(x[1]), reverse=True)
        
        for level, stocks in sorted_levels:
            percentage = (len(stocks) / daily_total * 100) if daily_total > 0 else 0
            
            # 选择合适的emoji
            level_emoji = {
                '亢奋': '🚀',
                '恐慌': '😰', 
                '分歧': '🤔',
                'Unknown': '❓'
            }.get(level, '📊')
            
            print(f"│ {level_emoji} 【{level}】: {len(stocks)}只 ({percentage:.1f}%)" + " " * (98 - len(f" {level_emoji} 【{level}】: {len(stocks)}只 ({percentage:.1f}%)")) + "│")
            
            # 显示前5只代表性股票
            display_stocks = stocks[:5]
            for i, stock in enumerate(display_stocks):
                confidence = stock.get('confidence_score', 0)
                verdict = stock.get('verdict', 'Unknown')
                behavior_type = stock.get('behavior_type', 'Unknown')
                core_players = stock.get('core_players', {})
                players_summary = core_players.get('summary', '普通散户')
                title = stock.get('title', f"[{stock['name']}分析](./analysis/{stock['ts_code']}_analysis.html)")
                prefix = "│   ├─" if i < len(display_stocks) - 1 else "│   └─"
                
                # 从markdown链接中提取纯文本标题用于控制台显示
                title_text = title.split(']')[0][1:] if '[' in title and ']' in title else f"{stock['name']}分析"
                stock_info = f"{title_text} (置信度:{confidence:.2f})"
                print(f"{prefix} {stock_info}" + " " * (98 - len(f"{prefix} {stock_info}")) + "│")
            
            # 如果股票太多，显示省略信息
            if len(stocks) > 5:
                remaining = len(stocks) - 5
                print(f"│     ... 还有{remaining}只股票" + " " * (98 - len(f"     ... 还有{remaining}只股票")) + "│")
            
            print("│" + " " * 98 + "│")
        
        print("└" + "─" * 98 + "┘")
        print()
    
    # 跨日期汇总统计
    print("=" * 100)
    print("📈 跨日期汇总统计")
    print("=" * 100)
    
    all_levels = defaultdict(int)
    for date_stats in daily_stats.values():
        for level, stocks in date_stats.items():
            all_levels[level] += len(stocks)
    
    sorted_all_levels = sorted(all_levels.items(), key=lambda x: x[1], reverse=True)
    
    for level, count in sorted_all_levels:
        percentage = (count / total_stocks * 100) if total_stocks > 0 else 0
        level_emoji = {
            '亢奋': '🚀',
            '恐慌': '😰', 
            '分歧': '🤔',
            'Unknown': '❓'
        }.get(level, '📊')
        
        print(f"{level_emoji} 【{level}】: {count}只股票 ({percentage:.1f}%)")
    
    # 显示错误文件（如果有）
    if error_files:
        print("\n❌ 错误文件列表:")
        for error in error_files:
            print(f"   {error['file']}: {error['error']}")


def save_to_file(daily_stats, total_stocks):
    """保存每日报告格式的统计结果到Markdown文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"lhb_daily_analysis_summary_{timestamp}.md"
    
    # 生成Markdown内容
    current_time = datetime.now()
    md_content = []
    
    # 报告标题
    md_content.append("# 📊 Gushen AI 龙虎榜每日分析汇总")
    md_content.append("")
    
    # 生成每日报告
    for date in sorted(daily_stats.keys()):
        date_stats = daily_stats[date]
        daily_total = sum(len(stocks) for stocks in date_stats.values())
        formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        
        md_content.append(f"## 📅 {formatted_date} 龙虎榜分析汇总")
        md_content.append("")
        md_content.append(f"**📊 当日统计**: 共分析 {daily_total} 只个股")
        md_content.append("")
        
        # 统计当日情绪分布
        sorted_levels = sorted(date_stats.items(), key=lambda x: len(x[1]), reverse=True)
        
        # 情绪分布表格
        md_content.append("### 情绪分布概览")
        md_content.append("")
        md_content.append("| 情绪级别 | 数量 | 占比 | 代表个股 |")
        md_content.append("|---------|------|------|---------|")
        
        for level, stocks in sorted_levels:
            percentage = (len(stocks) / daily_total * 100) if daily_total > 0 else 0
            emoji = {
                '亢奋': '🚀',
                '恐慌': '😰', 
                '分歧': '🤔',
                'Unknown': '❓'
            }.get(level, '📊')
            
            # 选择前3只代表个股
            representative_stocks = stocks[:3]
            stock_names = [f"{s['name']}" for s in representative_stocks]
            if len(stocks) > 3:
                stock_names.append(f"等{len(stocks)}只")
            
            md_content.append(f"| {emoji} {level} | {len(stocks)}只 | {percentage:.1f}% | {', '.join(stock_names)} |")
        
        md_content.append("")
        
        # 生成关键洞察
        if sorted_levels:
            dominant_level = sorted_levels[0][0]
            dominant_count = len(sorted_levels[0][1])
            dominant_percentage = (dominant_count / daily_total * 100) if daily_total > 0 else 0
            
            md_content.append("### 🎯 关键洞察")
            md_content.append("")
            md_content.append(f"**主导情绪**: {dominant_level} ({dominant_count}只, {dominant_percentage:.1f}%)")
            md_content.append("")
            
            # 个股情绪判断
            if dominant_level == "亢奋" and dominant_percentage > 50:
                market_mood = "个股情绪普遍高涨，多头氛围浓厚"
                risk_level = "中等偏高"
            elif dominant_level == "恐慌" and dominant_percentage > 40:
                market_mood = "个股恐慌情绪蔓延，空头压制明显"
                risk_level = "高风险"
            elif dominant_level == "分歧":
                market_mood = "个股分歧严重，多空博弈激烈"
                risk_level = "高波动"
            else:
                market_mood = "个股情绪相对均衡"
                risk_level = "中等"
            
            md_content.append(f"**整体特征**: {market_mood}")
            md_content.append("")
            md_content.append(f"**风险等级**: {risk_level}")
            md_content.append("")
        
        # 详细个股列表
        md_content.append("### 📋 详细个股分析")
        md_content.append("")
        
        for level, stocks in sorted_levels:
            emoji = {
                '亢奋': '🚀',
                '恐慌': '😰', 
                '分歧': '🤔',
                'Unknown': '❓'
            }.get(level, '📊')
            
            md_content.append(f"#### {emoji} {level}情绪个股 ({len(stocks)}只)")
            md_content.append("")
            md_content.append("| 代码 | 分析结论 | K线形态 | 核心参与者 | 题目 |")
            md_content.append("|------|---------|---------|----------|------|")
            
            for stock in stocks:
                verdict = stock.get('verdict', 'Unknown')
                behavior_type = stock.get('behavior_type', 'Unknown')
                core_players = stock.get('core_players', {})
                players_summary = core_players.get('summary', '普通散户')
                title = stock.get('title', f"[{stock['name']}分析](./analysis/{stock['ts_code']}_analysis.html)")
                
                md_content.append(f"| {stock['ts_code']} | {verdict} | {behavior_type} | {players_summary} | {title} |")
            
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # 添加报告结尾
    md_content.append("*本报告由 Gushen AI 自动生成，仅供参考，不构成投资建议*")
    md_content.append("")
    md_content.append(f"*报告生成时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # 保存Markdown文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"📝 每日报告已保存到: {output_file}")
    return output_path


def main():
    """主函数"""
    print("🚀 Gushen AI 龙虎榜每日分析汇总报告生成器")
    print("=" * 80)
    
    # 扫描并统计
    daily_stats, total_stocks, error_files = scan_market_sentiment_levels()
    
    # 显示结果
    display_statistics(daily_stats, total_stocks, error_files)
    
    # 保存到文件
    if total_stocks > 0:
        save_to_file(daily_stats, total_stocks)
    
    print("\n✅ 每日分析报告生成完成! 🎉")


if __name__ == "__main__":
    main() 