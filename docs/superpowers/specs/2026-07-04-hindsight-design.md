# Hindsight — 时光机评估深度研究 Agent 设计文档

日期：2026-07-04 ｜ 状态：待用户批准（已经 4 视角对抗审查修订）｜ 作者：赵成浩 + Claude

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
5. 评估方法论文档诚实框定所有已知局限（小样本、参数记忆污染、裁判偏差），把局限本身转化为面试讨论素材。

## 2. 面试叙事映射（JD → 模块）

| JD / 面试考点 | Hindsight 对应物 |
|---|---|
| evaluation-driven agent | 三轨评估引擎 + 经验回流 + `docs/eval-log.md` 开发期评估留痕 |
| automated eval infrastructure | 评估套件（EvalSuite）批量跑案例 × 配置，自动出分 |
| observable / maintainable | 飞行记录仪 trace（每步 prompt/响应/token 落盘）+ 前端逐步回放 |
| performance–cost trade-offs | 配置对比排行榜（含 context_budget 轴）+ 质量-成本散点图 |
| RAG | 时间过滤混合检索（BM25 主 + 可选向量），引用接地 |
| Agent 工具调用 | 统一工具注册表 + 函数调用（原生 tools 或 prompt-JSON，D1 探针定） |
| ReAct 架构 | 规划 Agent 的 Thought→Action→Observation 循环 |
| 长文档 deep research | 至少 1 篇 8k+ token 的 SEC 全文文档走分块→时间过滤检索→引用溯源全链路 |
| improve over time | 经验库跨代对比（时间合法的经验回流）+ eval-log 分数曲线 |
| why it behaves as it does | 未命中声明的失败归因（evidence_missing / misread_evidence / reasonable_but_wrong） |
| 防未来函数 / look-ahead bias | 时间沙箱（数据 + 记忆双通道）+ 泄漏单元测试 + 访问审计日志 + 污染探针 |

## 3. 系统架构

五层（自上而下）：

```
React 前端（研究台 / 轨迹回放 / 评估看板 / 排行榜）
        │ WebSocket + REST
FastAPI 服务层
        │
Agent 管线：规划(ReAct) → 检索 → 分析 → 审查
        │ 所有数据访问必经
时间沙箱（as-of 信息闸门 + 审计日志，覆盖数据与记忆两条通道）
        │
工具/数据层：行情工具(冻结快照) · 语料检索(BM25+时间过滤) · SQLite
        │ run 结束后
评估引擎：结局评分器 → LLM 裁判(含失败归因) · 成本台账 → 经验库 ──(时间合法回流)──> 规划
```

### 3.1 Agent 管线（多 Agent，单进程编排）

同一 LLM 后端、不同角色 prompt + 不同工具白名单的四个 Agent，由确定性编排器串联（不搞黑盒自治群，可观测优先）：

1. **Planner（规划）**：ReAct 循环。输入研究问题 + as_of 日期 + 经验库检索到的时间合法经验卡；拆解子问题，决定调用哪些工具，维护研究状态（已知/待查），决定何时收敛。最大步数可配（默认 8）。
2. **Researcher（检索）**：执行 Planner 指定的检索/工具动作：语料检索（时间过滤 RAG）、行情工具（as_of 前的 OHLCV/涨跌幅/波动）、计算器。产出带来源 ID 的证据集（evidence chunks）。
3. **Analyst（分析）**：把证据集合成结构化研报备忘录（memo）：市场背景、多空论点、结论；每条结论必须挂 1+ 条可证伪声明（claim），每条声明必须引用证据 ID。输出为 JSON（Pydantic Schema）。
4. **Critic（审查）**：三层校验——① Schema 校验（Pydantic）；② 一致性检查（声明与结论方向矛盾、horizon 超出案例结局窗口、置信度越界、引用的证据 ID 不存在）；③ 语义检查（LLM 判断声明是否真的可证伪、证据是否支撑）。失败带具体反馈退回 Analyst 重试（最多 2 次），仍失败则降级标记 `unverified` 并在 UI 明示。

