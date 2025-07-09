# 动态龙虎榜营销报告生成系统 - 设计方案 V1.0

## 1. 核心目标与理念

### 1.1 目标

摆脱当前固定的、基于模板的报告生成模式，引入大语言模型（LLM）作为核心决策引擎。系统将根据每日真实的市场数据，动态地创建报告的主题、分类和叙事角度，旨在最大化内容的营销吸引力和时效性。

### 1.2 核心理念

将LLM的角色从一个“内容填充者”提升为“**顶尖金融内容策略师**”。每天收盘后，LLM会分析当日的市场“战报”，并决定当天应该从哪些最引人入胜的角度去“讲故事”，从而实现报告的“**千日千面**”，让每一篇报告都独一无二且直击市场要害。

## 2. 系统工作流程

完整的自动化流程分为四个主要阶段：

![Workflow Diagram](placeholder_for_diagram)
*（后续可补充流程图）*

### 阶段一：数据分析 (现有流程)

- 保持现有数据流水线不变。
- 每日收盘后，系统照常运行，处理原始龙虎榜数据，生成所有上榜个股的深度分析文件（`analysis.json`）以及一份全局的摘要文件（`summary.json`）。

### 阶段二：动态策略生成 (LLM核心决策)

这是新增的核心步骤，负责定义当日报告的“灵魂”。

#### 2.1 LLM输入 (Input) - V2.0 增强版

- 从当日生成的 `summary.json` 文件中，提取 **增强后** 的 `summary_stats` 部分作为给LLM的输入。
- 这份输入从五个核心维度为LLM提供了一幅更完整、更立体的“市场全景图”。

**输入JSON示例:**
```json
{
  "trade_date": "20250703",
  "total_stocks": 69,
  "summary_stats": {
    "verdict_distribution": { "多方胜利": 7, "空方胜出": 6, "...": "..." },
    "average_confidence": 0.84,

    "kline_behavior_distribution": {
      "上涨中继": 15,
      "超跌反弹": 12,
      "趋势突破": 8,
      "高位滞涨": 5
    },

    "market_sentiment_distribution": {
      "亢奋": 40,
      "乐观": 15,
      "谨慎": 10,
      "恐慌": 4
    },

    "capital_confrontation_distribution": {
        "激烈": 25,
        "主力强力控盘": 10,
        "多方占优": 15,
        "空方占优": 12
    },

    "player_activity_summary": {
      "buy_side_appearances": {
        "机构": 22,
        "知名游资": 35 
      },
      "sell_side_appearances": {
        "机构": 18,
        "知名游资": 25
      }
    },

    "listing_reason_distribution": {
        "日涨幅偏离值达到7%": 20,
        "日换手率达到20%": 15,
        "日涨幅达到15%": 10
    }
  }
}
```
**输入维度解读**:
- **`verdict_distribution` (战局概览)**: 揭示当日多空双方的最终实力对比。
- **`average_confidence` (整体可信度)**: 代表当日分析结论的平均确定性。
- **`kline_behavior_distribution` (技术形态分布)**: 描绘出当日市场主流的技术形态剧本（如“超跌反弹”或“上涨中继”）。
- **`market_sentiment_distribution` (市场情绪温度)**: 反映了市场的真实情绪状态（如“亢奋”或“谨慎”）。
- **`capital_confrontation_distribution` (资金博弈强度)**: 刻画了资金的对抗激烈程度（如“激烈”或“主力控盘”）。
- **`player_activity_summary` (核心玩家动态)**: 统计了关键角色（机构、游资）的活跃度，揭示谁在主导市场。
- **`listing_reason_distribution` (上榜原因分布)**: 揭示了驱动当天市场热点的主要事件类型。

有了这份增强版的输入，LLM就能够洞察到更深层次的市场动态，从而制定出更精准、更具吸引力的内容策略。

#### 2.2 LLM输出 (Output)

- 要求LLM返回一个严格的、可供程序解析的JSON对象，作为后续步骤的“指令集”。
- 该JSON对象包含当日报告的**主题**和**具体的分类规则**。

**输出JSON示例:**
```json
{
  "daily_theme": "今日市场多头占据上风，但分歧依旧显著。部分个股上演激烈攻防战，超跌反弹成为重要机会点。",
  "categories": [
    {
      "name": "今日最强音：多头核心阵营",
      "description": "市场最强的力量！这些股票获得压倒性的多方资金支持，是今日行情的领涨核心。",
      "rules": [
        {
          "field": "overall_assessment.verdict",
          "operator": "in",
          "value": ["多方胜利", "多头胜出", "多方获胜", "多头获胜", "多头大胜"]
        },
        {
          "field": "overall_assessment.confidence_score",
          "operator": "gte",
          "value": 0.9
        }
      ]
    },
    {
      "name": "剧本杀：激烈交锋的阵地战",
      "description": "这里是资金博弈最前线！多空双方在此投入重兵激烈厮杀，每一次的微弱优势都可能预示着未来的方向。",
      "rules": [
        {
          "field": "overall_assessment.verdict",
          "operator": "in",
          "value": ["多方小胜", "空方略占优势", "多空持平"]
        }
      ]
    },
    {
      "name": "反转信号旗：超跌反弹先锋",
      "description": "机会在下跌中孕育。这些股票在连续回调后迎来强力资金抄底，技术形态与资金面形成共振。",
      "rules": [
        {
            "field": "kline_behavior_analysis.behavior_type",
            "operator": "eq",
            "value": "超跌反弹"
        },
        {
            "field": "overall_assessment.verdict",
            "operator": "not_in",
            "value": ["空方胜出", "空方胜利", "空方获胜", "空方大胜"]
        }
      ]
    }
  ]
}
```

**输出结构解析**:
- `daily_theme`: 当日报告的“开场白”，由LLM生成。
- `categories`: 一个数组，包含2-3个由LLM动态创建的分类。
    - `name`: 分类的营销标题。
    - `description`: 对分类的故事性描述。
    - `rules`: **指令核心**。定义了如何筛选股票的规则集。
        - `field`: `analysis.json` 中需要判断的字段路径。
        - `operator`: 筛选操作符 (`in`, `gte`, `lte`, `eq`, `not_in`, `contains`)。
        - `value`: 用于比较的值。

### 阶段三：规则解析与执行 (代码实现)

- 编写一个“规则引擎”模块。
- 该模块负责解析LLM返回的JSON指令集。
- 遍历当日所有上榜股票，读取各自的 `analysis.json` 文件。
- 针对每一支股票，应用 `rules` 进行逐条判断，将其归入满足条件的分类中。
- 可根据需要对每个分类内的股票进行排序（例如，按置信度或相关金额）。

### 阶段四：报告排版与生成

- 使用LLM在阶段二生成的 `daily_theme`, `categories.name`, `categories.description` 作为报告的框架。
- 将阶段三分类好的股票列表填充到对应的分类下。
- **(可选增强)** 对每个入选的股票，可再次调用LLM，输入其 `analysis.json` 的摘要，为其生成一句更具吸引力的“一句话亮点”。
- 最终，将所有内容组装成完整的Markdown营销报告。

## 3. 方案优势

1.  **策略智能化**: 从“报告生成器”升级为“**内容策略引擎**”。
2.  **营销效果最大化**: 每日报告都能量身定制，直击当天市场最核心、最吸引人的脉搏。
3.  **高度自动化**: 在提升内容质量的同时，进一步减少人工干预和模板维护成本。
4.  **可持续迭代**: `rules` 的字段和操作符可以不断扩展，使系统能力持续增强。 