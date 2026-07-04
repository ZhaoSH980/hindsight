import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { pct } from "../lib/format";
import { ScoreCards } from "../components/ScoreCards";
import { ConfidenceStrip } from "../components/ConfidenceStrip";
import { AttributionBadge } from "../components/AttributionBadge";
import { RunPicker } from "../components/RunPicker";
import { HelpTip } from "../components/HelpTip";
import type { Claim, RunDetail } from "../lib/types";

const TYPE_KEY: Record<Claim["type"], "typeDirection" | "typeMagnitude" | "typeVolatility"> = {
  direction: "typeDirection",
  magnitude: "typeMagnitude",
  volatility: "typeVolatility",
};

const STATUS_STYLE: Record<string, string> = {
  hit: "bg-up/15 text-up border-up/40",
  miss: "bg-down/15 text-down border-down/40",
  ungradable: "bg-ink-700 text-muted border-line",
};

export default function EvalDashboard() {
  const { t } = useLang();
  const { runId } = useParams<{ runId: string }>();
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [probeOpen, setProbeOpen] = useState(false);

  useEffect(() => {
    if (!runId || runId === "_") return;
    setDetail(null);
    setNotFound(false);
    setProbeOpen(false);
    api
      .run(runId)
      .then(setDetail)
      .catch(() => setNotFound(true));
  }, [runId]);

  const attributions = detail?.scores?.process?.attributions ?? {};
  const probe = detail?.scores?.contamination_probe;
  const isFailed = detail?.status === "failed";
  const isUnverified = detail?.scores?.unverified === true;

  const claimsSorted = useMemo(() => detail?.claims ?? [], [detail]);

  if (!runId || runId === "_") {
    return <RunPicker linkTo={(id) => `/runs/${id}`} />;
  }

  if (notFound) {
    return (
      <div className="p-6 flex flex-col gap-3">
        <p className="text-down text-sm">{t("runNotFound")}</p>
        <RunPicker linkTo={(id) => `/runs/${id}`} />
      </div>
    );
  }

  if (!detail) {
    return <div className="p-6 text-muted text-sm">{t("running")}</div>;
  }

  return (
    <div className="p-6 flex flex-col gap-4">
      {/* Header */}
      <section className="panel hud-corners p-4 flex flex-wrap items-center gap-4">
        <div>
          <div className="text-[10px] text-muted font-mono">{t("runHeader")}</div>
          <div className="font-mono text-sm text-accent">{runId}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted font-mono">{t("case")}</div>
          <div className="text-sm text-slate-200">{detail.case_id}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted font-mono">{t("createdAt")}</div>
          <div className="text-xs text-slate-300 font-mono">{detail.created_at ?? "—"}</div>
        </div>
        <Link
          to={`/runs/${runId}/trace`}
          className="ml-auto rounded border border-line px-2.5 py-1 font-mono text-xs text-accent transition-all duration-200 hover:border-accent/60 hover:shadow-glow-sm"
        >
          {t("viewTrace")}
        </Link>
      </section>
      <p className="text-xs text-muted">{t("evalsSubtitle")}</p>

      {/* Banners */}
      {isFailed && (
        <div className="panel border-down/50 p-3 text-down text-sm font-semibold">{t("failed")}</div>
      )}
      {isUnverified && (
        <div className="panel border-amber/50 p-3 text-amber text-sm">{t("unverified")}</div>
      )}

      {/* Score cards — tolerant of missing keys (failed runs carry only scores.status) */}
      <ScoreCards scores={detail.scores} />

      {/* Confidence vs outcome — every claim shown individually; honest at tiny n */}
      <section className="flex flex-col gap-2">
        <h3 className="hud-label">{t("confVsOutcome")}</h3>
        <ConfidenceStrip claims={detail.claims} />
        <div className="panel border-amber/40 border-l-2 border-l-amber p-3 text-xs text-slate-300 leading-relaxed">
          {t("calibrationHonesty")}
        </div>
      </section>

      {/* Claims table */}
      <section className="flex flex-col gap-2">
        <h3 className="hud-label">
          {t("claimsTable")}
          <HelpTip text={t("claimsHelp")} />
        </h3>
        {claimsSorted.length === 0 ? (
          <p className="text-xs text-muted">{t("noClaims")}</p>
        ) : (
          <div className="panel overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-muted border-b border-line font-mono">
                  <th className="py-2 px-3 font-normal">{t("id")}</th>
                  <th className="py-2 px-3 font-normal">{t("type")}</th>
                  <th className="py-2 px-3 font-normal">{t("statement")}</th>
                  <th className="py-2 px-3 font-normal text-right">{t("horizon")}</th>
                  <th className="py-2 px-3 font-normal text-right">{t("confidence")}</th>
                  <th className="py-2 px-3 font-normal">{t("status")}</th>
                  <th className="py-2 px-3 font-normal text-right">{t("realizedReturn")}</th>
                  <th className="py-2 px-3 font-normal">
                    <span className="inline-flex items-center gap-1">
                      {t("attribution")}
                      <HelpTip text={t("attributionHelp")} />
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {claimsSorted.map((claim) => {
                  const attribution = attributions[claim.claim_id];
                  return (
                    <tr key={claim.claim_id} className="border-b border-line/60 last:border-0 align-top">
                      <td className="py-2 px-3 font-mono text-muted">{claim.claim_id}</td>
                      <td className="py-2 px-3">
                        <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-accent">
                          {t(TYPE_KEY[claim.type] ?? "typeDirection")}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-200 max-w-md">{claim.statement}</td>
                      <td className="py-2 px-3 text-right num text-slate-300">
                        {claim.horizon_days}{t("days")}
                      </td>
                      <td className="py-2 px-3 text-right num text-slate-300">
                        {Math.round((claim.confidence ?? 0) * 100)}%
                      </td>
                      <td className="py-2 px-3">
                        {claim.status ? (
                          <span
                            className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${
                              STATUS_STYLE[claim.status] ?? STATUS_STYLE.ungradable
                            }`}
                          >
                            {claim.status === "hit" ? t("hit") : claim.status === "miss" ? t("miss") : t("ungradable")}
                          </span>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-right num">
                        {claim.realized_return_pct === undefined || claim.realized_return_pct === null ? (
                          <span className="text-muted">—</span>
                        ) : (
                          <span className={claim.realized_return_pct >= 0 ? "text-up" : "text-down"}>
                            {pct(claim.realized_return_pct / 100, 2)}
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        {claim.status === "miss" && attribution ? (
                          <AttributionBadge attribution={attribution} />
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Contamination probe — collapsible */}
      <section className="panel p-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="hud-label">
            {t("contaminationProbe")}
            <HelpTip text={t("probeHelp")} />
          </h3>
          <button
            type="button"
            onClick={() => setProbeOpen((o) => !o)}
            className="rounded border border-line px-2 py-0.5 font-mono text-[10px] text-muted transition-colors duration-200 hover:border-accent/60 hover:text-accent"
          >
            {probeOpen ? t("hideProbe") : t("showProbe")}
          </button>
        </div>
        {probeOpen && (
          <div className="mt-2 flex flex-col gap-2 animate-fade-in">
            <p className="text-xs text-muted">{t("probeHint")}</p>
            {probe ? (
              <pre className="whitespace-pre-wrap rounded border border-line bg-ink-900 p-3 font-mono text-xs text-slate-300">
                {probe}
              </pre>
            ) : (
              <p className="text-xs text-muted">{t("noProbe")}</p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
