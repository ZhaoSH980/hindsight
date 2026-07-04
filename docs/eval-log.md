# Eval log

Development-time record of evaluation-driven changes: every prompt or
architecture change is logged with before/after suite scores. This file is
the receipts for "evaluation as the primary mechanism to guide behavior".

## D1 — endpoint probe (2026-07-04)

- Endpoint: xf-yun MaaS, model `astron-code-latest` (GLM-5.2)
- Native `tools/tool_choice` support: **True.** A single `tools=[get_price]`
  request returned a well-formed `tool_calls` entry:
  `{"id": "call_ca43e3358ab5410f98003d64", "function": {"name": "get_price",
  "arguments": "{\"ticker\": \"NVDA\"}"}, "type": "function"}` — correct
  function name, valid JSON arguments, required `ticker` key present.
- JSON stability (5 attempts): **2/5 completed before the run was cut short**
  by an endpoint rate limit (`429 authorization failed`, error code 11210)
  after ~4 calls in quick succession. Both completed attempts (0 and 1)
  produced valid JSON matching the requested schema (`action`/`query`/
  `confidence`). A second full run was attempted per the probe protocol's
  "one retry on transient failure" allowance; it failed immediately on the
  very first call with the same 429, indicating the account/key is
  momentarily throttled rather than a fluke — no further retries were run to
  avoid burning additional metered quota.
- Usage shape (captured via a temporary debug print on one native-tools
  response, then removed): `{"completion_tokens": 11, "prompt_tokens": 161,
  "total_tokens": 172, "completion_tokens_details": {"accepted_prediction_tokens":
  null, "audio_tokens": null, "reasoning_tokens": 0, "rejected_prediction_tokens":
  null}, "prompt_tokens_details": {"audio_tokens": null, "cached_tokens": 0},
  "question_tokens": 4}`. Confirms xf-yun adds the nonstandard
  `question_tokens` field on top of the standard OpenAI `usage` shape.
- **Decision:** Planner uses **native function calling.** The one completed
  native-tools probe was clean (correct name, valid arguments, required key
  present), and the JSON-mode probe — while cut short by rate limiting —
  showed no format failures in the attempts that did complete (2/2 valid).
  Combined with the design-decision default (§4 of design-decisions.md:
  native calling is preferred whenever the endpoint supports
  `tools/tool_choice` reliably), this is enough signal to commit to native
  function calling for D2. If a later D2 integration run surfaces
  inconsistent `tool_calls` behavior under load, re-probe with a longer
  inter-call delay to control for the rate limit observed here.

## D2 — first live NVDA run (2026-07-04)

