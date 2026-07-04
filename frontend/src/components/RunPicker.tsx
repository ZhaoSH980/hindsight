import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { shortId } from "../lib/format";
import type { RunSummary } from "../lib/types";

export function RunPicker({ linkTo }: { linkTo: (runId: string) => string }) {
  const { t } = useLang();
  const [runs, setRuns] = useState<RunSummary[]>([]);

  useEffect(() => {
    api.runs().then(setRuns).catch(() => setRuns([]));
  }, []);

  return (
    <div className="p-6 flex flex-col gap-3">
      <h2 className="text-sm font-mono text-muted">{t("pickARun")}</h2>
      {runs.length === 0 ? (
        <p className="text-xs text-muted">{t("noRunsYet")}</p>
      ) : (
        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-mono text-muted">{t("recentRuns")}</span>
          {runs
            .slice()
            .reverse()
            .map((r) => (
              <Link
                key={r.run_id}
                to={linkTo(r.run_id)}
                className="panel p-3 flex flex-wrap items-center gap-3 hover:border-accent/60 transition-colors"
              >
                <span className="font-mono text-xs text-accent">{shortId(r.run_id, 24)}</span>
                <span className="text-xs text-slate-300">{r.case_id}</span>
                <span
                  className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${
                    r.status === "done"
                      ? "bg-up/15 text-up border-up/40"
                      : r.status === "failed"
                        ? "bg-down/15 text-down border-down/40"
                        : "bg-ink-700 text-muted border-line"
                  }`}
                >
                  {r.status}
                </span>
                <span className="text-[10px] text-muted font-mono ml-auto">{r.created_at}</span>
              </Link>
            ))}
        </div>
      )}
    </div>
  );
}
