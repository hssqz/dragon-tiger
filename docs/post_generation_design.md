# Gushen AI - 龙虎榜帖子生成设计文档 (V1.0)

## 1. 概述

### 1.1. 目标
本文档旨在为开发人员提供一个清晰的指南，说明如何利用 `deepseek_interface.py` 模块，将 `funding_battle_analysis_report.json` 中结构化的龙虎榜分析数据，自动生成一篇符合 `prd.md` 产品设计要求的、高质量的Markdown格式解读帖子。

### 1.2. 设计原则
- **忠于PRD**：严格遵循 `prd.md` 中定义的帖子结构、风格和内容层次。
- **数据驱动**：生成的内容必须完全基于输入的JSON数据，避免AI产生无依据的幻觉。
- **模板化与自动化**：通过精巧的Prompt工程，实现整个生成过程的高度自动化，减少人工干预。
- **可读性与专业性**：最终输出的帖子既要让普通散户易于理解，又要体现Gushen AI的专业性。

## 2. 技术实现方案

### 2.1. 核心模块
我们将使用 `core/deepseek_interface.py` 中的 `generate_text_with_thinking` 函数来完成此任务。

- **选择理由**：为了在开发和调试阶段能够清晰地观察AI的推理过程，确保生成内容的逻辑性和准确性，我们选用 `generate_text_with_thinking`。这使我们能获得除最终回答外的完整“思考过程”，便于调试和优化Prompt。

### 2.2. 工作流程
1.  **加载数据**：程序读取 `funding_battle_analysis_report-3.json` 文件内容。
2.  **构建Prompt (阶段一)**：根据 **Prompt模板1**，构建用于生成帖子主要内容的Prompt。
3.  **调用API (阶段一)**：调用 `generate_text_with_thinking` 生成帖子的核心部分，并记录思考过程以供调试。
4.  **构建Prompt (阶段二)**：根据 **Prompt模板2**，将原始JSON数据和阶段一生成的内容结合，构建用于生成“智能问答角”的Prompt。
5.  **调用API (阶段二)**：再次调用 `generate_text_with_thinking` 生成智能问答部分。
6.  **合并与保存**：将两次生成的内容合并，保存为最终的 `.md` 文件。

## 3. Prompt设计 (两阶段生成)

为了解决单次调用可能面临的Max Token限制，并提高生成质量，我们将生成过程拆分为两个阶段。

### 3.1. 阶段一：生成帖子主干
此阶段生成除“智能问答角”之外的所有内容。

```python
# Python伪代码，展示如何构建Prompt
import json

# 1. 加载JSON分析报告
with open('data/output/funding_battle_analysis_report-3.json', 'r', encoding='utf-8') as f:
    analysis_data = json.load(f)

# 2. 准备基础信息
stock_info = analysis_data.get("stock_info", {})
stock_name = stock_info.get("name", "N/A")
trade_date = stock_info.get("trade_date", "N/A")
stock_code = stock_info.get("ts_code", "N/A")

# 3. 构建System Prompt 和 User Prompt
SYSTEM_PROMPT_PART_1 = """
你是股神AI，一个顶级的A股市场分析专家和内容创作者。你的任务是根据我提供的JSON格式的龙虎榜分析报告，严格按照指定的Markdown格式和要求，生成一篇结构清晰、内容详实、语言生动、洞察深刻的个股龙虎榜解读帖子。

**核心要求**:
1.  **严格遵循格式**: 必须完全按照我给出的Markdown模板和标题结构进行输出。
2.  **忠于原文**: 所有分析都必须基于提供的JSON数据，不能杜撰。
3.  **语言风格**: 专业、客观，同时要通俗易懂，多使用确定性、指导性的语言。
4.  **完整性**: 确保帖子包含所有要求的部分，从核心摘要到核心推演。
5.  **避免自我标榜**: 在生成的帖子内容中，绝对不能使用‘AI’、‘我是一个模型’等词语，应始终以一个专业分析师的口吻进行叙述。
"""

USER_PROMPT_PART_1 = f"""
请根据以下JSON数据，为 **{stock_name}** 在 **{trade_date}** 的龙虎榜表现，生成一篇解读帖子。

**分析报告JSON数据:**
```json
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}
```

---

**请严格按照以下Markdown模板和指令生成帖子内容 (注意：本次只需生成到“核心推演”部分，不要生成“智能问答角”):**

### **零、帖子标题**
**指令**: 首先，请为这篇帖子生成一个引人注目的主标题。格式为 `# {stock_name}({stock_code})：{一句话亮点}`。这个亮点需要你从整个数据中提炼出最关键、最吸引眼球的信息。例如：“# 厦门信达(000701.SZ)：机构大笔出货，拉萨天团高位做T，后市何去何从？”
**(你的输出在这里)**

