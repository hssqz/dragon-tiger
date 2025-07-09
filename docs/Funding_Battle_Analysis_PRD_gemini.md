### Gushen AI - 龙虎榜资金博弈分析系统 - V2.0 PRD

---

**文档状态：** `定稿`
**负责人：** `Gushen AI`
**更新日期：** `2024-07-15`

---

### 1. 产品愿景 (Vision)

**"让每一位散户都能看懂龙虎榜背后的资金秘密。"**

我们旨在利用大语言模型（LLM）的深度分析能力，将复杂、零散的龙虎榜数据，转化为对散户有直接指导意义的、清晰易懂的资金博弈分析报告。我们追求的不是数据的简单罗列，而是**深度、可信、可执行的投资洞见**。

### 2. 用户痛点 (User Pain Points)

散户面对龙虎榜时，普遍存在以下痛点：
*   **看不懂：** 营业部名称繁多，分不清是机构、游资还是散户。
*   **算不清：** 无法快速判断多空力量对比，计算买卖双方的集中度。
*   **想不透：** 不理解知名游资的操作手法，看不出其背后意图是"抬轿"还是"出货"。
*   **用不上：** 分析完后，依然不知道第二天该如何操作，缺少具体策略指导。

### 3. 功能概述 (Feature Overview)

本系统通过一个**模块化的LLM分析流水线 (Pipeline)**，对单只股票的龙虎榜数据进行多维度、深层次的自动化分析，并最终生成一份结构化的JSON分析结果，该结果可被前端直接渲染成图文并茂的分析报告。

**核心设计理念：**
借鉴 `docs/Funding_battle_prd.md` 中的核心思想，我们追求**分析的深度**。我们将复杂的分析任务拆解为多个独立的**分析模块 (Analysis Modules)**。每个模块都是一次独立的LLM调用，负责从一个特定角度进行深度分析，并以JSON格式返回结果。最后，将所有模块的JSON结果拼装成完整的分析报告。

**数据源：**
系统分析的唯一数据输入为 `core/test-seat.json` 格式的单日龙虎榜数据。

**技术实现:**
所有LLM调用均通过 `core/deepseek_interface.py` 中的 `generate_json_output` 方法实现，以确保输出结果的格式稳定可靠。

### 4. 模块化分析框架 (Modular Analysis Framework)

我们将整个分析过程拆解为以下六个核心模块，依次调用执行：

---

#### **模块一：上榜原因解读 (Listing Reason Analysis)**

*   **目标：** 解读股票登上龙虎榜的具体原因，并评估该原因背后所蕴含的市场信号强度。
*   **输入数据 (`test-seat.json`)：** `basic_info` 下的 `reasons` 数组。
*   **LLM Prompt核心指令：**
    ```
    你是一位顶级的A股龙虎榜分析师。请严格遵循以下"实战解读要点"，分析给出的"上榜原因"，评估其市场信号强度，并给出"信号定性"和"核心解读"。

    ### 实战解读要点

    #### 1. 按原因类型分析：
    *   **涨停相关（最强信号）**:
        *   **原因示例**: `日涨幅偏离值达到7%`, `连续2/3个交易日涨幅偏离值累计达到20%`
        *   **解读**: 反映资金最强烈的做多意愿。重点关注连板情况，连板是市场总情绪的温度计。
    *   **振幅相关（中等信号）**:
        *   **原因示例**: `日振幅值达到15%`
        *   **解读**: 筹码松动，多空分歧严重。可能是主力洗盘或出货前兆，需结合后续的资金分析来判断。
    *   **换手率相关（观察信号）**:
        *   **原因示例**: `日换手率达到20%`
        *   **解读**: 资金关注度高，交投活跃。需警惕是主力出货还是新资金接力。老股突放高换手，通常预示有重大变化。

    #### 2. 综合研判规则：
    *   **多重上榜**: 若同时因多个原因上榜（如：涨停+高换手），信号会增强。
    *   **信号强度排序**: 一般来说，信号强度排序为： **涨停相关 > 振幅相关 > 换手率相关**。

    ---

    上榜原因: {reasons_string}
    ```