工具调用格式由 D1 端点探针决定：优先 OpenAI 原生 `tools/tool_choice`；若讯飞端点不支持或质量差，切换为 prompt 内 JSON 动作格式（工具注册表与 trace 协议不变，仅适配层切换）。

设计取舍：编排是**确定性状态机**，LLM 的自由度限制在每个 Agent 的单次决策内。理由：可观测、可回放、可评估——与 JD "why it behaves as it does" 对齐。

### 3.2 时间沙箱（核心创新点 ①）

- `RunContext.as_of_date` 注入所有工具；工具实现必须通过 `Sandbox.fetch(...)` 访问数据。
- 语料检索强制 `doc.published_at <= as_of`；行情工具强制 `bar.date <= as_of`，请求未来数据直接抛 `LookaheadError`。
- **记忆通道同样过闸门**：经验卡检索强制 `outcome_window_end <= as_of` 且 `source_case_id != 当前案例`（详见 3.5）——回流不是泄漏暗道。
- 每次数据/记忆访问写审计日志（工具名、参数、返回数据的时间范围），trace 中可查。
- **泄漏测试**：pytest 用例覆盖三条通道——未来文档、未来行情、时间非法/同案例经验卡，断言任何路径都取不到；CI 必跑。
- **已知局限——参数记忆泄漏**：沙箱只能闸门工具层访问，无法阻止模型从预训练语料中"回忆"as_of 之后的真实结局。缓解与诚实框定：(a) 案例选取优先取 as_of 接近或晚于模型知识截止日的近期事件（见 4.1）；(b) 每案例跑一次**污染探针**（独立 prompt 直接问模型"as_of 后 ticker 发生了什么"，回答落盘并在 Eval Dashboard 作为案例级污染参考指标展示，每案例仅 +1 次调用）；(c) README 评估方法论章节明示：受污染案例的轨道 A 分数应解读为"评分管线正确性与校准行为的演示"，而非无污染的研究能力测量。此局限作为面试讨论点主动呈现。

### 3.3 可证伪声明 Schema（核心创新点 ②）

```json
{
  "claim_id": "c1",
  "statement": "NVDA closes >=5% above the as_of price on the 20th trading day after as_of",
  "type": "direction",            // direction | magnitude | volatility
  "ticker": "NVDA",
  "horizon_days": 20,             // 交易日（见判定语义）
  "prediction": {"direction": "up", "threshold_pct": 5.0},
  "confidence": 0.72,             // [0,1]，用于校准分析
  "evidence": ["chunk_014", "chunk_027"]
}
```

memo 与 claims 一律**英文生成**（中英切换仅作用于 UI 界面文案字典）。研报 memo = 叙述性 markdown 段落 + claims 数组，两者由 Analyst 一次生成。

**判定语义（评分器规格，同时是 test_grader.py 的测试规格）**：
1. 基准价 `P0` = as_of 当日复权收盘价；as_of 非交易日则取之前最近交易日收盘价。
2. 交易日计数：数据缓存中 as_of 之后的第 N 根日线 bar（as_of 非交易日自下一交易日起算）；案例入库时校验缓存覆盖最大 horizon。
3. `direction`：**at-horizon-end 语义**——记 `r = P(第 horizon_days 根 bar 收盘)/P0 − 1`；up 命中 ⟺ `r ≥ threshold_pct/100`，down 命中 ⟺ `r ≤ −threshold_pct/100`。不采用"路径内任意时点触及"语义。
4. `magnitude`：`prediction = {"low_pct": x, "high_pct": y}`，命中 ⟺ horizon 末收益率 `r×100 ∈ [x, y]`（闭区间）。聚合只报区间覆盖率，不做幅度误差。
5. `volatility`：`prediction = {"relation": "above"|"below", "percentile": p}`；实现为 horizon 窗口内日对数收益标准差（不年化）与 as_of 前 252 个交易日同长度滚动窗口分布的 p 分位比较。
6. 评分结果 `grade_status ∈ {hit, miss, ungradable}`：行情数据不足覆盖 horizon、或声明被降级 `unverified` 时记 `ungradable`，不计入命中率与 Brier。Critic 的"horizon 超界"检查基准 = 案例 `meta.json` 的结局窗口长度。

