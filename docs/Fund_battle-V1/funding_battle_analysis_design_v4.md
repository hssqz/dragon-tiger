# 设计方案：龙虎榜资金博弈分析模块 (V4 - 混合拼接版)

## 1. 核心目标 (最终版)

我们采纳最终的优化方案：**将代码的精确事实与LLM的深度洞察进行高效拼接**。这个方案将信息提炼推向极致，LLM不再"复述"任何代码已经能明确提供的信息，只专注于生成纯粹的、高价值的"洞察"。

- **代码做"事实层" (Facts Layer)**：生成`StructuredFacts`，包含所有100%准确的计算和原始数据。
- **LLM做"洞察层" (Insight Layer)**：接收`StructuredFacts`，仅输出一个全新的、精简的`FundingBattleInsights`对象，这里面只包含无法由代码直接计算出的分析、评估和意图判断。
- **最终产物 (Composition)**：将`StructuredFacts`和`FundingBattleInsights`两个JSON对象直接拼接，形成最终的`FundingBattleSummary`。

## 2. 混合分析流程：三阶段处理 (优化版)

### **第一阶段：代码预处理 (事实层 - Fact Layer)**
- **执行者**: `funding_battle_builder.py` (纯代码)
- **输入**: 原始的 `test-seat.json`
- **任务**: 将原始数据转换为一个结构化的**中间层数据 `StructuredFacts`**。
- **输出**: `StructuredFacts` JSON 对象。

### **第二阶段：LLM洞察增强与数据拼接 (洞察与组合层 - Insight & Composition Layer)**
- **执行者**: `funding_battle_enricher.py`
- **输入**: `StructuredFacts` JSON 对象
- **核心任务**:
    1.  **洞察生成**: 将`StructuredFacts`喂给LLM，让其专注分析，并返回一个只包含纯洞察的 `FundingBattleInsights` JSON。
    2.  **数据拼接**: 在代码中，将第一步的`StructuredFacts`和LLM返回的`FundingBattleInsights`合并，组装成最终的`FundingBattleSummary`。
- **输出**: 最终的、信息密度最高的 `FundingBattleSummary` JSON。

### **第三阶段：LLM叙事生成 (叙事层 - Narrative Layer)**
- **执行者**: `post_generator.py`
- **输入**: `FundingBattleSummary` JSON 对象
- **任务**: 基于高密度的情报（包含事实和洞察），生成最终给用户看的、图文并茂的分析帖子。

---

## 3. 关键数据结构定义 (V4)

### 3.1 `StructuredFacts` 结构 (代码层输出)

**此结构保持不变**，它是代码处理的产物，是后续所有分析的唯一事实来源。

```json
// StructuredFacts - 保持V3设计不变
{
  "ts_code": "股票代码",
  "name": "股票名称",
  "raw_basic_info": { "..."}, // 保留原始基础信息
  "long_side_facts": {
    "total_amount_wan": 23700.0,
    "player_count": 5,
    "famous_player_count": 1,
    "concentration_metrics": { 
      "top1_pct": 27.4, "top2_pct": 50.2, "top5_pct": 100.0 
    },
    "contribution_by_type": { 
      "知名游资_net_wan": 4100.0, "普通席位_net_wan": 17800.0 
    },
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

### 3.2 `FundingBattleInsights` 结构 (LLM洞察层输出)

这是LLM需要生成的**全新、精简结构**。它不包含任何来自`StructuredFacts`的重复信息。

```json
// FundingBattleInsights - LLM输出的纯粹洞察 (V4)
{
  "long_side_insights": {
    "core_players": [
      {
        "seat_name": "中信证券...", // 用于关联事实数据
        "player_type": "普通席位",
        "role_tags": ["主导多头", "锁仓主力"],
        "reasons": ["净买入金额最大"],
        "analysis": {
          "actions": "净买入0.61亿元，是多方绝对主力。",
          "intention_tags": ["坚决做多", "锁仓看好"],
          "intention": "基于其巨大的净买入额，并无卖出行为，判断其意图为利用资金优势强力拉升并锁仓。"
        }
      },
      {
        "seat_name": "国泰君安证券股份有限公司成都北一环路证券营业部", // 用于关联
        "player_name": "成都系",
        "style_tags": ["短线", "打板"],
        "reasons": ["知名游资参与"],
        "analysis": {
          "actions": "净买入0.41亿元，是多方核心力量之一。",
          "intention_tags": ["打板突击", "寻求次日溢价"],
          "intention": "基于其'打板'风格和坚决的净买入行为，推断其核心意图是制造涨停，引导市场情绪，并博取次日的高开溢价。"
        }
      }
    ],
    "summary": {
      "style_tags": ["打板", "短线突击"],
      "conclusion": "由普通席位主导，知名游资'成都系'积极参与，形成合力猛攻。"
    }
  },
  "short_side_insights": { /* ... 结构同上 ... */ },
  "battle_assessment": {
    "long_strength_score": 85,
    "short_strength_score": 52,
    "battle_tags": ["游资主导局", "多头强攻", "高位换手"],
    "key_takeaway": "多方凭借核心力量的压倒性优势，牢牢控制战局，空方抵抗分散且力度不足。"
  }
}
```

### 3.3 `FundingBattleSummary` 结构 (最终拼接产物)

这是交付给第三阶段（叙事层）的最终数据。它通过简单的拼接，同时提供了精确的事实和深刻的洞察。

```json
// FundingBattleSummary - 最终拼接产物 (V4)
{
  "facts": {
    // ... 这里是完整的 StructuredFacts 对象 ...
  },
  "insights": {
    // ... 这里是完整的 FundingBattleInsights 对象 ...
  }
}
```

---

## 4. LLM洞察增强层 (Stage 2) 的提示词设计 (V4)

新的提示词将引导LLM只输出`FundingBattleInsights`。

```prompt
# 龙虎榜资金博弈洞察提炼任务 (V4)