*   **输出JSON Schema (`module_1_result.json`)：**
    ```json
    {
      "listing_reason_analysis": {
        "reasons": ["string"], // e.g. ["日涨幅偏离值达到7%的前5只证券"]
        "signal_strength": "string", // 枚举值: "强", "中", "弱"
        "interpretation": "string" // 核心解读，例如: "以'连续三日涨幅偏离值累计达到20%'的核心原因上榜，属于最强烈的看多信号，表明主力资金接力意愿极强。"
      }
    }
    ```

---

#### **模块二：战局总览 (Overall Situation Assessment)**

*   **目标：** 对当日龙虎榜的整体态势给出一个快速、高级别的定性结论。
*   **输入数据 (`test-seat.json`)：** `basic_info` 下的 `pct_change`, `turnover_rate`, `l_buy`, `l_sell`, `net_amount`, `net_rate`, `amount_rate`, `float_values`。
*   **LLM Prompt核心指令：** 
    ```
    你是一位顶级的龙虎榜分析师，擅长从宏观数据中解读战局。请基于以下龙虎榜核心摘要数据，进行一个三维度的综合评估：

    1.  **战局定性**: 给出多空胜负的最终判断。
    2.  **市场情绪评估**: 基于`涨跌幅`和`换手率`，评估市场的真实情绪是亢奋、分歧还是恐慌。
    3.  **资金对抗评估**: 基于`龙虎榜总买入`、`总卖出`、`净额`、`净额占比`、`成交占比`和`换手率`等数据，评估主力资金的控盘力度和多空对抗的激烈程度。**特别注意**：通过对比`总买入`和`总卖出`的绝对值大小来判断博弈强度。高换手率背景下的资金对抗，意味着筹码交换更充分。
    4.  **核心结论**: 用一句话点出今天战局的核心看点。

    请确保你的分析是数据驱动的。例如，同样的净买入额，对于小盘股（流通市值低）的影响力远大于大盘股。

    数据：
    - 涨跌幅: {pct_change}
    - 换手率: {turnover_rate}
    - 龙虎榜总买入: {l_buy}
    - 龙虎榜总卖出: {l_sell}
    - 龙虎榜净买入额: {net_amount}
    - 龙虎榜净买入额占总成交额比例: {net_rate}
    - 龙虎榜总成交额占总成交额比例: {amount_rate}
    - 流通市值: {float_values}
    ```
*   **输出JSON Schema (`module_2_result.json`)：**
    ```json
    {
      "overall_assessment": {
        "verdict": "string", // 枚举值: "多方压倒性胜利", "多方惨胜", "多空势均力敌", "空方惨胜", "空方压倒性胜利"
        "confidence_score": "float", // 0.0 ~ 1.0
        "market_sentiment": {
          "level": "string", // "极度亢奋", "偏向乐观", "分歧加剧", "偏向悲观", "极度恐慌"
          "interpretation": "string" // e.g., "以9.99%涨停收盘，市场情绪极度亢奋，买盘力量占据绝对主导。"
        },
        "capital_confrontation": {
          "level": "string", // "主力高度控盘", "主力优势明显", "多空均衡", "主力集中卖出"
          "interpretation": "string" // e.g., "在高达16.46%的换手率下，榜上资金净流入超1.2亿，净买入占比高达8.76%，龙虎榜成交占总成交的23.77%，显示主力资金在充分换手中依然牢牢控盘，空方抵抗微弱。"
        },
        "key_takeaway": "string" // e.g., "高换手+巨额资金强力封板，是典型的游资暴力拉升手法，短期势头锐不可当。"
      }
    }
    ```

---

#### **模块三：核心力量分析 (Key Forces Analysis)**