---

### **一、核心看点**
**指令**: 根据`final_verdict.outlook`和`key_forces`，用PRD中定义的模板，一段话高度概括战局。要突出核心玩家、多空格局和后市预判。
**PRD模板**: `**核心看点**：{{公司名}}今日龙虎榜呈现“{{格局描述}}”格局，“{{最核心玩家}}”强势主导，多空博弈激烈，明日走势{{预判}}。`
**(你的输出在这里)**

---

### **二、资金博弈图谱**
**指令**: 使用Markdown文本格式，清晰展示多空双方阵营。
1.  从`key_forces.buying_force`和`key_forces.selling_force`中提取数据。
2.  对核心主力进行标注，标注内容直接采用`action_interpretation`字段。
3.  计算并展示总买入和总卖出金额。

**(你的输出在这里，请使用以下格式)**
```markdown
#### **多方阵营 (总买入: XXX万)**
- **核心主力**: 【{席位名称}】(买入/净买入 {金额}) - *主力动态: {行为解读}*
- **助攻力量**: ...

#### **空方阵营 (总卖出: XXX万)**
- **核心主力**: 【{席位名称}】(卖出/净卖出 {金额}) - *主力动态: {行为解读}*
- **主要卖压**: ...
```

---

### **三、历史行为追溯**
**指令**: 结合`historical_context`部分，对主力的上榜行为进行定性分析。
1.  **行为定性**: 直接引用 `historical_context.behavior_type`。
2.  **趋势解读**: 概括 `historical_context.trend_interpretation` 的内容，说明当前榜单在股价历史趋势中所处的位置和意义。

**(你的输出在这里)**

---

### **四、后市推演与策略**
**指令**: 这是帖子的核心价值所在。请整合`buyer_analysis`, `seller_analysis`, 和 `final_verdict`的信息，生成三层次结构的内容。

#### **1. 战局解读 (The Big Picture)**
**指令**: 综合`buyer_analysis.concentration_desc`, `buyer_analysis.synergy_analysis`, 和 `seller_analysis.pressure_desc`，用生动、形象的语言描绘当前的多空博弈局面。点出是“协同作战”还是“散兵游勇”，是“机构砸盘”还是“游资接力”。

**(你的输出在这里)**

#### **2. 核心推演 (Core Inference)**
**指令**: 给出直接、明确的核心判断，并提供验证判断的"标尺"。
- **核心判断**: 直接提炼 `final_verdict.outlook` 的核心观点。
- **判断依据**: 简要说明AI做出该判断的核心逻辑，关联主力的操盘风格、历史行为等。例如，可以引用`listing_reason_analysis.interpretation`和`key_forces`中的信息作为支撑。
- **明日看点**: 给出次日开盘后最值得观察的盘面现象，作为验证AI判断的剧本，避免给出具体价位。可以从`final_verdict.strategy`中提炼。

**(你的输出在这里)**
"""

# 4. (实际调用)
# deepseek = DeepSeekInterface()
# response_part1, thinking_part1 = deepseek.generate_text_with_thinking(USER_PROMPT_PART_1)
# print(f"---思考过程 (阶段一)---\n{thinking_part1}")
# print(f"---帖子主干 (阶段一)---\n{response_part1}")
```

### 3.2. 阶段二：生成智能问答角
此阶段利用阶段一生成的内容作为上下文，以保证问答与正文的连贯性。

```python
# 伪代码

SYSTEM_PROMPT_PART_2 = """
你是股神AI，一个顶级的A股市场分析专家。你的任务是基于我提供的原始JSON分析报告和已经生成的帖子主体内容，设计3个散户最关心的高频问题，并给出"三层次"（策略指导+原理解释+风险提示）的回答，作为帖子的"智能问答角"部分。