### 3.4 三轨评估引擎（核心创新点 ③）

Run 结束即评（回测场景下"未来"已实现）。**执行顺序：A 轨先行，其结果作为 B 轨输入**：

- **A. 客观结局（outcome）**：按 3.3 判定语义机械评分；聚合指标：方向命中率、区间覆盖率、**Brier 分数**、**校准图**。校准图以分桶散点 + 完美校准对角线呈现（非平滑折线），每桶标注样本数 n；Dashboard 所有聚合指标旁显示样本数。
- **B. 过程质量（process）+ 失败归因**：LLM 裁判（独立 prompt）接收 memo、证据原文与 A 轨逐条命中结果，打分：引用接地率（抽查证据原文是否支撑声明）、推理一致性、检索充分性；并为每条**未命中**声明输出归因枚举 `failure_attribution ∈ {evidence_missing, misread_evidence, reasonable_but_wrong}`——区分"检索没找到 / 推理误读 / 过程正确但市场噪声"。裁判输出结构化 JSON，同样过 Schema 校验。
  - **裁判元评估**：评估套件出分后，作者人工标注 10–20 条裁判判例，方法论文档报告裁判-人工一致率；配额允许时对 3–5 条样本重跑 3 次报告自一致性（"尽量"优先级，并入 D4）。
  - 裁判默认同主模型（`JUDGE_MODEL` 可覆盖）。方法论文档明示 self-preference bias，并说明 v1 排行榜对比不跨主模型、偏好近似常量偏移、不影响配置间相对排序；若配额允许，录制演示 runs 时用第二模型作对照裁判（录制/回放层使对照成本一次性）。
- **C. 成本效率（cost）**：token 台账（每 Agent、每步）、调用次数、延迟、按供应商单价折算成本；派生指标"每条命中声明的成本"。
- **污染探针**（见 3.2）：案例级参考指标，随三轨分数一起展示。

**评估套件（EvalSuite）**：N 个案例（ticker × as_of）× M 个配置，批量运行出分，结果入 SQLite，排行榜页可视化。**统计诚实框定**：3 案例样本量下所有聚合指标定位为回归/诊断信号与机制演示，而非统计结论；同 run 内声明彼此相关（同标的同时段），不满足独立样本假设——方法论文档设"统计局限与指标定位"一节明示效力边界，统计显著性依赖案例集扩展（EvalSuite 的可扩展设计正为此预留）。

**评估驱动迭代留痕**：自 D2 起维护 `docs/eval-log.md`——每次 prompt/架构改动记录改动前后评估套件分数，作为 "evaluation as the primary mechanism to guide behavior" 的开发期实物证据，面试直接展示。

### 3.5 经验库（核心创新点 ④）

- 评分后生成经验卡：`{source_case_id, source_run_id, as_of, outcome_window_end, 案例特征(标的/事件类型/市场状态), 研究策略摘要, 声明结局, lesson: {attribution 枚举, 一句话}}`。
- **写入规则**：经验卡在评分后无条件写入（与 RunConfig 无关）；`RunConfig.memory_on` 只控制 Planner 是否**读取**。
- **检索规则（时间闸门，三条硬约束）**：
  1. `outcome_window_end <= 当前run.as_of`——结局尚未完全实现的经验对本 run 是未来信息，不可见；该过滤天然保证案例 X 自己的经验卡永远不会注入案例 X 的 run。
  2. `source_case_id != 当前案例`（leave-one-out 双保险，防答案泄漏）。
  3. EvalSuite 内所有 run 只读**套件启动前已存在**的经验卡（`created_at < suite.started_at`），消除套件内执行顺序依赖，保证配置可比。
