import type { Bar, CaseMeta, RunDetail, RunSummary, SuiteStatus, SuiteSummary, TraceEvent } from "./types";

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

export const api = {
  cases: () => get<CaseMeta[]>("/api/cases"),
  bars: (caseId: string) => get<{ ticker: string; bars: Bar[] }>(`/api/cases/${caseId}/bars`),
  runs: () => get<RunSummary[]>("/api/runs"),
  run: (runId: string) => get<RunDetail>(`/api/runs/${runId}`),
  trace: (runId: string) => get<TraceEvent[]>(`/api/runs/${runId}/trace`),
  suites: () => get<SuiteSummary[]>("/api/eval/suites"),
  suite: (suiteId: string) => get<SuiteStatus>(`/api/eval/suites/${suiteId}`),
  startRun: async (caseId: string, memoryOn: boolean, maxSteps: number, language: "en" | "zh" = "en") => {
    const r = await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: caseId, memory_on: memoryOn, max_steps: maxSteps, language }),
    });
    if (!r.ok) throw new Error(`start run failed: ${r.status}`);
    return (await r.json()) as { run_id: string };
  },
};
