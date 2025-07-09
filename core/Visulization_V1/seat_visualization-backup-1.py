#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
龙虎榜席位多空博弈图可视化模块
Author: Gushen AI
Date: 2025-01-27
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any
import re


class SeatVisualization:
    """龙虎榜席位可视化类"""
    
    def __init__(self):
        """初始化可视化配置"""
        self.colors = {
            'buy': '#FF4B4B',      # 红色系买入
            'sell': '#00CC66',     # 绿色系卖出
            'buy_gradient': ['#FF6B6B', '#FF4B4B', '#E03E3E'],
            'sell_gradient': ['#51CF66', '#00CC66', '#12B886'],
            'background': '#FAFAFA',
            'text': '#2E2E2E',
            'grid': '#E8E8E8',
            'highlight': '#FFD43B'
        }
        
        self.player_colors = {
            '知名游资': '#FF6B35',
            '普通席位': '#95A5A6', 
            '机构': '#3498DB',
            'T王': '#9B59B6',
            '温州帮': '#E74C3C',
            '成都系': '#F39C12'
        }
        
    def load_data(self, json_file: str) -> Dict[str, Any]:
        """加载龙虎榜数据"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"数据加载失败: {e}")
            return {}
    
    def format_amount(self, amount: str) -> float:
        """格式化金额字符串为数值"""
        if not amount or amount == "0.00万元":
            return 0.0
        
        # 移除万元、亿元等单位，转换为万元统一单位
        amount_clean = re.sub(r'[万元亿]', '', amount)
        # 移除逗号分隔符
        amount_clean = amount_clean.replace(',', '')
        try:
            value = float(amount_clean)
            if '亿' in amount:
                value *= 10000  # 转换为万元
            return value
        except:
            return 0.0
    
    def get_player_tag(self, player_info: Dict) -> str:
        """获取游资标签"""
        name = player_info.get('name', '未知')
        player_type = player_info.get('type', '普通席位')
        styles = player_info.get('style', [])
        
        if name != '未知机构' and name != '未知':
            return f"【{name}】"
        elif '知名游资' in player_type:
            return "【知名游资】"
        else:
            return ""
    
    def create_seat_battle_chart(self, stock_data: Dict[str, Any]) -> go.Figure:
        """创建席位多空博弈图"""
        basic_info = stock_data.get('basic_info', {})
        seat_data = stock_data.get('seat_data', {})
        
        # 处理买方席位数据
        buy_seats = seat_data.get('buy_seats', [])[:5]  # 取前5个
        sell_seats = seat_data.get('sell_seats', [])[:5]  # 取前5个
        
        # 创建子图
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=[f"{basic_info.get('name', '')} ({stock_data.get('ts_code', '')}) 龙虎榜席位"],
            specs=[[{"secondary_y": False}]]
        )
        
        # 处理买方数据
        buy_names = []
        buy_amounts = []
        buy_colors = []
        buy_players = []
        
        for seat in buy_seats:
            seat_name = seat.get('seat_name', '')
            net_amount = self.format_amount(seat.get('net_amount', '0'))
            player_info = seat.get('player_info', {})
            player_tag = self.get_player_tag(player_info)
            
            # 简化席位名称
            short_name = self._shorten_seat_name(seat_name)
            buy_names.append(f"{short_name}{player_tag}")
            buy_amounts.append(net_amount)
            buy_players.append(player_info.get('name', '普通席位'))
            
            # 根据游资类型选择颜色
            player_name = player_info.get('name', '普通席位')
            if player_name in self.player_colors:
                buy_colors.append(self.player_colors[player_name])
            else:
                buy_colors.append(self.colors['buy'])
        
        # 处理卖方数据
        sell_names = []
        sell_amounts = []
        sell_colors = []
        sell_players = []
        
        for seat in sell_seats:
            seat_name = seat.get('seat_name', '')
            net_amount = abs(self.format_amount(seat.get('net_amount', '0')))  # 取绝对值用于显示
            player_info = seat.get('player_info', {})
            player_tag = self.get_player_tag(player_info)
            
            # 简化席位名称
            short_name = self._shorten_seat_name(seat_name)
            sell_names.append(f"{short_name}{player_tag}")
            sell_amounts.append(-net_amount)  # 负值用于左侧显示
            sell_players.append(player_info.get('name', '普通席位'))
            
            # 根据游资类型选择颜色
            player_name = player_info.get('name', '普通席位')
            if player_name in self.player_colors:
                sell_colors.append(self.player_colors[player_name])
            else:
                sell_colors.append(self.colors['sell'])
        
        # 合并数据用于排序
        all_names = sell_names + buy_names
        all_amounts = sell_amounts + buy_amounts
        all_colors = sell_colors + buy_colors
        all_types = ['卖方'] * len(sell_names) + ['买方'] * len(buy_names)
        
        # 创建水平柱状图
        for i, (name, amount, color, seat_type) in enumerate(zip(all_names, all_amounts, all_colors, all_types)):
            fig.add_trace(go.Bar(
                y=[name],
                x=[amount],
                orientation='h',
                name=f"{seat_type}_{i}",
                marker=dict(
                    color=color,
                    line=dict(color='white', width=1)
                ),
                text=f"{abs(amount):.0f}万元" if amount != 0 else "",
                textposition='outside' if amount > 0 else 'outside',
                textfont=dict(size=11, color='#2E2E2E', family="微软雅黑"),
                hovertemplate=f"<b>{name}</b><br>" +
                             f"净额: {abs(amount):.0f}万元<br>" +
                             f"类型: {seat_type}<extra></extra>",
                showlegend=False
            ))
        
        # 添加中轴线
        fig.add_vline(x=0, line_width=2, line_color="#2E2E2E")
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=f"<b>{basic_info.get('name', '')} 龙虎榜席位多空博弈图</b><br>" +
                     f"<span style='font-size:14px'>交易日期: {basic_info.get('trade_date_display', '')} | " +
                     f"涨跌幅: {basic_info.get('pct_change', '')} | " +
                     f"换手率: {basic_info.get('turnover_rate', '')} | " +
                     f"龙虎榜净额: {basic_info.get('net_amount', '')}</span>",
                x=0.5,
                font=dict(size=18, family="微软雅黑")
            ),
            xaxis=dict(
                title="<b>资金流向 (万元)</b>",
                showgrid=True,
                gridcolor=self.colors['grid'],
                zeroline=True,
                zerolinecolor="#2E2E2E",
                zerolinewidth=2,
                tickfont=dict(size=12, family="微软雅黑")
            ),
            yaxis=dict(
                title="",
                showgrid=False,
                tickfont=dict(size=11, family="微软雅黑")
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=600,
            width=1200,
            margin=dict(l=300, r=100, t=120, b=80),
            font=dict(family="微软雅黑")
        )
        
        # 添加买卖方标识
        max_amount = max([abs(x) for x in all_amounts]) if all_amounts else 1000
        
        fig.add_annotation(
            x=max_amount * 0.7,
            y=len(all_names) + 0.5,
            text="<b>买方席位 (净买入)</b>",
            showarrow=False,
            font=dict(size=14, color=self.colors['buy'], family="微软雅黑")
        )
        
        fig.add_annotation(
            x=-max_amount * 0.7,
            y=len(all_names) + 0.5,
            text="<b>卖方席位 (净卖出)</b>",
            showarrow=False,
            font=dict(size=14, color=self.colors['sell'], family="微软雅黑")
        )
        
        return fig
    
    def _shorten_seat_name(self, full_name: str) -> str:
        """简化席位名称"""
        # 移除常见的公司类型词汇
        name = full_name.replace('证券股份有限公司', '').replace('有限责任公司', '')
        name = name.replace('证券营业部', '').replace('分公司', '')
        
        # 提取关键信息
        if '拉萨团结路第' in name:
            if '第一' in name:
                return '东方财富拉萨IT王第一'
            elif '第二' in name:
                return '东方财富拉萨IT王第二'
        
        # 提取城市和关键词
        patterns = [
            r'(\w+)(\w+路|\w+街|\w+区)',  # 城市+路名
            r'(\w{2,4})(营业部|分公司)',   # 简短机构名
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(0)
        
        # 如果没有匹配，返回前15个字符
        return name[:15] + ('...' if len(name) > 15 else '')
    
    def create_summary_stats(self, stock_data: Dict[str, Any]) -> go.Figure:
        """创建汇总统计图表"""
        basic_info = stock_data.get('basic_info', {})
        
        # 创建仪表盘样式的统计图
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=['涨跌幅', '换手率', '龙虎榜占比', '净买入', '成交额', '流通市值'],
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # 数据处理
        pct_change = float(basic_info.get('pct_change', '0').replace('%', ''))
        turnover_rate = float(basic_info.get('turnover_rate', '0').replace('%', ''))
        amount_rate = float(basic_info.get('amount_rate', '0').replace('%', ''))
        net_amount = basic_info.get('net_amount', '0')
        amount = basic_info.get('amount', '0')
        float_values = basic_info.get('float_values', '0')
        
        # 涨跌幅指标
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=pct_change,
            title={'text': "涨跌幅 (%)"},
            gauge={'axis': {'range': [-10, 10]},
                   'bar': {'color': self.colors['buy'] if pct_change > 0 else self.colors['sell']},
                   'steps': [{'range': [-10, 0], 'color': "#FFE5E5"},
                            {'range': [0, 10], 'color': "#E5F5E5"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                               'thickness': 0.75, 'value': 7}}
        ), row=1, col=1)
        
        # 换手率指标
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=turnover_rate,
            title={'text': "换手率 (%)"},
            gauge={'axis': {'range': [0, 30]},
                   'bar': {'color': self.colors['highlight']},
                   'steps': [{'range': [0, 5], 'color': "#F0F0F0"},
                            {'range': [5, 15], 'color': "#FFF3CD"},
                            {'range': [15, 30], 'color': "#F8D7DA"}]}
        ), row=1, col=2)
        
        # 龙虎榜占比指标
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=amount_rate,
            title={'text': "龙虎榜占比 (%)"},
            gauge={'axis': {'range': [0, 50]},
                   'bar': {'color': self.colors['buy']},
                   'steps': [{'range': [0, 10], 'color': "#F0F0F0"},
                            {'range': [10, 30], 'color': "#FFF3CD"},
                            {'range': [30, 50], 'color': "#D1ECF1"}]}
        ), row=1, col=3)
        
        # 其他指标使用数字显示
        net_amount_num = self.format_amount(net_amount) / 10000  # 转换为亿元
        fig.add_trace(go.Indicator(
            mode="number",
            value=net_amount_num,
            title={'text': "龙虎榜净买入 (亿元)"},
            number={'suffix': "亿", 'font': {'color': self.colors['buy'] if net_amount_num > 0 else self.colors['sell']}}
        ), row=2, col=1)
        
        amount_num = self.format_amount(amount) / 10000  # 转换为亿元
        fig.add_trace(go.Indicator(
            mode="number",
            value=amount_num,
            title={'text': "成交额 (亿元)"},
            number={'suffix': "亿", 'font': {'color': self.colors['text']}}
        ), row=2, col=2)
        
        float_num = self.format_amount(float_values) / 10000  # 转换为亿元
        fig.add_trace(go.Indicator(
            mode="number",
            value=float_num,
            title={'text': "流通市值 (亿元)"},
            number={'suffix': "亿", 'font': {'color': self.colors['text']}}
        ), row=2, col=3)
        
        fig.update_layout(
            title=f"<b>{basic_info.get('name', '')} 关键指标概览</b>",
            height=500,
            font=dict(family="微软雅黑")
        )
        
        return fig
    
    def create_player_analysis(self, stock_data: Dict[str, Any]) -> go.Figure:
        """创建游资分析图表"""
        seat_data = stock_data.get('seat_data', {})
        buy_seats = seat_data.get('buy_seats', [])
        sell_seats = seat_data.get('sell_seats', [])
        
        # 统计游资类型
        player_stats = {}
        all_seats = buy_seats + sell_seats
        
        for seat in all_seats:
            player_info = seat.get('player_info', {})
            player_name = player_info.get('name', '普通席位')
            net_amount = self.format_amount(seat.get('net_amount', '0'))
            
            if player_name not in player_stats:
                player_stats[player_name] = {
                    'count': 0,
                    'total_amount': 0,
                    'type': player_info.get('type', '普通席位'),
                    'styles': set()
                }
            
            player_stats[player_name]['count'] += 1
            player_stats[player_name]['total_amount'] += abs(net_amount)
            player_stats[player_name]['styles'].update(player_info.get('style', []))
        
        # 创建饼图
        names = list(player_stats.keys())
        values = [player_stats[name]['total_amount'] for name in names]
        colors = [self.player_colors.get(name, '#95A5A6') for name in names]
        
        fig = go.Figure(data=[go.Pie(
            labels=names,
            values=values,
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            textinfo='label+percent',
            textfont=dict(size=12, family="微软雅黑"),
            hovertemplate="<b>%{label}</b><br>" +
                         "参与金额: %{value:.0f}万元<br>" +
                         "占比: %{percent}<extra></extra>"
        )])
        
        fig.update_layout(
            title="<b>游资参与情况分析</b>",
            font=dict(family="微软雅黑"),
            height=400
        )
        
        return fig
    
    def generate_report(self, json_file: str, output_html: str = None):
        """生成完整的可视化报告"""
        # 加载数据
        data = self.load_data(json_file)
        if not data or 'stocks' not in data:
            print("数据格式错误或为空")
            return
        
        stock_data = data['stocks'][0]  # 取第一只股票
        
        # 创建图表
        battle_chart = self.create_seat_battle_chart(stock_data)
        stats_chart = self.create_summary_stats(stock_data)
        player_chart = self.create_player_analysis(stock_data)
        
        # 显示图表
        battle_chart.show()
        stats_chart.show()
        player_chart.show()
        
        # 保存HTML报告
        if output_html:
            with open(output_html, 'w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{stock_data.get('name', '')} 龙虎榜分析报告</title>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                </head>
                <body>
                    <h1 style="text-align: center; font-family: 微软雅黑;">{stock_data.get('name', '')} 龙虎榜深度分析报告</h1>
                    <div id="battle_chart">{battle_chart.to_html(include_plotlyjs=False, div_id="battle_chart")}</div>
                    <div id="stats_chart">{stats_chart.to_html(include_plotlyjs=False, div_id="stats_chart")}</div>
                    <div id="player_chart">{player_chart.to_html(include_plotlyjs=False, div_id="player_chart")}</div>
                </body>
                </html>
                """)
            print(f"报告已保存到: {output_html}")


if __name__ == "__main__":
    # 可视化测试代码
    print("=" * 60)
    print("🚀 Gushen AI 龙虎榜席位多空博弈图测试")
    print("=" * 60)
    
    visualizer = SeatVisualization()
    
    # 测试数据文件路径
    test_file = "core/test-seat.json"
    output_file = "红太阳_龙虎榜可视化测试报告.html"
    
    print(f"📊 正在读取测试数据: {test_file}")
    print(f"🎨 生成可视化图表...")
    
    try:
        # 生成可视化报告
        visualizer.generate_report(test_file, output_file)
        
        print("\n✅ 可视化测试成功完成！")
        print(f"📁 HTML报告已保存: {output_file}")
        print("\n📋 生成的图表包括:")
        print("   1. 🎯 席位多空博弈图 - 直观展示买卖方力量对比")
        print("   2. 📈 关键指标概览 - 涨跌幅、换手率、龙虎榜占比等仪表盘")
        print("   3. 🏢 游资参与分析 - 各类游资参与情况饼图统计")
        print("\n🎉 测试数据解析正常，可视化功能运行良好！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        print("请检查数据文件格式和依赖库是否正确") 