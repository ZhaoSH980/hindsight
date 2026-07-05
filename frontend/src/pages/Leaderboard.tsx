import { Fragment, useEffect, useMemo, useState } from "react";
import {
  CartesianGrid, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import { num, pct } from "../lib/format";
import { HelpTip } from "../components/HelpTip";
import type { Scores, SuiteRunRow, SuiteStatus, SuiteSummary } from "../lib/types";

function parseJsonSafe<T>(text: string | null | undefined): T | null {
  if (!text) return null;
  try {
    return JSON.parse(text) as T;
  } catch {
    return null;
  }
}

// Mirrors backend/hindsight/eval/suite.py PRESETS — used to recover a run's
// config *name* from its recorded config_json, since the store only carries
// the RunConfig fields (memory_on, context_budget, pipeline), not the label.
const PRESET_SHAPES: {
  name: string;
  memory_on: boolean;
  context_budget: number;
  pipeline: string;
}[] = [
  { name: "base", memory_on: false, context_budget: 8000, pipeline: "full" },
  { name: "memory", memory_on: true, context_budget: 8000, pipeline: "full" },
  { name: "tight", memory_on: true, context_budget: 2000, pipeline: "full" },
  { name: "naive", memory_on: false, context_budget: 8000, pipeline: "naive" },
  { name: "no_planner", memory_on: false, context_budget: 8000, pipeline: "no_planner" },
];

function configNameForRun(run: SuiteRunRow, knownConfigs: string[]): string | null {
  const cfg = parseJsonSafe<{ memory_on?: boolean; context_budget?: number; pipeline?: string }>(
    run.config_json
  );
  if (!cfg) return null;
  const pipeline = cfg.pipeline ?? "full"; // configs recorded before the field default to full
  const candidates = PRESET_SHAPES.filter(
    (p) =>
      p.memory_on === cfg.memory_on &&
      p.context_budget === cfg.context_budget &&
      p.pipeline === pipeline
  ).map((p) => p.name);
  const match = candidates.find((c) => knownConfigs.includes(c)) ?? candidates[0];
  return match ?? null;
}

function totalTokens(scores: Scores | null | undefined): number | null {
  if (!scores?.cost) return null;
  return Object.values(scores.cost).reduce(
    (sum, c) => sum + (c?.prompt_tokens ?? 0) + (c?.completion_tokens ?? 0),
    0
  );
}

const CASE_LABEL_COLORS = ["#38bdf8", "#f59e0b", "#a78bfa", "#22c55e", "#ef4444", "#eab308"];
const CONFIG_COLORS: Record<string, string> = {
  base: "#7d8aa5",
  memory: "#22d3ee",
  tight: "#8b5cf6",
  naive: "#f87171", // the zero-intelligence floor reads as the red line
  no_planner: "#fbbf24",
};

function colorForConfig(name: string, idx: number): string {
  return CONFIG_COLORS[name] ?? CASE_LABEL_COLORS[idx % CASE_LABEL_COLORS.length];
}

function SuitePicker({
  suites,
  selected,
  onSelect,
}: {
  suites: SuiteSummary[];
  selected: string | null;
  onSelect: (suiteId: string) => void;
}) {
  const { t } = useLang();
  return (
    <div className="flex flex-col gap-3">
      <h2 className="hud-label">{t("pickASuite")}</h2>
      {!selected && <p className="text-xs text-muted">{t("leaderboardSubtitle")}</p>}
      {suites.length === 0 ? (
        <p className="text-xs text-muted">{t("noSuitesYet")}</p>
      ) : (
        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-mono text-muted">{t("recentSuites")}</span>
          {suites.map((s) => (
            <button
              key={s.suite_id}
              type="button"
              onClick={() => onSelect(s.suite_id)}
              className={`panel panel-hover p-3 flex flex-wrap items-center gap-3 text-left ${
                s.suite_id === selected ? "border-accent/60" : ""
              }`}
            >
              <span className="font-mono text-xs text-accent">{s.suite_id}</span>
              <span className="text-xs text-slate-300">{s.cases.join(", ")}</span>
              <span className="text-[10px] text-muted font-mono ml-auto">{s.started_at ?? "—"}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function fmtBrier(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : v.toFixed(3);
}

function deltaClass(better: boolean | null): string {
  if (better === null) return "text-muted";
  return better ? "text-up" : "text-down";
}

function hitRateClass(v: number | null | undefined): string {
  if (v === null || v === undefined) return "text-slate-200";
  return v >= 0.5 ? "text-up" : "text-down";
}

export default function Leaderboard() {
  const { t, lang } = useLang();
  const [suites, setSuites] = useState<SuiteSummary[]>([]);
  const [suitesLoaded, setSuitesLoaded] = useState(false);
  const [suiteId, setSuiteId] = useState<string | null>(null);
  const [runs, setRuns] = useState<SuiteRunRow[]>([]);
  const [summary, setSummary] = useState<SuiteStatus["summary"]>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api
      .suites()
      .then((s) => {
        setSuites(s);
        setSuitesLoaded(true);
        if (s.length > 0) setSuiteId(s[s.length - 1].suite_id);
      })
      .catch(() => {
        setSuites([]);
        setSuitesLoaded(true);
      });
  }, []);

  useEffect(() => {
    if (!suiteId) return;
    setNotFound(false);
    setRuns([]);
    setSummary(null);
    api
      .suite(suiteId)
      .then((status) => {
        if (!status.known || !status.summary) {
          setNotFound(true);
          return;
        }
        setRuns(status.runs ?? []);
        setSummary(status.summary);
      })
      .catch(() => setNotFound(true));
  }, [suiteId]);

  const cases: string[] = summary?.cases ?? [];
  const configs: string[] = summary?.configs ?? [];
  const results: Record<string, Record<string, Scores>> = summary?.results ?? {};
  const baseConfig = configs[0] === "base" ? "base" : configs.find((c) => c === "base") ?? configs[0];

  // Quality-vs-cost scatter points: one per (case, config), tokens summed
  // from the RUN rows' scores_json (defensive parse — a run may lack cost).
  const scatterByConfig = useMemo(() => {
    const grouped: Record<string, { x: number; y: number; case: string }[]> = {};
    for (const run of runs) {
      const cfgName = configNameForRun(run, configs);
      if (!cfgName) continue;
      const scores = parseJsonSafe<Scores>(run.scores_json);
      const tokens = totalTokens(scores);
      const hitRate = scores?.outcome?.hit_rate;
      if (tokens === null || hitRate === null || hitRate === undefined) continue;
      grouped[cfgName] = grouped[cfgName] ?? [];
      grouped[cfgName].push({ x: tokens, y: hitRate, case: run.case_id });
    }
    return grouped;
  }, [runs, configs]);

  if (!suitesLoaded) {
    return <div className="p-6 text-muted text-sm">{t("running")}</div>;
  }

  return (
    <div className="p-6 flex flex-col gap-6">
      <section className="panel p-4">
        <SuitePicker suites={suites} selected={suiteId} onSelect={setSuiteId} />
      </section>

      {!suiteId && suites.length > 0 && (
        <p className="text-xs text-muted">{t("noSuiteSelected")}</p>
      )}

      {suiteId && notFound && <p className="text-down text-sm">{t("suiteNotFound")}</p>}

      {suiteId && !notFound && summary && (
        <>
          <section className="panel hud-corners p-4 flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <div className="text-[10px] text-muted font-mono">{t("suiteHeader")}</div>
                <div className="font-mono text-sm text-accent">{suiteId}</div>
              </div>
              <div>
                <div className="text-[10px] text-muted font-mono">{t("startedAt")}</div>
                <div className="text-xs text-slate-300 font-mono">{summary.started_at ?? "—"}</div>
              </div>
              <div>
                <div className="text-[10px] text-muted font-mono">{t("casesLabel")}</div>
                <div className="text-xs text-slate-300">{cases.join(", ") || "—"}</div>
              </div>
              <div>
                <div className="text-[10px] text-muted font-mono">{t("configsLabel")}</div>
                <div className="text-xs text-slate-300">{configs.join(", ") || "—"}</div>
              </div>
            </div>
            <p className="text-xs text-muted">{t("leaderboardSubtitle")}</p>
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="hud-label">{t("matrixTitle")}</h3>
            <div className="panel overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-muted border-b border-line font-mono">
                    <th className="py-2 px-3 font-normal">{t("case")}</th>
                    {configs.map((cfg) => (
                      <th key={cfg} colSpan={3} className="py-2 px-3 font-normal text-center border-l border-line">
                        {cfg}
                      </th>
                    ))}
                  </tr>
                  <tr className="text-left text-muted border-b border-line font-mono">
                    <th className="py-1 px-3 font-normal" />
                    {configs.map((cfg) => (
                      <Fragment key={cfg}>
                        <th className="py-1 px-3 font-normal text-right border-l border-line">
                          <span className="inline-flex items-center gap-1">
                            {t("hitRate")}
                            <HelpTip text={t("hitRateHelp")} />
                          </span>
                        </th>
                        <th className="py-1 px-3 font-normal text-right">
                          <span className="inline-flex items-center gap-1">
                            {t("brier")}
                            <HelpTip text={t("brierHelp")} />
                          </span>
                        </th>
                        <th className="py-1 px-3 font-normal text-right">
                          <span className="inline-flex items-center gap-1">
                            {t("grounding")}
                            <HelpTip text={t("groundingHelp")} />
                          </span>
                        </th>
                      </Fragment>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cases.map((caseName) => {
                    const row = results[caseName] ?? {};
                    return (
                      <tr key={caseName} className="border-b border-line/60 last:border-0 align-top">
                        <td className="py-2 px-3 text-slate-200 font-mono">{caseName}</td>
                        {configs.map((cfg) => {
                          const scores = row[cfg];
                          const status = scores?.status ?? "ok";
                          const outcome = scores?.outcome;
                          const process = scores?.process;
                          return (
                            <Fragment key={cfg}>
                              <td
                                className={`py-2 px-3 text-right num border-l border-line ${
                                  status !== "ok" ? "text-slate-200" : hitRateClass(outcome?.hit_rate)
                                }`}
                              >
                                {status !== "ok" ? (
                                  <span
                                    title={status}
                                    className="rounded border border-amber/50 text-amber px-1.5 py-0.5 font-mono text-[10px]"
                                  >
                                    {status}
                                  </span>
                                ) : (
                                  pct(outcome?.hit_rate ?? null)
                                )}
                              </td>
                              <td className="py-2 px-3 text-right num text-slate-200">
                                {status !== "ok" ? "—" : fmtBrier(outcome?.brier)}
                              </td>
                              <td className="py-2 px-3 text-right num text-slate-200">
                                {status !== "ok" ? "—" : pct(process?.grounding_rate ?? null)}
                              </td>
                            </Fragment>
                          );
                        })}
                      </tr>
                    );
                  })}
                  {configs
                    .filter((cfg) => cfg !== baseConfig)
                    .map((cfg) => {
                      const otherConfigsBefore = configs.filter(
                        (col) => col !== cfg && configs.indexOf(col) < configs.indexOf(cfg)
                      );
                      const otherConfigsAfter = configs.filter(
                        (col) => col !== cfg && configs.indexOf(col) > configs.indexOf(cfg)
                      );
                      return (
                        <tr key={`delta-${cfg}`} className="border-t border-line bg-ink-800/50">
                          <td className="py-2 px-3 text-muted font-mono text-[11px]">
                            {t("deltaRow")} ({cfg})
                          </td>
                          {otherConfigsBefore.map((col) => (
                            <td key={col} colSpan={3} className="border-l border-line" />
                          ))}
                          <td className="py-2 px-3 text-right num border-l border-line" colSpan={2}>
                            {cases.map((caseName) => {
                              const baseScores = results[caseName]?.[baseConfig];
                              const cfgScores = results[caseName]?.[cfg];
                              const baseHr = baseScores?.outcome?.hit_rate;
                              const cfgHr = cfgScores?.outcome?.hit_rate;
                              if (
                                baseHr === null || baseHr === undefined ||
                                cfgHr === null || cfgHr === undefined
                              ) {
                                return (
                                  <div key={caseName} className="flex justify-between gap-2">
                                    <span className="text-muted">{caseName}</span>
                                    <span className="text-muted">—</span>
                                  </div>
                                );
                              }
                              const delta = cfgHr - baseHr;
                              const better = delta === 0 ? null : delta > 0;
                              return (
                                <div key={caseName} className="flex justify-between gap-2">
                                  <span className="text-muted">{caseName} Δ{t("hitRate")}</span>
                                  <span className={deltaClass(better)}>
                                    {delta > 0 ? "+" : ""}
                                    {(delta * 100).toFixed(1)}%
                                  </span>
                                </div>
                              );
                            })}
                          </td>
                          <td className="py-2 px-3 text-right num">
                            {cases.map((caseName) => {
                              const baseScores = results[caseName]?.[baseConfig];
                              const cfgScores = results[caseName]?.[cfg];
                              const baseBr = baseScores?.outcome?.brier;
                              const cfgBr = cfgScores?.outcome?.brier;
                              if (
                                baseBr === null || baseBr === undefined ||
                                cfgBr === null || cfgBr === undefined
                              ) {
                                return (
                                  <div key={caseName} className="flex justify-between gap-2">
                                    <span className="text-muted">{caseName}</span>
                                    <span className="text-muted">—</span>
                                  </div>
                                );
                              }
                              const delta = cfgBr - baseBr; // brier: lower is better, so a negative delta is "better"
                              const better = delta === 0 ? null : delta < 0;
                              return (
                                <div key={caseName} className="flex justify-between gap-2">
                                  <span className="text-muted">{caseName} Δ{t("brier")}</span>
                                  <span className={deltaClass(better)}>
                                    {delta > 0 ? "+" : ""}
                                    {delta.toFixed(3)}
                                  </span>
                                </div>
                              );
                            })}
                          </td>
                          {otherConfigsAfter.map((col) => (
                            <td key={col} colSpan={3} className="border-l border-line" />
                          ))}
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-slate-300 border-l-2 border-l-amber pl-3">{t("sampleSizeHonesty")}</p>
          </section>

          <section className="flex flex-col gap-2">
            <h3 className="hud-label">{t("scatterTitle")}</h3>
            <div className="panel p-3 h-72">
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 16, bottom: 8, left: 0 }}>
                  <CartesianGrid stroke="#1c2740" strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="x"
                    name={t("scatterX")}
                    tick={{ fill: "#7d8aa5", fontSize: 10 }}
                    label={{ value: t("scatterX"), fill: "#7d8aa5", fontSize: 10, position: "insideBottom", offset: -2 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="y"
                    name={t("scatterY")}
                    domain={[0, 1]}
                    width={40}
                    tick={{ fill: "#7d8aa5", fontSize: 10 }}
                    label={{ value: t("scatterY"), fill: "#7d8aa5", fontSize: 10, angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip
                    contentStyle={{ background: "#0b111e", border: "1px solid #1c2740" }}
                    formatter={(v: number | string | readonly (number | string)[] | undefined, key: string | number | undefined) =>
                      typeof v === "number" ? (key === "y" ? pct(v) : num(v)) : v
                    }
                  />
                  <Legend wrapperStyle={{ fontSize: 10, color: "#7d8aa5" }} />
                  {Object.entries(scatterByConfig).map(([cfgName, pts], idx) => (
                    <Scatter
                      key={cfgName}
                      name={cfgName}
                      data={pts}
                      fill={colorForConfig(cfgName, idx)}
                      shape={(p: any) => (
                        <g>
                          <circle cx={p.cx} cy={p.cy} r={9} fill={colorForConfig(cfgName, idx)} fillOpacity={0.15} />
                          <circle cx={p.cx} cy={p.cy} r={4.5} fill={colorForConfig(cfgName, idx)} fillOpacity={0.85} />
                          <text x={p.cx} y={p.cy - 12} fill="#7d8aa5" fontSize={9} textAnchor="middle">
                            {p.payload.case}
                          </text>
                        </g>
                      )}
                    />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}
      {/* lang is read to force re-render on toggle even where t() output is memoized elsewhere */}
      <span className="hidden">{lang}</span>
    </div>
  );
}
