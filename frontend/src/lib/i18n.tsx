import { createContext, useContext, useState, type ReactNode } from "react";

const dict = {
  en: {
    studio: "Research Studio", trace: "Trace Explorer", evals: "Eval Dashboard",
    run: "Run research", running: "Running…", reveal: "Reveal the future",
    revealed: "Future revealed", memory: "Experience memory", maxSteps: "Max steps",
    claims: "Claims", memo: "Research memo", hit: "HIT", miss: "MISS",
    ungradable: "UNGRADABLE", failed: "Validation failed — no memo was produced",
    unverified: "Unverified: the semantic critic never approved this memo; claims are not scored",
    probe: "Contamination probe", calibration: "Calibration", costs: "Token costs",
    auditLog: "Sandbox audit log", allEvents: "All events", asOf: "as-of",
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
    payload: "Payload", tokens: "tokens", expand: "Expand", collapse: "Collapse",
    tool: "Tool", params: "Params", dataMaxDate: "Data max date", note: "Note",
    denied: "DENIED lookahead",
    costFooter: "Token costs by agent", agent: "Agent", calls: "Calls",
    promptTokens: "Prompt", completionTokens: "Completion", totalTokens: "Total",
    noCostData: "No cost data recorded for this run.",
    runNotFound: "Run not found.",
    hitRate: "Hit rate", brier: "Brier score", groundingRate: "Grounding rate",
    reasoningConsistency: "Reasoning consistency", retrievalSufficiency: "Retrieval sufficiency",
    calibrationHint: "Confidence vs. realized hit rate, bucketed. Points on the diagonal are well-calibrated.",
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
    noCalibration: "No calibration data for this run.",
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
    statusOk: "ok",
  },
  zh: {
    studio: "研究台", trace: "轨迹回放", evals: "评估看板",
    run: "开始研究", running: "运行中…", reveal: "揭示未来",
    revealed: "未来已揭示", memory: "经验记忆", maxSteps: "最大步数",
    claims: "可证伪声明", memo: "研究备忘录", hit: "命中", miss: "未中",
    ungradable: "不可评分", failed: "校验失败——未产出备忘录",
    unverified: "未验证：语义审查未通过，声明不计分",
    probe: "污染探针", calibration: "校准", costs: "Token 成本",
    auditLog: "沙箱审计日志", allEvents: "全部事件", asOf: "研究基准日",
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
    payload: "载荷", tokens: "tokens", expand: "展开", collapse: "收起",
    tool: "工具", params: "参数", dataMaxDate: "数据截止日期", note: "备注",
    denied: "拒绝：越界查看未来",
    costFooter: "按智能体统计的 Token 成本", agent: "智能体", calls: "调用次数",
    promptTokens: "输入", completionTokens: "输出", totalTokens: "合计",
    noCostData: "本次运行没有成本数据。",
    runNotFound: "未找到该运行。",
    hitRate: "命中率", brier: "Brier 分数", groundingRate: "依据覆盖率",
    reasoningConsistency: "推理一致性", retrievalSufficiency: "检索充分性",
    calibrationHint: "置信度与实际命中率的分桶对比。落在对角线上表示校准良好。",
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
    noCalibration: "本次运行没有校准数据。",
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
    statusOk: "正常",
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
