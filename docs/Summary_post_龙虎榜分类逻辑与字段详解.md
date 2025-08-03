# 龙虎榜AI分析系统：分类逻辑与字段详解

## 📋 概述

本文档详细阐述龙虎榜AI分析系统的核心分类逻辑和数据字段提取机制，为理解系统的数据处理和分类算法提供完整的技术参考。

## 🎯 核心分类体系

### 1. 情绪分类逻辑

#### 主分类维度
系统基于`market_sentiment.level`字段进行核心情绪分类：

```python
# 情绪分类的核心代码逻辑：market_sentiment_stats.py:200
level = market_sentiment.get('level', 'Unknown')

# 三大情绪分类
情绪分类映射 = {
    '亢奋': '🚀',  # 个股情绪高涨，多头氛围浓厚
    '恐慌': '😰',  # 个股恐慌情绪，空头压制明显  
    '分歧': '🤔'   # 多空博弈激烈，个股分歧严重
}
```

#### 分类特征描述

| 情绪级别 | 特征描述 | 市场表现 | 风险评级 |
|---------|---------|---------|---------|
| 🚀 **亢奋** | 个股情绪高涨，多头氛围浓厚 | 资金涌入，价格上涨 | 中等偏高 |
| 😰 **恐慌** | 个股恐慌情绪，空头压制明显 | 恐慌抛售，价格下跌 | 高风险 |
| 🤔 **分歧** | 多空博弈激烈，个股分歧严重 | 震荡整理，方向不明 | 高波动 |
| ❓ **Unknown** | 情绪级别未识别 | 数据异常或待分析 | 未知 |

### 2. 参与者分类逻辑

#### 核心参与者识别算法 (`analyze_core_players` 函数)

```python
# 参与者分类数据结构：market_sentiment_stats.py:81-85
players = {
    'institutions': {'buy': False, 'sell': False},    # 机构参与情况
    'famous_traders': {'buy': [], 'sell': []},        # 知名游资列表
    'summary': ''                                     # 参与者摘要
}
```

#### 机构投资者识别逻辑

```python
# 机构识别：market_sentiment_stats.py:92-93, 102-103
if player_type == '机构':
    players['institutions']['buy'] = True   # 机构买入标记
    players['institutions']['sell'] = True  # 机构卖出标记

# 机构参与情况分类：market_sentiment_stats.py:111-116
机构参与模式 = {
    "机构(买卖)": "机构同时买卖，可能调仓或对冲",
    "机构(买)":   "机构净买入，看好后市发展", 
    "机构(卖)":   "机构净卖出，可能获利了结"
}
```

#### 知名游资识别逻辑

```python
# 知名游资识别：market_sentiment_stats.py:94-95, 104-105
elif player_type == '知名游资' and player_name:
    players['famous_traders']['buy'].append(player_name)   # 买方游资
    players['famous_traders']['sell'].append(player_name)  # 卖方游资

# 注：知名游资的识别完全基于数据中的player_type字段，无需硬编码席位库
```

#### 游资行为模式分类

```python
# 游资博弈分析：market_sentiment_stats.py:122-130
游资行为模式 = {
    "单一游资做T": f"{trader_name}(做T)",           # 同一游资当日买卖
    "多游资博弈": f"{trader_names}(博弈)",          # 多个游资对决
    "游资集中买入": f"{trader_names}(买)",          # 游资看多
    "游资集中卖出": f"{trader_names}(卖)"           # 游资看空
}
```

#### 参与者摘要生成算法

```python
# 摘要生成逻辑：market_sentiment_stats.py:146
summary_generation_logic = {
    "机构 vs 游资": "机构(买) vs 淮海,佛山(博弈)",
    "纯机构": "机构(买卖)",
    "纯游资": "佛山,淮海(博弈)", 
    "散户为主": "普通散户"
}

# 最终摘要格式
players['summary'] = " vs ".join(summary_parts) if summary_parts else "普通散户"
```

## 📊 数据字段提取体系

### 1. 股票基础信息字段

```python
# 股票基本信息提取：market_sentiment_stats.py:190-194
stock_basic_fields = {
    'name': stock_info.get('name', 'Unknown'),           # 股票名称
    'ts_code': stock_info.get('ts_code', 'Unknown'),     # 交易代码  
    'trade_date': stock_info.get('trade_date', date_item) # 交易日期
}
```