*   **目标：** 识别并解读买卖双方的"主角"是谁，他们的性质、行为以及操作风格。
*   **输入数据 (`test-seat.json`)：** `seat_data.buy_seats` 和 `seat_data.sell_seats` 列表，特别是每个席位关联的 `player_info` 对象。
*   **LLM Prompt核心指令：**
    ```
    你是一位精通识别游资和机构手法的专家。请基于以下龙虎榜席位数据，识别出买卖双方阵营中的核心力量（优先选择知名游资、机构等）。

    对于每个核心力量，请进行深入的风格画像分析：
    1.  **行为解读**: 他们今天具体做了什么？（例如：主封、接力、做T、出货）
    2.  **风格画像 (Style Profile)**: 输出一个结构化的风格评估：
        *   如果 `player_info.style` 信息不全，请深入分析 `player_info.description` (长段文字描述) 来推断并填充风格画像的各个字段。
        *   **核心概述**: 结合其风格和今日行为，一针见血地总结：他们今天是否在执行标准战法？后市最可能的剧本是什么？
        *   如果没有深入分析，不需要硬要分析，空着即可

    如果一个席位没有特殊的`player_info`，则可以不进行风格分析。

    买方席位: {buy_seats_json_string}
    卖方席位: {sell_seats_json_string}
    ```
*   **输出JSON Schema (`module_3_result.json`)：**
    ```json
    {
      "key_forces": {
        "buying_force": [
          {
            "seat_name": "string", // 席位名称
            "player_type": "string", // 玩家类型，如 "知名游资", "机构专用"
            "player_name": "string", // 玩家名称，如 "成都系", "T王"
            "net_amount": "string", // 净买入额
            "action_interpretation": "string", // 行为解读，例如: "斥资4100万主封涨停，是今日上涨的核心推手。"
            "style_profile": {
              "summary": "string", // "完全匹配其交易档案：今天的'直线拉升'正是其最经典的攻击模式。根据其'次日冲高砸盘'的退场方式，预示着明天早盘有获利了结的巨大可能，追高风险极高。"
              "time_horizon": "string", // "超短线 (1-2天)"
              "preferred_setup": "string", // "超跌板, 首板"
              "typical_exit": "string" // "次日冲高砸盘"
            }
          }
        ],
        "selling_force": [
          {
            "seat_name": "string",
            "player_type": "string",
            "player_name": "string",
            "net_amount": "string", // 净卖出额
            "action_interpretation": "string", // 行为解读，例如: "净卖出1500万，可能是在高位进行获利了结。"
            "style_profile": {
              "summary": "string", // "虽然'温州帮'在榜，但此次卖出金额和手法，与其闻名的'坐庄式'暴力拉升风格不符。这更像是一次试探性的高抛低吸，而非主力大举出货的信号，因此短期抛压风险有限。"
              "time_horizon": "string", // "短线 (3-5天)"
              "preferred_setup": "string", // "趋势加速"
              "typical_exit": "string" // "分批止盈"
            }
          }
        ]
      }
    }
    ```

---

#### **模块四：买方结构与协同性 (Buyer Structure & Synergy)**

*   **目标：** 分析买方的构成，判断是"一家独大"还是"群狼战术"，以及他们之间是否存在协同。
*   **输入数据 (`test-seat.json`)：** `seat_data.buy_seats` 列表。
*   **LLM Prompt核心指令：**
    ```
    分析以下买方席位数据。判断买方的集中度（是"高度集中"还是"相对分散"），并分析是否存在协同作战的迹象（比如多个知名游资同时上榜）。

    买方席位: {buy_seats_json_string}
    ```
*   **输出JSON Schema (`module_4_result.json`)：**
    ```json
    {
      "buyer_analysis": {
        "concentration_level": "string", // 枚举值: "高度集中 (一家独大)", "中度集中", "相对分散"
        "concentration_desc": "string", // 描述，例如: "买一中信浙江分公司净买入超6000万，占总买入超25%，呈现"一家独大"格局，控盘力度强。"
        "synergy_analysis": "string" // 协同性分析，例如: "买三'成都系'为知名游资，其余为普通席位，未见明显协同作战信号。"
      }
    }
    ```

---

#### **模块五：卖方压力与意图 (Seller Pressure & Intent)**

*   **目标：** 分析卖方的构成，判断是"主力出货"还是"散户止盈"。
*   **输入数据 (`test-seat.json`)：** `seat_data.sell_seats` 列表。
*   **LLM Prompt核心指令：**
    ```
    分析以下卖方席位数据。判断卖压的来源和性质，是来自特定主力的"集中出货"，还是普遍的"获利了结"？

    卖方席位: {sell_seats_json_string}
    ```
