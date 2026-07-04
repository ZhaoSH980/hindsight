# Hindsight — 时光机评估深度研究 Agent 设计文档

日期：2026-07-04 ｜ 状态：待用户批准 ｜ 作者：赵成浩 + Claude

## 1. 背景与目标

**一句话**：一个把 deep research agent 放进"时光机"里跑、再用真实历史结局自动打分的评估驱动（evaluation-driven）研究系统。

**要解决的问题**：通用 deep research 项目无法客观回答"研究做得好不好"——评估几乎全靠 LLM-as-judge 主观打分。金融领域有独特优势：研究结论可以被未来行情**证伪**。Hindsight 让 Agent 在历史上任意一天（`as_of` 日期）做研究，产出带可证伪声明（falsifiable claims）的结构化研报，然后用已实现的真实数据自动评分，形成客观 + 主观 + 成本三轨评估闭环，评估结果再以经验案例形式回流给后续研究。

**用途定位**：作者面试 Senior Agent Researcher / Engineer 岗位的旗舰展示项目。目标 JD 核心信号：
- "evaluation-driven Agent systems, using evaluation as the primary mechanism to guide behavior"
- "automated Agent evaluation infrastructure"
- "how well it performs, why it behaves as it does, how it can continue to improve over time"

**成功标准**：
1. 4 天内完成可演示闭环：选案例 → 看 Agent 实时做研究 → 研报声明卡片 → 时间前进 → 声明逐条被真实数据判绿/判红 → 评估看板。
2. 断网可完整演示（录制回放模式）。
3. GitHub 公开仓库具备旗舰级 README（双语、架构图、GIF、评估方法论）。
4. 面试考点全覆盖：RAG、工具调用、ReAct、多 Agent、评估设计、长文档处理、成本-性能权衡。

## 2. 面试叙事映射（JD → 模块）

| JD / 面试考点 | Hindsight 对应物 |
|---|---|
| evaluation-driven agent | 三轨评估引擎 + 经验回流，评估驱动迭代 |
| automated eval infrastructure | 评估套件（EvalSuite）批量跑案例 × 配置，自动出分 |
| observable / maintainable | 飞行记录仪 trace（每步 prompt/响应/token 落盘）+ 前端逐步回放 |
| performance–cost trade-offs | 配置对比排行榜 + 质量-成本散点图 |
| RAG | 时间过滤混合检索（BM25 主 + 可选向量），引用接地 |
| Agent 工具调用 | 统一工具注册表 + JSON Schema 函数调用 |
| ReAct 架构 | 规划 Agent 的 Thought→Action→Observation 循环 |
| 长文档 deep research | 财报/电话会纪要分块、引用溯源 |
| improve over time | 经验库跨代对比：同一评估套件多代分数曲线 |
| 防未来函数 / look-ahead bias | 时间沙箱 + 泄漏单元测试 + 访问审计日志 |

## 3. 系统架构

五层（自上而下）：

```
React 前端（研究台 / 轨迹回放 / 评估看板 / 排行榜）
        │ WebSocket + REST
FastAPI 服务层
        │
Agent 管线：规划(ReAct) → 检索 → 分析 → 审查
        │ 所有数据访问必经
时间沙箱（as-of 信息闸门 + 审计日志）
        │
工具/数据层：行情工具(yfinance缓存) · 语料检索(BM25+时间过滤) · SQLite
        │ run 结束后
评估引擎：结局评分器 · LLM 裁判 · 成本台账 → 经验库 ──(回流)──> 规划
```

### 3.1 Agent 管线（多 Agent，单进程编排）

同一 LLM 后端、不同角色 prompt + 不同工具白名单的四个 Agent，由确定性编排器串联（不搞黑盒自治群，可观测优先）：

1. **Planner（规划）**：ReAct 循环。输入研究问题 + as_of 日期 + 经验库检索到的相似案例摘要；拆解子问题，决定调用哪些工具，维护研究状态（已知/待查），决定何时收敛。最大步数可配（默认 8）。
2. **Researcher（检索）**：执行 Planner 指定的检索/工具动作：语料检索（时间过滤 RAG）、行情工具（as_of 前的 OHLCV/涨跌幅/波动）、计算器。产出带来源 ID 的证据集（evidence chunks）。
3. **Analyst（分析）**：把证据集合成结构化研报备忘录（memo）：市场背景、多空论点、结论；每条结论必须挂 1+ 条可证伪声明（claim），每条声明必须引用证据 ID。输出为 JSON（Pydantic Schema）。
4. **Critic（审查）**：三层校验——① Schema 校验（Pydantic）；② 一致性检查（声明与结论方向矛盾、horizon 超界、置信度越界、引用的证据 ID 不存在）；③ 语义检查（LLM 判断声明是否真的可证伪、证据是否支撑）。失败带具体反馈退回 Analyst 重试（最多 2 次），仍失败则降级标记 `unverified` 并在 UI 明示。

