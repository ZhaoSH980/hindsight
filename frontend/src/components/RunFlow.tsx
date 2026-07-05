import type { ReactNode } from "react";

import { useLang } from "../lib/i18n";
import { IconCompass, IconFlag, IconPen, IconSearch, IconShield } from "./icons";
import type { TraceEvent } from "../lib/types";

/** Live pipeline diagram derived purely from the trace event stream:
 *  planner → analyst → critic → scoring, with the sandbox standing guard.
 *  The active stage pulses, hand-off edges flow, critic rejections light a
 *  rewrite loop, denied lookaheads turn the sandbox chip red. */

type NodeState = "pending" | "active" | "done" | "failed";

interface Derived {
  stage: number; // 0 planner, 1 analyst(+rewrite loop), 3 scoring, 4 complete
  planSteps: number;
  toolCalls: number;
  checks: number;
  retries: number;
  audits: number;
  denied: number;
  detail: string;
}

function derive(events: TraceEvent[]): Derived {
  const d: Derived = {
    stage: 0, planSteps: 0, toolCalls: 0, checks: 0, retries: 0, audits: 0, denied: 0, detail: "",
  };
  for (const evt of events) {
    const p = (evt.payload ?? {}) as Record<string, unknown>;
    switch (evt.type) {
      case "plan_step": {
        d.planSteps += 1;
        d.detail = String(p.thought ?? "");
        break;
      }
      case "tool_call": {
        d.toolCalls += 1;
        const args = (p.args ?? {}) as Record<string, unknown>;
        if (p.tool === "finish_research") {
          d.stage = Math.max(d.stage, 1);
          d.detail = String(args.reason ?? "");
        } else {
          d.detail = String(args.query ?? p.tool ?? "");
        }
        break;
      }
      case "validation": {
        d.checks += 1;
        const failed = p.ok === false || (Array.isArray(p.errors) && (p.errors as unknown[]).length > 0);
        if (failed) {
          d.retries += 1;
          d.stage = Math.max(d.stage, 1); // back to the analyst's desk
        } else {
          d.stage = Math.max(d.stage, 3); // semantic pass -> judge is scoring
        }
        break;
      }
      case "audit": {
        d.audits += 1;
        if (String(p.note ?? "").toUpperCase().includes("DENIED")) d.denied += 1;
        break;
      }
      case "score": {
        d.stage = 4;
        break;
      }
    }
  }
  return d;
}

function nodeClass(state: NodeState): string {
  switch (state) {
    case "active":
      return "border-accent shadow-glow text-slate-100";
    case "done":
      return "border-up/40 text-slate-300";
    case "failed":
      return "border-down shadow-glow-down text-down";
    default:
      return "border-line text-muted opacity-60";
  }
}

function Edge({ from, to }: { from: NodeState; to: NodeState }) {
  const flowing = from === "done" && to === "active";
  const done = from === "done" && (to === "done" || to === "failed");
  return (
    <div className="flex-1 min-w-4 self-center" aria-hidden="true">
      <div
        className={`h-px w-full ${flowing ? "animate-shimmer" : ""}`}
        style={
          flowing
            ? {
                backgroundImage:
                  "linear-gradient(90deg, rgba(34,211,238,0.15), rgba(34,211,238,0.9), rgba(34,211,238,0.15))",
                backgroundSize: "200% 100%",
              }
            : { background: done ? "rgba(52,211,153,0.45)" : "rgba(28,39,64,1)" }
        }
      />
    </div>
  );
}

interface NodeProps {
  icon: ReactNode;
  label: string;
  sub: string;
  state: NodeState;
}

function Node({ icon, label, sub, state }: NodeProps) {
  return (
    <div className={`panel flex min-w-[7.5rem] flex-col items-center gap-0.5 px-3 py-2 transition-all duration-300 ${nodeClass(state)}`}>
      <div className="flex items-center gap-1.5">
        {icon}
        <span className="font-display text-xs font-semibold">{label}</span>
        {state === "active" && (
          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse-dot" aria-hidden="true" />
        )}
        {state === "done" && <span className="text-up text-[10px]">✓</span>}
      </div>
      <span className="num text-[10px] text-muted">{sub || " "}</span>
    </div>
  );
}

export function RunFlow({ events, status }: { events: TraceEvent[]; status: string }) {
  const { t } = useLang();
  const d = derive(events);
  const running = status === "running";
  const failed = status === "failed";
  const complete = status === "done" || d.stage >= 4;

  const stateFor = (idx: number): NodeState => {
    if (complete) return "done";
    // map stage -> which node index is live: 0->planner(0), 1->analyst(1), 3->scoring(3)
    const liveIdx = d.stage === 0 ? 0 : d.stage === 1 ? 1 : 3;
    if (idx < liveIdx) return "done";
    if (idx === liveIdx) return failed ? "failed" : running ? "active" : "pending";
    // the critic node sits between analyst and scoring: done once scoring starts,
    // "active" while a rewrite loop is in flight
    if (idx === 2 && d.stage === 1 && d.checks > 0) return running ? "active" : "pending";
    return "pending";
  };

  const s0 = stateFor(0);
  const s1 = stateFor(1);
  const s2 = d.stage >= 3 || complete ? (complete || d.stage >= 3 ? "done" : "pending") : stateFor(2);
  const s3 = stateFor(3);

  return (
    <section className="panel p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h3 className="hud-label">{t("flowTitle")}</h3>
        {/* sandbox guard chip — always on duty */}
        <span
          className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-[10px] ${
            d.denied > 0
              ? "border-down/50 bg-down/10 text-down"
              : "border-line text-muted"
          }`}
        >
          <IconSearch size={12} /> {t("agentSandbox")} <span className="num">{d.audits}</span>
          {d.denied > 0 && (
            <span className="font-semibold">· {t("feedAuditDenied")} ×{d.denied}</span>
          )}
        </span>
      </div>

      <div className="flex items-stretch gap-1 overflow-x-auto pb-1">
        <Node
          icon={<IconCompass size={15} />}
          label={t("agentPlanner")}
          sub={`${d.planSteps} ${t("flowSteps")} · ${d.toolCalls} ${t("flowTools")}`}
          state={s0}
        />
        <Edge from={s0} to={s1} />
        <Node icon={<IconPen size={15} />} label={t("agentAnalyst")} sub={d.stage >= 1 ? t("flowMemo") : ""} state={s1} />
        <Edge from={s1} to={s2} />
        <Node
          icon={<IconShield size={15} />}
          label={t("agentCritic")}
          sub={d.checks > 0 ? `${d.checks} ${t("flowChecks")}${d.retries > 0 ? ` · ↺${d.retries} ${t("flowRewrite")}` : ""}` : ""}
          state={s2}
        />
        <Edge from={s2} to={s3} />
        <Node icon={<IconFlag size={15} />} label={t("flowScoring")} sub={complete ? "✓" : ""} state={s3} />
      </div>

      {/* live action ticker */}
      {running && d.detail && (
        <p className="truncate font-mono text-[11px] text-muted animate-fade-in" key={d.detail}>
          ▸ {d.detail}
        </p>
      )}
    </section>
  );
}