- 满足约束的候选按特征相似度（BM25 over 特征文本，v1 不上向量）取 top-3 注入 Planner 上下文。
- **代际对比构造**：第 1 代 `memory_off` 跑完整套件（同时积累经验卡），第 2 代同一套件 `memory_on` 重跑（读到的正是第 1 代的时间合法经验），两代分数对比即 Leaderboard 代际曲线。3 个案例的 as_of 按时间错开排布，且前序案例的结局窗口先于后序案例的 as_of 结束，使后序案例确有合法经验可用；若某案例无可用卡则在方法论文档明示。分数对比**演示 improve-over-time 的度量机制**（3 案例为机制演示，非统计结论）。

### 3.6 配置对比（B 精简版）

`RunConfig = {model, temperature, max_steps, memory_on, context_budget, retrieval_top_k}`。

- **context_budget 语义**：Analyst 输入证据集的 token 上限；Researcher 累积证据超限时按检索相关性得分从低到高裁剪，每次裁剪写一条 `context_trim` trace 事件（丢弃的 chunk_id + 原因），可观测、可回放。滚动摘要压缩不做（YAGNI）。主模型 500k 上下文，该预算是人为约束，正好构成成本-质量权衡叙事。
- v1 预置三个配置构成两条对比轴：`memory_on/off` × `context_budget 2k vs 8k`（如 base / +memory / +memory+tight-context）。
- 配置对比以**同案例配对差值**（paired per-case delta）呈现而非绝对分排名；排行榜 UI 注明样本量局限。质量-成本散点图中 context_budget 是有数据支撑的对比轴。

## 4. 数据设计

### 4.1 数据源（美股为主 + 适配器预留）

- **行情 ground truth**：yfinance 日线 OHLCV，**显式传 `auto_adjust=True`**（统一复权口径，不依赖版本默认值）。每案例的行情在案例制作时一次性拉取并**冻结**为 `datasets/<case_id>/bars.json`（同一快照产出基准价与结局价，随 git 分发，保证评分可复现）；`data_cache/` 仅作开发期临时缓存（gitignore）。数据层定义 `MarketDataSource` 协议（`get_bars(ticker, start, end)`），yfinance 为默认实现，AkShare/OKX 留接口不实现（README 说明扩展方式）。
- **研究语料**：随仓库分发的精选案例包（`datasets/<case_id>/docs/*.md`），每篇为 markdown + frontmatter 元数据（`title, source, published_at, url, doc_type`）。来源：SEC 公开文件、财报电话会纪要、公开新闻摘要（注明出处）。**至少 1 个案例包含 1 篇 8k+ token 全文级文档**（如 10-Q MD&A 完整章节——SEC 公开文件可完整分发，绕开版权约束），为"长文档 deep research"考点提供真实载体。
- **3 个演示案例**（初选，实施时可调；as_of 按时间错开升序排布，见 3.5）：
  1. NVDA 2025Q1（FY2026Q1）财报季，as_of 取财报发布前数日——AI 叙事高热，多空证据丰富；含 10-Q 全文文档。
  2. TSLA 2025Q2 交付数据事件，as_of 取交付数据公布前——方向分歧大，适合展示辩证分析。
  3. **失败案例**（刻意保留，演示评估体系暴露过度自信的能力）：初选 SMCI 2025 年反弹叙事（主流叙事与真实结局相反的事件）。选择标准：语料中多头叙事浓厚、随后 20–40 个交易日被行情证伪；**需经"选候选→跑→验证失败形态"确认**（D2 晚间做），不做 D4 一次性人工挑选。
  - 案例选取附加准则：如可行，至少一个案例 as_of 接近或晚于模型知识截止日（2026 年事件、结局窗口已实现），最小化参数记忆污染（见 3.2）。
- 每案例 10–20 篇文档、语料覆盖 as_of 前 90 天、结局窗口在 `meta.json` 中定为确定值（20–40 个交易日之间）。
- **方法论披露**：失败案例系刻意挑选，用于演示评估体系的暴露能力，README 明示。

### 4.2 检索