- Run 1 (record mode): `run_nvda_fy26q1_20260704_074410_b3e722`, 14 metered
  calls (probe 1, planner 5, analyst 3, critic 3, judge 2), no 429s hit (call
  timestamps show no 15/30/60s gaps). Contamination probe was clean ("I do
  not know what happened to NVDA... after May 22, 2025").
- **`tool_calls` shape check (task requirement A):** inspected
  `llm_calls.sqlite` for all 5 planner responses carrying `tools`. Real
  xf-yun/GLM-5.2 `tool_calls` entries are `{"id": "call_...", "function":
  {"name": "...", "arguments": "..."}, "type": "function", "index": 0}` —
  i.e. they carry an extra `"index"` field (list position) beyond the
  `id`/`type`/`function` triple the test stubs (`llm_stubs.tool_call_response`)
  produce. This did **not** cause any API error: `planner.py` never reads or
  depends on `index`, and both the `openai` SDK client-side validation and
  the xf-yun server accepted the verbatim echo of the full `tool_calls` list
  (including `index`) back in the next request's `messages`. No parsing/echo
  fix was needed — noting the observed shape only, per the task's
  no-error branch.
- **Quality bug found and fixed (task requirement C):** the memo was
  `unverified` after exhausting all 3 attempts (2 retries). The semantic
  critic — a real LLM, not a stub — correctly and consistently flagged the
  same root cause on attempts 0, 1, and 2: the analyst's `direction` claim
  (e.g. "closes >=3% up over 5d") and its `magnitude` claim (e.g. "return in
  [-7%, +2%]") are graded off the *same* horizon-end return `r`, but their
  predicted ranges overlapped/disagreed on sign, making the pair jointly
  incoherent as a single view of one `r`. `ANALYST_SYSTEM` in
  `backend/hindsight/agents/prompts.py` documented direction and magnitude
  semantics individually but never stated that claims sharing a horizon must
  be mutually consistent about the one `r` that actually happens.
  - Before: example magnitude claim was `[-2%, +8%]` alongside a `direction:
    up >=5%` example — internally inconsistent as written (a "-2%" outcome
    would satisfy the magnitude claim but fail the direction claim), modeling
    exactly the failure mode the critic kept catching.
  - After: added an explicit "MUTUAL CONSISTENCY" rule — claims on the same
    `horizon_days` are graded off one shared `r`; a magnitude band must sit
    entirely on the same side of a direction claim's threshold (no overlap
    below/above it). Replaced the magnitude example with one that is
    consistent with the direction example (`[+5%, +15%]` fully at/above the
    direction's `+5%` threshold).
  - Scores before (run 1, pre-fix): `unverified: true`, `n_gradable: 0`,
    3 semantic-critic rejections, memo otherwise well-grounded (3 claims, 1
    direction, all citing real chunk ids, grounding_rate 1.0).
  - Full test suite re-run after the edit: 138 passed (no regressions; the
    edit only adds prose to `ANALYST_SYSTEM`, which `test_prompts.py` checks
    by substring presence, not exact match).
  - See run 2 below for scores after the fix.

- Run 2 (record mode, first attempt): crashed with `openai.InternalServerError:
  503 {'code': 10310, 'message': 'The system is busy, please try again later.'}`
  from the semantic-critic call. This is a transient upstream outage, distinct
  from the 429/11210 rate-limit case the retry transport special-cases — it
  fell into the generic-backoff bucket (2/4/8s, 3 tries) and correctly
  re-raised after exhaustion rather than hanging. 5 calls were recorded before
  the crash (now free replays). Re-ran immediately (run 2b) per the
  coordinator's mid-task update relaxing the live-run budget to ~6 (quota is
  ample; burst rate-limiting was the only real constraint) — this crash/retry
  is not counted as a quality-iteration attempt, just an infra retry.

- Run 2b (record mode): `run_nvda_fy26q1_20260704_075823_3fdb4f`. The mutual-
  consistency fix worked as intended on the first critic attempt (attempt 0's
  c1/c2 pair: direction "up>=3%" + magnitude "[3%,12%]", band fully at/above
  the threshold — no more overlap on that pair, and the realized +8.54% return
  would have made both a HIT). Still ended `unverified: true` after 3 attempts,
  but the blocking reason changed and revealed a **second, distinct root
  cause**: the semantic critic repeatedly rejected the `volatility`-type claim
  as "not objectively checkable" / requiring data "not specified in the
  memo" — a misreading of `CRITIC_SEMANTIC_SYSTEM`'s first rejection bullet,
  which the critic model was interpreting as "the evidence must let a human
  independently derive the exact numeric threshold," rather than "the type is
  mechanically gradable from daily closes" (which volatility legitimately is
  — realized log-return vol vs. rolling windows is exactly what
  `outcome_grader.py` computes from bars, no evidence-side proof needed). A
  secondary attempt-1 draft also transiently reintroduced the same direction/
  magnitude overlap bug on a different horizon (5d) — the analyst fix reduces
  but doesn't guarantee the failure mode disappears on every sampled draft;
  the critic itself is the backstop, so it must judge that failure mode
  correctly instead of over-rejecting on an unrelated, correct claim.
  - Before: `CRITIC_SEMANTIC_SYSTEM`'s bullet 1 was a single ambiguous phrase
    ("not objectively checkable against daily closing prices") that let the
    critic conflate "type is checkable" with "evidence must independently
    prove the number." Bullet 2 ("a cited evidence excerpt does not actually
    support its claim") was similarly read as "evidence must derive the exact
    threshold," which no probabilistic forecast claim can satisfy by
    construction.
  - After: rewrote bullet 1 to explicitly state all three claim types
    (direction/magnitude/volatility) are mechanically checkable from a daily-
    close series, that volatility is graded by the outcome grader from bars
    (not proven by evidence), and that a claim is a probabilistic forecast —
    evidence only needs to motivate the claim's direction/theme, not derive
    its numeric threshold. Reworded bullet 2 to "topically unrelated," not
    "doesn't prove the number." Added an explicit mutual-consistency
    cross-reference so the critic's overlap check stays anchored to the
    analyst's rule instead of drifting.
  - Scores before (run 2b, pre-fix): `unverified: true`, `n_gradable: 0`,
    grounding_rate 1.0, reasoning_consistency 4, retrieval_sufficiency 4 —
    process scores were already healthy; only the critic-gate was miscalibrated.
  - Full test suite re-run after the edit: 138 passed.
  - See run 3 below for scores after this second fix.

