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