- 入库：markdown 按标题/段落分块（约 300–500 token/块），块级元数据继承文档 `published_at`。
- 检索：rank-bm25（纯 Python、离线、确定性）+ 时间过滤；接口预留 `EmbeddingRetriever`（可选 API 向量，v1 不做）。语料为英文，检索查询由 Planner 的工具调用参数给出（英文）；Researcher 是确定性的证据管理阶段（工具执行、证据去重、context_budget 裁剪），不消耗 LLM 调用。
- 实现注意：BM25Okapi 在极小语料下 IDF 会把高频词打成 0 分（已实测），入库测试需设最小语料量下限。

### 4.3 存储

SQLite 单文件（`hindsight.db`）+ 文件落盘双轨：
- 表：`runs`（配置、状态、汇总分）、`experiences`、`llm_calls`（录制：请求哈希 → 响应，供回放与配额节省）。claims 与逐事件 trace 以 run 目录文件为权威（`claims.json`/`trace.jsonl`），不设独立表——D3 详情页直接读文件，排行榜读 `runs` 表汇总分（YAGNI：独立 claims/traces 表待真实查询需求出现再建）。
- 每个 run 同时落盘 `runs/<run_id>/`：memo.md、claims.json、trace.jsonl、scores.json——git 跟踪，录制的演示 run 随仓库分发。

### 4.4 LLM 接入

- OpenAI 兼容客户端；配置来自 `.env`：`LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`（当前：讯飞 MaaS `astron-code-latest`，GLM-5.2，500k 上下文，按次计费）。
- **D1 端点探针**（约 30 分钟脚本）：实测 (a) `tools/tool_choice` 原生函数调用支持度；(b) 纯 JSON 输出稳定性（连续 5 次合法率）。当天确定 Planner 走原生 function calling 还是 prompt-JSON 动作格式。
- **录制/回放层（必做）**：所有 LLM 调用经 `RecordingLLMClient`——记录模式写 `llm_calls`；回放模式按请求哈希查库命中则不发网络请求。`HINDSIGHT_OFFLINE=1` 强制回放，未命中显式报错（提示缺失的请求哈希）而非静默调 API。回放确定性要求：录制 run 固定 `temperature`、prompt 中不嵌入时钟时间戳（as_of 是业务字段不受影响）。节省按次配额 + 断网演示 + 测试夹具三合一。
- 裁判模型默认同主模型，`JUDGE_MODEL` 可覆盖（self-preference bias 讨论见 3.4）。

## 5. API 设计（FastAPI）

- `GET /api/cases` — 案例列表（含语料统计、as_of、结局窗口）
- `GET /api/cases/{id}/bars` — 该案例覆盖窗口的完整日线 OHLCV（含结局窗口，读冻结快照）。**纯展示端点**：时间沙箱只约束 Agent 工具访问；as_of 遮罩与 "Reveal the future" 揭幕由前端客户端完成。
- `POST /api/runs` — 发起研究 run `{case_id, config}` → `{run_id}`
- `GET /api/runs/{id}` — run 详情（memo、claims、scores、归因、成本）
- `WS /api/runs/{id}/stream` — 实时事件流（Agent 步骤、工具调用、token 计数）
- `GET /api/runs/{id}/trace` — 完整 trace（回放用）
- `POST /api/eval/suites` — 发起批量评估，立即返回 `{suite_id}` 异步执行；`GET /api/eval/suites/{id}` 轮询状态与逐案例进度
- `GET /api/leaderboard?suite_id=` — 配置对比数据（配对差值）
- `GET /api/experiences` — 经验库浏览

事件流协议：`{type: plan_step|tool_call|tool_result|agent_output|validation|context_trim|score|audit, agent, payload, tokens, ts}` ——前端实时渲染与事后回放共用同一协议。`audit` 事件承载沙箱 `AuditEntry` 载荷（由 D2 编排器在每次沙箱访问后转发进 trace），供 Trace Explorer 的审计日志视图使用。声明卡片"点击展开原文"由前端从 trace 的 `tool_result` payload 中按 chunk_id 解析证据全文，不设独立证据端点。