**核心要求**:
1.  **高度相关**: 问题必须与帖子主体内容和JSON数据紧密相关。
2.  **格式严格**: 严格按照 "Q: ... \nA: 【策略】...【原理】...【风险】..." 的格式输出。
3.  **内容来源**: 回答中的【策略】和【风险】应主要提炼自JSON中的`final_verdict`部分，【原理】则需要结合全局信息进行解释。
4.  **简洁输出**: 只输出“智能问答角”部分的内容，不要包含其他任何标题或说明文字。
5.  **避免自我标榜**: 在生成的回答中，绝对不能使用‘AI’、‘我是一个模型’等词语，应始终以一个专业分析师的口吻进行叙述。
"""

USER_PROMPT_PART_2 = f"""
请为以下这篇关于 **{stock_name}** 的龙虎榜分析帖子，生成“智能问答角”部分。

**原始分析报告JSON数据:**
```json
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}
```

---

**已生成的帖子主体内容:**
```markdown
{response_part1} 
```

---

**指令**:
请现在开始生成“智能问答角”部分，包含3个问题和答案，严格遵循输出格式。
"""

# (实际调用)
# response_part2, thinking_part2 = deepseek.generate_text_with_thinking(USER_PROMPT_PART_2)
# final_post = response_part1 + "\n\n### **3. 智能问答角 (Intelligent Q&A Corner)**\n" + response_part2
# print(f"---思考过程 (阶段二)---\n{thinking_part2}")
# print(f"---最终帖子---\n{final_post}")

```
## 4. 数据映射关系

| 帖子章节             | 对应JSON字段                                                                                                                                                             | 处理逻辑                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **零、帖子标题**     | `stock_info`, 全局信息                                                                                                                                                   | **阶段一**：LLM根据全局信息，提炼最核心亮点，生成动态标题。                                                       |
| **一、核心看点**     | `stock_info.name`, `final_verdict.outlook`, `key_forces`                                                                                                                 | **阶段一**：LLM根据指令和模板，融合信息，生成一段话摘要。                                                         |
| **二、资金博弈图谱** | `key_forces.buying_force`, `key_forces.selling_force`                                                                                                                    | **阶段一**：遍历数组，格式化输出席位、金额和`action_interpretation`。                                              |
| **三、历史行为追溯** | `historical_context.behavior_type`, `historical_context.trend_interpretation`                                                                                            | **阶段一**：直接引用或概括字段内容。                                                                              |
| **四、后市推演与策略** |                                                                                                                                                                          |                                                                                                                 |
| 1. 战局解读          | `buyer_analysis.concentration_desc`, `buyer_analysis.synergy_analysis`, `seller_analysis.pressure_desc`                                                                  | **阶段一**：LLM综合这些描述，用更生动的语言进行全局解读。                                                         |
| 2. 核心推演        | `final_verdict.outlook`, `final_verdict.strategy`, `listing_reason_analysis.interpretation`                                                                              | **阶段一**：LLM提炼核心观点，并组织成"判断-依据-看点"的结构。                                                    |
| 3. 智能问答角        | `final_verdict.strategy`, `final_verdict.risk_warning`, 全局信息, **阶段一生成的内容**                                                                                   | **阶段二**：LLM根据全局信息和主贴内容设计问题，并从`strategy`和`risk_warning`中提炼内容，填充到答案框架中。 |

## 5. V1功能限制与迭代
根据 `prd.md`，当前 `funding_battle_analysis_report-3.json` 的数据结构**暂未完全支持**以下功能点，可在未来迭代中补充：

1.  **席位深度剖析 (In-depth Seat Analysis)**:
    - **缺失数据**: JSON中虽有`player_type`和`player_name`，但缺少`prd.md`中要求的席位历史战绩、关联席位网络、资金体量估算、情绪指标、雷达图等详细数据。
    - **迭代建议**: 后续数据处理流程中可以增加一个模块，专门用于关联席位数据库，计算并丰富这些深度分析指标到JSON报告中。
2.  **历史K线对照**:
    - **缺失数据**: JSON中没有包含历史K线数据及龙虎榜标注点。
    - **迭代建议**: 生成帖子后，可以由前端或另一个服务负责渲染K线图并叠加标记。或者，可以考虑生成一个包含K线图的图片链接，并将其插入Markdown中。

---

## 6. V2核心升级：交互式AI Agent设计

基于 `prd.md` 的规划，V2的核心是将静态的帖子升级为动态的、可交互的投研服务。

### 6.1. 功能概述
在V1生成的帖子下方，增加一个问答输入框。用户可以针对当前分析的个股自由提问，由AI Agent进行实时、上下文感知的回答，实现“千人千策”的个性化投研体验。

### 6.2. 技术实现思路
1.  **上下文持久化**: 在V1帖子生成后，必须将关键上下文信息（至少包括`analysis_data`的JSON和V1生成的主贴`response_part1`）与该帖子关联存储在数据库中。
2.  **API接口**: 需要一个独立的API端点，接收用户问题（user_question）和帖子ID（post_id）。
3.  **上下文检索**: 当用户提问时，后端通过`post_id`检索出对应的上下文（JSON数据和主贴内容）。
4.  **构建Prompt (V2)**: 使用下文定义的 **Prompt模板 V2**，将检索到的上下文和用户的新问题整合起来。
5.  **调用LLM**: 调用`deepseek_interface.py`中的`generate_text_with_thinking`（或为实现打字机效果的`stream_output_with_thinking`）来生成回答。
6.  **返回结果**: 将AI生成的回答返回给前端展示。

### 6.3. Prompt设计 (V2 - 交互式问答)

```python
# 伪代码
# post_id, user_question 从API请求中获取
# analysis_data, response_part1 从数据库中检索

SYSTEM_PROMPT_V2 = """
你是股神AI，一个顶级的A股市场分析专家。你正在一个帖子的评论区与用户进行互动。你的任务是基于帖子的原始分析报告和主贴内容，精准、深入地回答用户提出的关于这只股票的问题。

