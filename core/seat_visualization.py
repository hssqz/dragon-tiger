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
        # GushenAI 设计语言颜色方案 + 中国股市传统颜色逻辑
        self.colors = {
            'buy': '#FF4444',      # 红色 - 买入/多方（中国股市传统）
            'sell': '#00AA66',     # 绿色 - 卖出/空方（中国股市传统）
            'up': '#FF4444',       # 红色 - 上涨
            'down': '#00AA66',     # 绿色 - 下跌
            'positive': '#FF4444', # 红色 - 正值
            'negative': '#00AA66', # 绿色 - 负值
            'background': '#FAFBFC', # GushenAI 浅底色
            'text': '#1F2937',     # 深灰文字
            'grid': '#E5E7EB',     # 网格线
            'highlight': '#EAEFFB', # GushenAI 高亮辅色
            'accent': '#356BFD',   # GushenAI 主色蓝（用于装饰）
            'secondary': '#FB9D0E'  # GushenAI 辅色橙（用于装饰）
        }
        self.type_colors = {
            '量化': '#356BFD',      # GushenAI 主色蓝
            '机构': '#FA8072',      # GushenAI 辅色橙
            '知名游资': '#8B5CF6',  # 紫色变种
            '普通席位': '#6B7280'   # 中性灰
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

    def format_amount_display(self, amount: float):
        if amount > 10**4:
            return str(round(float(amount) / 10**4, 2)) + '亿元'
        elif amount > 1:
            return str(round(float(amount), 2)) + '万元'
        else:
            return str(round(float(amount) * 10**4, 2)) + '元'

    def get_player_type_icon(self, player_type: str) -> str:
        """获取席位类型对应的文本图标"""
        type_map = {
            '量化': f"<span style='color:{self.type_colors['量化']}'><b>[量]</b></span>",
            '机构': f"<span style='color:{self.type_colors['机构']}'><b>[机]</b></span>",
            '知名游资': f"<span style='color:{self.type_colors['知名游资']}'><b>[游]</b></span>",
            '普通席位': f"<span style='color:{self.colors['text']}'>[普]</span>"
        }
        return type_map.get(player_type, f"<span style='color:{self.colors['text']}'>[普]</span>")

    def get_player_tag(self, player_info: Dict) -> str:
        """获取游资标签"""
        name = player_info.get('name', '未知')
        player_type = player_info.get('type', '普通席位')
        styles = player_info.get('style', [])

        if name != '未知机构' and name != '未知':
            return f"<span style='color:{self.colors['accent']}'><b>【{name}】</b></span>"
        elif '知名游资' in player_type:
            return f"<span style='color:#8B5CF6'><b>【知名游资】</b></span>"
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
        sell_amounts_display = []
        buy_names = []
        buy_amounts = []
        buy_amounts_display = []

        for i in range(max_seats):
            if i == 0:
                position_labels.append("<b>买一/卖一</b>")
            elif i == 1:
                position_labels.append("<b>买二/卖二</b>")
            elif i == 2:
                position_labels.append("<b>买三/卖三</b>")
            elif i == 3:
                position_labels.append("<b>买四/卖四</b>")
            elif i == 4:
                position_labels.append("<b>买五/卖五</b>")
            else:
                # 对于可能的更多席位，使用数字
                chinese_nums = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                if i+1 < len(chinese_nums):
                    position_labels.append(f"<b>买{chinese_nums[i+1]}/卖{chinese_nums[i+1]}</b>")
                else:
                    position_labels.append(f"<b>买{i+1}/卖{i+1}</b>")

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
                sell_amounts_display.append(self.format_amount_display(net_amount))
            else:
                sell_names.append("")
                sell_amounts.append(0)
                sell_amounts_display.append("")

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
                buy_amounts_display.append(self.format_amount_display(net_amount))
            else:
                buy_names.append("")
                buy_amounts.append(0)
                buy_amounts_display.append("")

        # 创建卖方柱状图（左侧，绿色）
        fig.add_trace(go.Bar(
            y=position_labels,
            x=sell_amounts,
            orientation='h',
            name="卖方席位",
            marker=dict(
                color=self.colors['sell'],  # GushenAI 绿色
                line=dict(color='white', width=1),
                opacity=0.9  # 添加透明度
            ),
            text=[f"<b>{name}</b><br><b>{amount_display}</b>"
                  for name, amount_display in zip(sell_names, sell_amounts_display)],
            textposition='outside',
            textfont=dict(size=15, color=self.colors['text'], family="'PingFang SC', 'Microsoft YaHei', sans-serif"),
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
                color=self.colors['buy'],  # GushenAI 红色
                line=dict(color='white', width=1),
                opacity=0.9  # 添加透明度
            ),
            text=[f"<b>{name}</b><br><b>{amount_display}</b>"
                  for name, amount_display in zip(buy_names, buy_amounts_display)],
            textposition='outside',
            textfont=dict(size=15, color=self.colors['text'], family="'PingFang SC', 'Microsoft YaHei', sans-serif"),
            hoverinfo='none',
            customdata=buy_names
        ))

        # 添加中轴线
        fig.add_vline(x=0, line_width=3, line_color=self.colors['text'])

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
        stock_name = stock_data.get('name', '')

        # 更新布局
        fig.update_layout(
            title=dict(
                text=f"<b>({stock_code}) {stock_name} - 龙虎榜多空博弈席位图</b>",
                x=0.5,
                y=0.92,
                font=dict(size=25, color=self.colors['accent'], family="'PingFang SC', 'Microsoft YaHei', sans-serif")
            ),
            xaxis=dict(
                title=dict(text="<b style='color:" + self.colors['text'] + "'>资金流向 (万元)</b>"),
                showgrid=True,
                gridcolor=self.colors['grid'],
                zeroline=True,
                zerolinecolor=self.colors['text'],
                zerolinewidth=3,
                tickfont=dict(size=15, family="'PingFang SC', 'Microsoft YaHei', sans-serif", color=self.colors['text']),
                range=[-max_amount * 1.3, max_amount * 1.3],  # 设置对称范围
                fixedrange=True,
                showticklabels=False,
            ),
            yaxis=dict(
                title=dict(text="<b style='color:" + self.colors['text'] + "'>席位排名</b>"),
                showgrid=True,
                gridcolor=self.colors['grid'],
                tickfont=dict(size=15, family="'PingFang SC', 'Microsoft YaHei', sans-serif", color=self.colors['secondary']),
                categoryorder='array',
                categoryarray=position_labels[::-1],  # 反转显示顺序，买一卖一在顶部
                fixedrange=True
            ),
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            height=700,
            width=max(1200, min(2200, int(max_amount * 3 + 800))),  # 根据最大金额动态调整宽度
            margin=dict(l=100, r=100, t=160, b=100),
            font=dict(family="'PingFang SC', 'Microsoft YaHei', sans-serif", color=self.colors['text']),
            barmode='overlay',  # 重叠模式
            showlegend=False
        )



        # 添加关键指标注释 - 第一行
        # 涨跌幅颜色判断
        try:
            pct_value = float(pct_change.replace('%', '')) if pct_change else 0
            pct_color = self.colors['positive'] if pct_value > 0 else self.colors['negative'] if pct_value < 0 else 'black'
        except (ValueError, AttributeError):
            pct_color = 'black'

        fig.add_annotation(
            text=f"<b>收盘价</b>: {close_price}\t\t\t<b>涨跌幅</b>: <span style='color:{pct_color}'>{pct_change}</span>\t\t\t<b>换手率</b>: {turnover_rate}\t\t\t<b>成交额</b>: {amount}",
            xref="paper", yref="paper",
            x=0.5, y=1.16,
            showarrow=False,
            font=dict(size=15, color=self.colors['text'], family="'PingFang SC', 'Microsoft YaHei', sans-serif"),
            align="center"
        )

        # 添加关键指标注释 - 第二行
        # 龙虎榜净额颜色判断
        try:
            # 清理货币字符串
            clean_net = net_amount.replace('万', '').replace('亿', '').replace('-', '').replace('元', '').replace(',', '')
            net_value = float(clean_net) if clean_net else 0
            net_color = self.colors['positive'] if not net_amount.startswith('-') and net_value > 0 else self.colors['negative'] if net_amount.startswith('-') else 'black'
        except (ValueError, AttributeError):
            net_color = 'black'

        # 买入占比颜色判断
        try:
            buy_ratio_value = float(buy_ratio.replace('%', '')) if buy_ratio else 0
            buy_color = self.colors['positive'] if buy_ratio_value > 0 else self.colors['negative'] if buy_ratio_value < 0 else 'black'
        except (ValueError, AttributeError):
            buy_color = 'black'

        # 卖出占比颜色判断
        try:
            sell_ratio_value = float(sell_ratio.replace('%', '')) if sell_ratio else 0
            sell_color = self.colors['positive'] if sell_ratio_value > 0 else self.colors['negative'] if sell_ratio_value < 0 else 'black'
        except (ValueError, AttributeError):
            sell_color = 'black'

        fig.add_annotation(
            text=f"<b>龙虎榜净额</b>: <span style='color:{net_color}'>{net_amount} ({net_rate})</span>\t\t\t<b>买入占比</b>: <span style='color:{buy_color}'>{buy_ratio}</span>\t\t\t<b>卖出占比</b>: <span style='color:{sell_color}'>{sell_ratio}</span>\t\t\t<b>流通市值</b>: {float_values}",
            xref="paper", yref="paper",
            x=0.5, y=1.11,
            showarrow=False,
            font=dict(size=15, color=self.colors['text'], family="'PingFang SC', 'Microsoft YaHei', sans-serif"),
            align="center"
        )

        # 添加买卖方区域标识
        fig.add_annotation(
            x=max_amount * 0.7,
            y=len(position_labels) - 0.3,
            text="<b>买方席位</b>",
            showarrow=True,
            arrowhead=2,
            arrowcolor=self.colors['buy'],
            font=dict(size=16, color=self.colors['buy'], family="'PingFang SC', 'Microsoft YaHei', sans-serif"),
            bgcolor=f"rgba(255, 68, 68, 0.1)",  # 红色透明背景
            bordercolor=self.colors['buy'],
            borderwidth=2
        )

        fig.add_annotation(
            x=-max_amount * 0.7,
            y=len(position_labels) - 0.3,
            text="<b>卖方席位</b>",
            showarrow=True,
            arrowhead=2,
            arrowcolor=self.colors['sell'],
            font=dict(size=16, color=self.colors['sell'], family="'PingFang SC', 'Microsoft YaHei', sans-serif"),
            bgcolor=f"rgba(0, 170, 102, 0.1)",  # 绿色透明背景
            bordercolor=self.colors['sell'],
            borderwidth=2
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
        # battle_chart.write_image(
        #     'tmp.png',
        #     format='png',
        #     width=battle_chart.layout.width,
        #     height=battle_chart.layout.height
        # )

        # 显示图表（禁用交互）
        # battle_chart.show(config={'displayModeBar': False})

        # 保存HTML报告
        if output_html:
            with open(output_html, 'w', encoding='utf-8') as f:
                # 格式化HTML文件标题
                stock_code = stock_data.get('ts_code', '').split('.')[0] if stock_data.get('ts_code') else ''
                stock_name = basic_info.get('name', '')
                html_title = f"({stock_code}) {stock_name} - 龙虎榜多空博弈席位图"

                # 简化图表渲染，避免复杂的字符串操作
                chart_html = battle_chart.to_html(include_plotlyjs=False, div_id="battle_chart", config={'displayModeBar': False, 'responsive': True})

                f.write(f"""
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{html_title}</title>

                    <!-- TailwindCSS 3.0+ -->
                    <script src="https://cdn.tailwindcss.com"></script>
                    <script>
                        tailwind.config = {{
                            theme: {{
                                extend: {{
                                    colors: {{
                                        'gushen': {{
                                            'primary': '#356BFD',     // GushenAI 主色蓝
                                            'accent': '#FB9D0E',      // GushenAI 辅色橙
                                            'light': '#EAEFFB',       // GushenAI 浅色
                                            'bg': '#FAFBFC',          // GushenAI 背景色
                                            'buy': '#FF4444',         // 红色买方
                                            'sell': '#00AA66'         // 绿色卖方
                                        }}
                                    }},
                                    fontFamily: {{
                                        'sans': ["'PingFang SC'", "'Microsoft YaHei'", 'sans-serif']
                                    }}
                                }}
                            }}
                        }}
                    </script>

                    <!-- Plotly.js -->
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

                    <!-- Font Awesome -->
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

                    <style>
                        body {{
                            background: linear-gradient(135deg, #FAFBFC 0%, #EAEFFB 100%);
                        }}
                        .gushen-gradient {{
                            background: linear-gradient(135deg, rgba(53, 107, 253, 0.1) 0%, rgba(53, 107, 253, 0.05) 100%);
                        }}
                        .gushen-shadow {{
                            box-shadow: 0 20px 25px -5px rgba(53, 107, 253, 0.1), 0 10px 10px -5px rgba(53, 107, 253, 0.04);
                        }}
                        .animate-fade-in {{
                            animation: fadeIn 1s ease-in-out;
                        }}
                        .animate-slide-up {{
                            animation: slideUp 0.8s ease-out;
                        }}
                        @keyframes fadeIn {{
                            from {{ opacity: 0; }}
                            to {{ opacity: 1; }}
                        }}
                        @keyframes slideUp {{
                            from {{
                                opacity: 0;
                                transform: translateY(30px);
                            }}
                            to {{
                                opacity: 1;
                                transform: translateY(0);
                            }}
                        }}
                        .tech-glow {{
                            position: relative;
                        }}
                        .tech-glow::before {{
                            content: '';
                            position: absolute;
                            top: -2px;
                            left: -2px;
                            right: -2px;
                            bottom: -2px;
                            background: linear-gradient(45deg, rgba(255, 68, 68, 0.3), rgba(0, 170, 102, 0.3));
                            border-radius: inherit;
                            z-index: -1;
                            filter: blur(10px);
                            opacity: 0.7;
                        }}
                        .bg-gushen-buy {{ background-color: #FF4444; }}
                        .bg-gushen-sell {{ background-color: #00AA66; }}
                        .text-gushen-primary {{ color: #356BFD; }}
                        .text-gushen-accent {{ color: #FB9D0E; }}
                    </style>
                </head>
                <body class="min-h-screen font-sans text-gray-900">
                    <!-- 主容器 -->
                    <div class="min-h-screen flex flex-col items-center justify-center p-4 lg:p-8">
                        <!-- 顶部标题区域 -->
                        <div class="animate-fade-in text-center mb-8">
                            <div class="flex items-center justify-center mb-4">
                                <i class="fas fa-chart-line text-gushen-primary text-3xl mr-3"></i>
                                <h1 class="text-3xl lg:text-4xl font-bold text-gray-800">
                                    <span class="text-gushen-primary">Gushen AI</span> 龙虎榜分析
                                </h1>
                            </div>
                            <p class="text-lg text-gray-600 flex items-center justify-center">
                                <i class="fas fa-robot text-gushen-accent mr-2"></i>
                                <span class="font-semibold">AI驱动的智能投资决策平台</span>
                            </p>
                        </div>

                        <!-- 图表容器 -->
                        <div class="animate-slide-up w-full max-w-7xl">
                            <div class="bg-white rounded-2xl gushen-shadow tech-glow gushen-gradient p-6 lg:p-8">
                                <!-- 图表标题栏 -->
                                <div class="flex items-center justify-between mb-6 pb-4 border-b border-gushen-light">
                                    <div class="flex items-center">
                                        <div class="bg-gushen-primary bg-opacity-10 rounded-lg p-3 mr-4">
                                            <i class="fas fa-balance-scale text-gushen-primary text-xl"></i>
                                        </div>
                                        <div>
                                            <h2 class="text-xl font-bold text-gray-800">{html_title}</h2>
                                            <p class="text-sm text-gray-500 mt-1">
                                                <i class="fas fa-clock mr-1 text-gushen-primary"></i>
                                                <span class="text-gushen-primary font-semibold">实时数据分析</span> · <span class="text-gushen-accent font-semibold">AI智能解读</span>
                                            </p>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-3">
                                        <div class="bg-gushen-primary bg-opacity-10 rounded-lg px-3 py-2">
                                            <span class="text-gushen-primary font-semibold text-sm">
                                                <i class="fas fa-users mr-1"></i>
                                                <span class="text-gushen-primary font-bold">席位博弈</span>
                                            </span>
                                        </div>
                                        <div class="bg-gushen-accent bg-opacity-10 rounded-lg px-3 py-2">
                                            <span class="text-gushen-accent font-semibold text-sm">
                                                <i class="fas fa-chart-bar mr-1"></i>
                                                <span class="text-gushen-accent font-bold">资金流向</span>
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <!-- 主图表区域 -->
                                <div id="battle_chart" class="w-full">
                                    {chart_html}
                                </div>

                                <!-- 底部说明区域 -->
                                <div class="mt-6 pt-4 border-t border-gushen-light">
                                    <div class="flex flex-wrap items-center justify-between text-sm text-gray-600">
                                        <div class="flex items-center space-x-4">
                                            <div class="flex items-center">
                                                <div class="w-4 h-4 bg-gushen-buy rounded mr-2 opacity-90"></div>
                                                <span><strong class="text-gushen-primary">买方席位</strong> - <span class="text-gushen-accent">主力资金流入</span>（红色表示多方）</span>
                                            </div>
                                            <div class="flex items-center">
                                                <div class="w-4 h-4 bg-gushen-sell rounded mr-2 opacity-90"></div>
                                                <span><strong class="text-gushen-primary">卖方席位</strong> - <span class="text-gushen-accent">资金流出压力</span>（绿色表示空方）</span>
                                            </div>
                                        </div>
                                        <div class="flex items-center text-gray-500">
                                            <i class="fas fa-info-circle mr-1 text-gushen-primary"></i>
                                            <span><span class="text-gushen-accent font-semibold">数据来源：龙虎榜</span> | 由 <strong class="text-gushen-primary">Gushen AI</strong> 智能分析</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 底部品牌区域 -->
                        <div class="animate-fade-in mt-8 text-center">
                            <div class="flex items-center justify-center text-gray-500 text-sm">
                                <i class="fas fa-shield-alt text-gushen-primary mr-2"></i>
                                <span>Powered by <strong class="text-gushen-primary">Gushen AI</strong> · 智能投资新时代</span>
                            </div>
                        </div>
                    </div>

                    <script>
                        // 添加交互效果
                        document.addEventListener('DOMContentLoaded', function() {{
                            const chartContainer = document.querySelector('.tech-glow');
                            if (chartContainer) {{
                                chartContainer.addEventListener('mouseenter', function() {{
                                    this.style.transform = 'translateY(-5px)';
                                    this.style.transition = 'transform 0.3s ease';
                                }});
                                chartContainer.addEventListener('mouseleave', function() {{
                                    this.style.transform = 'translateY(0)';
                                }});
                            }}
                        }});
                    </script>
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
    test_file = "/Users/qishen-zhen/Cursor/dragon & tiger/core/test-seat-4.json"

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