## 6. 前端（React 18 + Vite + TS + Tailwind + Recharts）

深色量化终端风格（深底、等宽数字、绿涨红跌语义色），中英双语（轻量字典 + 顶栏 EN/中 切换，默认英文；LLM 生成内容为英文，不参与切换）。四页：

1. **Research Studio**：左侧案例选择 + as_of 时间轴滑块 + 配置选择；中间 K 线图（as_of 右侧遮罩为"未知的未来"）；右侧 Agent 实时工作流（步骤卡片流式追加）。run 完成 → memo 渲染 + 声明卡片（引用可点击展开原文）→ 高光交互 **"Reveal the future"**：K 线揭幕延伸，声明卡逐条判绿/红，Brier 分数浮现。
2. **Trace Explorer**：步骤时间线树 + 每步 prompt/响应/token 折叠面板 + 沙箱审计日志视图 + 成本累计条。
3. **Eval Dashboard**：单 run 评分卡（三轨 + 污染探针）+ 校准分桶散点图（含 n 标注）+ 声明明细表（判红声明带归因徽标列）。
4. **Leaderboard**：套件 × 配置矩阵（配对差值）、质量-成本散点、经验库开关代际对比曲线。可选加分项（时间富余）：run 级"过程分 × 命中率"2×2 象限散点（复用既有分数与 Recharts）。

演示模式：页面均可从录制 run 渲染，无后端 LLM 依赖。WebSocket 断连自动降级为轮询。

## 7. 目录结构

```
hindsight/
├── backend/
│   ├── hindsight/
│   │   ├── agents/          # planner.py researcher.py analyst.py critic.py orchestrator.py
│   │   ├── sandbox/         # gate.py audit.py errors.py
│   │   ├── rag/             # ingest.py chunker.py bm25_retriever.py
│   │   ├── tools/           # registry.py market_data.py corpus_search.py calc.py
│   │   ├── eval/            # outcome_grader.py judge.py calibration.py suite.py probe.py
│   │   ├── memory/          # experience.py
│   │   ├── trace/           # recorder.py events.py cost_ledger.py
│   │   ├── llm/             # client.py recording.py
│   │   ├── data/            # market_source.py cache.py models.py
│   │   ├── api/             # app.py routes/ ws.py
│   │   └── schemas.py       # Pydantic：Claim, Memo, RunConfig, Scores, Experience...
│   ├── tests/               # test_sandbox_leakage.py test_grader.py test_claims_schema.py test_replay.py ...
│   └── pyproject.toml
├── frontend/                # Vite + React + TS + Tailwind
├── datasets/                # <case_id>/{meta.json, bars.json, docs/*.md}
├── runs/                    # 录制的演示 run（git 跟踪，随仓库分发）
├── docs/                    # 架构、评估方法论（含"统计局限与指标定位"一节）、eval-log.md
├── README.md                # 双语旗舰 README
└── .env.example
```

## 8. 错误处理与降级

- LLM 输出不合 Schema → Critic 带错误反馈重试（≤2 次）→ 仍败标记 `unverified`（评分记 `ungradable`），run 不中断。
- LLM API 网络错误 → 指数退避重试 3 次 → 失败则 run 置 `failed`，trace 保留已完成步骤。
- 回放未命中（OFFLINE 模式）→ 显式报错并提示缺失的请求哈希。
- yfinance 拉取失败 → 案例制作期问题（运行期读冻结快照，无此风险）；制作期失败则重试或换数据窗口。
- WebSocket 断连 → 前端自动降级为轮询 `GET /runs/{id}`。

## 9. 测试策略

优先级排序（4 天内必须 vs 尽量）：
1. **必须**：沙箱泄漏测试（未来文档/未来行情/时间非法与同案例经验卡三通道不可达）、结局评分器判定逻辑（构造已知结局的假数据，含一个结局窗口内拆股的构造用例验证复权序列判定）、Claim Schema 校验与 Critic 一致性规则、录制/回放层（离线命中与未命中）。
2. **尽量**：BM25 时间过滤检索（含最小语料量下限）、校准分桶计算、API 冒烟测试（TestClient）、裁判元评估人工标注。
3. 前端：手工验收为主（时间有限），关键交互录 GIF 兼作 README 素材。
4. CI：GitHub Actions 跑 pytest（D1 一并建好，泄漏测试必跑）。