| 字段名 | 数据路径 | 类型 | 描述 | 示例 |
|-------|---------|------|------|------|
| `name` | `data.stock_info.name` | String | 股票名称 | "贵州茅台" |
| `ts_code` | `data.stock_info.ts_code` | String | 交易代码 | "600519.SH" |
| `trade_date` | `data.stock_info.trade_date` | String | 交易日期 | "20250702" |

### 2. 市场情绪分析字段

```python
# 市场情绪数据提取：market_sentiment_stats.py:196-201
sentiment_fields = {
    'level': market_sentiment.get('level', 'Unknown'),              # 情绪级别
    'interpretation': market_sentiment.get('interpretation', '')     # 情绪解释
}
```

| 字段名 | 数据路径 | 类型 | 描述 | 可能值 |
|-------|---------|------|------|-------|
| `level` | `data.analysis_report.overall_assessment.market_sentiment.level` | String | 情绪级别 | "亢奋"/"恐慌"/"分歧" |
| `interpretation` | `data.analysis_report.overall_assessment.market_sentiment.interpretation` | String | 情绪解释说明 | "市场情绪高涨，多头氛围浓厚" |

### 3. 综合评估字段

```python
# 综合评估数据提取：market_sentiment_stats.py:203-205
assessment_fields = {
    'verdict': overall_assessment.get('verdict', 'Unknown')           # 分析结论
}
```

| 字段名 | 数据路径 | 类型 | 描述 | 取值范围 |
|-------|---------|------|------|---------|
| `verdict` | `data.analysis_report.overall_assessment.verdict` | String | 最终分析结论 | "看多"/"看空"/"中性" |

### 4. K线行为分析字段

```python
# K线行为分析：market_sentiment_stats.py:207-209
kline_fields = {
    'behavior_type': kline_behavior_analysis.get('behavior_type', 'Unknown')  # K线行为类型
}
```

| 字段名 | 数据路径 | 类型 | 描述 | 典型值 |
|-------|---------|------|------|-------|
| `behavior_type` | `data.analysis_report.kline_behavior_analysis.behavior_type` | String | K线技术形态 | "高位出货"/"低位吸筹"/"震荡整理" |

### 5. 核心参与者字段

```python
# 核心参与者数据提取：market_sentiment_stats.py:211-214
participant_fields = {
    'buying_force': key_forces.get('buying_force', []),    # 买方力量数组
    'selling_force': key_forces.get('selling_force', [])   # 卖方力量数组
}
```

#### 买卖方力量数据结构

```python
# 买卖方力量的数据结构
force_structure = {
    'player_type': '机构' | '知名游资' | '普通散户',    # 参与者类型
    'player_name': 'String',                         # 参与者具体名称
    'amount': 'Float',                              # 交易金额
    'percentage': 'Float'                           # 占比
}
```

### 6. 综合股票条目字段

```python
# 最终股票条目数据结构：market_sentiment_stats.py:223-234
stock_entry = {
    'name': stock_name,                    # 股票名称
    'ts_code': ts_code,                    # 交易代码
    'trade_date': trade_date,              # 交易日期
    'file': json_file,                     # 原始文件名
    'verdict': verdict,                    # 分析结论
    'interpretation': interpretation,       # 情绪解释
    'behavior_type': behavior_type,        # K线行为类型
    'core_players': core_players,          # 核心参与者分析结果
    'title': stock_title                   # 模拟生成的标题（通过generate_stock_title函数生成，用于展示分类能力）
}
```

## 🏗️ 数据流处理逻辑

### 1. 文件扫描与过滤

```python
# 目录扫描逻辑：market_sentiment_stats.py:165-172
scanning_logic = {
    "目录筛选": "只处理8位数字命名的日期目录",
    "日期过滤": "当前只处理20250702数据",
    "文件匹配": "只处理*_analysis.json文件"
}

# 实际代码
date_dirs = [item for item in os.listdir(current_dir) 
             if os.path.isdir(os.path.join(current_dir, item)) 
             and item.isdigit() and len(item) == 8]
target_date = "20250702"
```

### 2. 数据统计结构

