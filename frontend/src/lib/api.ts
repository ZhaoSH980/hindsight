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
  edgarFilings: async (ticker: string, before: string) => {
    const r = await fetch(
      `/api/edgar/filings?ticker=${encodeURIComponent(ticker)}&before=${encodeURIComponent(before)}`
    );
    if (!r.ok) {
      let detail = `${r.status}`;
      try {
        detail = String((await r.json()).detail ?? detail);
      } catch {
        // keep status code
      }
      throw new Error(detail);
    }
    return (await r.json()) as {
      cik: number;
      form: string;
      filed: string;
      accession: string;
      document: string;
    }[];
  },
  edgarFetch: async (payload: {
    ticker: string;
    cik: number;
    accession: string;
    document: string;
    form: string;
    filed: string;
  }) => {
    const r = await fetch("/api/edgar/fetch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      let detail = `${r.status}`;
      try {
        detail = String((await r.json()).detail ?? detail);
      } catch {
        // keep status code
      }
      throw new Error(detail);
    }
    return (await r.json()) as {
      title: string;
      published_at: string;
      source: string;
      url: string;
      doc_type: string;
      text: string;
    };
  },
  createCase: async (payload: {
    ticker: string;
    as_of: string;
    outcome_window_days: number;
    title: string;
    title_zh: string;
    description: string;
    description_zh: string;
    tags: string[];
    docs: { title: string; published_at: string; source: string; url: string; doc_type: string; text: string }[];
  }) => {
    const r = await fetch("/api/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      let detail = `${r.status}`;
      try {
        const body = await r.json();
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      } catch {
        // non-JSON error body — keep the status code
      }
      throw new Error(detail);
    }
    return (await r.json()) as {
      case_id: string;
      n_docs: number;
      n_bars: number;
      bars_after_as_of: number;
      outcome_window_still_open: boolean;
    };
  },
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