Agent prompt 质量本身不写单测——由评估套件量化，迭代记录进 `docs/eval-log.md`（吃自己的狗粮，这本身就是面试话术）。

## 10. 里程碑（4 天）

- **D1**：backend 骨架 + schemas + 时间沙箱 + 数据层（案例 1 行情拉取并冻结提交、语料入库、BM25 时间过滤）+ trace 记录器 + 录制/回放层 + 泄漏测试 + CI（pytest）+ **LLM 端点探针**（tools 支持度 + JSON 稳定性，定工具调用格式）+ **案例 1（NVDA）粗糙语料约 10 篇当日整理入库**（够测试与 e2e 用，精修留后）✅ 可 CLI 跑通"检索+行情"无 LLM 流程
- **D2**：四 Agent 管线 + 编排器 + 声明 Schema 全链路 + 三轨评估（含归因）+ 经验库 + 起 `docs/eval-log.md` ✅ CLI 端到端案例 1 出分（e2e run 经录制层自动落盘 `runs/<run_id>/`，即为 D3 前端夹具与演示素材草稿）。**晚间**：对案例 3 候选（SMCI）跑全链路，确认失败形态成立，不成立则换候选；案例 2 语料利用调试间隙整理。
- **D3**：FastAPI + WS + 前端 Research Studio / Trace Explorer / Eval Dashboard ✅ 浏览器完整演示一个 run。**晚间**：起草英文 README 骨架 + 架构图 banner（中文版后续由英文版翻译，半小时级）。
- **D4**：Leaderboard + UI 打磨 + 语料扩充至 3 案例并精修（frontmatter/published_at 核对）+ 重录最终演示 runs + GIF 定稿 + 双语 README 定稿（含评估方法论与统计局限）+ 裁判元评估标注 + 公开仓库 ✅ 断网演示彩排

## 11. 非目标（YAGNI）

- 不做实盘/下单/任何券商连接；不做用户系统与部署（本地跑）。
- 不做向量数据库/Embedding（接口预留）；不做爬虫（语料人工精选随库分发）。
- 不做滚动摘要式上下文压缩（context_budget 用排序裁剪实现）。
- 不做多空辩论模式（方案 C，时间富余再说）；不做 A 股/加密适配器实现（只留协议接口）。
- 不追求研究结论真的能赚钱——项目卖点是**评估基础设施**，失败案例反而是叙事素材。

## 12. 风险与保底

| 风险 | 保底 |
|---|---|
| 讯飞端点不支持/劣化 OpenAI tools 语义 | D1 探针决策；切换 prompt-JSON 动作格式（工具注册表与 trace 协议不变）。若走 prompt-JSON（意味着 D2 prompt 调试成本上升），经验库与校准分桶后移至 D3/D4，代际曲线降级为静态图表 |
| GLM-5.2 结构化输出不稳 | Critic 重试 + JSON 修复；prompt few-shot；最坏降级简化 Schema |
| 按次配额烧太快 | 录制/回放层 D1 就位；开发期反复跑同一请求零成本 |
| D4 被 D3 滑点挤压 | README 英文骨架与架构图已于 D3 完成，中文按翻译处理；GIF 可用 D2/D3 已录 run 先行制作；Leaderboard 降级为静态图表 |
| 4 天做不完前端四页 | 优先级：Studio > Trace > Eval > Leaderboard |
| 语料整理超时 | 案例从 3 减到 2；每案例文档从 20 减到 10（保留 1 篇 8k+ 长文档） |
| 面试官追问参数记忆污染 | 3.2 已知局限 + 污染探针 + 方法论章节主动讨论——把风险转化为方法论成熟度展示 |
| 演示现场翻车 | 录制回放模式彩排；README GIF 兜底 |
