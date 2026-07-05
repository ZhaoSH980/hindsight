# Evaluation methodology

This document consolidates how Hindsight measures itself: the exact grading
rules, the anti-lookahead guarantees, the judge's validity limits, and the
honest statistical framing a reviewer should apply to every number this
project reports. It invents nothing — every claim below traces to a spec
section, a source file, or a dated entry in `docs/eval-log.md` /
`docs/judge-meta-eval.md`. See the **Artifact index** at the bottom for the
exact file/line each claim maps to.

## 1. Three tracks

A run is graded once it completes — in a backtest, the "future" already
exists, so grading is not live and runs entirely outside the agent's time
sandbox (`backend/hindsight/eval/outcome_grader.py` module docstring: "Runs
deliberately OUTSIDE the time sandbox — evaluation is entitled to realized
data. The boundary is the orchestrator: agents never see this module's
inputs."). Execution order is fixed: **track A runs first, and its
per-claim results feed track B** (spec §3.4).

### A. Outcome (mechanical grading)

Implemented in `outcome_grader.py`, mirroring spec §3.3's six grading rules
exactly:

1. **Baseline `P0`.** The last close at or before `as_of` (`_baseline_index`):
   if `as_of` is not a trading day, the grader walks back to the most recent
   prior bar.
2. **Trading-day counting.** The horizon is counted in bars, not calendar
   days: `hi = i0 + claim.horizon_days`, i.e. the Nth bar strictly after the
   baseline bar in the frozen bar series. If the cached bars don't reach that
   index (`hi >= len(bars)`), the claim is `ungradable` with a detail message
   reporting how many trading days actually are covered.
3. **`direction` — at-horizon-end semantics.** Let `r = close[hi]/P0 - 1`.
   An "up" claim hits iff `r >= threshold_pct/100`; a "down" claim hits iff
   `r <= -threshold_pct/100`. This is a single point-in-time comparison at
   the horizon's last bar — **not** "touched at any point during the
   window." A `math.isclose(..., abs_tol=1e-9)` tolerance guards the
   boundary against floating-point noise so a claim landing exactly on its
   stated threshold isn't spuriously flipped to a miss by rounding direction
   (documented inline in `outcome_grader.py`).
4. **`magnitude` — closed interval.** Prediction is `{low_pct, high_pct}`;
   hit iff the horizon-end return in percent falls in `[low_pct, high_pct]`
   inclusive (same float-boundary tolerance applied to both endpoints).
   Aggregation reports interval coverage only — no magnitude-error scoring.
5. **`volatility` — realized vs. rolling history.** Realized volatility is
   the standard deviation of daily log returns over the horizon window
   (not annualized). It is compared against a distribution of same-length
   rolling windows drawn from the 252 trading days before `as_of`
   (`HISTORY_BARS = 252`); the claim's stated percentile locates the
   threshold in that distribution. If fewer than `MIN_VOL_SAMPLES = 20`
   rolling windows are available, the claim is `ungradable` ("insufficient
   history for volatility percentile") rather than scored against a thin
   sample.
6. **`grade_status ∈ {hit, miss, ungradable}`.** Ungradable claims (insufficient
   bar coverage for the horizon, insufficient volatility history, or a memo
   that never cleared the Critic and was marked `unverified`) are excluded
   from hit rate and Brier — they are not scored as misses. The Critic's own
   "horizon exceeds the case's outcome window" check is benchmarked against
   the case's `meta.json` outcome-window length, so an ungradable claim from
   *bar* coverage should not occur for claims that passed the Critic.

Aggregation (`aggregate()` in the same file) reports, over gradable claims
only: `n_claims`, `n_gradable`, `n_hit`, `hit_rate`, **Brier score**
(mean squared error between each claim's stated `confidence` and its 0/1
outcome), and a **calibration table** bucketed into five confidence bands
(`[0,0.2) … [0.8,1.0]`), each bucket carrying its own sample count `n` and
average confidence/hit-rate — deliberately a bucketed table with visible
`n`, never a smoothed reliability curve, so a bucket with `n=1` reads as
`n=1` rather than as a confident point on a line (spec §3.4-A). That table
is what `aggregate()` writes into `scores.json`. The **UI goes one step
further and renders no buckets at all**: the Eval Dashboard draws a
per-claim ConfidenceStrip — every claim plotted individually at its stated
confidence, colored by hit/miss — with an explicit note that bucketed
calibration needs dozens of claims and a single run has 3–5, so each claim
is shown rather than any aggregate shape being implied.

### B. Process + failure attribution (LLM judge)

An independent judge call (`backend/hindsight/eval/judge.py`) receives the
memo JSON, the track-A outcome line for every claim, and the verbatim cited
evidence excerpts (truncated to 1,200 characters per chunk), and returns a
schema-validated `JudgeReport`:

- **`grounding`**: per claim, `supported: bool` + a comment — does the cited
  evidence genuinely back the claim's stated thesis/direction.
- **`reasoning_consistency`** and **`retrieval_sufficiency`**: 1–5 integer
  scores.
- **`attributions`**: for every claim that track A marked a **miss**, one of
  `evidence_missing` / `misread_evidence` / `reasonable_but_wrong`
  (hallucinated attributions on non-missed claim ids are silently dropped —
  `judge.py`'s `run_judge`, the line filtering `report.attributions` against
  the actual `missed` set). This is the answer to "why did it behave that
  way": retrieval failed, the analyst misread what it retrieved, or the
  process was sound and the market simply went the other way.

The judge gets up to two attempts; on schema-validation failure the second
attempt is retried with the validation error appended as feedback. If both
fail, `judge_scores(None)` reports `judge_failed: true` and the run's
process metrics are absent rather than defaulted to a value.

### C. Cost

A token ledger (`CostLedger`, referenced from `judge.py`/`contamination.py`
`ledger.add(...)` calls) tracks prompt/completion token counts and call
counts per agent (`planner`, `analyst`, `critic`, `judge`, `probe` — the
Researcher stage is deterministic and makes no LLM calls). That is the
entire track: **no latency is measured, no provider-priced cost is
computed, and there is no cost-per-hit-claim ratio**. The Leaderboard's
quality-vs-cost scatter uses **total tokens** as its cost proxy — an
honest proxy given that all compared runs use the same model and pricing.
Per-call latency, provider-priced cost, and a cost-per-hit-claim ratio are
named as future work (`docs/future-work.md`), not claimed as shipped.

A **contamination probe** (`contamination.py`) runs once per case: a bare,
temperature-0 prompt asking the model directly what happened to the ticker
after `as_of`. It is stored and surfaced next to the three tracks as a
case-level honesty indicator — explicitly not folded into the hit-rate or
Brier numbers.

## 2. Statistical limitations

This is the section reviewers explicitly asked for; it is stated here as
plainly as in the spec, not softened.

- **Small N is a mechanism demo, not a significance claim.** The committed
  suite (`suite_c3b22b4b`, `docs/eval-log.md` "D4 — evaluation suite") covers
  **2 cases × 2 configs = 4 runs, 4 claims per run**. Every hit_rate/brier
  number in this project is computed over `n_gradable=4` per run. Spec §3.4
  states this directly: "3-case sample size positions all aggregate metrics
  as regression/diagnostic signals and mechanism demonstration, not
  statistical conclusions" (the design targeted 3 cases; D4 shipped 2 — see
  `docs/future-work.md` for the case-2/TSLA deferral — which only tightens
  the same caveat). `EvalSuite`'s batch design exists specifically so this
  scales without an architecture change once more cases are authored.
- **Claims within a run are correlated, not independent samples.** All
  claims in one memo share the same ticker and the same (or overlapping)
  as_of window; they are not independent draws in the statistical sense a
  naive hit-rate reading would assume. A single macro surprise moves every
  claim on that ticker in the same direction at once.
- **The SMCI case is deliberately selected, not randomly sampled.** Spec
  §4.1 names it explicitly as "the failure case (kept on purpose, to
  demonstrate the evaluation system's ability to expose overconfidence)":
  SMCI 2025 was chosen *because* the contemporaneous bullish narrative was
  falsified by realized prices within the 20–40 trading day window (verified
  in `docs/eval-log.md` "D2 — case 3" before authoring: +90% rally into
  as_of, then -16.0%/-23.9%/-27.5%/-28.2%/-29.9% at horizons +1d/+5d/+20d/
  +30d/+40d). Its hit_rate/brier numbers measure whether the harness
  *catches* narrative-following, not a general research accuracy rate — the
  README states this plainly, and it is restated here so it cannot be
  mistaken for an unbiased case draw.
- **Calibration is reported in two deliberately different layers.** In the
  data layer, `aggregate()` still emits the five-bucket calibration table
  into `scores.json`, each bucket carrying its own sample count `n`
  (`avg_confidence`/`hit_rate` reported as `None` when a bucket is empty) —
  a bucket with `n=1` must be read as a single data point, not a
  reliability estimate, and no smoothed line is ever derived from it (spec
  §3.4-A). In the presentation layer, the UI does not chart those buckets
  at all: the Eval Dashboard renders a per-claim **ConfidenceStrip** (every
  claim at its stated confidence, colored hit/miss) plus a note saying why —
  bucketed calibration is meaningful over dozens of claims, and a single
  run has 3–5. Showing every claim individually is the small-n-honest
  rendering of the same underlying numbers.
- **Corpus-composition hindsight bias.** The author curated *which*
  documents exist in each case's corpus while already knowing the outcome.
  Per-fact dating is verified (every statement in every doc is checked to
  be true at its stated publication date), but the *mix* — how many bullish
  versus bearish contemporaneous voices made the cut — is discretionary,
  and an author who knows SMCI collapsed can (even unconsciously) tilt the
  shelf the agent reads from. The mitigation path is mechanical inclusion
  rules that remove the discretion: e.g. *all* EDGAR filings in the window
  via the importer, plus a fixed top-N of contemporaneous notes selected by
  a rule rather than by taste. This became practical rather than
  aspirational once the EDGAR importer shipped; it is not yet applied to
  the committed cases.
- **Claim-difficulty gaming is unscored.** The agent authors its own
  claims, and the schema only requires `threshold_pct > 0` — so a strategy
  of emitting trivially easy claims ("up ≥0.1% in 40 days") could inflate
  hit rate without any research skill. Nothing in the current grading
  penalizes this: hit rate and Brier are difficulty-blind. Honest reading:
  compare configs on the *same* case (paired deltas), where both sides face
  the same temptation. Named mitigations, none implemented yet: a naive
  baseline config as a permanent leaderboard row (what does a no-research
  agent score?), difficulty-stratified reporting, and a minimum-threshold
  floor enforced by the critic.
- **Paired deltas over absolute ranks.** The Leaderboard compares
  same-case, same-config-family deltas (`Δhit_rate`, `Δbrier` vs. a `base`
  config on that same case) rather than ranking configs by absolute score
  across cases — spec §3.6: "config comparison is presented as paired
  per-case deltas, not absolute score ranking; the leaderboard UI notes the
  sample-size limitation." A paired delta at least holds the ticker/window
  fixed across the compared runs; an absolute cross-case rank would not.

### The ablation ladder (added post-D4)

Two pipeline presets exist purely to test the instrument's sensitivity:
`naive` (no LLM anywhere — mechanical always-up-1% claims at coin-flip
confidence, the zero-intelligence floor) and `no_planner` (fixed
title/description retrieval feeds the analyst; the score gap against
`base` is the planner's measured worth). Neither writes experience cards,
so ablations can never contaminate memory-run inputs.

The first full ladder (`suite_bae85908`, 3 cases × 4 configs) produced
this document's most important honest sentence: **at this N, in a
mostly-rising window, raw hit rate cannot separate the full agent from
the always-up floor** — naive collects market beta for free. The
separation the ladder does show is structural: naive posts no grounding,
no reasoning-consistency, no attributable failures, because it has no
process — which is exactly why outcome, process, and cost are three
tracks instead of one number. Consequence: beta-adjusted outcome
thresholds are promoted on the roadmap (see future-work).

## 3. The three anti-lookahead channels (and the one that can't be closed)

The time sandbox (spec §3.2) makes it structurally impossible for the agent
to see the future through three tool-layer doors, and each is asserted
directly by named tests in `backend/tests/test_sandbox_leakage.py` — the
file CI must always keep green:

| Channel | Guarantee | Tests |
|---|---|---|
| **Documents** | Corpus retrieval filters to `doc.published_at <= as_of`; a document published after `as_of` is invisible to retrieval, not merely down-ranked. | `test_corpus_never_returns_future_docs`, `test_corpus_writes_audit_entry` |
| **Market bars** | The price tool raises `LookaheadError` for any request whose range extends past `as_of`, rather than silently truncating; denials are themselves audited. | `test_market_range_ending_after_as_of_raises`, `test_market_range_up_to_as_of_allowed`, `test_market_writes_audit_entry`, `test_denied_market_access_is_audited`, `test_source_error_is_audited` |
| **Experience memory** | Cross-run recall gates on `outcome_window_end <= as_of` **and** excludes the current case (leave-one-out); a suite additionally only reads cards that existed before the suite started (`created_at < suite.started_at`). | `test_memory_channel_hides_unclosed_windows`, `test_memory_channel_leave_one_out`, `test_memory_channel_respects_suite_snapshot` |

`test_as_of_is_read_only` additionally asserts `as_of` on
both sandboxed sources cannot be mutated after construction — the gate's
input can't be tampered with from application code either.

This is not hypothetical: the memory channel's gate produced a real,
observed asymmetry in the committed suite. Verified directly against
`llm_calls.sqlite`'s recorded request bodies (`docs/eval-log.md`, "D4 —
evaluation suite" → "Memory asymmetry check"):

- On **SMCI** (`as_of` 2025-02-26), **none** of the memory run's calls
  contained the injected lessons block — correct, because the only candidate
  card (from `nvda_fy26q1`, whose `outcome_window_end` is 2025-07-22) closes
  *after* SMCI's `as_of` and is gated out. SMCI's memory run replayed
  byte-identical to its base run (same `memo.md`/`claims.json` sha256; all 10
  logical calls served from the record/replay cache — 0 new network calls for
  that run).
- On **NVDA** (`as_of` 2025-05-22), **all 8 planner calls** — 8 of the run's
  13 logical calls (12 hit the network as new `llm_calls.sqlite` rows; the
  contamination probe replayed from cache) — did carry the lessons block,
  because SMCI's `outcome_window_end` (2025-04-24) closes before NVDA's
  `as_of` and leave-one-out doesn't touch a different case's card. The injected text is quoted verbatim in the eval log. The
  memory-primed NVDA run's Brier (0.30063) was in fact *worse* than base's
  (0.26125) — reported as an honest, un-cherry-picked result, not adjusted
  or hidden (see §2's small-N caveat: N=1 per config is not enough to claim
  memory helps or hurts calibration in general — only that the time gate
  behaved exactly as designed and demonstrably changed the planner's brief).

### The fourth channel that cannot be closed: parametric memory

The sandbox gates *tool-layer* access. It cannot stop the underlying LLM
from "remembering" real outcomes after `as_of` from its own pretraining —
spec §3.2's "known limitation" section names this directly. Mitigations, in
the order the spec states them:

1. Cases are chosen close to or after the model's knowledge cutoff where
   feasible (spec §4.1).
2. A **contamination probe** runs once per case (+1 call each): a bare
   prompt asking the model directly what happened to the ticker after
   `as_of`. It is logged and shown on the Eval Dashboard as a case-level
   reference indicator.
3. Both probes run in this project came back clean: the NVDA probe
   answered "I do not know what happened to NVDA... after May 22, 2025"
   (`docs/eval-log.md`, D2 first live run), and the SMCI probe answered "I do
   not know what happened to SMCI... after February 26, 2025" (`docs/eval-log.md`,
   D2 case-3 validation run) — repeated again clean across all runs in the
   D4 suite ("Both contamination probes stayed clean throughout").

**What is the model's training cutoff?** The honest answer: unknown. The
provider (xf-yun MaaS) does not publish an official training cutoff for
`astron-code-latest`, so mitigation #1 above cannot be applied with
documentation — only inferred. Both committed cases' probes (as_of
2025-02-26 and 2025-05-22) returned clean "I don't know" answers, which is
*consistent with* a cutoff before mid-2025, but that is inference from
probe behavior, not a documented fact, and it is exactly the kind of claim
this project refuses to state as if it were checked. The consequence is
the existing rule applied more broadly: absolute outcome scores on these
cases should be read primarily as pipeline-correctness evidence, with the
paired-delta comparisons carrying the analytical weight. The durable
mitigation is structural rather than forensic — author new cases whose
`as_of` postdates the model's release, which the case wizard now makes
cheap to do.

**What a clean probe does and does not prove.** It demonstrates the model
did not produce the realized outcome when asked directly and bluntly in a
single bare turn — it does **not** prove the model has no latent, partially
activated memory of the event that a differently-phrased or multi-turn
prompt could surface, and it does not prove the *agent's* multi-step
research process (which sees real retrieved evidence, not a bare
"what happened" question) is equally uncontaminated. The honest reading
(spec §3.2): outcome scores on a case whose probe is *not* clean should be
interpreted as a demonstration of "grading pipeline correctness and
calibration behavior," not as an uncontaminated measurement of research
skill. Both cases actually run here (NVDA, SMCI) had clean probes, so this
caveat is a standing methodological limit of the approach rather than a
flag on either committed case specifically.

## 4. Judge validity

- **Self-preference risk.** The judge defaults to the same model as the
  agent it grades (`JUDGE_MODEL` can override — spec §3.4). A model judging
  its own output has a structural incentive/bias risk that a
  cross-model judge would avoid.
- **Why relative config comparisons survive it.** Per spec §3.4: "v1
  leaderboard comparisons do not cross main-model families; the preference
  bias approximates a near-constant offset and does not affect relative
  ranking between configs." Because every compared run in this project's
  suite uses the same judge model, a constant self-preference offset cancels
  out of a *paired delta* (base vs. memory, same case) even if it does not
  cancel out of an absolute score. This is exactly why §2 and spec §3.6
  insist on paired deltas over absolute ranks — the judge-bias argument and
  the small-N argument point at the same mitigation.
- **Meta-evaluation receipts.** `docs/judge-meta-eval.md` re-derives every
  judge grounding verdict the project has produced from the recorded LLM
  calls (13 judge-call rows in `llm_calls.sqlite`, deduplicated by shared
  byte-identical replay down to **7 unique judge reports** across **10
  scored runs**, yielding **26 unique grounding entries** — above the
  spec's 10-entry floor) and independently re-labels each by re-reading the
  cited evidence chunks as the judge saw them. Result: **26/26 = 100%
  agreement** between the judge's `supported` verdict and the independent
  re-read.
  - **Provenance caveat, stated in that document's own header and repeated
    here:** these labels were produced by the Claude coordinator's agent
    re-reading the evidence, not by an independent human rater; they are
    explicitly flagged for author review, and the agreement rate
    "recomputes trivially" if any row is relabeled.
  - **False-positive-only caveat.** Every judge verdict across all 26
    entries was `supported` (consistent with `grounding_rate: 1.0` in every
    committed run's `scores.json`). The meta-eval therefore shows the judge
    produced **zero false positives** on this data — it provides **no
    evidence** about whether the judge would correctly flag an ungrounded
    claim, because there is not one negative instance in the data to test
    it against. `docs/judge-meta-eval.md` attributes this to the pipeline's
    upstream constraints (the analyst can only cite retrieved chunk ids; the
    critic's consistency gate rejects evidence problems before the judge
    ever sees the memo) rather than to judge leniency, and names a
    deliberate evidence-swap perturbation test as the natural next step
    (recorded in future work, not yet run).

## 5. Reproducibility

- **Frozen bars.** Each case's market data is pulled once at case-authoring
  time with `auto_adjust=True` and frozen to `datasets/<case_id>/bars.json`,
  committed to the repo — the same snapshot produces both the grading
  baseline and the realized outcome, so scoring is reproducible without a
  live network call at run time (spec §4.1).
- **Record/replay determinism.** All LLM calls go through a
  `RecordingLLMClient`: record mode persists request→response pairs (keyed
  by a hash of the fully-constructed request) to `llm_calls.sqlite`; replay
  mode looks up that hash and serves the recorded response with zero network
  traffic. `HINDSIGHT_OFFLINE=1` forces replay-only and raises explicitly on
  a cache miss instead of silently calling the API.
- **Byte-identical offline replay — direct evidence.** `docs/eval-log.md`
  ("D2 — case 3: SMCI falsification case") records exactly this: the record-mode
  validation run `run_smci_case3_20260704_082812_622419` was re-run offline
  as `run_smci_case3_20260704_083129_603736` with `--offline`, "completed
  without network, memo byte-identical to the record-mode run." The same
  determinism shows up again, independently, in the D4 suite: the
  `smci_case3` memory-config run reduced to a byte-for-byte identical replay
  of its own base-config run (same `memo.md`/`claims.json` sha256; all 10
  logical calls were cache hits, 0 new network rows) precisely because
  identical prompts hash to the same request key — the replay layer's
  correctness is corroborated by an *independent* run pair, not just the
  one explicit `--offline` A/B.
- **Fixed prompts as versioned code, with eval-log receipts.** Agent system
  prompts (`backend/hindsight/agents/prompts.py`) are ordinary
  version-controlled source, not runtime-tunable config — every prompt edit
  is a diff reviewable in git history. `docs/eval-log.md`'s D2 entries are
  the receipts for two such edits made in direct response to evaluation
  failures, each with before/after suite-relevant scores and a full backend
  test re-run: the **mutual-consistency rule** added to `ANALYST_SYSTEM`
  after `run_nvda_fy26q1_20260704_074410_b3e722` came back `unverified`
  with `n_gradable=0` because direction and magnitude claims on the same
  horizon disagreed about the sign of one shared return (test suite: 138
  passed after the edit, no regressions); and the **critic rubric rewrite**
  in `CRITIC_SEMANTIC_SYSTEM` after `run_nvda_fy26q1_20260704_075823_3fdb4f`
  still came back `unverified` because the critic was over-rejecting
  correctly-gradable `volatility` claims as "not objectively checkable" (test
  suite: 138 passed after that edit too). The very next run,
  `run_nvda_fy26q1_20260704_080442_ce7ca0`, passed the critic on the first
  attempt. This before/after-scored, git-diffable prompt history is the
  literal evidentiary trail for "evaluation as the primary mechanism to
  guide behavior."

## Artifact index

| Claim | Source |
|---|---|
| Grading runs outside the sandbox; A-then-B order | `backend/hindsight/eval/outcome_grader.py` module docstring; spec §3.4 |
| Baseline P0, trading-day counting, direction/magnitude/volatility rules, `hit`/`miss`/`ungradable` | `backend/hindsight/eval/outcome_grader.py` (`_baseline_index`, `grade_claim`); spec §3.3 rules 1-6 |
| `MIN_VOL_SAMPLES = 20`, `HISTORY_BARS = 252` | `backend/hindsight/eval/outcome_grader.py` |
| Float-boundary `math.isclose` tolerance on direction/magnitude thresholds | `backend/hindsight/eval/outcome_grader.py` inline comments |
| Calibration table in `scores.json` carries per-bucket `n`, never a smoothed line; UI renders the per-claim strip instead | `backend/hindsight/eval/outcome_grader.py` `aggregate()`; `frontend/src/components/ConfidenceStrip.tsx`; spec §3.4-A |
| Judge schema (`grounding`, `reasoning_consistency`, `retrieval_sufficiency`, `attributions`), 2-attempt retry, hallucinated-attribution filtering | `backend/hindsight/eval/judge.py` |
| Contamination probe design (bare prompt, temperature 0, +1 call/case) | `backend/hindsight/eval/contamination.py`; spec §3.2 |
| Judge runs after track A; self-preference bias framing; paired deltas over absolute ranks | Spec §3.4, §3.6 |
| Small-N / correlated-claims / SMCI-deliberate-selection framing | Spec §3.4, §4.1 |
| SMCI case selection rationale and verified pre-as_of rally / post-as_of drawdown numbers | `docs/eval-log.md` "D2 — case 3: SMCI falsification case" |
| Three anti-lookahead channels, per-channel leakage tests | `backend/tests/test_sandbox_leakage.py` |
| Memory asymmetry: SMCI 0 lessons calls, NVDA lessons block in all 8 planner calls, byte-identical SMCI memory run, worse NVDA memory Brier (0.30063 vs 0.26125) | `docs/eval-log.md` "D4 — evaluation suite" → "Memory asymmetry check" (row partition corrected at D4 wrap-up) |
| Contamination probes clean on both NVDA and SMCI | `docs/eval-log.md` "D2 — first live NVDA run", "D2 — case 3" |
| Judge self-preference mitigation via paired deltas | Spec §3.4 |
| Judge meta-eval: 26/26 = 100% agreement, provenance caveat, false-positive-only caveat, 7 unique reports / 10 scored runs | `docs/judge-meta-eval.md` |
| Frozen bars, `auto_adjust=True` | Spec §4.1 |
| Record/replay client, `HINDSIGHT_OFFLINE=1` behavior | Spec §4.4 |
| Byte-identical offline replay (`--offline` A/B) | `docs/eval-log.md` "D2 — case 3" → "Offline replay proof" |
| Independent byte-identical replay corroboration (SMCI memory run = cache hits) | `docs/eval-log.md` "D4 — evaluation suite" → "Memory asymmetry check" / "CAVEAT confirmed" |
| Prompt-as-code, mutual-consistency fix and critic rubric fix with before/after scores | `docs/eval-log.md` "D2 — first live NVDA run" (runs 1, 2b, 3) |
| Full backend suite passes offline | Verified locally: `cd backend && .venv/Scripts/python -m pytest -q`; enforced in CI on every push |