```python
# 统计数据结构：market_sentiment_stats.py:157
daily_stats = defaultdict(lambda: defaultdict(list))
# 结构：{date: {level: [stock_list]}}

# 示例数据结构
statistics_structure = {
    "20250702": {
        "亢奋": [stock_entry1, stock_entry2, ...],
        "恐慌": [stock_entry3, stock_entry4, ...], 
        "分歧": [stock_entry5, stock_entry6, ...]
    }
}
```

### 3. 异常处理机制

```python
# 错误处理：market_sentiment_stats.py:240-245
error_handling = {
    "JSON解析失败": "记录文件路径和错误信息",
    "字段缺失": "使用默认值避免程序崩溃",
    "类型错误": "继续处理其他文件"
}

# 错误记录结构
error_files.append({
    'file': file_path,
    'error': str(e)
})
```

## 🎨 标题生成逻辑（模拟生成）

### 标题生成函数（generate_stock_title）

系统通过 `generate_stock_title` 函数模拟生成标题，用于展示系统的分类能力。该函数根据情绪级别、参与者类型和行为特征生成模拟的个性化标题。

**注意**：这些标题是系统自动生成的模拟标题，不是从原始数据中提取的。主要用于：
1. 展示系统对数据的理解和分类能力
2. 提供更直观的信息展示
3. 方便用户快速理解个股特征

```python
# 标题生成核心逻辑：market_sentiment_stats.py:31-76
def generate_stock_title(stock_name, level, verdict, behavior_type, core_players, ts_code):
    """生成个股分析标题"""
    # 情绪emoji映射
    emoji_map = {
        '亢奋': '🚀',
        '恐慌': '😰',
        '分歧': '🤔'
    }
    
    emotion_emoji = emoji_map.get(level, '📊')
    players_summary = core_players.get('summary', '普通散户')
```

### 标题生成决策树

```python
# 标题生成决策逻辑：market_sentiment_stats.py:46-70
title_generation_logic = {
    # 1. 机构+游资博弈场景
    "机构+游资博弈": {
        "条件": "'机构' in players_summary and any(trader in players_summary for trader in ['买', '卖', '博弈'])",
        "模板": f"{emotion_emoji} {stock_name}：机构游资激烈博弈，{behavior_type}态势明确"
    },
    
    # 2. 纯机构参与场景
    "机构买入": {
        "条件": "'机构' in players_summary and '买' in players_summary",
        "模板": f"{emotion_emoji} {stock_name}：机构重金抄底，{behavior_type}信号强烈"
    },
    "机构卖出": {
        "条件": "'机构' in players_summary and not '买' in players_summary",
        "模板": f"{emotion_emoji} {stock_name}：机构大举减仓，{behavior_type}趋势确立"
    },
    
    # 3. 知名游资参与场景
    "游资博弈": {
        "条件": "any(famous_trader in players_summary for famous_trader in ['佛山', '淮海', '东莞', '华鑫', '光大']) and '博弈' in players_summary",
        "模板": f"{emotion_emoji} {stock_name}：知名游资对决升级，{behavior_type}成关键"
    },
    "游资买入": {
        "条件": "知名游资存在 and '买' in players_summary",
        "模板": f"{emotion_emoji} {stock_name}：游资大佬重仓出击，{behavior_type}爆发在即"
    },
    "游资卖出": {
        "条件": "知名游资存在 and not '买' in players_summary",
        "模板": f"{emotion_emoji} {stock_name}：游资高位派发，{behavior_type}风险加剧"
    },
    
    # 4. 散户为主场景（根据情绪级别区分）
    "散户亢奋": {
        "条件": "level == '亢奋' and 无机构无知名游资",
        "模板": f"{emotion_emoji} {stock_name}：散户情绪高涨，{behavior_type}值得关注"
    },
    "散户恐慌": {
        "条件": "level == '恐慌' and 无机构无知名游资",
        "模板": f"{emotion_emoji} {stock_name}：恐慌抛售加剧，{behavior_type}底部显现"
    },
    "散户分歧": {
        "条件": "level == '分歧' and 无机构无知名游资",
        "模板": f"{emotion_emoji} {stock_name}：多空分歧严重，{behavior_type}方向待定"
    }
}
```

### 标题链接生成

```python
# 生成文件链接：market_sentiment_stats.py:73-76
link_url = f"./analysis/{ts_code}_analysis.html"
# 返回Markdown链接格式
return f"[{title}]({link_url})"
```

### 模拟标题的作用

