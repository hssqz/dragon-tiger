# 设计方案：龙虎榜资金博弈分析模块 (混合增强版)

## 1. 核心目标 (升级)

您提出的"智能的本质是压缩"非常精准。我们的新目标是**将代码的精确性与LLM的洞察力相结合**，创造一个信息密度最高、同时又不失真的**"资金博弈概要 (FundingBattleSummary)"**。

我们将采用一种**代码-LLM混合增强**的新模式：
- **代码做"事实层"**：负责所有确定性的计算和数据结构化，确保100%的准确性。
- **LLM做"洞察层"**：将代码处理过的高质量"事实"作为输入，专注进行分析、提炼和总结，生成高价值洞察。

## 2. 混合分析流程：三阶段处理

我们将整个流程拆分为三个独立的阶段，实现逻辑的解耦和效率的最大化。


### **第一阶段：代码预处理 (事实层 - Fact Layer)**
- **执行者**: `funding_battle_builder.py` (纯代码)
- **输入**: 原始的 `test-seat.json`
- **任务**: 将原始数据转换为一个结构化的**中间层数据 `StructuredFacts`**。这一步负责所有基于规则的计算，确保数据的准确性和一致性。
- **输出**: `StructuredFacts` JSON 对象。它只包含计算好的数值和基础标签，不包含任何解释性文本。

### **第二阶段：LLM洞察增强 (洞察层 - Insight Layer)**
- **执行者**: `funding_battle_enricher.py` (调用LLM的模块)
- **输入**: `StructuredFacts` JSON 对象
- **任务**: 将精确的"事实"喂给LLM，让它专注进行**分析、推理、提炼和总结**，生成高信息密度的"洞察"字段。
- **输出**: 最终的、信息密度最高的 `FundingBattleSummary` JSON。

### **第三阶段：LLM叙事生成 (叙事层 - Narrative Layer)**
- **执行者**: `post_generator.py` (调用LLM的模块)
- **输入**: `FundingBattleSummary` JSON 对象
- **任务**: 基于高密度的情报，生成最终给用户看的、图文并茂的分析帖子。

---

## 3. 关键数据结构定义

### 3.1 `StructuredFacts` 结构 (代码层输出)

这是代码处理后的产物，是LLM进行分析的基石。它采用"摘要+附录"的模式，既包含高信息密度的**分析指标**，也保留了**未经修改的原始席位列表**，以供LLM随时查证细节。

```json
// 全新设计的 StructuredFacts - 细节与洞察并存
{
  "ts_code": "股票代码",
  "name": "股票名称",
  "raw_basic_info": { "..."}, // 保留原始基础信息
  "long_side_facts": {
    // ---- 洞察层：代码生成的分析指标 ----
    "total_amount_wan": 23700.0,
    "player_count": 5,
    "famous_player_count": 1,
    "concentration_metrics": { 
      "top1_pct": 27.4, "top2_pct": 50.2, "top5_pct": 100.0 
    },
    "contribution_by_type": { 
      "知名游资_net_wan": 4100.0, "普通席位_net_wan": 17800.0 
    },
    // ---- 细节层：未经修改的原始席位数据 ----
    "players": [ // 字段和值均100%拷贝自原始数据，不作任何格式或单位的统一处理
      { 
        "seat_name": "中信证券...",
        "net_amount": "0.61亿元",
        "buy": "0.65亿元",
        "sell": "456.11万元",
        "buy_rate": "4.46%",
        "sell_rate": "0.31%",
        "net_rate": "4.15%",
        "type": "普通席位",
        "name": "普通席位",
        "description": "暂无相关信息",
        "style": ["风格未明"]
      },
      { 
        "seat_name": "国泰海通证券股份有限公司成都北一环路证券营业部", 
        "net_amount": "0.41亿元",
        "buy": "0.41亿元",
        "sell": "0.00万元",
        "buy_rate": "2.81%",
        "sell_rate": "0.00%",
        "net_rate": "2.81%",           
        "type": "知名游资",
        "name": "成都系",
        "description": "超短游资，具备短时间内引导个股价格的能力，风格稳定，以超跌板为主，盘中都是直线拉升涨停，引导资金合力封板。擅长做首板个股并且盘中喜欢直线拉升，次日冲高后爱砸盘，偏爱中小盘个股。",
        "style": ["打板", "短线交易"]
      }
    ]
  },
  "short_side_facts": {
    // ... 结构同上 ...
  },
  "battle_facts": {
    "net_advantage_wan": 12800.0, 
    "winner": "多方",
    "net_advantage_pct": 36.9, 
    "on_list_turnover_pct": 23.8
  }
}
```

### 3.2 `FundingBattleSummary` 结构 (LLM增强后输出)

这是最终用于生成报告和前端可视化的核心数据。**它包含了代码的精确计算和LLM的深度洞察**。

