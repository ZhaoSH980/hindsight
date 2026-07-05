import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { useRunStream } from "../lib/useRunStream";
import { PriceChart } from "../components/PriceChart";
import { ClaimCard } from "../components/ClaimCard";
import { HelpTip } from "../components/HelpTip";
import { ProvenanceBadge } from "../components/ProvenanceBadge";
import { CaseWizard } from "../components/CaseWizard";
import { RunFlow } from "../components/RunFlow";
import {
  IconCompass, IconFile, IconFlag, IconSearch, IconShield, IconWrench,
} from "../components/icons";
import type { Bar, CaseMeta, RunDetail, TraceEvent } from "../lib/types";

const TYPE_ICON: Record<string, (props: { size?: number; className?: string }) => JSX.Element> = {
  plan_step: IconCompass,
  tool_call: IconWrench,
  tool_result: IconFile,
  validation: IconShield,
  audit: IconSearch,
  score: IconFlag,
};

const STEPS = [
  { index: "01", title: "step1Title", desc: "step1Desc" },
  { index: "02", title: "step2Title", desc: "step2Desc" },
  { index: "03", title: "step3Title", desc: "step3Desc" },
  { index: "04", title: "step4Title", desc: "step4Desc" },
] as const;

const AGENT_KEY = {
  planner: "agentPlanner",
  analyst: "agentAnalyst",
  critic: "agentCritic",
  judge: "agentJudge",
  sandbox: "agentSandbox",
  eval: "agentEval",
  probe: "agentProbe",
} as const;

const TOOL_ACTION = {
  corpus_search: "feedSearchCorpus",
  price_history: "feedPriceHistory",
  calc: "feedCalc",
  finish_research: "feedFinish",
} as const;

/** The live feed narrates each raw trace event as a localized human sentence:
 *  who did what, with the salient argument. Raw payloads live in the Trace
 *  Explorer; this view is for humans watching the run. */
function EventLine({ evt }: { evt: TraceEvent }) {
  const { t } = useLang();
  const Icon = TYPE_ICON[evt.type];
  const p = (evt.payload ?? {}) as Record<string, unknown>;

  let action = evt.type;
  let detail = "";
  let danger = false;

  switch (evt.type) {
    case "plan_step": {
      action = t("feedThink");
      detail = String(p.thought ?? "");
      break;
    }
    case "tool_call": {
      const key = TOOL_ACTION[String(p.tool) as keyof typeof TOOL_ACTION];
      const args = (p.args ?? {}) as Record<string, unknown>;
      action = key ? t(key) : String(p.tool ?? evt.type);
      detail = String(
        args.query ?? args.expression ?? args.reason ??
        (args.lookback_days !== undefined ? `${args.lookback_days}d` : "")
      );
      break;
    }
    case "tool_result": {
      const key = TOOL_ACTION[String(p.tool) as keyof typeof TOOL_ACTION];
      action = `${key ? t(key) : String(p.tool ?? "")} · ${t("feedToolResult")}`;
      detail = String(p.result ?? "");
      break;
    }
    case "validation": {
      const failed = p.ok === false || (Array.isArray(p.errors) && p.errors.length > 0);
      action = failed ? t("feedValidationFail") : t("feedValidationPass");
      detail = String(p.layer ?? "");
      danger = failed;
      break;
    }
    case "audit": {
      const note = String(p.note ?? "");
      const denied = note.toUpperCase().includes("DENIED");
      action = denied ? t("feedAuditDenied") : t("feedAuditOk");
      detail = denied ? `${String(p.tool ?? "")} ${note}` : String(p.tool ?? "");
      danger = denied;
      break;
    }
    case "score": {
      action = t("scoreSummary");
      break;
    }
  }

  const agentKey = AGENT_KEY[evt.agent as keyof typeof AGENT_KEY];
  return (
    <div className={`animate-fade-up flex items-start gap-2 font-mono text-xs py-1 border-b border-line/60 last:border-0 ${danger ? "bg-down/10" : ""}`}>
      <span className="mt-0.5 shrink-0 text-muted">{Icon ? <Icon size={13} /> : "•"}</span>
      <span className="text-muted w-14 shrink-0">{agentKey ? t(agentKey) : evt.agent}</span>
      <span className={`shrink-0 ${danger ? "text-down font-semibold" : "text-slate-200"}`}>{action}</span>
      {detail && <span className="text-muted truncate">{detail}</span>}
    </div>
  );
}

