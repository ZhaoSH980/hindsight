import { createContext, useContext, useState, type ReactNode } from "react";

const dict = {
  en: {
    studio: "Research Studio", trace: "Trace Explorer", evals: "Eval Dashboard",
    run: "Run research", running: "Running…", reveal: "Reveal the future",
    revealed: "Future revealed", maxSteps: "Max steps",
    claims: "Claims", memo: "Research memo", hit: "HIT", miss: "MISS",
    ungradable: "UNGRADABLE", failed: "Validation failed — no memo was produced",
    unverified: "Unverified: the semantic critic never approved this memo; claims are not scored",
    asOf: "as-of",
    theFuture: "the future does not exist yet",
    selectCase: "Select a case", docs: "docs", liveFeed: "Live feed",
    waitingForRun: "Start a run to see the agent think, step by step.",
    viewTrace: "View full trace", viewEval: "View evaluation", noMemo: "No memo for this run.",
    memoryOnLabel: "Memory on", memoryOffLabel: "Memory off",
    revealHint: "The outcome window has closed. See what actually happened.",
    confidence: "confidence",
    typeDirection: "DIR", typeMagnitude: "MAG", typeVolatility: "VOL", days: "d",
    runHeader: "Run", case: "Case", createdAt: "Created", config: "Config",
    statusQueued: "queued", statusRunning: "running", statusDone: "done", statusFailed: "failed",
    filterAll: "All", filterPlan: "Plan", filterTool: "Tool", filterValidation: "Validation",
    filterAudit: "Audit", filterScore: "Score",
    noEvents: "No events recorded for this run.",
    tokens: "tokens",
    tool: "Tool", params: "Params", dataMaxDate: "Data max date", note: "Note",
    denied: "DENIED lookahead",
    costFooter: "Token costs by agent", agent: "Agent", calls: "Calls",
    promptTokens: "Prompt", completionTokens: "Completion", totalTokens: "Total",
    noCostData: "No cost data recorded for this run.",
    runNotFound: "Run not found.",
    hitRate: "Hit rate", brier: "Brier score", groundingRate: "Grounding rate",
    reasoningConsistency: "Reasoning consistency", retrievalSufficiency: "Retrieval sufficiency",
    claimsTable: "Claims", id: "ID", type: "Type", statement: "Statement",
    horizon: "Horizon", status: "Status", realizedReturn: "Realized %", attribution: "Attribution",
    attrEvidenceMissing: "evidence missing", attrMisreadEvidence: "misread evidence",
    attrReasonableButWrong: "reasonable but wrong",
    contaminationProbe: "Contamination probe", probeHint: "Asked the model, unaided, what happened after the as-of date.",
    showProbe: "Show probe response", hideProbe: "Hide probe response",
    noProbe: "No contamination probe recorded for this run.",
    pickARun: "Pick a run", recentRuns: "Recent runs",
    noRunsYet: "No runs yet — start one from the Research Studio.",
    noClaims: "No claims recorded for this run.",
    leaderboard: "Leaderboard",
    pickASuite: "Pick a suite", recentSuites: "Recent suites",
    noSuitesYet: "No suites yet — run backend/hindsight/cli.py suite to produce one.",
    suiteHeader: "Suite", startedAt: "Started", casesLabel: "Cases", configsLabel: "Configs",
    matrixTitle: "Case × config matrix",
    deltaRow: "Δ vs base",
    grounding: "Grounding",
    sampleSizeHonesty: "N is small by design — this compares mechanisms, not statistical significance.",
    scatterTitle: "Quality vs. cost",
    scatterX: "total tokens", scatterY: "hit rate",
    noSuiteSelected: "Select a suite above to see its results.",
    suiteNotFound: "Suite not found.",

    // ——— narrative layer ———
    heroTitle: "Send a research agent back in time.",
    heroTagline:
      "Hindsight drops an AI research agent onto a past trading day, seals off everything after that date, forces it to commit falsifiable predictions — then grades them against what actually happened.",
    heroProblem:
      "Why a time machine? Because agent research skill is nearly impossible to grade. Ask it about today and nobody knows the answer yet. Ask it about the past and the model has already memorized the ending. The only honest exam is a sealed past with anti-cheat.",
    step1Title: "Pick a case",
    step1Desc: "Each case pins an as-of date — that day becomes the agent's “today”.",
    step2Title: "Research in the sandbox",
    step2Desc: "It searches filings, pulls prices, runs math. Anything dated after as-of is blocked on the spot — and the attempt is logged.",
    step3Title: "Commit falsifiable claims",
    step3Desc: "It must state concrete predictions with a confidence and a deadline. Vague hedging fails validation.",
    step4Title: "Reveal the future",
    step4Desc: "When the window closes, real market data grades every claim mechanically — and every miss gets a failure attribution.",
    traceSubtitle: "Every thought, every tool call, every blocked lookahead — the full replayable record of one run.",
    evalsSubtitle: "Three-track scoring for one run: outcome (was it right), process (how it worked), and cost.",
    leaderboardSubtitle: "Cases × configs, side by side: does switching on experience memory actually help?",
    liveFeedHint: "The agent's steps stream in live: plan → tool → validation → sandbox audit.",

    // ——— metric explainers ———
    hitRateHelp: "Share of gradable claims that came true. The sample is tiny — read it as a signal, not a statistic.",
    brierHelp: "Honesty of confidence: being confidently wrong costs the most. 0 = perfect, 0.25 ≈ coin-flip guessing. A low hit rate with a low Brier means the agent knew it was unsure.",
    groundingHelp: "How many key statements in the memo trace back to document chunks the agent actually retrieved. Does it cite what it read?",
    reasoningHelp: "An LLM judge scores 1–5 whether the memo's conclusions actually follow from the evidence it cites.",
    retrievalHelp: "An LLM judge scores 1–5 whether the agent's searches covered the information that mattered for this case.",
    tokensHelp: "Total tokens across every LLM call in this run. Quality only means something next to its cost.",
    claimsHelp: "A falsifiable claim is a prediction that market data can mechanically grade as right or wrong once its deadline passes. These are the anchor of the whole evaluation.",
    attributionHelp: "Every miss is attributed to a cause: evidence missing (didn't find it), misread evidence (found it, read it wrong), or reasonable-but-wrong (sound process, uncooperative world — not the agent's fault).",
    probeHelp: "With no tools at all, the model is asked what happened after the as-of date. If it answers from memory, its training data leaks the future — and sandbox walls can't stop that. This probe detects it.",
    memoryHelp: "When on, the agent may read lessons distilled from earlier runs — but only from runs whose outcome window closed before this case's as-of date. The past may teach; the future may not.",

    // ——— memo language + run provenance ———
    researchLang: "Memo language",
    researchLangHelp: "The language the agent writes its memo and claims in. Recorded demo runs exist for both languages at default settings; in offline mode, other combinations have nothing to replay and will fail.",
    provReplay: "replayed from recordings",
    provLive: "live LLM calls",
    provHelp: "Identical requests are replayed byte-for-byte from the recorded-calls cache instead of hitting the API — that's why a repeated run with the same settings finishes in seconds, deterministically. Change any setting (language, memory, steps) to trigger real calls.",

    // ——— live feed narration ———
    agentPlanner: "planner", agentAnalyst: "analyst", agentCritic: "critic",
    agentJudge: "judge", agentSandbox: "sandbox", agentEval: "eval", agentProbe: "probe",
    feedThink: "thinks", feedSearchCorpus: "searches filings", feedPriceHistory: "pulls price history",
    feedCalc: "calculates", feedFinish: "finishes research", feedToolResult: "returns",
    feedValidationPass: "validation passed", feedValidationFail: "validation failed",
    feedAuditOk: "sandbox check", feedAuditDenied: "BLOCKED lookahead",
    flowTitle: "Execution flow", flowRewrite: "rewrite", flowSteps: "steps",
    flowTools: "tool calls", flowChecks: "checks", flowScoring: "Scoring",
    flowMemo: "Memo",

    // ——— case wizard ———
    newCase: "New case", newCaseTitle: "Create a case",
    newCaseIntro: "A case is a sealed moment in time: pick a ticker and an as-of date, then paste documents that were genuinely published before that date. Prices are fetched and frozen automatically.",
    newCaseHonesty: "The evaluation is only as honest as this corpus. Every document must truly predate the as-of date — the wizard rejects wrong dates, but the truthfulness of the text is on you.",
    wizTicker: "Ticker", wizAsOf: "As-of date", wizWindow: "Outcome window (trading days)",
    wizTitleEn: "Title (English)", wizTitleZh: "Title (Chinese, optional)",
    wizDescEn: "Description (English)", wizDescZh: "Description (Chinese, optional)",
    wizTags: "Tags (comma separated)",
    wizDocs: "Documents", wizAddDoc: "Add document", wizRemoveDoc: "Remove",
    wizDocTitle: "Document title", wizDocDate: "Published date", wizDocSource: "Source",
    wizDocUrl: "URL (optional)", wizDocText: "Full text (paste here)",
    wizDocDateBad: "published after as-of — will be rejected",
    wizMinDocs: "At least 2 documents; 5+ recommended for meaningful retrieval.",
    wizSubmit: "Create case", wizSubmitting: "Creating…",
    wizCancel: "Cancel",
    wizCreated: "Case created",
    wizWindowOpen: "Note: the outcome window has not fully closed yet — some claims may grade as ungradable until it does.",
    wizNeedsOnline: "Creating a case fetches live market data — the server must run in online mode.",
    edgarSection: "Import SEC filings (one click)",
    edgarHint: "Filing dates are stamped by the SEC itself — the one automatable source whose dates cannot lie. News articles still need manual curation.",
    edgarSearch: "Find filings", edgarSearching: "Searching EDGAR…",
    edgarImport: "Import selected", edgarImporting: "Importing…",
    edgarNone: "No filings found before the as-of date (the search covers EDGAR's most recent ~1000 filings).",
    edgarNeedTickerDate: "Enter ticker and as-of date first.",
    featuredCases: "Featured cases", gridCases: "Mechanical grid",
    showGrid: "Show all", hideGrid: "Collapse",
    gridCasesHint: "Fixed universe × pre-committed dates, corpus by rule — the statistical sample behind the leaderboard.",

    // ——— confidence vs outcome (calibration replacement) ———
    confVsOutcome: "Confidence vs. outcome",
    confVsOutcomeHint: "Each marker is one claim, placed at the confidence the agent stated. Green = hit, red = miss. A well-calibrated agent keeps its misses to the left and earns its right-side dots.",
    scoreSummary: "outcome + process scored",
    calibrationHonesty: "Why no calibration curve? Bucketed calibration needs dozens of claims to mean anything; a single run has three to five. Drawing a curve from that would be self-deception — so we show every claim instead.",
    noGradedClaims: "Claims have not been graded yet — reveal the future first.",
  },
  zh: {
    studio: "研究台", trace: "轨迹回放", evals: "评估看板",
    run: "开始研究", running: "运行中…", reveal: "揭示未来",
    revealed: "未来已揭示", maxSteps: "最大步数",
    claims: "可证伪声明", memo: "研究备忘录", hit: "命中", miss: "未中",
    ungradable: "不可评分", failed: "校验失败——未产出备忘录",
    unverified: "未验证：语义审查未通过，声明不计分",
    asOf: "研究基准日",
    theFuture: "未来尚不存在",
    selectCase: "选择案例", docs: "份文档", liveFeed: "实时动态",
    waitingForRun: "开始一次运行，逐步查看智能体的思考过程。",
    viewTrace: "查看完整轨迹", viewEval: "查看评分详情", noMemo: "本次运行没有备忘录。",
    memoryOnLabel: "记忆已开启", memoryOffLabel: "记忆已关闭",
    revealHint: "结果窗口已结束。看看实际发生了什么。",
    confidence: "置信度",
    typeDirection: "方向", typeMagnitude: "幅度", typeVolatility: "波动", days: "天",
    runHeader: "运行", case: "案例", createdAt: "创建时间", config: "配置",
    statusQueued: "排队中", statusRunning: "运行中", statusDone: "已完成", statusFailed: "失败",
    filterAll: "全部", filterPlan: "计划", filterTool: "工具", filterValidation: "校验",
    filterAudit: "审计", filterScore: "评分",
    noEvents: "本次运行没有记录任何事件。",
    tokens: "tokens",
    tool: "工具", params: "参数", dataMaxDate: "数据截止日期", note: "备注",
    denied: "拒绝：越界查看未来",
    costFooter: "按智能体统计的 Token 成本", agent: "智能体", calls: "调用次数",
    promptTokens: "输入", completionTokens: "输出", totalTokens: "合计",
    noCostData: "本次运行没有成本数据。",
    runNotFound: "未找到该运行。",
    hitRate: "命中率", brier: "Brier 分数", groundingRate: "依据覆盖率",
    reasoningConsistency: "推理一致性", retrievalSufficiency: "检索充分性",
    claimsTable: "声明列表", id: "编号", type: "类型", statement: "陈述",
    horizon: "周期", status: "状态", realizedReturn: "实际收益 %", attribution: "归因",
    attrEvidenceMissing: "证据缺失", attrMisreadEvidence: "误读证据",
    attrReasonableButWrong: "合理但错误",
    contaminationProbe: "污染探针", probeHint: "在不借助任何工具的情况下，询问模型基准日之后发生了什么。",
    showProbe: "显示探针回答", hideProbe: "隐藏探针回答",
    noProbe: "本次运行没有记录污染探针。",
    pickARun: "选择一次运行", recentRuns: "最近的运行",
    noRunsYet: "暂无运行——请从研究台发起一次运行。",
    noClaims: "本次运行没有记录任何声明。",
    leaderboard: "排行榜",
    pickASuite: "选择一个评测套件", recentSuites: "最近的套件",
    noSuitesYet: "暂无套件——运行 backend/hindsight/cli.py suite 以生成一个。",
    suiteHeader: "套件", startedAt: "开始时间", casesLabel: "案例", configsLabel: "配置",
    matrixTitle: "案例 × 配置 矩阵",
    deltaRow: "相对 base 的差值",
    grounding: "依据覆盖率",
    sampleSizeHonesty: "样本量小是刻意设计——本比较验证的是机制差异，而非统计显著性。",
    scatterTitle: "质量与成本",
    scatterX: "总 token 数", scatterY: "命中率",
    noSuiteSelected: "请在上方选择一个套件以查看结果。",
    suiteNotFound: "未找到该套件。",

    // ——— 叙事层 ———
    heroTitle: "把研究智能体送回过去",
    heroTagline:
      "Hindsight 把 AI 研究智能体投放到过去的某个交易日，封锁那一天之后的全部信息，强制它做出可证伪的预测——然后用真实发生的未来给它评分。",
    heroProblem:
      "为什么需要时光机？因为智能体的“研究能力”几乎无法评分：问它当下，答案还没揭晓；问它过去，模型早就背过结局。唯一诚实的考法，是一段被封印的过去，外加防作弊。",
    step1Title: "选择案例",
    step1Desc: "每个案例锁定一个研究基准日——那一天就是智能体的“今天”。",
    step2Title: "沙箱内研究",
    step2Desc: "它检索公告、拉取行情、做计算。任何晚于基准日的数据都会被当场拦截——而且每次越界尝试都留有记录。",
    step3Title: "提交可证伪声明",
    step3Desc: "必须给出带置信度、带期限的具体预测。含糊其辞过不了校验。",
    step4Title: "揭示未来",
    step4Desc: "结果窗口关闭后，真实行情机械评分每一条声明——每个错误都会被归因。",
    traceSubtitle: "每一步思考、每次工具调用、每次越界拦截——一次运行的完整可回放留痕。",
    evalsSubtitle: "一次运行的三轨评分：结局（对没对）、过程（怎么做的）、成本。",
    leaderboardSubtitle: "案例 × 配置并排对比：开启经验记忆到底有没有用？",
    liveFeedHint: "智能体的每一步实时推送：计划 → 工具 → 校验 → 沙箱审计。",

    // ——— 指标解释 ———
    hitRateHelp: "可评分声明中预测正确的比例。样本很小——当信号看，别当统计结论看。",
    brierHelp: "置信度的诚实度：错得越自信罚得越重。0 = 完美，0.25 ≈ 对半瞎猜。命中率低但 Brier 也低，说明智能体知道自己没把握。",
    groundingHelp: "备忘录里的关键论断有多少能追溯到智能体实际检索到的文档片段——它说的话有没有出处？",
    reasoningHelp: "LLM 裁判按 1–5 分评价：备忘录的结论是否真的能从它引用的证据推出来。",
    retrievalHelp: "LLM 裁判按 1–5 分评价：智能体的检索是否覆盖了这个案例真正关键的信息。",
    tokensHelp: "本次运行全部 LLM 调用的 token 总量。质量必须和成本放在一起看才有意义。",
    claimsHelp: "可证伪声明 = 到期后能用行情数据机械判定对错的预测。它是整个评测的锚点。",
    attributionHelp: "每条未命中都会被归因：证据缺失（该找的没找到）、误读证据（找到了但读错了）、合理但错误（过程没毛病，世界不配合——这不算智能体的错）。",
    probeHelp: "不给任何工具，直接问模型基准日之后发生了什么。如果它能靠记忆答出来，说明训练数据泄露了未来——沙箱的墙拦不住这条通道，探针专门检测它。",
    memoryHelp: "开启后，智能体可以读取从更早的运行中提炼的经验——但只限结果窗口在本案例基准日之前就已关闭的运行。过去可以教它，未来不行。",

    // ——— 研究语言 + 运行来源 ———
    researchLang: "研究语言",
    researchLangHelp: "智能体撰写备忘录和声明所用的语言。默认设置下两种语言都有已录制的演示运行；离线模式下，其它组合没有录制可回放，会运行失败。",
    provReplay: "录制回放",
    provLive: "次实时 LLM 调用",
    provHelp: "相同的请求会从录制缓存中逐字节回放，而不是真正调用 API——所以相同设置的重复运行几秒内就能确定性地完成。改变任何设置（语言、记忆、步数）都会触发真实调用。",

    // ——— 实时动态叙述 ———
    agentPlanner: "规划器", agentAnalyst: "分析师", agentCritic: "审查员",
    agentJudge: "裁判", agentSandbox: "沙箱", agentEval: "评估", agentProbe: "探针",
    feedThink: "思考", feedSearchCorpus: "检索语料", feedPriceHistory: "查询行情",
    feedCalc: "计算", feedFinish: "结束研究", feedToolResult: "返回结果",
    feedValidationPass: "校验通过", feedValidationFail: "校验未通过",
    feedAuditOk: "沙箱审计", feedAuditDenied: "拦截越界访问",
    flowTitle: "执行流程", flowRewrite: "次重写", flowSteps: "步",
    flowTools: "次工具", flowChecks: "次校验", flowScoring: "评分",
    flowMemo: "备忘录",

    // ——— 案例向导 ———
    newCase: "新建案例", newCaseTitle: "创建一个案例",
    newCaseIntro: "一个案例就是一个被封印的时间点：选定股票和研究基准日，然后粘贴真实发布于基准日之前的文档。行情会自动拉取并冻结。",
    newCaseHonesty: "评测的可信度完全取决于这份语料：每份文档必须真实发布于基准日之前——日期错误会被拒绝，但文本内容的真实性由你负责。",
    wizTicker: "股票代码", wizAsOf: "研究基准日", wizWindow: "结果窗口（交易日）",
    wizTitleEn: "标题（英文）", wizTitleZh: "标题（中文，可选）",
    wizDescEn: "描述（英文）", wizDescZh: "描述（中文，可选）",
    wizTags: "标签（逗号分隔）",
    wizDocs: "文档", wizAddDoc: "添加文档", wizRemoveDoc: "移除",
    wizDocTitle: "文档标题", wizDocDate: "发布日期", wizDocSource: "来源",
    wizDocUrl: "URL（可选）", wizDocText: "全文（粘贴到这里）",
    wizDocDateBad: "晚于基准日——会被拒绝",
    wizMinDocs: "至少 2 份文档；建议 5 份以上，检索才有意义。",
    wizSubmit: "创建案例", wizSubmitting: "创建中…",
    wizCancel: "取消",
    wizCreated: "案例已创建",
    wizWindowOpen: "注意：结果窗口尚未完全关闭——部分声明在窗口关闭前会评为不可评分。",
    wizNeedsOnline: "创建案例需要拉取实时行情——服务器必须以在线模式运行。",
    edgarSection: "一键导入 SEC 申报文件",
    edgarHint: "申报日期由 SEC 官方盖章——这是唯一日期不会说谎的可自动化来源。新闻类文档仍需人工甄别。",
    edgarSearch: "查询申报文件", edgarSearching: "正在查询 EDGAR…",
    edgarImport: "导入所选", edgarImporting: "导入中…",
    edgarNone: "基准日之前没有找到申报文件（查询范围为 EDGAR 最近约 1000 条申报）。",
    edgarNeedTickerDate: "请先填写股票代码和研究基准日。",
    featuredCases: "精选案例", gridCases: "机械网格",
    showGrid: "展开全部", hideGrid: "收起",
    gridCasesHint: "固定股票池 × 预定日期，语料按规则生成——排行榜统计背后的样本。",

    // ——— 置信度 vs 结果（替代校准曲线）———
    confVsOutcome: "置信度 vs 实际结果",
    confVsOutcomeHint: "每个标记是一条声明，位置就是智能体给出的置信度。绿色 = 命中，红色 = 未中。校准良好的智能体：错的都在左边，右边的点都对得起它的自信。",
    scoreSummary: "结局 + 过程已评分",
    calibrationHonesty: "为什么没有校准曲线？分桶校准需要几十条以上的声明才有统计意义，而单次运行只有三到五条——硬画一条曲线是自欺。所以我们把每条声明都直接画出来。",
    noGradedClaims: "声明尚未评分——请先揭示未来。",
  },
} as const;

type Lang = keyof typeof dict;
type Key = keyof (typeof dict)["en"];

const LangCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string }>(
  { lang: "en", setLang: () => {}, t: (k) => k }
);

const LANG_STORAGE_KEY = "hindsight.lang";

function initialLang(): Lang {
  try {
    const saved = window.localStorage.getItem(LANG_STORAGE_KEY);
    if (saved === "en" || saved === "zh") return saved;
  } catch {
    // storage unavailable (private mode etc.) — fall back to default
  }
  return "en";
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      window.localStorage.setItem(LANG_STORAGE_KEY, l);
    } catch {
      // best-effort persistence only
    }
  };
  const t = (k: Key) => dict[lang][k];
  return <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>;
}

export const useLang = () => useContext(LangCtx);