- Run 3 (record mode): `run_nvda_fy26q1_20260704_080442_ce7ca0` — **PASSED
  the full acceptance bar on the first critic attempt** (analyst 1 call,
  critic 1 call; previous runs needed all 3 attempts and still failed).
  - Memo: 4 claims (2 direction, 1 magnitude, 1 volatility), all citing real
    chunk ids from the nvda_fy26q1 corpus (`hyperscaler_capex`,
    `blackwell_ramp`, `analyst_preview`, `q4_fy25_recap`,
    `h20_export_restriction`, `ai_capex_skeptic`).
  - Outcome: `n_gradable=4/4`, `n_hit=1`, `hit_rate=0.25`, `brier=0.299`. c1/c2/c3
    (5-day horizon) all missed — realized 5d return was +1.73%, short of the
    +3% thresholds both claims needed; c3's realized volatility (0.0245) fell
    short of its 70th-percentile bar (0.0366). c4 (20-day "up >=5%") hit — the
    realized 20-day return was +8.54%.
  - Process: `judge_failed=false`, `grounding_rate=1.0`, `reasoning_consistency=4`,
    `retrieval_sufficiency=4`, all 3 misses attributed `reasonable_but_wrong`
    (the judge agreed the process was sound — evidence was retrieved and
    read correctly, the 5-day window just didn't move as far as the analyst's
    reasonable bull case implied; this is the market disagreeing with a
    grounded thesis, not a process failure).
  - Total metered calls this run: 14 (probe 1, planner 5, analyst 1, critic 1,
    judge 2) — well under the ~12-17/run estimate.
  - Total live-run calls across the whole Task 14 sequence: run1=14,
    run2(crashed after 5)=5, run2b=19 cumulative (14 replayed free + 5 new),
    run3=14 new. 3 quality-relevant live attempts (run1, run2b, run3) plus one
    infra-retry (run2's 503 crash) — within the relaxed ~6-run budget.
  - Full test suite: 138 passed throughout, no regressions from either
    prompt edit.

## D2 — case 3: SMCI falsification case (2026-07-04)

Spec §4.1 case 3: a window where the contemporaneous bullish narrative was
falsified within 20-40 trading days. SMCI (the plan's initial candidate)
offered exactly such a window — no ticker swap needed.

- **Window research (verified with real yfinance bars BEFORE authoring).**
  Chose `as_of = 2025-02-26`, the day after SMCI filed its delayed FY2024
  10-K (Feb 25, the Nasdaq deadline day) and regained listing compliance —
  the crest of a month-long turnaround rally: $26.85 close on Feb 3 → $60.25
  on Feb 19 → $51.11 on Feb 26 (+90% off the Feb 3 low). The prior 60-90 days'
  public narrative was predominantly bullish: special-committee exoneration
  (Dec 2), Nasdaq extension (Dec 6), Blackwell rack-scale full production
  (Feb 5), the $40B FY26 revenue target (Feb 11), the on-time 10-K with no
  restatements + clean BDO opinion on the financials (Feb 25), Loop Capital
  reiterating Buy with a raised $70 target (Feb 26). Frozen-bar returns from
  the $51.11 baseline falsify it at EVERY horizon: +1d -16.0%, +5d -23.9%,
  +20d -27.5%, +30d -28.2%, +40d -29.9% (closing trough $29.51 on Apr 21,
  -42%). Well past the ≥15% drawdown bar. The thesis also broke
  fundamentally inside the calendar window: Apr 29 preliminary Q3 FY25 miss
  ($4.5-4.6B vs $5.0-6.0B guided), May 6 final print (GM 9.6%, FY25 guide cut
  again to $21.8-22.6B) — captured in the deliberate future doc.
- **Corpus:** `datasets/smci_case3/` — meta.json (`outcome_window_days: 40`)
  + 8 English docs: 7 dated ≤ as_of (Dec 6 saga recap; Feb 5 Blackwell/DLC
  production; Feb 8 hyperscaler-capex macro; Feb 11 Q2 update with the $40B
  target AND the buried FY25 cut; Feb 24 bear view on margins/dilution/
  governance; Feb 26 10-K-filed news; Feb 26 bull thesis) and ONE deliberate
  future doc (May 7) recording what actually happened. Every number was
  verified against primary/secondary sources via web search during curation
  (SMCI IR releases, SEC filings, CNBC/Bloomberg/CFO Dive coverage) and every
  price/percentage against the frozen yfinance bars; pre-as_of docs state
  facts only as known at their publication dates (one violation caught and
  fixed during authoring: the Feb 11 doc originally cited the convert's
  conversion price, which priced off the Feb 12 VWAP — moved to the Feb 24
  doc). Bars frozen 2024-10-29 → 2025-05-30 (146 bars; 81 pre-as_of survive
  → volatility grading has ≥41 rolling samples ≥ MIN_VOL_SAMPLES=20).
- **Validation run (record mode):** `run_smci_case3_20260704_082812_622419`,
  12 metered calls (probe 1, planner 6, analyst 2, critic 1, judge 2), passed
  the critic on the second analyst attempt, `unverified: false`. Probe clean
  ("I do not know what happened to SMCI... after February 26, 2025").
- **Results:** 4 claims, 4/4 gradable, `n_hit=1`, `hit_rate=0.25`,
  `brier=0.237`.
  - c1 direction 20d "down ≥5%" conf 0.55 → **hit** (realized -27.53%)
  - c2 magnitude 20d "[-15%, -5%]" conf 0.40 → **miss** (realized -27.53%,
    below the band — the drawdown exceeded even the bearish scenario)
  - c3 volatility 40d "above p70" conf 0.68 → **miss** (realized 0.0694 vs
    p70 0.0867 — the pre-as_of history it is ranked against contains the
    Oct-Dec 2024 saga (-33% and +31% days), so "turbulent by this stock's
    own recent standards" was a high bar even in a -30% window)
  - c4 direction 40d "up ≥10%" conf 0.35 → **miss** (realized -29.94%)
- **Failure-shape verdict: HOLDS.** The narrative-following bullish claim
  (c4, citing the bull-thesis/capex/Blackwell chunks) was falsified, which is
  this case's purpose. Notably the agent did NOT swallow the bull narrative
  whole: it weighted the bear-doc evidence (margins, governance, JPM's $23
  target), led with a bearish direction claim that hit, and kept the bullish
  claim at low confidence (0.35) — the acceptable-alternative shape the plan
  anticipated ("if the agent is bearish and hits — also acceptable"). The
  case still punishes narrative-following on two axes: the bullish claim
  missed outright, and even the bearish magnitude band underestimated the
  crash (c2 miss). Judge: `judge_failed=false`, grounding 1.0, reasoning 4,
  retrieval 4; attributions c2/c4 `reasonable_but_wrong`, c3
  `evidence_missing`.
- **Offline replay proof:** `run_smci_case3_20260704_083129_603736` —
  re-ran with `--offline`, completed without network, memo byte-identical to
  the record-mode run.
- **Tests:** `backend/tests/test_smci_case.py` (3 integrity tests, long-doc
  test deliberately dropped — that is case 1's job) → full suite 141 passed.
- Live-call budget: 1 record run (12 calls) + 1 free offline replay — well
  under the ~6-run allowance; no 429 stalls observed.

## D4 — evaluation suite (2026-07-04)

First real `EvalSuite` run — the data source for the Leaderboard page.
Command: `backend/.venv/Scripts/python -m hindsight.cli suite --cases
datasets/smci_case3,datasets/nvda_fy26q1 --presets base,memory`, launched
from the repo root. Completed in a single pass (no crash, no re-launch
needed) in ~6.5 minutes wall clock (10:59:22 -> 11:05:45 UTC), well inside
the "several minutes, up to ~30-40 with 429 waits" estimate — no 429s were
actually hit this run.

- **suite_id: `suite_c3b22b4b`** — `runs/suites/suite_c3b22b4b.json`.
  Cases auto-sorted ascending by `as_of` as designed: `smci_case3`
  (2025-02-26) before `nvda_fy26q1` (2025-05-22).

### Per-run outcomes

| # | run_id | case | config | status | n_gradable | hit_rate | brier | grounding_rate | reasoning | retrieval |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `run_smci_case3_20260704_105922_28a79f` | smci_case3 | base | done, `unverified:false` | 4/4 | 0.25 | 0.26805 | 1.0 | 4 | 3 |
| 2 | `run_smci_case3_20260704_110057_faa55c` | smci_case3 | memory | done, `unverified:false` | 4/4 | 0.25 | 0.26805 | 1.0 | 4 | 3 |
| 3 | `run_nvda_fy26q1_20260704_110057_5107e6` | nvda_fy26q1 | base | done, `unverified:false` | 4/4 | 0.25 | 0.26125 | 1.0 | 4 | 4 |
| 4 | `run_nvda_fy26q1_20260704_110357_439805` | nvda_fy26q1 | memory | done, `unverified:false` | 4/4 | 0.25 | 0.30063 | 1.0 | 4 | 4 |

All 4 runs passed the critic on the first analyst attempt and cleared the
full acceptance bar (`unverified: false` for every run — no re-launches were
needed). Both contamination probes stayed clean throughout ("I do not know
what happened to \[ticker\]... after \[as_of\]").

### Memory asymmetry check (showcase material)

Verified directly against `llm_calls.sqlite` `request_json` (the planner's
actual user-message brief), not just the trace, by grepping for the literal
marker string `"Lessons from previously graded research"` and partitioning
calls by `created_at` into each run's time window:

- **`smci_case3` memory run**: **0** of its calls contain the lessons
  block — the run made **0 new network calls** at all (all 10 logical calls
  were cache hits; see CAVEAT below). Expected: at SMCI's `as_of`
  (2025-02-26), the only candidate experience cards would have to come from
  `nvda_fy26q1` runs, whose `outcome_window_end` (2025-07-22) is *after*
  SMCI's `as_of` — the time gate correctly excludes them. No cards passed
  the gate, so the planner brief was byte-identical to the base run's.
  *(Correction, D4 wrap-up review: this bullet originally read "7 new
  metered calls in its window, 0/7 with lessons" — a `created_at` window
  partition that had actually captured rows belonging to the concurrent
  nvda/base run, which started the same second. Re-partitioned by agent
  system prompt: the smci/memory run wrote no rows. The conclusion — zero
  lessons injected at SMCI's as_of — is unchanged and now rests on the
  stronger byte-identical/cache-hit evidence.)*
- **`nvda_fy26q1` memory run** (13 logical calls, of which 12 hit the
  network as new rows — the contamination probe replayed from cache):
  **all 8 planner calls** contain the lessons block; the probe/analyst/
  critic/judge calls do not (only the planner receives the brief).
  *(Correction, D4 wrap-up review: originally "13 new metered calls in its
  window, 8/13 with lessons" — same window-partition slip; the 13th row was
  nvda/base's second judge call at 11:03:56, and the probe never hit the
  network. The 8-planner-calls figure is unchanged.)* Expected: SMCI's
  `outcome_window_end` (2025-04-24) is well before NVDA's `as_of`
  (2025-05-22), so SMCI's experience card(s) legally pass the gate and
  leave-one-out (`exclude_case_id=nvda_fy26q1`) doesn't touch them. The
  exact injected text (verbatim from the first planner call at
  `2026-07-04T11:03:59Z`):
  > Lessons from previously graded research (older cases whose outcomes are
  > already known as of your research date):
  > - \[smci_case3\] SMCI turnaround servers ai-capex SMCI after the delayed
  >   10-K filing rally (Feb 2025) — 4 claims, 1 hit (1/4 claims hit).
  >   Lesson (reasonable_but_wrong): Missed claims were mostly
  >   reasonable_but_wrong; adjust research accordingly.
  >
  > (rendered twice — the retriever's `top_k=3` BM25 ranking returned both
  > the base-run and memory-run SMCI experience cards as distinct top hits,
  > since their `features_text` is identical and both passed the gate.)
- **CAVEAT confirmed:** SMCI base vs memory is **byte-identical** end to
  end — `memo.md` and `claims.json` sha256 match exactly, and all 10 logical
  calls in the memory run's cost ledger were record/replay cache hits (0 new
  rows in `llm_calls.sqlite` for that run). This is *correct* behavior, not
  a bug: identical prompts (no cards passed the gate) hash to the same
  request key, so the replay layer serves the recorded response for free.
  It also means the SMCI-memory row cost nothing extra in metered calls.
- **Qualitative effect on NVDA:** the memory-primed run's claim set differs
  from base's — same hit_rate (0.25, 1/4) but a different claim structure.
  Base's hitting claim was a 20-day direction call (`c4`, "up >=5%", conf
  0.4, realized +8.54%); memory's hitting claim was a 40-day direction call
  (`c3`, "up >=5%", conf 0.5, realized +25.76%) — a longer horizon than any
  base claim used, plausibly reflecting the SMCI lesson nudging the analyst
  toward less confidence in the tight 5-day claims (which still missed
  identically in both: `c1`/`c2`, +1.73% realized vs both claims' >=3%
  bars) and toward hedging with a longer window instead. Memory's brier
  (0.30063) is *worse* than base's (0.26125) despite the horizon change,
  because it raised confidence on both a still-missing 5-day volatility
  claim (`c4`, conf 0.7, vs base's `c3` conf 0.6, both miss) and the
  overlapping 5-day pair (conf 0.55/0.4 vs base's 0.45/0.35) — i.e. the
  lesson changed *what* was claimed and *how confidently*, not whether the
  tight-horizon claims stopped missing. This is an honest, un-cherry-picked
  result: memory demonstrably changed the planner's brief and the analyst's
  output (asymmetrically, exactly per the time-gate design), but one run of
  N=1 per config is not enough signal to claim memory improves or hurts
  calibration — see the forthcoming evaluation-methodology doc's
  small-N framing.

### Total calls

- **30 new metered LLM calls** across the whole suite (`llm_calls.sqlite`
  rows with `created_at >= 2026-07-04T10:59:22Z`, the suite's snapshot
  timestamp, verified against the table's pre/post row counts: 36 -> 66)
  — under the ~50-65 estimate, the gap explained by cache hits: the
  smci_case3/memory run replayed all 10 of its logical calls for free
  (byte-identical to smci_case3/base, per the asymmetry check above), and a
  handful of smci_case3/base's and nvda_fy26q1/base's own logical calls
  (e.g. the contamination probe, whose prompt depends only on
  ticker+as_of) also hit cache rows already recorded by the D2/D3 runs of
  the same cases committed earlier this project.
- Per-run logical call counts from each run's `cost` ledger (includes cache
  hits, i.e. what the agents *logically* invoked, not what hit the network):
  smci/base 10 (probe 1, planner 5, analyst 1, critic 1, judge 2);
  smci/memory 10, all 10 replayed from cache — 0 new network calls;
  nvda/base 12 (probe 1, planner 5, analyst 2, critic 2, judge 2);
  nvda/memory 13 (probe 1, planner 8, analyst 1, critic 1, judge 2). Sum of
  logical calls: 45; actual new rows written to `llm_calls.sqlite`: 30.
- No process crashes, no 429 waits observed, no re-launch needed — the
  suite completed cleanly end to end in one pass.

### Tests

No backend code touched for this task; full suite re-confirmed green
immediately before launch: `backend/.venv/Scripts/python -m pytest -q` ->
**168 passed**.

## 2026-07-05 — memo language option (prompt change, replay-safety audited)

### What changed

`analyst_user_prompt()` gained a `language` parameter (default `"en"`).
For `language="zh"` one instruction block (`MEMO_LANGUAGE_LINES["zh"]`) is
inserted immediately before the closing "Write the memo JSON now." line,
telling the analyst to write all free-text fields in Simplified Chinese
while keeping JSON keys, enum values, tickers, and chunk_ids in English
(the structural validator depends on those staying English).

### Replay-safety audit (the invariant that matters)

`language="en"` produces BYTE-IDENTICAL prompts to the pre-language era —
verified by `test_en_prompt_is_byte_identical_to_pre_language_era`, which
reconstructs the legacy prompt string literally and compares equality, and
by `test_zh_prompt_adds_only_the_language_line` (zh minus the block == en).
`RunConfig.language` defaults to `"en"` and legacy `config_json` rows
without the field still parse (covered by test). Net effect: every
recording committed before this change keeps replaying byte-for-byte.

### Why not localize planner thoughts too

Planner queries feed BM25 over an English corpus — Chinese queries would
degrade retrieval. Thoughts and queries stay English; the UI localizes the
*framing* of the live feed instead, and the memo/claims (the human-facing
artifact) follow the selected language.

### Tests

`pytest -q` -> **176 passed** (6 new: prompt byte-identity, zh insertion,
config compat, provenance counters live/replay/offline).