*   **输出JSON Schema (`module_5_result.json`)：**
    ```json
    {
      "seller_analysis": {
        "pressure_level": "string", // 枚举值: "极高 (主力清仓式出货)", "较高", "中等", "较低 (正常获利了结)"
        "pressure_desc": "string", // 描述，例如: "卖盘由多个"T王"和"温州帮"游资席位构成，但单席位卖出金额均不大，更偏向于短线客的获利了结，而非主力砸盘。"
      }
    }
    ```

---

#### **模块六：历史趋势与行为定性 (Historical Trend & Behavior Context)**

*   **目标：** 结合过去一段时间的K线走势，为当日龙虎榜的资金行为提供一个宏观的趋势背景，判断其所处的阶段和性质。
*   **输入数据 (`test-seat.json`)：** `historical_data` 对象，包含过去十几个交易日的K线数据。
*   **LLM Prompt核心指令：**
    ```
    你是一位精通"量价时空"分析的K线专家。请基于以下该股过去一段时间的日K线数据（包含开、高、低、收、成交量、涨跌幅），结合今天的龙虎榜日（即最后一天的数据），分析并判断本次上榜行为在整个K线趋势中所处的阶段和性质。

    你的任务是给出一个明确的"行为定性"，并进行"趋势解读"。

    历史K线数据: {historical_data_json_string}
    ```
*   **输出JSON Schema (`module_6_result.json`)：**
    ```json
    {
      "historical_context": {
        "behavior_type": "string", // 枚举值: "底部首次建仓", "上升趋势加仓", "高位放量出货", "下跌中继抵抗", "箱体震荡对倒", "跌停撬板试探"
        "trend_interpretation": "string" // 趋势解读，例如: "该股在经历了长期下跌后，近期已在底部盘整多日，今日的放量涨停是典型的底部启动信号，属于首次建仓阶段，后续有继续上攻的潜力。"
      }
    }
    ```

---

#### **模块七：后市策略与风险展望 (Outlook, Strategy & Risks)**

*   **目标：** 综合以上所有模块的分析结果，为用户提供明确、可执行的后市展望、操作策略和风险提示。
*   **输入数据：** 模块1、2、3、4、5、6的JSON输出结果。
*   **LLM Prompt核心指令：**
    ```
    你是一位经验丰富的投资顾问，擅长为散户提供清晰的交易策略。请综合以下所有分析模块的结论，给出一个完整的后市展望、具体的操作策略建议和明确的风险提示。

    上榜原因解读: {module_1_json_string}
    战局总览: {module_2_json_string}
    核心力量分析: {module_3_json_string}
    买方结构分析: {module_4_json_string}
    卖方压力分析: {module_5_json_string}
    历史趋势分析: {module_6_json_string}
    ```
*   **输出JSON Schema (`module_7_result.json`)：**
    ```json
    {
      "final_verdict": {
        "outlook": "string", // 枚举值: "强烈看涨", "谨慎看涨", "中性观察", "谨慎看跌", "强烈看跌"
        "strategy": "string", // 具体策略，例如: "鉴于成都系游资主封，且买方高度集中，次日可关注竞价表现。若高开在3%以上，可小仓位跟随；若平开或低开，则观望为主。"
        "risk_warning": "string" // 风险提示，例如: "风险点在于，成都系有"一日游"习惯，需警惕次日冲高回落的风险。若股价跌破今日涨停价9.03元，应考虑止损。"
      }
    }
    ```

### 5. 最终交付物 (Final Deliverable)

流水线执行完毕后，会将上述7个模块的JSON结果合并成一个大的JSON对象。例如：

```json
{
  "stock_info": {
    "ts_code": "000525.SZ",
    "name": "红太阳",
    "trade_date": "20250617"
  },
  "analysis_report": {
    "listing_reason_analysis": { ... },
    "overall_assessment": { ... },
    "key_forces": { ... },
    "buyer_analysis": { ... },
    "seller_analysis": { ... },
    "historical_context": { ... },
    "final_verdict": { ... }
  }
}
```