export default function Studio() {
  const { t, lang } = useLang();
  const [cases, setCases] = useState<CaseMeta[]>([]);
  const [selected, setSelected] = useState<CaseMeta | null>(null);
  const [bars, setBars] = useState<Bar[]>([]);
  const [memoryOn, setMemoryOn] = useState(false);
  const [maxSteps, setMaxSteps] = useState(8);
  const [runId, setRunId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [revealed, setRevealed] = useState(false);
  // memo language follows the UI language until the user explicitly picks one
  const [memoLang, setMemoLang] = useState<"en" | "zh">(lang);
  const [memoLangTouched, setMemoLangTouched] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardNotice, setWizardNotice] = useState<string | null>(null);
  const [gridOpen, setGridOpen] = useState(false);

  const { events, status } = useRunStream(runId);
  const feedRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!memoLangTouched) setMemoLang(lang);
  }, [lang, memoLangTouched]);

  useEffect(() => {
    api.cases().then(setCases).catch(() => setCases([]));
  }, []);

  useEffect(() => {
    // scroll only the feed container — scrollIntoView would drag the whole
    // page down every 1.5s while the user is reading elsewhere
    const el = feedRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [events]);

  useEffect(() => {
    if (status === "done" && runId) {
      api.run(runId).then(setDetail).catch(() => setDetail(null));
    }
  }, [status, runId]);

  function selectCase(c: CaseMeta) {
    setSelected(c);
    setRunId(null);
    setDetail(null);
    setRevealed(false);
    api.bars(c.case_id).then((r) => setBars(r.bars)).catch(() => setBars([]));
  }

  async function startRun() {
    if (!selected || starting) return;
    setStarting(true);
    setDetail(null);
    setRevealed(false);
    try {
      const { run_id } = await api.startRun(selected.case_id, memoryOn, maxSteps, memoLang);
      setRunId(run_id);
    } finally {
      setStarting(false);
    }
  }

  const running = status === "running";
  const isFailed = status === "failed";
  const isDone = status === "done" && detail;

  return (
    <div className="p-6 flex flex-col gap-6">
      {/* 0. Hero — what is this thing? */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <div className="flex flex-col gap-3">
          <h1 className="font-display text-3xl lg:text-4xl font-semibold text-slate-100 glow-text leading-tight">
            {t("heroTitle")}
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">{t("heroTagline")}</p>
          <p className="text-xs text-muted leading-relaxed">{t("heroProblem")}</p>

          {/* decorative timeline: sealed past | as-of | unknown future */}
          <div aria-hidden="true" className="relative mt-3 h-10 select-none">
            {/* sealed past — solid */}
            <div className="absolute left-0 top-3 h-px w-1/2 bg-accent shadow-glow-sm" />
            {/* as-of tick */}
            <div className="absolute left-1/2 top-1 h-4 w-px -translate-x-1/2 bg-amber shadow-glow-amber" />
            <span className="absolute left-1/2 top-6 -translate-x-1/2 font-mono text-[10px] text-amber">
              {t("asOf")}
            </span>
            {/* unknown future — dashed, faded */}
            <div className="absolute right-0 top-3 w-1/2 border-t border-dashed border-accent/25" />
            <div className="absolute right-0 top-3 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-accent/60 animate-blink" />
          </div>
        </div>

        <div className="stagger grid grid-cols-2 gap-3">
          {STEPS.map((s) => (
            <div key={s.index} className="panel hud-corners p-3 flex flex-col gap-1">
              <span className="font-mono text-xs text-accent">{s.index}</span>
              <span className="text-sm font-semibold text-slate-200">{t(s.title)}</span>
              <p className="text-xs text-muted leading-relaxed">{t(s.desc)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 1. Case selector */}
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="hud-label">{t("selectCase")}</h2>
          <button
            type="button"
            onClick={() => setWizardOpen((o) => !o)}
            className="rounded border border-line px-3 py-1 font-mono text-xs text-accent transition hover:border-accent/60 hover:shadow-glow-sm"
          >
            + {t("newCase")}
          </button>
        </div>
        {wizardOpen && (
          <div className="mb-4">
            <CaseWizard
              onCancel={() => setWizardOpen(false)}
              onCreated={(caseId, windowOpen) => {
                setWizardOpen(false);
                setWizardNotice(windowOpen ? "created_window_open" : "created");
                api.cases().then((cs) => {
                  setCases(cs);
                  const created = cs.find((c) => c.case_id === caseId);
                  if (created) selectCase(created);
                }).catch(() => {});
              }}
            />
          </div>
        )}
        {wizardNotice && (
          <div className="mb-3 border-l-2 border-l-amber pl-3 text-xs text-slate-300">
            {t("wizCreated")}
            {wizardNotice === "created_window_open" && ` — ${t("wizWindowOpen")}`}
          </div>
        )}
        {/* featured (hand-authored) cases keep full cards — one focal tier */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {cases.filter((c) => !c.tags.includes("grid")).map((c) => (
            <button
              key={c.case_id}
              type="button"
              onClick={() => selectCase(c)}
              className={`panel panel-hover p-3 text-left ${
                selected?.case_id === c.case_id ? "border-accent shadow-glow" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-accent">{c.ticker}</span>
                <span className="text-[10px] font-mono text-muted">{c.as_of}</span>
              </div>
              <p className="text-sm text-slate-200 mt-1">
                {lang === "zh" && c.title_zh ? c.title_zh : c.title}
              </p>
              <p className="text-xs text-muted mt-1 line-clamp-2">
                {lang === "zh" && c.description_zh ? c.description_zh : c.description}
              </p>
              <div className="flex flex-wrap gap-1 mt-2">
                {c.tags.map((tag) => (
                  <span key={tag} className="rounded bg-ink-700 px-1.5 py-0.5 text-[10px] text-muted">
                    {tag}
                  </span>
                ))}
                <span className="rounded bg-ink-700 px-1.5 py-0.5 text-[10px] text-muted">
                  {c.n_docs} {t("docs")}
                </span>
              </div>
            </button>
          ))}
        </div>

        {/* the mechanical grid — the statistical sample, deliberately demoted
            to a collapsed compact tier so it can't drown the featured cases */}
        {cases.some((c) => c.tags.includes("grid")) && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setGridOpen((o) => !o)}
              className="flex items-center gap-2 font-display text-[11px] font-medium uppercase tracking-[0.14em] text-muted transition-colors hover:text-slate-200"
            >
              <span className={`inline-block transition-transform ${gridOpen ? "rotate-90" : ""}`}>▸</span>
              {t("gridCases")}
              <span className="num">({cases.filter((c) => c.tags.includes("grid")).length})</span>
              <span className="normal-case tracking-normal font-sans font-normal">— {t("gridCasesHint")}</span>
            </button>
            {gridOpen && (
              <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 animate-fade-in">
                {cases.filter((c) => c.tags.includes("grid")).map((c) => (
                  <button
                    key={c.case_id}
                    type="button"
                    onClick={() => selectCase(c)}
                    className={`panel panel-hover px-2.5 py-2 text-left ${
                      selected?.case_id === c.case_id ? "border-accent shadow-glow" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-accent">{c.ticker}</span>
                      <span className="num text-[10px] text-muted">{c.n_docs}</span>
                    </div>
                    <span className="font-mono text-[10px] text-muted">{c.as_of}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {selected && (
        <>
          {/* 2. Config row */}
          <section className="flex flex-wrap items-center gap-4 panel p-3">
            <div className="flex items-center gap-2 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={memoryOn}
                  onChange={(e) => setMemoryOn(e.target.checked)}
                  disabled={running}
                />
                {memoryOn ? t("memoryOnLabel") : t("memoryOffLabel")}
              </label>
              <HelpTip text={t("memoryHelp")} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              {t("maxSteps")}
              <input
                type="number"
                min={1}
                max={20}
                value={maxSteps}
                onChange={(e) => setMaxSteps(Number(e.target.value) || 8)}
                disabled={running}
                className="num w-16 rounded bg-ink-700 border border-line px-2 py-1 text-sm"
              />
            </label>
            <div className="flex items-center gap-2 text-sm">
              {t("researchLang")}
              <div className="flex rounded-md border border-line overflow-hidden">
                {(["en", "zh"] as const).map((l) => (
                  <button
                    key={l}
                    type="button"
                    disabled={running}
                    onClick={() => {
                      setMemoLang(l);
                      setMemoLangTouched(true);
                    }}
                    className={`px-2.5 py-1 font-mono text-xs transition-colors ${
                      memoLang === l
                        ? "bg-accent/15 text-accent"
                        : "text-muted hover:text-slate-200"
                    }`}
                  >
                    {l === "en" ? "EN" : "中文"}
                  </button>
                ))}
              </div>
              <HelpTip text={t("researchLangHelp")} />
            </div>
            <button
              type="button"
              onClick={startRun}
              disabled={running || starting}
              className="ml-auto flex items-center gap-2 rounded-md bg-accent px-4 py-1.5 text-sm font-semibold text-ink-950 shadow-glow transition hover:brightness-110 disabled:opacity-50"
            >
              {(running || starting) && (
                <span className="h-2 w-2 rounded-full bg-ink-950 animate-pulse-dot" />
              )}
              {running || starting ? t("running") : t("run")}
            </button>
          </section>

          {/* 3. Chart */}
          <section>
            <PriceChart bars={bars} asOf={selected.as_of} revealed={revealed} />
          </section>

          {/* 4a. Dynamic pipeline diagram, driven by the same event stream */}
          {runId && <RunFlow events={events} status={status} />}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 4. Live feed */}
            <section className="panel p-3 flex flex-col h-80">
              <div className="mb-2">
                <h3 className="hud-label">{t("liveFeed")}</h3>
                <p className="text-[10px] text-muted mt-1">{t("liveFeedHint")}</p>
              </div>
              <div ref={feedRef} className="flex-1 overflow-y-auto">
                {events.length === 0 && !running && (
                  <p className="text-xs text-muted">{t("waitingForRun")}</p>
                )}
                {events.map((evt, i) => (
                  <EventLine key={i} evt={evt} />
                ))}
              </div>
            </section>

            {/* 6. failed banner */}
            {isFailed && (
              <section className="panel border-down/50 shadow-glow-down p-4 flex flex-col gap-2 justify-center">
                <p className="text-down text-sm font-semibold">{t("failed")}</p>
                {runId && (
                  <Link
                    to={`/runs/${runId}/trace`}
                    className="w-fit rounded border border-line px-2.5 py-1 font-mono text-[11px] text-accent transition hover:border-accent/60 hover:shadow-glow-sm"
                  >
                    {t("viewTrace")}
                  </Link>
                )}
              </section>
            )}
          </div>

          {/* 5. Memo + claims + reveal */}
          {isDone && detail && (
            <section className="flex flex-col gap-4">
              {runId && (
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    to={`/runs/${runId}/trace`}
                    className="rounded border border-line px-2.5 py-1 font-mono text-[11px] text-accent transition hover:border-accent/60 hover:shadow-glow-sm"
                  >
                    {t("viewTrace")}
                  </Link>
                  <Link
                    to={`/runs/${runId}`}
                    className="rounded border border-line px-2.5 py-1 font-mono text-[11px] text-accent transition hover:border-accent/60 hover:shadow-glow-sm"
                  >
                    {t("viewEval")}
                  </Link>
                  <ProvenanceBadge scores={detail.scores} />
                </div>
              )}
              {detail.scores?.unverified && (
                <div className="panel border-amber/50 p-3 text-amber text-sm">{t("unverified")}</div>
              )}

              <div className="panel p-4">
                <h3 className="hud-label mb-2">{t("memo")}</h3>
                {detail.memo_md ? (
                  <pre className="whitespace-pre-wrap text-sm text-slate-200 font-sans">{detail.memo_md}</pre>
                ) : (
                  <p className="text-xs text-muted">{t("noMemo")}</p>
                )}
              </div>

              <div>
                <h3 className="hud-label mb-2">
                  {t("claims")}
                  <HelpTip text={t("claimsHelp")} />
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {detail.claims.map((claim) => (
                    <ClaimCard key={claim.claim_id} claim={claim} revealed={revealed} />
                  ))}
                </div>
              </div>

              {!revealed && (
                <div className="flex flex-col items-center gap-3 panel border-amber/40 shadow-glow-amber p-6">
                  <p className="text-xs text-muted">{t("revealHint")}</p>
                  <button
                    type="button"
                    onClick={() => setRevealed(true)}
                    className="rounded-md bg-amber px-8 py-2.5 text-sm font-bold text-ink-950 shadow-glow-amber transition hover:brightness-110"
                  >
                    {t("reveal")}
                  </button>
                </div>
              )}
              {revealed && (
                <p
                  className="text-center text-xs font-mono text-up"
                  style={{ textShadow: "0 0 12px rgba(52, 211, 153, 0.45)" }}
                >
                  {t("revealed")}
                </p>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