**核心要求**:
1.  **上下文感知**: 你的回答必须紧密结合已经分析过的内容，保持一致性。
2.  **聚焦问题**: 直接、清晰地回答用户提出的问题，不要跑题。
3.  **三层次回答**: 尽可能遵循“策略指导 + 原理解释 + 风险提示”的结构来组织你的回答，体现专业性。
4.  **安全边界**: 如果用户问题超出了当前数据的分析范围，要明确告知用户，避免提供未经证实的猜测。例如，可以说：“根据当前龙虎榜数据，我们无法判断……”。
5.  **避免自我标榜**: 在生成的回答中，绝对不能使用‘AI’、‘我是一个模型’等词语，应始终以一个专业分析师的口吻进行叙述。
"""

USER_PROMPT_V2 = f"""
这是关于 **{stock_name}** 的原始分析报告和我们已经发布的解读帖子。

**原始分析报告JSON数据:**
```json
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}
```

---

**已发布的帖子主体内容:**
```markdown
{response_part1} 
```

---

**现在，请根据以上所有信息，回答用户提出的以下问题:**

**用户问题**: "{user_question}"
"""

# (实际调用)
# v2_answer, v2_thinking = deepseek.generate_text_with_thinking(USER_PROMPT_V2)
```

### 6.4. 上下文管理 (技术挑战)
- **挑战**: 如何在多轮对话中维持上下文。`prd.md`中提到的核心技术挑战是“让AI理解并继承当前帖子的完整分析上下文”。
- **V2.0解决方案**: 初版交互式Agent可以实现单轮问答。
- **V2.1+解决方案**: 要实现多轮追问（例如，用户问完一个问题后，可以接着追问“为什么？”），需要在 `6.2` 的技术流程中增加对话历史的管理。即，每次调用`USER_PROMPT_V2`时，不仅要传入原始JSON和主贴，还要传入之前的“用户问题-AI回答”对，这将对Token消耗提出更高要求，可能需要更精细的上下文压缩和管理策略。


---
**文档版本**: V1.1 (新增V2设计)
**创建者**: AI
**日期**: 2024-07-26