设计取舍：编排是**确定性状态机**，LLM 的自由度限制在每个 Agent 的单次决策内。理由：可观测、可回放、可评估——与 JD "why it behaves as it does" 对齐。

### 3.2 时间沙箱（核心创新点 ①）

- `RunContext.as_of_date` 注入所有工具；工具实现必须通过 `Sandbox.fetch(...)` 访问数据。
- 语料检索强制 `doc.published_at <= as_of`；行情工具强制 `bar.date <= as_of`，请求未来数据直接抛 `LookaheadError`。
- 每次数据访问写审计日志（工具名、参数、返回数据的时间范围），trace 中可查。
- **泄漏测试**：pytest 用例构造"未来才发布"的文档与行情，断言任何路径都取不到；CI 必跑。

### 3.3 可证伪声明 Schema（核心创新点 ②）

```json
{
  "claim_id": "c1",
  "statement": "NVDA 财报后 20 个交易日内收盘价较 as_of 日上涨超 5%",
  "type": "direction",            // direction | magnitude | volatility
  "ticker": "NVDA",
  "horizon_days": 20,             // 交易日
  "prediction": {"direction": "up", "threshold_pct": 5.0},
  "confidence": 0.72,             // [0,1]，用于校准分析
  "evidence": ["chunk_014", "chunk_027"]
}
```

- v1 支持三种声明类型：`direction`（方向±阈值）、`magnitude`（涨跌幅区间）、`volatility`（波动率高低于历史分位）。全部可用日线 OHLCV 机械判定，无歧义。
- 研报 memo = 叙述性 markdown 段落 + claims 数组，两者由 Analyst 一次生成。

### 3.4 三轨评估引擎（核心创新点 ③）

Run 结束即评（回测场景下"未来"已实现）：

- **A. 客观结局（outcome）**：按声明类型机械判定命中/未中；聚合指标：方向命中率、幅度平均绝对误差、**Brier 分数**、**校准曲线**（按置信度分桶的实际命中率）。
- **B. 过程质量（process）**：LLM 裁判（独立 prompt，可配不同模型）打分：引用接地率（声明证据是否真实支撑——抽查证据原文）、推理一致性、检索充分性。裁判输出结构化 JSON，同样过 Schema 校验。
- **C. 成本效率（cost）**：token 台账（每 Agent、每步）、调用次数、延迟、按供应商单价折算成本；派生指标"每条命中声明的成本"。

**评估套件（EvalSuite）**：N 个案例（ticker × as_of）× M 个配置，批量运行出分，结果入 SQLite，排行榜页可视化。

### 3.5 经验库（核心创新点 ④）

- 评分后生成经验卡：`{案例特征(标的/事件类型/市场状态), 研究策略摘要, 声明结局, 教训一句话}`。
- 新 run 开始时按特征相似度（BM25 over 特征文本，v1 不上向量）检索 top-3 经验卡注入 Planner 上下文。
- 展示方式：同一评估套件跑"无经验库 vs 有经验库"两代，分数对比 = "improve over time" 的可测量证据。

### 3.6 配置对比（B 精简版）

`RunConfig = {model, temperature, max_steps, memory_on, context_budget, retrieval_top_k}`。排行榜页支持任选 2+ 配置在同一案例集上对比：各轨分数表 + 质量-成本散点图。v1 预置两个配置（如 max_steps 4 vs 8、memory on/off）即可讲故事。

## 4. 数据设计

### 4.1 数据源（美股为主 + 适配器预留）

