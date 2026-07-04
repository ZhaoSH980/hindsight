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
    viewTrace: "View full trace", noMemo: "No memo for this run.",
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
    viewTrace: "查看完整轨迹", noMemo: "本次运行没有备忘录。",
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
  },
} as const;

type Lang = keyof typeof dict;
type Key = keyof (typeof dict)["en"];

const LangCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string }>(
  { lang: "en", setLang: () => {}, t: (k) => k }
);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");
  const t = (k: Key) => dict[lang][k];
  return <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>;
}

export const useLang = () => useContext(LangCtx);