```json
// FundingBattleSummary - 最终产物
{
  "ts_code": "股票代码",
  "name": "股票名称",
  "basic_info": { "..."}, // 格式化后的基础信息
  "long_side": { // 由LLM增强
    "total_amount_on_list": "2.37亿元", // (LLM格式化)
    "player_count": 5,                  // (来自Facts)
    "famous_player_count": 1,           // (来自Facts)
    "core_players": [                   // (LLM挑选并标注)
      {
        "seat_name": "中信证券...",
        "player_type": "普通席位",
        "role_tags": ["主导多头", "锁仓主力"],
        "reasons": ["净买入金额最大"]
      },
      {
        "seat_name": "国泰海通证券股份有限公司成都北一环路证券营业部",
        "player_type": "知名游资",
        "role_tags": ["核心游资", "成都系"],
        "reasons": ["知名游资参与"],
        "analysis": {
          "actions": "净买入0.41亿元，是多方核心力量之一。此操作与该游资'打板'的风格相符，表现出强势进攻姿态。",
          "intention": "基于其风格和操作，推断其意图是引导市场情绪，博取次日高溢价。"
        }
      }
    ],
    "summary": { // 此处的值由LLM基于分析和计算后，统一格式进行填充
      "concentration": "50.2%",            // (LLM格式化)
      "style_tags": ["打板", "短线突击"],   // <-- LLM提炼
      "conclusion": "由普通席位主导，知名游资'成都系'积极参与，形成合力猛攻。" // <-- LLM总结
    }
  },
  "short_side": { /* ... 结构同上 ... */ },
  "battle_assessment": { // 完全由LLM基于Facts生成
    "winner": "多方",
    "net_advantage": "1.28亿元",
    "long_strength_score": 85,        // <-- LLM评估
    "short_strength_score": 52,       // <-- LLM评估
    "battle_tags": ["游资主导局", "多头强攻", "高位换手"], // <-- LLM生成
    "key_takeaway": "多方凭借核心力量的压倒性优势，牢牢控制战局，空方抵抗分散" // <-- LLM总结
  }
}
```

---

## 4. LLM洞察增强层 (Stage 2) 的提示词设计

这是新流程的核心，它的目标是"画龙点睛"，而不是重复计算。

```prompt
# 龙虎榜资金博弈洞察提炼任务

你是一位顶级的A股龙虎榜分析师。现在有一份经过代码预处理的结构化战报事实（StructuredFacts），请你基于这份事实，进行深度分析和洞察压缩，生成一份信息密度极高的"资金博弈概要 (FundingBattleSummary)"。

**你的任务是"画龙点睛"，而不是重复计算。**

## 战报事实 (StructuredFacts)
```json
{
  // 这里将 StructuredFacts 对象序列化为字符串
}
```

## 分析与生成要求

请严格按照下面的JSON格式，填充你的分析洞察：

1.  **阵营分析 (`long_side` / `short_side`)**:
    *   请综合利用代码生成的**分析指标**（如`contribution_by_type`, `concentration_metrics`）和**原始席位列表**(`players`)来进行判断。
    *   从 `players` 列表中，挑选出最重要的1-2名核心主力，并放入 `core_players`。
    *   为核心主力打上精准的 `role_tags`（例如："主攻手"、"锁仓主力"、"跟风资金"、"砸盘元凶"）。
    *   在 `reasons` 中简明扼要地解释为什么他们是核心。
    *   **游资专项分析**: 如果一个核心主力是"知名游资"，则必须为其添加一个`analysis`字段，您重点参考 `players`列表中的 `description` 和 `styles` 字段, 深入分析其具体操作(`actions`)和战术意图(`intention`)。分析时，请明确区分**可验证的行为**（如净买入金额）和**基于风格的推断**（如"疑似打板"）。
    *   从所有玩家的风格中，提炼出该阵营的整体风格，填入 `summary.style_tags`。
    *   在 `summary.conclusion` 中，用一句话总结该阵营的战术意图和构成。
    *   **格式统一**: 在生成`total_amount_on_list`和`summary.concentration`等字段时，请将数值转化为带单位或百分号的、易于阅读的字符串。

2.  **战局评估 (`battle_assessment`)**:
    *   `long_strength_score` / `short_strength_score`: 结合资金量、玩家质量（`contribution_by_type`）、资金集中度(`concentration_metrics`)，给出一个0-100的实力评分。
    *   `battle_tags`: 结合`on_list_turnover_pct`和`net_advantage_pct`等指标，生成最能体现战局本质的标签（例如："游资闪电战"、"机构与游资的对决"、"多杀多"）。
    *   `key_takeaway`: 给出整场战局最核心的结论。

**重要约束：**
*   **你的所有分析和结论，都必须严格基于以上提供的`StructuredFacts`数据。**
*   **禁止对任何未在`StructuredFacts`中明确给出的信息进行猜测或假设，特别是关于历史K线形态、股价的绝对高低位、或技术指标（如均线、MACD）等。**
*   例如，你可以说"多方力量强劲"，但不能说"股价突破了前期高点"，除非`StructuredFacts`里有这个信息。

**请严格按照指定的JSON Schema输出最终结果。**

```json
{
  // 这里是 FundingBattleSummary 的目标JSON结构
}
```
```

## 5. 实施建议与总结

这个新的混合增强方案，完美融合了代码和LLM的优点：

*   **高精度**: 所有基础计算由代码完成，杜绝LLM的数字幻觉。
*   **高洞察**: LLM从重复计算中解放出来，专注于其最擅长的分析、推理和总结。
*   **高效率**: 喂给LLM的数据是经过压缩的结构化事实，减少了Token消耗，提高了响应速度。
*   **易维护**: "事实层"和"洞察层"逻辑分离，未来调整规则或更换模型都更加清晰。

这个方案将确保我们产出的`FundingBattleSummary`是市场上最精准、信息密度最高的情报之一。 