1. **信息整合**：将股票名称、情绪级别、K线形态、参与者信息整合成一句话
2. **快速理解**：帮助用户快速理解该股票的核心特征
3. **分类展示**：体现系统对不同类型股票的分类和理解能力
4. **用户友好**：比单纯的数据字段更加直观易懂

**重要说明**：所有标题都是基于提取的数据字段（情绪级别、参与者、K线形态等）模拟生成的，不是原始数据中的字段。

## 📈 统计分析逻辑

### 1. 情绪分布统计

```python
# 按情绪级别统计：market_sentiment_stats.py:277
sorted_levels = sorted(date_stats.items(), key=lambda x: len(x[1]), reverse=True)

# 统计指标
statistics_metrics = {
    "情绪占比": "(len(stocks) / daily_total * 100)",
    "代表股票": "stocks[:3]",  # 取前3只代表股票
    "主导情绪": "sorted_levels[0][0]"  # 数量最多的情绪
}
```

### 2. 市场情绪判断

```python
# 市场整体情绪判断：market_sentiment_stats.py:412-423
market_mood_logic = {
    "亢奋主导且>50%": "个股情绪普遍高涨，多头氛围浓厚",
    "恐慌主导且>40%": "个股恐慌情绪蔓延，空头压制明显", 
    "分歧主导": "个股分歧严重，多空博弈激烈",
    "其他情况": "个股情绪相对均衡"
}

# 风险等级评估
risk_assessment = {
    "亢奋主导": "中等偏高",
    "恐慌主导": "高风险",
    "分歧主导": "高波动", 
    "均衡状态": "中等"
}
```

## 🔧 技术实现要点

### 1. 内存优化策略

```python
# 使用defaultdict避免KeyError并优化内存分配
from collections import defaultdict

daily_stats = defaultdict(lambda: defaultdict(list))
all_levels = defaultdict(int)
```

### 2. 字符编码处理

```python
# 确保中文字符正确处理
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
```

### 3. 数据验证

```python
# 字段存在性验证
stock_name = stock_info.get('name', 'Unknown')
level = market_sentiment.get('level', 'Unknown')
```

## 📱 移动端报告生成功能

### save_mobile_version 函数

系统新增了专门为移动端优化的报告生成功能，通过 `save_mobile_version` 函数实现。

```python
# 移动端报告生成函数：market_sentiment_stats.py:348-488
def save_mobile_version(daily_stats, total_stocks):
    """保存移动端友好的统计结果到Markdown文件"""
    output_file = f"每日汇总帖子_mobile.md"
```

### 移动端优化特点

1. **简化表格结构**
   ```python
   # 情绪分布表格（简化版）：market_sentiment_stats.py:375-390
   md_content.append("| 情绪 | 数量 | 占比 |")
   md_content.append("|------|------|------|")
   # 去掉了"代表个股"列，让表格更紧凑
   ```

2. **卡片式个股展示**
   ```python
   # 移动端个股展示格式：market_sentiment_stats.py:459-464
   md_content.append(f"{title_link}  ")
   md_content.append(f"**结论**: {verdict} | **形态**: {behavior_type}  ")
   md_content.append(f"**参与者**: {players_summary}")
   md_content.append("")
   md_content.append("---")
   ```

3. **数量限制与提示**
   ```python
   # 只显示前10只股票：market_sentiment_stats.py:439
   display_count = min(10, len(stocks))
   
   # 超出部分提示：market_sentiment_stats.py:467-470
   if len(stocks) > display_count:
       remaining = len(stocks) - display_count
       md_content.append(f"> 注：为节省空间，其余{remaining}只{level}情绪个股请在GushenAI中查看完整表格")
   ```

4. **标题去emoji处理**
   ```python
   # 提取标题文本并去掉emoji：market_sentiment_stats.py:449-455
   if '[' in title and ']' in title:
       title_parts = title.split(']')[0][1:].split(' ', 1)
       if len(title_parts) > 1 and title_parts[0] in ['🚀', '😰', '🤔']:
           clean_title = title_parts[1]
       else:
           clean_title = title_parts[0] if title_parts else stock['name']
       title_link = f"[**{clean_title}**](./analysis/{stock['ts_code']}_analysis.html)"
   ```

### 移动端报告结构

