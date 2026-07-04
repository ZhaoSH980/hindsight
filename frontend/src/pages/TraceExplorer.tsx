import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { num } from "../lib/format";
import { EventRow } from "../components/EventRow";
import type { RunDetail, TraceEvent } from "../lib/types";

type FilterKey = "all" | "plan_step" | "tool" | "validation" | "audit" | "score";

const FILTERS: { key: FilterKey; labelKey: "filterAll" | "filterPlan" | "filterTool" | "filterValidation" | "filterAudit" | "filterScore"; types: string[] }[] = [
  { key: "all", labelKey: "filterAll", types: [] },
  { key: "plan_step", labelKey: "filterPlan", types: ["plan_step"] },
  { key: "tool", labelKey: "filterTool", types: ["tool_call", "tool_result"] },
  { key: "validation", labelKey: "filterValidation", types: ["validation"] },
  { key: "audit", labelKey: "filterAudit", types: ["audit"] },
  { key: "score", labelKey: "filterScore", types: ["score", "context_trim"] },
];

const STATUS_STYLE: Record<string, string> = {
  queued: "bg-ink-700 text-muted border-line",
  running: "bg-accent/15 text-accent border-accent/40",
  done: "bg-up/15 text-up border-up/40",
  failed: "bg-down/15 text-down border-down/40",
};

const STATUS_KEY: Record<string, "statusQueued" | "statusRunning" | "statusDone" | "statusFailed"> = {
  queued: "statusQueued",
  running: "statusRunning",
  done: "statusDone",
  failed: "statusFailed",
};

export default function TraceExplorer() {
  const { t } = useLang();
  const { runId } = useParams<{ runId: string }>();
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [filter, setFilter] = useState<FilterKey>("all");

  useEffect(() => {
    if (!runId || runId === "_") return;
    setNotFound(false);
    setEvents([]);
    setDetail(null);
    Promise.all([api.trace(runId), api.run(runId)])
      .then(([trace, run]) => {
        setEvents(trace);
        setDetail(run);
      })
      .catch(() => setNotFound(true));
  }, [runId]);

  const counts = useMemo(() => {
    const c: Record<FilterKey, number> = { all: events.length, plan_step: 0, tool: 0, validation: 0, audit: 0, score: 0 };
    for (const evt of events) {
      for (const f of FILTERS) {
        if (f.key !== "all" && f.types.includes(evt.type)) c[f.key] += 1;
      }
    }
    return c;
  }, [events]);

  const visible = useMemo(() => {
    if (filter === "all") return events;
    const types = FILTERS.find((f) => f.key === filter)?.types ?? [];
    return events.filter((e) => types.includes(e.type));
  }, [events, filter]);

  const cost = detail?.scores?.cost;
  const costRows = useMemo(() => {
    if (!cost) return [];
    return Object.entries(cost).map(([agent, c]) => ({
      agent,
      calls: c.calls,
      prompt: c.prompt_tokens,
      completion: c.completion_tokens,
      total: c.prompt_tokens + c.completion_tokens,
    }));
  }, [cost]);
  const costTotals = useMemo(
    () =>
      costRows.reduce(
        (acc, r) => ({
          calls: acc.calls + r.calls,
          prompt: acc.prompt + r.prompt,
          completion: acc.completion + r.completion,
          total: acc.total + r.total,
        }),
        { calls: 0, prompt: 0, completion: 0, total: 0 }
      ),
    [costRows]
  );

  if (!runId || runId === "_") {
    return <div className="p-6 text-muted text-sm">{t("runNotFound")}</div>;
  }

  if (notFound) {
    return <div className="p-6 text-down text-sm">{t("runNotFound")}</div>;
  }

  return (
    <div className="p-6 flex flex-col gap-4">
      {/* Run header */}
      <section className="panel p-4 flex flex-wrap items-center gap-4">
        <div>
          <div className="text-[10px] text-muted font-mono">{t("runHeader")}</div>
          <div className="font-mono text-sm text-accent">{runId}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted font-mono">{t("case")}</div>
          <div className="text-sm text-slate-200">{detail?.case_id ?? "—"}</div>
        </div>
        {detail?.status && (
          <span className={`rounded border px-2 py-0.5 font-mono text-[10px] ${STATUS_STYLE[detail.status] ?? STATUS_STYLE.queued}`}>
            {t(STATUS_KEY[detail.status] ?? "statusQueued")}
          </span>
        )}
        <div>
          <div className="text-[10px] text-muted font-mono">{t("createdAt")}</div>
          <div className="text-xs text-slate-300 font-mono">{detail?.created_at ?? "—"}</div>
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[10px] text-muted font-mono">{t("config")}</div>
          <div className="text-xs text-slate-300 font-mono truncate">
            {detail?.config ? JSON.stringify(detail.config) : "—"}
          </div>
        </div>
      </section>

      {/* Filter pills */}
      <section className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setFilter(f.key)}
            className={`rounded-full border px-3 py-1 text-xs font-mono transition-colors ${
              filter === f.key
                ? "border-accent bg-accent/15 text-accent"
                : "border-line text-muted hover:text-slate-200"
            }`}
          >
            {t(f.labelKey)} <span className="num">{counts[f.key]}</span>
          </button>
        ))}
      </section>

      {/* Event list */}
      <section className="panel p-2">
        {visible.length === 0 ? (
          <p className="p-4 text-xs text-muted">{t("noEvents")}</p>
        ) : (
          <div className="flex flex-col">
            {visible.map((evt, i) => (
              <EventRow key={i} evt={evt} />
            ))}
          </div>
        )}
      </section>

      {/* Cost footer */}
      <section className="panel p-4">
        <h3 className="text-sm font-mono text-muted mb-3">{t("costFooter")}</h3>
        {costRows.length === 0 ? (
          <p className="text-xs text-muted">{t("noCostData")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <thead>
                <tr className="text-left text-muted border-b border-line">
                  <th className="py-1 pr-4 font-normal">{t("agent")}</th>
                  <th className="py-1 pr-4 font-normal text-right">{t("calls")}</th>
                  <th className="py-1 pr-4 font-normal text-right">{t("promptTokens")}</th>
                  <th className="py-1 pr-4 font-normal text-right">{t("completionTokens")}</th>
                  <th className="py-1 pr-4 font-normal text-right">{t("totalTokens")}</th>
                </tr>
              </thead>
              <tbody>
                {costRows.map((r) => (
                  <tr key={r.agent} className="border-b border-line/60 last:border-0">
                    <td className="py-1 pr-4 text-slate-200">{r.agent}</td>
                    <td className="py-1 pr-4 text-right num text-slate-300">{num(r.calls)}</td>
                    <td className="py-1 pr-4 text-right num text-slate-300">{num(r.prompt)}</td>
                    <td className="py-1 pr-4 text-right num text-slate-300">{num(r.completion)}</td>
                    <td className="py-1 pr-4 text-right num text-slate-200">{num(r.total)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t border-line font-semibold">
                  <td className="py-1 pr-4 text-slate-200">{t("totalTokens")}</td>
                  <td className="py-1 pr-4 text-right num text-slate-200">{num(costTotals.calls)}</td>
                  <td className="py-1 pr-4 text-right num text-slate-200">{num(costTotals.prompt)}</td>
                  <td className="py-1 pr-4 text-right num text-slate-200">{num(costTotals.completion)}</td>
                  <td className="py-1 pr-4 text-right num text-accent">{num(costTotals.total)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