- **行情 ground truth**：yfinance 日线 OHLCV，首次拉取后落盘 parquet/JSON 缓存（`data_cache/`），之后离线可用。数据层定义 `MarketDataSource` 协议（`get_bars(ticker, start, end)`），yfinance 为默认实现，AkShare/OKX 留接口不实现（README 说明扩展方式）。
- **研究语料**：随仓库分发的精选案例包（`datasets/<case_id>/`），每篇文档为 markdown + frontmatter 元数据（`title, source, published_at, url, doc_type`）。来源：SEC 财报节选、财报电话会纪要节选、公开新闻摘要（人工整理，注明出处，仅节选以避版权问题）。
- **3 个演示案例**（初选，实施时可调）：
  1. NVDA 2025Q1 财报季（AI 叙事高热，多空证据都丰富）
  2. TSLA 交付数据事件（方向分歧大，适合展示辩证分析）
  3. 一个"Agent 判断错误"的案例——**故意保留失败案例**，演示评估体系如何暴露过度自信（校准曲线），这是面试叙事的点睛之笔。
- 每案例 10–20 篇文档、语料覆盖 as_of 前 90 天、结局窗口 as_of 后 20–40 个交易日。

### 4.2 检索

- 入库：markdown 按标题/段落分块（约 300–500 token/块），块级元数据继承文档 `published_at`。
- 检索：rank-bm25（纯 Python、离线、确定性）+ 时间过滤；接口预留 `EmbeddingRetriever`（可选 API 向量，v1 不做）。
- 中文说明：语料为英文；检索查询由 Researcher 生成英文查询词。

### 4.3 存储

SQLite 单文件（`hindsight.db`）+ 文件落盘双轨：
- 表：`runs`（配置、状态、汇总分）、`traces`（结构化事件流）、`claims`（含评分结果）、`experiences`、`llm_calls`（录制：请求哈希 → 响应，供回放与配额节省）。
- 每个 run 同时落盘 `runs/<run_id>/`：memo.md、claims.json、trace.jsonl、scores.json——git 可分发录制的演示 run。

### 4.4 LLM 接入

- OpenAI 兼容客户端；配置来自 `.env`：`LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`（当前：讯飞 MaaS `astron-code-latest`，GLM-5.2，500k 上下文，按次计费）。
- **录制/回放层（必做）**：所有 LLM 调用经 `RecordingLLMClient`——记录模式写 `llm_calls`；回放模式按请求哈希查库命中则不发网络请求。`HINDSIGHT_OFFLINE=1` 强制回放，未命中报错而非静默调 API。节省按次配额 + 断网演示 + 测试夹具三合一。
- 裁判模型默认同主模型，`JUDGE_MODEL` 可覆盖。

## 5. API 设计（FastAPI）

- `GET /api/cases` — 案例列表（含语料统计、as_of、结局窗口）
- `POST /api/runs` — 发起研究 run `{case_id, config}` → `{run_id}`
- `GET /api/runs/{id}` — run 详情（memo、claims、scores、成本）
- `WS /api/runs/{id}/stream` — 实时事件流（Agent 步骤、工具调用、token 计数）
- `GET /api/runs/{id}/trace` — 完整 trace（回放用）
- `POST /api/eval/suites` / `GET /api/eval/suites/{id}` — 批量评估
- `GET /api/leaderboard?suite_id=` — 配置对比数据
- `GET /api/experiences` — 经验库浏览

事件流协议：`{type: plan_step|tool_call|tool_result|agent_output|validation|score, agent, payload, tokens, ts}` ——前端实时渲染与事后回放共用同一协议。

## 6. 前端（React 18 + Vite + TS + Tailwind + Recharts）

深色量化终端风格（深底、等宽数字、绿涨红跌语义色），中英双语（轻量字典 + 顶栏 EN/中 切换，默认英文）。四页：

1. **Research Studio**：左侧案例选择 + as_of 时间轴滑块 + 配置选择；中间 K 线图（as_of 右侧遮罩为"未知的未来"）；右侧 Agent 实时工作流（步骤卡片流式追加）。run 完成 → memo 渲染 + 声明卡片（引用可点击展开原文）→ 高光交互 **"Reveal the future"**：K 线揭幕延伸，声明卡逐条判绿/红，Brier 分数浮现。
2. **Trace Explorer**：步骤时间线树 + 每步 prompt/响应/token 折叠面板 + 沙箱审计日志视图 + 成本累计条。
3. **Eval Dashboard**：单 run 评分卡（三轨）+ 校准曲线图 + 声明明细表。
4. **Leaderboard**：套件 × 配置矩阵、质量-成本散点、经验库开关代际对比曲线。

演示模式：页面均可从录制 run 渲染，无后端 LLM 依赖。

## 7. 目录结构