```markdown
# 📊 龙虎榜每日分析汇总

## 📅 2025-07-02 龙虎榜分析

### 情绪分布
| 情绪 | 数量 | 占比 |

### 🎯 关键洞察
**主导情绪**: 亢奋 (40只, 58.8%)  
**整体特征**: 个股情绪普遍高涨，多头氛围浓厚  
**风险等级**: 中等偏高

## 🚀 亢奋情绪个股 (40只)

[**大烨智能：机构游资激烈博弈，趋势加速态势明确**](./analysis/300670.SZ_analysis.html)  
**结论**: 多方获胜 | **形态**: 趋势加速  
**参与者**: 机构(卖) vs 量化打板,瑞鹤仙(博弈)

---

### 更多股票...
> 注：为节省空间，其余30只亢奋情绪个股请在GushenAI中查看完整表格
```

## 📋 字段映射总表

| 系统内部字段 | JSON数据路径 | 数据类型 | 用途 | 默认值 |
|-------------|-------------|---------|------|--------|
| `name` | `stock_info.name` | String | 股票名称显示 | "Unknown" |
| `ts_code` | `stock_info.ts_code` | String | 股票标识与链接生成 | "Unknown" |
| `trade_date` | `stock_info.trade_date` | String | 时间维度分组 | 当前处理日期 |
| `level` | `overall_assessment.market_sentiment.level` | String | **主分类依据** | "Unknown" |  
| `interpretation` | `overall_assessment.market_sentiment.interpretation` | String | 情绪解释说明 | "" |
| `verdict` | `overall_assessment.verdict` | String | 分析结论 | "Unknown" |
| `behavior_type` | `kline_behavior_analysis.behavior_type` | String | 技术形态 | "Unknown" |
| `buying_force` | `key_forces.buying_force` | Array | 买方参与者分析 | [] |
| `selling_force` | `key_forces.selling_force` | Array | 卖方参与者分析 | [] |

## 📄 输出文件格式

### 1. PC端完整版报告（已停用）
```python
# 原save_to_file函数生成：market_sentiment_stats.py:491-617
output_file = f"lhb_daily_analysis_summary_{timestamp}.md"
# 包含完整表格格式，所有股票详情
```

### 2. 移动端优化版报告（当前使用）
```python
# save_mobile_version函数生成：market_sentiment_stats.py:348-488
output_file = f"每日汇总帖子_mobile.md"
# 特点：
# - 固定文件名，方便自动化处理
# - 卡片式布局，移动端友好
# - 限制每个情绪级别显示10只股票
# - 标题直接可点击跳转
```

## 🚀 主函数逻辑

### 更新后的执行流程

```python
# 主函数：market_sentiment_stats.py:620-636
def main():
    """主函数"""
    # 1. 扫描并统计
    daily_stats, total_stocks, error_files = scan_market_sentiment_levels()
    
    # 2. 显示结果
    display_statistics(daily_stats, total_stocks, error_files)
    
    # 3. 保存到文件
    if total_stocks > 0:
        # 只生成移动端版报告
        save_mobile_version(daily_stats, total_stocks)
```

### 关键变化
1. **移除了PC端报告生成**：不再调用 `save_to_file()`
2. **专注移动端优化**：只生成移动端友好的报告格式
3. **固定输出文件名**：便于自动化集成和发布

## 🎯 分类逻辑总结

系统采用**多维度分类体系**：

1. **主分类**：基于`market_sentiment.level`的三元情绪分类
2. **子分类**：基于核心参与者的机构/游资/散户分类  
3. **统计分类**：按日期、占比、数量进行汇总分类
4. **输出分类**：按风险等级、市场特征进行结果分类

整个系统通过**字段提取→参与者分析→情绪分类→统计汇总→移动端优化输出**的完整数据流，实现对龙虎榜数据的智能化分类和分析。

## 🔄 版本更新说明

### v2.0 更新内容（2025-08-03）
1. **新增移动端报告生成功能**：`save_mobile_version` 函数
2. **优化标题生成逻辑**：去除emoji，适配移动端显示
3. **更新主函数**：只生成移动端版本报告
4. **修改提示文字**：从"PC端"改为"GushenAI"

### v1.1 原始版本（2025-07-30）
- 初始版本，包含PC端完整报告生成功能

---

*本文档详细阐述了龙虎榜AI系统的分类逻辑核心机制，为系统维护、扩展和优化提供技术参考。*

*文档版本：v2.0*  
*更新时间：2025-08-03*