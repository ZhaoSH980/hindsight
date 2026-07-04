import { useState, type CSSProperties } from "react";
import { useLang } from "../lib/i18n";
import type { TraceEvent } from "../lib/types";

interface Props {
  evt: TraceEvent;
  className?: string;
  style?: CSSProperties;
}

const RAIL_COLOR: Record<string, string> = {
  plan_step: "bg-accent",
  tool_call: "bg-violet",
  tool_result: "bg-violet",
  validation: "bg-amber",
  audit: "bg-up",
  score: "bg-up",
  context_trim: "bg-up",
};

const CHIP_STYLE: Record<string, string> = {
  plan_step: "border-accent/40 text-accent",
  tool_call: "border-violet/40 text-violet",
  tool_result: "border-violet/40 text-violet",
  validation: "border-amber/40 text-amber",
  audit: "border-up/40 text-up",
  score: "border-up/40 text-up",
  context_trim: "border-up/40 text-up",
};

function truncate(s: string, n = 90): string {
  return s.length > n ? `${s.slice(0, n)}…` : s;
}

function summarize(evt: TraceEvent): string {
  const p = (evt.payload ?? {}) as Record<string, unknown>;
  switch (evt.type) {
    case "plan_step":
      return truncate(String(p.thought ?? ""));
    case "tool_call": {
      const args = p.args ? JSON.stringify(p.args) : "";
      return `${String(p.tool ?? "")} ${truncate(args, 70)}`.trim();
    }
    case "tool_result":
      return `${String(p.tool ?? "")} → ${truncate(String(p.result ?? ""), 70)}`;
    case "validation":
      return `${String(p.layer ?? "")} ok=${String(p.ok ?? "")}`;
    case "audit": {
      const note = String(p.note ?? "");
      return `${String(p.tool ?? "")}${note ? ` — ${note}` : ""}`;
    }
    default:
      return evt.type;
  }
}

function isDenied(evt: TraceEvent): boolean {
  if (evt.type !== "audit") return false;
  const note = String((evt.payload as { note?: string })?.note ?? "");
  return note.toUpperCase().includes("DENIED");
}

export function EventRow({ evt, className, style }: Props) {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const denied = isDenied(evt);
  const rail = denied ? "bg-down shadow-glow-down" : (RAIL_COLOR[evt.type] ?? "bg-line");
  const chip = denied ? "border-down/40 text-down" : (CHIP_STYLE[evt.type] ?? "border-line text-muted");
  const p = (evt.payload ?? {}) as Record<string, unknown>;

  return (
    <div
      className={`flex gap-2 border-b border-line/60 last:border-0 animate-fade-up ${denied ? "bg-down/10" : ""} ${className ?? ""}`}
      style={style}
    >
      <div className={`w-1 shrink-0 rounded-full ${rail}`} />
      <div className="flex-1 py-1.5 pr-2 min-w-0">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="w-full flex items-center gap-2 text-left"
        >
          <span className="rounded bg-ink-700 px-1.5 py-0.5 font-mono text-[10px] text-muted shrink-0">
            {evt.agent}
          </span>
          <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] shrink-0 transition-colors ${chip}`}>
            {evt.type}
          </span>
          <span className="font-mono text-xs text-slate-300 truncate flex-1">
            {evt.type === "score" ? t("scoreSummary") : summarize(evt)}
          </span>
          {evt.tokens > 0 && (
            <span className="num text-[10px] text-muted shrink-0">{evt.tokens} {t("tokens")}</span>
          )}
          <span className="text-muted text-[10px] shrink-0">{open ? "▾" : "▸"}</span>
        </button>

        {open && (
          <div className="mt-1.5 flex flex-col gap-1.5">
            {evt.type === "audit" && (
              <div className="rounded border border-line bg-ink-900 p-2 font-mono text-[11px] flex flex-col gap-1">
                <div>
                  <span className="text-muted">{t("tool")}: </span>
                  <span className="text-slate-200">{String(p.tool ?? "—")}</span>
                </div>
                <div>
                  <span className="text-muted">{t("params")}: </span>
                  <span className="text-slate-200">{JSON.stringify(p.params ?? {})}</span>
                </div>
                <div>
                  <span className="text-muted">{t("dataMaxDate")}: </span>
                  <span className="text-slate-200">{String(p.data_max_date ?? "—")}</span>
                </div>
                {denied ? (
                  <div className="rounded bg-down/20 border border-down/50 px-1.5 py-1 text-down font-semibold animate-fade-in">
                    {t("denied")}: {String(p.note ?? "")}
                  </div>
                ) : (
                  p.note ? (
                    <div>
                      <span className="text-muted">{t("note")}: </span>
                      <span className="text-slate-200">{String(p.note)}</span>
                    </div>
                  ) : null
                )}
              </div>
            )}
            <pre className="whitespace-pre-wrap break-all rounded border border-line bg-ink-900 p-2 font-mono text-[11px] text-slate-300 max-h-64 overflow-y-auto">
              {JSON.stringify(evt.payload ?? {}, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
