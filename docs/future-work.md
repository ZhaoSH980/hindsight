# Future work & conscious scope decisions

Recorded at the D4 wrap-up (tag `d4-complete`). Two kinds of entries:
**scope decisions** made deliberately during the 4-day build (with the
rationale that made them safe to defer), and **minor findings** from the
final whole-repo review that did not warrant blocking the tag. Nothing here
is a known-broken behavior; the full backend suite is green (`pytest -q`)
and every README / methodology claim traces to a committed artifact.
Entries resolved by later work are marked **done** in place rather than
deleted, so the decision trail stays readable.

## Conscious scope decisions

- **Case 2 (TSLA) deferred — 3 cases became 2.** The D1 plan pre-sanctioned
  exactly this fallback: case authoring is the slowest, most
  correctness-critical work (every fact in every doc must be true *at its
  publication date*), and two verified cases (NVDA contamination-window +
  SMCI falsification) already exercise every mechanism — including the
  memory-gate asymmetry that needs two different as_of dates. `EvalSuite`
  and the Leaderboard are N-case by construction; when a third case lands
  in `datasets/`, `--cases a,b,c` scales with zero code change. The
  methodology doc's small-N framing already assumes the tighter N.
  *Update:* the Studio's case wizard + one-click EDGAR import now automate
  the mechanical parts of exactly this work — bar freezing, as-of
  validation at the door, and filing sourcing with regulator-stamped dates.
  The remaining cost of a TSLA (or any) case is the part that *should*
  stay manual: fact-checking the narrative documents.
- **Demo GIF skipped.** Static screenshots of all four pages shipped in
  `docs/assets/` and the rehearsed walkthrough lives in
  `docs/demo-script.md`; a GIF adds polish, not information. Skipped
  gracefully per the plan's explicit nice-to-have clause.
- **Chunker: heading-only merge polish.** The markdown chunker can emit a
  tiny chunk holding only a section heading when a heading directly abuts
  the chunk boundary; merging it forward into its section body would
  improve retrieval granularity slightly. Retrieval quality was never
  observed to suffer in graded runs (grounding 1.0 across the suite), so it
  stayed a polish item.
- **CLI UX hardening.** `hindsight.cli` is developer tooling: errors
  surface as tracebacks, there's no `--help` prose beyond argparse
  defaults, no progress indicator during multi-minute suite runs, and no
  subcommand to list/inspect runs. Fine for the build-and-demo loop; would
  need hardening for anyone else's hands.
- **Judge first attempt always loses one retry to the attributions schema.**
  Observed across all recorded runs (judge = 2 calls every time): the
  judge's first reply adds an extra `comment` field inside each
  `attributions` entry, `JudgeReport` forbids extra keys
  (`extra_forbidden`), and the schema-feedback retry then passes. Two
  one-line fixes are possible — allow an optional `comment` on
  `Attribution`, or add "attribution entries carry claim_id and category
  ONLY, no comment" to the judge prompt. Either saves ~1 metered call per
  run; deferred because the retry path is itself a tested feature and the
  cost is one call.
- **`RecordingLLMClient`: coarse lock vs per-request clients.** D3 made the
  shared sqlite connection thread-safe with `check_same_thread=False` plus
  a client-wide lock. The documented alternative — constructing a
  short-lived client (or connection) per request — would remove the
  serialization point entirely. At demo concurrency (one run at a time) the
  lock is invisible; revisit only if runs ever execute in parallel.
- **Suite snapshot boundary stays strict `<`.** Deliberate, do not "fix":
  a suite only reads experience cards with `created_at < suite.started_at`,
  so cards written by the suite's own earlier runs can never leak into its
  later runs. Recorded here because it looks like an off-by-one to fresh
  eyes; `test_memory_channel_respects_suite_snapshot` pins it.
- **D3 leftovers that stayed acceptable.** Memo bodies render in a
  `<pre>` block rather than a markdown renderer (readable, just plain);
  `Store` uses one coarse lock (same reasoning as the recording client);
  the WebSocket stream is a 0.4s file-tail poll with a ~10-minute ceiling
  (right-sized for replay/demo runs, not for hour-long live jobs).

## Minor findings from the final review (non-blocking)

- **Crashed-partial run row shows `running` forever — done.** Exactly the
  sweep proposed here now exists: at API startup, orphaned `queued`/
  `running` rows (runs execute in server daemon threads, so none can
  survive a restart) are marked `failed`. The D2 crashed partial
  (`run_nvda_fy26q1_20260704_075320_922d45`) remains documented in
  `docs/judge-meta-eval.md`.
- **Frontend ships one 615 kB JS chunk.** Vite warns at build time;
  Recharts dominates. Route-level `import()` splitting (Leaderboard and
  EvalDashboard are the only Recharts consumers) would cut initial load
  roughly in half. Cosmetic for a local demo.
- **Trace Explorer nav placeholder is a dead end — done.** The UI redesign
  added a run picker, so the nav link now lands on a usable run chooser
  instead of "Run not found."
- **`HEAD /` returns 405.** The SPA fallback registers GET only; HEAD
  probes (some uptime checkers, some tooling) get 405 instead of 200.
  One-line fix (`methods=["GET", "HEAD"]`) if it ever matters.
- **Judge meta-eval needs a negative-instance test.** All 26 recovered
  grounding verdicts are `supported` (zero false positives, no evidence on
  miss-catching). The named next step: an evidence-swap perturbation —
  re-run the judge on a memo whose citations are deliberately shuffled to
  not support the claims, and check it flags them. Costs a handful of
  metered calls; design is in `docs/judge-meta-eval.md`.

## Opened by the wizard / UI-redesign wave

New items that only became meaningful (or practical) once the case wizard,
EDGAR import, and redesigned dashboard landed:

- **EDGAR pagination beyond the "recent" window.** The importer reads
  EDGAR's recent-filings feed, which covers roughly the ~1000 most recent
  filings per company — plenty for recent as_of dates, but a case set in,
  say, 2018 for a filing-heavy company would need the full-index/paginated
  API. The server-side URL rebuild and UA handling carry over unchanged.
- **Naive baseline config as a leaderboard row.** **Done post-D4**: the
  `naive` (no LLM, always-up coin-flip claims) and `no_planner` (fixed
  retrieval) presets now anchor the leaderboard (`suite_bae85908`). The
  first run of the ladder produced the honest headline in
  eval-log 2026-07-05: hit rate can't separate the agent from the
  always-up floor at this N — market beta pays naive for free — which
  promotes the beta-adjusted-thresholds item below.
- **Beta-adjusted outcome thresholds.** The ablation ladder's headline
  finding: in a rising window, "always up ≥1%" collects market beta for
  free, so raw hit rate conflates research skill with market direction.
  Fix: grade direction/magnitude claims on return in excess of the
  market (or of the ticker's trailing drift), or require thresholds to
  clear a market-implied floor. This is the highest-leverage metric
  improvement the instrument itself surfaced.
- **Claim-difficulty scoring.** Today `threshold_pct > 0` is the only
  floor, so trivially easy claims could inflate hit rate unscored
  (methodology §2 now names this limitation). Candidate mechanics:
  difficulty-stratified reporting, a minimum-threshold floor in the critic,
  or scoring claims against the ticker's realized volatility so "up ≥0.1%"
  earns roughly nothing.
- **Per-call latency and provider-priced cost in the ledger.** The cost
  track deliberately records only per-agent token/call counts, with total
  tokens as the leaderboard's cost proxy. Wall-clock latency per call and a
  priced-cost column (per-model rates) would complete track C — and make a
  cost-per-hit-claim ratio honest to compute.
