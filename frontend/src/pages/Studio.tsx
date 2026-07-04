import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { useRunStream } from "../lib/useRunStream";
import { PriceChart } from "../components/PriceChart";
import { ClaimCard } from "../components/ClaimCard";
import type { Bar, CaseMeta, RunDetail, TraceEvent } from "../lib/types";

const TYPE_ICON: Record<string, string> = {
  plan_step: "\u{1F9ED}", // compass
  tool_call: "\u{1F527}", // wrench
  tool_result: "\u{1F4C4}", // page
  validation: "\u{1F6E1}", // shield
  audit: "\u{1F50D}", // magnifying glass
  score: "\u{1F3C1}", // checkered flag
};

function EventLine({ evt }: { evt: TraceEvent }) {
  const icon = TYPE_ICON[evt.type] ?? "•";
  const summary = useMemo(() => {
    const p = evt.payload ?? {};
    if (evt.type === "tool_call") return String((p as { tool?: string }).tool ?? evt.type);
    if (evt.type === "audit") return String((p as { note?: string }).note ?? evt.type);
    return evt.type;
  }, [evt]);
  return (
    <div className="flex items-start gap-2 font-mono text-xs py-1 border-b border-line/60 last:border-0">
      <span>{icon}</span>
      <span className="text-muted w-16 shrink-0">{evt.agent}</span>
      <span className="text-slate-300 truncate">{summary}</span>
    </div>
  );
}

export default function Studio() {
  const { t } = useLang();
  const [cases, setCases] = useState<CaseMeta[]>([]);
  const [selected, setSelected] = useState<CaseMeta | null>(null);
  const [bars, setBars] = useState<Bar[]>([]);
  const [memoryOn, setMemoryOn] = useState(false);
  const [maxSteps, setMaxSteps] = useState(8);
  const [runId, setRunId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [revealed, setRevealed] = useState(false);

  const { events, status } = useRunStream(runId);
  const feedEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    api.cases().then(setCases).catch(() => setCases([]));
  }, []);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
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
      const { run_id } = await api.startRun(selected.case_id, memoryOn, maxSteps);
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
      {/* 1. Case selector */}
      <section>
        <h2 className="text-sm font-mono text-muted mb-2">{t("selectCase")}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {cases.map((c) => (
            <button
              key={c.case_id}
              type="button"
              onClick={() => selectCase(c)}
              className={`panel p-3 text-left transition-colors hover:border-accent/60 ${
                selected?.case_id === c.case_id ? "border-accent" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-accent">{c.ticker}</span>
                <span className="text-[10px] font-mono text-muted">{c.as_of}</span>
              </div>
              <p className="text-sm text-slate-200 mt-1">{c.title}</p>
              <p className="text-xs text-muted mt-1 line-clamp-2">{c.description}</p>
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
      </section>

      {selected && (
        <>
          {/* 2. Config row */}
          <section className="flex flex-wrap items-center gap-4 panel p-3">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={memoryOn}
                onChange={(e) => setMemoryOn(e.target.checked)}
                disabled={running}
              />
              {memoryOn ? t("memoryOnLabel") : t("memoryOffLabel")}
            </label>
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
            <button
              type="button"
              onClick={startRun}
              disabled={running || starting}
              className="ml-auto rounded-md bg-accent px-4 py-1.5 text-sm font-semibold text-ink-950 disabled:opacity-50"
            >
              {running || starting ? t("running") : t("run")}
            </button>
          </section>

          {/* 3. Chart */}
          <section>
            <PriceChart bars={bars} asOf={selected.as_of} revealed={revealed} />
          </section>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 4. Live feed */}
            <section className="panel p-3 flex flex-col h-80">
              <h3 className="text-sm font-mono text-muted mb-2">{t("liveFeed")}</h3>
              <div className="flex-1 overflow-y-auto">
                {events.length === 0 && !running && (
                  <p className="text-xs text-muted">{t("waitingForRun")}</p>
                )}
                {events.map((evt, i) => (
                  <EventLine key={i} evt={evt} />
                ))}
                <div ref={feedEndRef} />
              </div>
            </section>

            {/* 6. failed banner */}
            {isFailed && (
              <section className="panel border-down/50 p-4 flex flex-col gap-2 justify-center">
                <p className="text-down text-sm font-semibold">{t("failed")}</p>
                {runId && (
                  <Link to={`/runs/${runId}/trace`} className="text-xs text-accent underline w-fit">
                    {t("viewTrace")}
                  </Link>
                )}
              </section>
            )}
          </div>

          {/* 5. Memo + claims + reveal */}
          {isDone && detail && (
            <section className="flex flex-col gap-4">
              {detail.scores?.unverified && (
                <div className="panel border-amber/50 p-3 text-amber text-sm">{t("unverified")}</div>
              )}

              <div className="panel p-4">
                <h3 className="text-sm font-mono text-muted mb-2">{t("memo")}</h3>
                {detail.memo_md ? (
                  <pre className="whitespace-pre-wrap text-sm text-slate-200 font-sans">{detail.memo_md}</pre>
                ) : (
                  <p className="text-xs text-muted">{t("noMemo")}</p>
                )}
              </div>

              <div>
                <h3 className="text-sm font-mono text-muted mb-2">{t("claims")}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {detail.claims.map((claim) => (
                    <ClaimCard key={claim.claim_id} claim={claim} revealed={revealed} />
                  ))}
                </div>
              </div>

              {!revealed && (
                <div className="flex flex-col items-center gap-2 panel p-6 border-accent/40">
                  <p className="text-xs text-muted">{t("revealHint")}</p>
                  <button
                    type="button"
                    onClick={() => setRevealed(true)}
                    className="rounded-md bg-accent px-6 py-2 text-sm font-semibold text-ink-950 shadow-lg shadow-accent/20"
                  >
                    {t("reveal")}
                  </button>
                </div>
              )}
              {revealed && (
                <p className="text-center text-xs font-mono text-up">{t("revealed")}</p>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
