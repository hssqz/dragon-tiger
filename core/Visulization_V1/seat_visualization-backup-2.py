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
import os


class SeatVisualization:
    """龙虎榜席位可视化类"""
    
    def __init__(self):
        """初始化可视化配置"""
        self.colors = {
            'buy': '#FF4B4B',      # 红色 - 中国股市：上涨/买入
            'sell': '#00CC66',     # 绿色 - 中国股市：下跌/卖出
            'up': '#FF4B4B',       # 红色 - 上涨
            'down': '#00CC66',     # 绿色 - 下跌
            'positive': '#FF4B4B', # 红色 - 正值
            'negative': '#00CC66', # 绿色 - 负值
            'background': '#FAFAFA',
            'text': '#2E2E2E',
            'grid': '#E8E8E8',
            'highlight': '#FFD43B'
        }
        self.type_colors = {
            '量化': '#4A90E2',      # 蓝色
            '机构': '#F5A623',      # 橙色
            '知名游资': '#9013FE',  # 紫色
            '普通席位': '#AAAAAA'   # 灰色
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
    
    def get_player_type_icon(self, player_type: str) -> str:
        """获取席位类型对应的文本图标"""
        type_map = {
            '量化': '[量]',
            '机构': '[机]', 
            '知名游资': '[游]',
            '普通席位': '[普]'
        }
        return type_map.get(player_type, '[普]')

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
        buy_seats_raw = seat_data.get('buy_seats', [])
        sell_seats_raw = seat_data.get('sell_seats', [])
        
        # 按金额大小排序买方和卖方席位
        buy_seats_sorted = sorted(buy_seats_raw, 
                                key=lambda x: self.format_amount(x.get('net_amount', '0')), 
                                reverse=True)[:5]  # 买入金额从大到小，取前5
        
        sell_seats_sorted = sorted(sell_seats_raw, 
                                 key=lambda x: abs(self.format_amount(x.get('net_amount', '0'))), 
                                 reverse=True)[:5]  # 卖出金额从大到小，取前5
        
        # 创建子图
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=[""],  # 清空副标题，整合到主标题中
            specs=[[{"secondary_y": False}]]
        )
        
        # 处理数据，确保买卖方数量一致
        max_seats = max(len(buy_seats_sorted), len(sell_seats_sorted))
        
        # 准备数据数组
        position_labels = []
        sell_names = []
        sell_amounts = []
        buy_names = []
        buy_amounts = []
        
        for i in range(max_seats):
            if i == 0:
                position_labels.append("买一/卖一")
            elif i == 1:
                position_labels.append("买二/卖二")
            elif i == 2:
                position_labels.append("买三/卖三")
            elif i == 3:
                position_labels.append("买四/卖四")
            elif i == 4:
                position_labels.append("买五/卖五")
            else:
                # 对于可能的更多席位，使用数字
                chinese_nums = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                if i+1 < len(chinese_nums):
                    position_labels.append(f"买{chinese_nums[i+1]}/卖{chinese_nums[i+1]}")
                else:
                    position_labels.append(f"买{i+1}/卖{i+1}")
            
            # 处理卖方数据（按金额从大到小）
            if i < len(sell_seats_sorted):
                seat = sell_seats_sorted[i]
                seat_name = seat.get('seat_name', '')
                net_amount = abs(self.format_amount(seat.get('net_amount', '0')))
                player_info = seat.get('player_info', {})
                player_tag = self.get_player_tag(player_info)
                player_type = player_info.get('type', '普通席位')
                type_icon = self.get_player_type_icon(player_type)
                
                # 简化席位名称显示
                short_name = self._shorten_seat_name(seat_name)
                display_name = f"{type_icon} {short_name}{player_tag}"
                sell_names.append(display_name)
                sell_amounts.append(-net_amount)  # 负值用于左侧显示
            else:
                sell_names.append("")
                sell_amounts.append(0)
            
            # 处理买方数据（按金额从大到小）
            if i < len(buy_seats_sorted):
                seat = buy_seats_sorted[i]
                seat_name = seat.get('seat_name', '')
                net_amount = self.format_amount(seat.get('net_amount', '0'))
                player_info = seat.get('player_info', {})
                player_tag = self.get_player_tag(player_info)
                player_type = player_info.get('type', '普通席位')
                type_icon = self.get_player_type_icon(player_type)
                
                # 简化席位名称显示
                short_name = self._shorten_seat_name(seat_name)
                display_name = f"{type_icon} {short_name}{player_tag}"
                buy_names.append(display_name)
                buy_amounts.append(net_amount)
            else:
                buy_names.append("")
                buy_amounts.append(0)
        
        # 创建卖方柱状图（左侧，绿色）
        fig.add_trace(go.Bar(
            y=position_labels,
            x=sell_amounts,
            orientation='h',
            name="卖方席位",
            marker=dict(
                color=self.colors['sell'],  # 统一绿色
                line=dict(color='white', width=1)
            ),
            text=[f"{name}<br>{abs(amount):.0f}万元" if amount != 0 else "" 
                  for name, amount in zip(sell_names, sell_amounts)],
            textposition='outside',
            textfont=dict(size=12, color='#2E2E2E', family="微软雅黑"),
            hoverinfo='none',
            customdata=sell_names
        ))
        
        # 创建买方柱状图（右侧，红色）
        fig.add_trace(go.Bar(
            y=position_labels,
            x=buy_amounts,
            orientation='h',
            name="买方席位",
            marker=dict(
                color=self.colors['buy'],  # 统一红色
                line=dict(color='white', width=1)
            ),
            text=[f"{name}<br>{amount:.0f}万元" if amount != 0 else "" 
                  for name, amount in zip(buy_names, buy_amounts)],
            textposition='outside',
            textfont=dict(size=12, color='#2E2E2E', family="微软雅黑"),
            hoverinfo='none',
            customdata=buy_names
        ))
        
        # 添加中轴线
        fig.add_vline(x=0, line_width=2, line_color="#2E2E2E")
        
        # 计算最大金额用于设置轴范围
        max_amount = max([abs(x) for x in sell_amounts + buy_amounts]) if (sell_amounts + buy_amounts) else 1000
        
        # 准备关键指标数据
        close_price = basic_info.get('close', '0.00')
        pct_change = basic_info.get('pct_change', '0%')
        turnover_rate = basic_info.get('turnover_rate', '0%')
        amount = basic_info.get('amount', '0')
        float_values = basic_info.get('float_values', '0')
        net_amount = basic_info.get('net_amount', '0')
        net_rate = basic_info.get('net_rate', '0%')
        l_buy = basic_info.get('l_buy', '0')
        l_sell = basic_info.get('l_sell', '0')
        
        # 计算买入占比和卖出占比
        amount_num = self.format_amount(amount)
        l_buy_num = self.format_amount(l_buy)
        l_sell_num = self.format_amount(l_sell)
        
        buy_ratio = f"{l_buy_num/amount_num*100:.2f}%" if amount_num > 0 else "0%"
        sell_ratio = f"{l_sell_num/amount_num*100:.2f}%" if amount_num > 0 else "0%"
        
        # 格式化股票代码（去掉.SZ/.SH后缀）
        stock_code = stock_data.get('ts_code', '').split('.')[0] if stock_data.get('ts_code') else ''
        stock_name = basic_info.get('name', '')
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=f"<b style='font-size:20px'>({stock_code}) {stock_name} - 龙虎榜多空博弈席位图</b><br><br>" +
                     f"<span style='font-size:12px;line-height:1.8'>" +
                     f"收盘价: {close_price} &nbsp;&nbsp; " +
                     f"涨跌幅: <span style='color:{self.colors['up'] if '+' in pct_change or not '-' in pct_change and pct_change != '0%' else self.colors['down']}'><b>{pct_change}</b></span> &nbsp;&nbsp; " +
                     f"换手率: {turnover_rate} &nbsp;&nbsp; " +
                     f"成交额: {amount}" +
                     f"</span><br>" +
                     f"<span style='font-size:12px;line-height:1.8'>" +
                     f"龙虎榜净额: <span style='color:{self.colors['positive'] if not '-' in net_amount and net_amount != '0' else self.colors['negative']}'><b>{net_amount}</b></span>({net_rate}) &nbsp;&nbsp; " +
                     f"买入占比: <span style='color:{self.colors['positive']}'><b>{buy_ratio}</b></span> &nbsp;&nbsp; " +
                     f"卖出占比: <span style='color:{self.colors['negative']}'><b>{sell_ratio}</b></span> &nbsp;&nbsp; " +
                     f"流通市值: {float_values}" +
                     f"</span>",
                x=0.5,
                y=0.98,
                font=dict(family="微软雅黑")
            ),
            xaxis=dict(
                title="<b>资金流向 (万元)</b>",
                showgrid=True,
                gridcolor=self.colors['grid'],
                zeroline=True,
                zerolinecolor="#2E2E2E",
                zerolinewidth=2,
                tickfont=dict(size=12, family="微软雅黑"),
                range=[-max_amount * 1.3, max_amount * 1.3],  # 设置对称范围
                fixedrange=True
            ),
            yaxis=dict(
                title="<b>席位排名</b>",
                showgrid=True,
                gridcolor=self.colors['grid'],
                tickfont=dict(size=12, family="微软雅黑"),
                categoryorder='array',
                categoryarray=position_labels[::-1],  # 反转显示顺序，买一卖一在顶部
                fixedrange=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=700,
            width=1400,
            margin=dict(l=100, r=100, t=160, b=100),
            font=dict(family="微软雅黑"),
            barmode='overlay',  # 重叠模式
            showlegend=False
        )
        

        
        # 添加买卖方区域标识
        fig.add_annotation(
            x=max_amount * 0.7,
            y=len(position_labels) - 0.3,
            text="<b>买方席位</b>",
            showarrow=True,
            arrowhead=2,
            arrowcolor=self.colors['buy'],
            font=dict(size=14, color=self.colors['buy'], family="微软雅黑"),
            bgcolor="rgba(255, 75, 75, 0.1)",
            bordercolor=self.colors['buy'],
            borderwidth=1
        )
        
        fig.add_annotation(
            x=-max_amount * 0.7,
            y=len(position_labels) - 0.3,
            text="<b>卖方席位</b>",
            showarrow=True,
            arrowhead=2,
            arrowcolor=self.colors['sell'],
            font=dict(size=14, color=self.colors['sell'], family="微软雅黑"),
            bgcolor="rgba(0, 204, 102, 0.1)",
            bordercolor=self.colors['sell'],
            borderwidth=1
        )
        
        return fig
    
    def _shorten_seat_name(self, full_name: str) -> str:
        """简化席位名称，保持关键信息"""
        # 移除常见的公司类型词汇
        name = full_name.replace('证券股份有限公司', '').replace('有限责任公司', '')
        name = name.replace('证券营业部', '营业部').replace('分公司', '')
        name = name.replace('股份有限公司', '')
        
        # 特殊处理知名席位
        if '拉萨团结路第' in name:
            if '第一' in name:
                return '东财拉萨一部'
            elif '第二' in name:
                return '东财拉萨二部'
        
        if '华泰证券' in name and '南京' in name:
            return '华泰南京'
        
        if '中信证券' in name:
            city_match = re.search(r'中信证券(\w{2,4})', name)
            if city_match:
                return f"中信{city_match.group(1)}"
        
        # 提取城市和关键词
        patterns = [
            r'(\w{2,4})(\w+路|\w+街|\w+大道)',  # 城市+路名
            r'(\w{2,4})(营业部)',   # 城市+营业部
            r'(\w{2,6})(证券)',     # 证券公司简称
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                if len(match.group(0)) <= 8:  # 如果提取的名称不太长
                    return match.group(0)
        
        # 如果没有匹配，返回前10个字符
        return name[:10] + ('...' if len(name) > 10 else '')


    

    
    def generate_report(self, json_file: str, output_html: str = None):
        """生成席位多空博弈图报告"""
        # 加载数据
        data = self.load_data(json_file)
        if not data or 'stocks' not in data:
            print("数据格式错误或为空")
            return
        
        stock_data = data['stocks'][0]  # 取第一只股票
        basic_info = stock_data.get('basic_info', {})
        
        # 只创建席位多空博弈图
        battle_chart = self.create_seat_battle_chart(stock_data)

        # 显示图表（禁用交互）
        battle_chart.show(config={'displayModeBar': False})
        
        # 保存HTML报告
        if output_html:
            with open(output_html, 'w', encoding='utf-8') as f:
                # 格式化HTML文件标题
                stock_code = stock_data.get('ts_code', '').split('.')[0] if stock_data.get('ts_code') else ''
                stock_name = basic_info.get('name', '')
                html_title = f"({stock_code}) {stock_name} - 龙虎榜多空博弈席位图"
                
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{html_title}</title>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                    <style>
                        html, body {{
                            margin: 0;
                            padding: 0;
                            width: 100%;
                            height: 100%;
                            background-color: #f8f9fa;
                            font-family: "Microsoft YaHei", Arial, sans-serif;
                        }}
                        .page-container {{
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            padding: 20px;
                            box-sizing: border-box;
                        }}
                        .chart-container {{
                            background-color: white;
                            border-radius: 8px;
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                            padding: 20px;
                            max-width: 95%;
                            max-height: 95%;
                        }}
                        #battle_chart {{
                            margin: 0 auto;
                        }}
                    </style>
                </head>
                <body>
                    <div class="page-container">
                        <div class="chart-container">
                            <div id="battle_chart">{battle_chart.to_html(include_plotlyjs=False, div_id="battle_chart", config={'displayModeBar': False})}</div>
                        </div>
                    </div>
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

    # 动态生成文件名
    data = visualizer.load_data(test_file)
    stock_name = "未知股票"
    if data and data.get('stocks'):
        # 修正：'name' 与 'basic_info' 同级
        stock_name = data['stocks'][0].get('name', '未知股票')

    output_html_file = f"{stock_name}_龙虎榜可视化测试报告.html"
    
    # 获取文件的绝对路径以便清晰展示
    output_html_path = os.path.abspath(output_html_file)
    
    print(f"📊 正在读取测试数据: {test_file}")
    print(f"🎨 生成可视化图表...")
    
    try:
        # 生成可视化报告
        visualizer.generate_report(test_file, output_html=output_html_file)
        
        print("\n✅ 席位多空博弈图生成成功！")
        print(f"📁 HTML报告已保存: {output_html_path}")
        print("\n📋 生成的图表:")
        print("   🎯 席位多空博弈图 - 直观展示买卖方力量对比")
        print("   📊 买一/卖一、买二/卖二等席位对应关系")
        print("   🎨 按金额大小排序，买方红色，卖方绿色")
        print("   📊 包含完整的关键指标信息")
        print("\n🎉 龙虎榜席位可视化功能运行良好！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        print("请检查数据文件格式和依赖库是否正确")