```
hindsight/
├── backend/
│   ├── hindsight/
│   │   ├── agents/          # planner.py researcher.py analyst.py critic.py orchestrator.py
│   │   ├── sandbox/         # gate.py audit.py errors.py
│   │   ├── rag/             # ingest.py chunker.py bm25_retriever.py
│   │   ├── tools/           # registry.py market_data.py corpus_search.py calc.py
│   │   ├── eval/            # outcome_grader.py judge.py calibration.py suite.py
│   │   ├── memory/          # experience.py
│   │   ├── trace/           # recorder.py events.py cost_ledger.py
│   │   ├── llm/             # client.py recording.py
│   │   ├── data/            # market_source.py cache.py models.py
│   │   ├── api/             # app.py routes/ ws.py
│   │   └── schemas.py       # Pydantic：Claim, Memo, RunConfig, Scores...
│   ├── tests/               # test_sandbox_leakage.py test_grader.py test_claims_schema.py ...
│   └── pyproject.toml
├── frontend/                # Vite + React + TS + Tailwind
├── datasets/                # cases/<case_id>/{meta.json, docs/*.md}
├── runs/                    # 录制的演示 run（随 git 分发）
├── docs/                    # 架构、评估方法论（README 链接）
├── README.md                # 双语旗舰 README
└── .env.example
```

## 8. 错误处理与降级

- LLM 输出不合 Schema → Critic 带错误反馈重试（≤2 次）→ 仍败标记 `unverified`，run 不中断。
- LLM API 网络错误 → 指数退避重试 3 次 → 失败则 run 置 `failed`，trace 保留已完成步骤。
- 回放未命中（OFFLINE 模式）→ 显式报错并提示缺失的请求哈希。
- yfinance 拉取失败 → 用缓存；无缓存则案例标记不可用。
- WebSocket 断连 → 前端自动降级为轮询 `GET /runs/{id}`。

## 9. 测试策略

优先级排序（4 天内必须 vs 尽量）：
1. **必须**：沙箱泄漏测试（未来文档/行情不可达）、结局评分器判定逻辑（构造已知结局的假数据）、Claim Schema 校验与 Critic 一致性规则、录制/回放层（离线命中与未命中）。
2. **尽量**：BM25 时间过滤检索、校准分桶计算、API 冒烟测试（TestClient）。
3. 前端：手工验收为主（时间有限），关键交互录 GIF 兼作 README 素材。

Agent prompt 质量本身不写单测——由评估套件量化（吃自己的狗粮，这本身就是面试话术）。

## 10. 里程碑（4 天）

- **D1**：backend 骨架 + schemas + 时间沙箱 + 数据层（yfinance 缓存、语料入库、BM25 时间过滤）+ trace 记录器 + 录制/回放层 + 泄漏测试 ✅ 可 CLI 跑通"检索+行情"无 LLM 流程
- **D2**：四 Agent 管线 + 编排器 + 声明 Schema 全链路 + 三轨评估 + 经验库 ✅ CLI 端到端一个案例出分
- **D3**：FastAPI + WS + 前端 Research Studio / Trace Explorer / Eval Dashboard ✅ 浏览器完整演示一个 run
- **D4**：Leaderboard + UI 打磨 + 3 案例语料精修 + 录制演示 runs + 双语 README（banner/架构图/GIF/方法论）+ 公开仓库 ✅ 断网演示彩排

## 11. 非目标（YAGNI）

- 不做实盘/下单/任何券商连接；不做用户系统与部署（本地跑）。
- 不做向量数据库/Embedding（接口预留）；不做爬虫（语料人工精选随库分发）。
- 不做多空辩论模式（方案 C，时间富余再说）；不做 A 股/加密适配器实现（只留协议接口）。
- 不追求研究结论真的能赚钱——项目卖点是**评估基础设施**，失败案例反而是叙事素材。

## 12. 风险与保底

| 风险 | 保底 |
|---|---|
| GLM-5.2 结构化输出不稳 | Critic 重试 + JSON 修复；prompt 里给 few-shot；最坏降级简化 Schema |
| 按次配额烧太快 | 录制/回放层从 D1 就位；开发期反复跑同一请求零成本 |
| 4 天做不完前端四页 | 优先级：Studio > Trace > Eval > Leaderboard；Leaderboard 可降级为静态图表 |
| 语料整理超时 | 案例从 3 个减到 2 个；每案例文档从 20 减到 10 |
| 演示现场翻车 | 录制回放模式彩排；README GIF 兜底 |