你是一位顶级的A股龙虎榜分析师，擅长通过席位操作行为"辨意图"。现有经代码预处理的`StructuredFacts`，请你基于此进行深度分析，**只输出纯粹的洞察部分**，格式为`FundingBattleInsights`。

**你的核心任务是：识别核心玩家，洞察其真实意图，并评估战局。不要重复任何`StructuredFacts`中已有的数据或数值。**

## 战报事实 (StructuredFacts)
```json
{
  // 这里将 StructuredFacts 对象序列化为字符串
}
```

## 分析与生成要求

请严格按照`FundingBattleInsights`的JSON格式和分析逻辑，填充你的分析洞察：

1.  **不要复述或格式化任何输入数据**：例如，不要在你的输出中包含`total_amount_wan`或`concentration_metrics`等字段。你的任务是创造新信息（洞察），而不是转述旧信息。

2.  **阵营洞察 (`long_side_insights` / `short_side_insights`)**:
    *   在`facts.long_side.players`中，挑选出最重要的1-2名核心主力，填充到`core_players`。
    *   为核心主力打上`role_tags`（如："主攻手"、"锁仓主力"、"砸盘元凶"）和`reasons`。
    *   **核心玩家意图分析 (`analysis`)**: 这是关键。
        *   `actions`: 简述其操作行为。
        *   `intention_tags`: 从标签库中选择最精准的1-3个标签：
            *   多头: `["坚决做多", "尝试拉升", "锁仓看好", "高抛低吸"]`
            *   空头: `["坚决做空", "派发砸盘", "高位出货"]`
            *   中性: `["做T套利", "风格不明"]`
        *   `intention`: 用一句话总结其战术意图。**你的推断必须结合其在`StructuredFacts`中的"行为"、"净额"和"风格"进行解释**。

3.  **核心玩家意图分析逻辑（重点）**
    *   **看净额**：大幅净买入 -> `坚决做多`；大幅净卖出 -> `坚决做空`；买卖均衡 -> `做T套利`。
    *   **看风格** (结合`facts.long_side.players[...].description` 和 `style`):
        *   "打板"风格 + 大额净买入 -> `尝试拉升`。
        *   "砸盘"风格 + 大额净卖出 -> `派发砸盘`。
        *   "锁仓"风格 + 大额净买入 -> `锁仓看好`。
    *   **综合判断**: 将净额和风格结合，形成最终结论。

4.  **阵营总结 (`summary`)**:
    *   `style_tags`: 从所有玩家风格中提炼出该阵营的整体风格。
    *   `conclusion`: 用一句话总结该阵营的战术意图和构成。

5.  **战局评估 (`battle_assessment`)**:
    *   `long_strength_score` / `short_strength_score`: 结合资金量、玩家质量、资金集中度，给出一个0-100的实力评分。
    *   `battle_tags`: 结合`facts.battle_facts`中的指标，生成最能体现战局本质的标签（例如："游资闪电战", "机构与游资的对决"）。
    *   `key_takeaway`: 给出整场战局最核心的结论。

**重要约束：**
*   你的所有分析都必须严格基于以上提供的`StructuredFacts`数据。
*   禁止猜测任何`StructuredFacts`中未给出的信息（如历史K线、技术指标等）。
*   **你的输出必须是严格的、不含任何额外注释的`FundingBattleInsights` JSON对象。**

**请严格按照指定的JSON Schema输出最终结果。**

```json
{
  // 这里是 FundingBattleInsights (V4) 的目标JSON结构
}
```
```

## 5. 实施建议与总结 (V4)

这个新的**混合拼接方案 (V4)** 是我们流程的最终形态，它具备以下优势：

*   **极致效率**: LLM的Token消耗被最小化，因为它只生成无法被代码计算的纯粹洞察。成本更低，响应更快。
*   **绝对精准**: 事实与洞察完全分离。`facts`部分保证了100%的数据准确性，`insights`部分则发挥了LLM的最大优势。
*   **高度可维护**: "事实层"和"洞察层"的逻辑完全解耦。未来无论是修改计算规则还是更换LLM模型，都互不影响，维护成本极低。
*   **结构清晰**: 最终的`FundingBattleSummary`结构清晰明了，下游的叙事生成模块或前端展示模块可以方便地按需取用数据。

这个方案确保了我们产出的`FundingBattleSummary`是市场上最精准、信息密度最高、且最具成本效益的情报之一。 