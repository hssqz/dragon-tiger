# Gushen AI - 个股龙虎榜解读开发任务清单

## Phase 0: 项目初始化
- [x] Task 0.1: 创建 `erd.md` 工程与数据结构设计文档
- [x] Task 0.2: 基于 `erd.md` 创建 `todolist.md`
- [x] Task 0.3: 创建 `cursor-log.md` 用于记录开发日志

## Phase 1: 数据基础建设 (Data Foundation)
- [x] Task 1.1: 搭建 `DataFetcher` 模块，实现 `top_list.csv` 的数据加载功能。
- [x] Task 1.2: 扩展 `DataFetcher`，实现 `top_data.csv` 的数据加载功能。
- [x] Task 1.3: 扩展 `DataFetcher`，实现 `daily_data.csv` 的数据加载功能。
- [x] Task 1.4: 扩展 `DataFetcher`，实现 `hm_list.csv` 的数据加载功能。
- [x] Task 1.5: 实现 `DataProcessor`，用于清洗、合并和预处理加载的数据。

## Phase 2: 核心分析引擎 (Core Analysis Engine)
- [x] Task 2.1: 实现 `SeatProfiler`，用于识别席位身份、关联游资画像。
- [ ] Task 2.2: 实现 `HistoryAnalyzer`，用于关联历史K线和历史龙虎榜数据。

## Phase 3: AI 解读生成 (AI Generation)
- [x] Task 3.0: 创建 `llm_design.md` 并完成V1版设计。
- [ ] Task 3.1: **子任务 - 生成核心摘要**:
  - [ ] Task 3.1.1: 实现 `LLM_Interpreter` 的数据准备方法，为"核心摘要"任务提供Prompt所需JSON。
  - [ ] Task 3.1.2: 实现调用LLM API并获取"核心摘要"结果的功能。
- [ ] Task 3.2: **子任务 - 生成战局解读**:
  - [ ] Task 3.2.1: 实现数据准备方法，为"战局解读"任务提供Prompt所需JSON。
  - [ ] Task 3.2.2: 实现调用LLM API并获取"AI标注"和"战局解读"的JSON结果。
  - [ ] Task 3.2.3: 编写解析函数，从返回的JSON中提取所需字段。
- [ ] Task 3.3: **子任务 - 生成历史行为分析**:
  - [ ] Task 3.3.1: 实现数据准备方法，为"历史行为分析"任务提供Prompt所需JSON。
  - [ ] Task 3.3.2: 实现调用LLM API并获取"历史行为解读"结果的功能。
- [ ] Task 3.4: **子任务 - 生成后市推演与策略**:
  - [ ] Task 3.4.1: 实现数据准备方法，整合前序所有信息，为最终决策提供Prompt所需JSON。
  - [ ] Task 3.4.2: 实现调用LLM API并获取"后市推演"和"核心策略"的JSON结果。
  - [ ] Task 3.4.3: 编写解析函数，从返回的JSON中提取所需字段。

## Phase 4: 整合与测试 (Integration & Testing)
- [ ] Task 4.1: 实现 `PostGenerator`，将所有数据和AI分析组装成最终的JSON输出。
- [ ] Task 4.2: 编写端到端(E2E)测试，确保整个流水线运行通畅。

## 待议/未来任务 (Backlog/Future)
- [ ] **V2 - 交互式AI Agent**
  - [ ] Task 5.1: 设计并实现前端的用户提问输入界面。
  - [ ] Task 5.2: 开发用于接收用户问题的API Endpoint。
  - [ ] Task 5.3: 实现 `Interactive_LLM_Agent`，能够根据上下文和新问题调用LLM。
  - [ ] Task 5.4: 实现数据库查询逻辑，为Agent提供分析上下文。
- [ ] **V1.1 - 功能增强**:
  - [ ] 探讨"资金博弈图谱"的可视化方案。
  - [ ] 增加"游资画像卡片"的点击交互功能设计。
  - [ ] 设计"席位强度分"的具体计算公式 (已延期)。 