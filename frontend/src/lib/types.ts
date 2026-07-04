export interface CaseMeta {
  case_id: string;
  title: string;
  ticker: string;
  as_of: string;
  outcome_window_days: number;
  description: string;
  tags: string[];
  n_docs: number;
}

export interface Bar { date: string; open: number; high: number; low: number; close: number; volume: number }

export interface CalBucket { lo: number; hi: number; n: number; avg_confidence: number | null; hit_rate: number | null }

export interface Claim {
  claim_id: string;
  statement: string;
  type: "direction" | "magnitude" | "volatility";
  ticker: string;
  horizon_days: number;
  prediction: Record<string, unknown>;
  confidence: number;
  evidence: string[];
  status?: "hit" | "miss" | "ungradable";
  realized_return_pct?: number | null;
  detail?: string;
}

export interface RunSummary {
  run_id: string;
  case_id: string;
  suite_id: string | null;
  status: string;
  created_at: string;
  config: Record<string, unknown>;
  scores: Scores | null;
}

export interface Scores {
  status?: string;
  outcome?: { n_claims: number; n_gradable: number; n_hit: number; hit_rate: number | null; brier: number | null; calibration: CalBucket[] };
  process?: { judge_failed: boolean; grounding_rate?: number | null; reasoning_consistency?: number; retrieval_sufficiency?: number; attributions?: Record<string, string> };
  cost?: Record<string, { prompt_tokens: number; completion_tokens: number; calls: number }>;
  contamination_probe?: string;
  unverified?: boolean;
}

export interface RunDetail extends RunSummary { memo_md: string | null; claims: Claim[] }

export interface TraceEvent { type: string; agent: string; payload: Record<string, unknown>; tokens: number; ts: string }

export interface SuiteSummary {
  suite_id: string;
  started_at: string | null;
  cases: string[];
  configs: string[];
  status: string;
}

// A suite's runs come straight from the store (raw SQLite row shape) —
// unlike /api/runs, this endpoint does NOT pre-parse config_json/scores_json.
export interface SuiteRunRow {
  run_id: string;
  case_id: string;
  suite_id: string | null;
  status: string;
  created_at: string;
  config_json?: string | null;
  scores_json?: string | null;
}

export interface SuiteStatus {
  suite_id: string;
  runs: SuiteRunRow[];
  summary: {
    suite_id: string;
    started_at?: string;
    cases?: string[];
    configs?: string[];
    status?: string;
    results?: Record<string, Record<string, Scores>>;
  } | null;
  known: boolean;
}
