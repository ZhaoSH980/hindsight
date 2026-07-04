import { useLang } from "../lib/i18n";
import { pct } from "../lib/format";
import type { Claim } from "../lib/types";

interface Props { claim: Claim; revealed: boolean }

const STATUS_STYLE: Record<string, string> = {
  hit: "bg-up/15 text-up border-up/40",
  miss: "bg-down/15 text-down border-down/40",
  ungradable: "bg-ink-700 text-muted border-line",
};

const TYPE_KEY: Record<Claim["type"], "typeDirection" | "typeMagnitude" | "typeVolatility"> = {
  direction: "typeDirection",
  magnitude: "typeMagnitude",
  volatility: "typeVolatility",
};

export function ClaimCard({ claim, revealed }: Props) {
  const { t } = useLang();
  const status = claim.status;
  const confPct = Math.round(claim.confidence * 100);

  return (
    <div className="panel p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-accent">
            {t(TYPE_KEY[claim.type])}
          </span>
          <span className="text-muted text-xs font-mono">{claim.horizon_days}{t("days")}</span>
        </div>
        {revealed && status && (
          <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${STATUS_STYLE[status] ?? STATUS_STYLE.ungradable}`}>
            {status === "hit" ? t("hit") : status === "miss" ? t("miss") : t("ungradable")}
          </span>
        )}
      </div>

      <p className="text-sm text-slate-200 leading-snug">{claim.statement}</p>

      <div>
        <div className="flex items-center justify-between text-[10px] text-muted font-mono mb-1">
          <span>{t("confidence")}</span>
          <span>{confPct}%</span>
        </div>
        <div className="h-1.5 w-full rounded bg-ink-700 overflow-hidden">
          <div className="h-full bg-accent" style={{ width: `${confPct}%` }} />
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {claim.evidence.map((chunkId) => (
          <span key={chunkId} className="rounded bg-ink-700 px-1.5 py-0.5 font-mono text-[10px] text-muted">
            {chunkId}
          </span>
        ))}
      </div>

      {revealed && status && (
        <div className="border-t border-line pt-2 flex flex-col gap-1">
          {claim.realized_return_pct !== undefined && claim.realized_return_pct !== null && (
            <span className={`num text-xs ${claim.realized_return_pct >= 0 ? "text-up" : "text-down"}`}>
              {pct(claim.realized_return_pct / 100, 2)}
            </span>
          )}
          {claim.detail && <span className="text-xs text-muted">{claim.detail}</span>}
        </div>
      )}
    </div>
  );
}
