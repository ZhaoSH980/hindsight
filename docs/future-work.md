# Future work & conscious scope decisions

Recorded at the D4 wrap-up (tag `d4-complete`). Two kinds of entries:
**scope decisions** made deliberately during the 4-day build (with the
rationale that made them safe to defer), and **minor findings** from the
final whole-repo review that did not warrant blocking the tag. Nothing here
is a known-broken behavior; the test suite (171) is green and every README /
methodology claim traces to a committed artifact.

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

- **Crashed-partial run row shows `running` forever.**
  `run_nvda_fy26q1_20260704_075320_922d45` (the D2 recording crash kept
  deliberately as a failure-tolerance artifact) still has status `running`
  in the committed `hindsight.db`, so the Eval Dashboard's run list shows a
  permanently running 2026-07-04 row. Honest, but a `stale`/`crashed`
  sweep (e.g. flag `running` rows older than N hours at API startup) would
  read better. The run is documented as a crashed partial in
  `docs/judge-meta-eval.md`.
- **Frontend ships one 615 kB JS chunk.** Vite warns at build time;
  Recharts dominates. Route-level `import()` splitting (Leaderboard and
  EvalDashboard are the only Recharts consumers) would cut initial load
  roughly in half. Cosmetic for a local demo.
- **Trace Explorer nav placeholder is a dead end.** The nav's "Trace
  Explorer" link points at `/runs/_/trace`, which renders only "Run not
  found." until a run is chosen via Studio or the Eval Dashboard list. An
  empty state that lists recent runs (like `/runs/_` does) would be
  friendlier.
- **`HEAD /` returns 405.** The SPA fallback registers GET only; HEAD
  probes (some uptime checkers, some tooling) get 405 instead of 200.
  One-line fix (`methods=["GET", "HEAD"]`) if it ever matters.
- **Judge meta-eval needs a negative-instance test.** All 26 recovered
  grounding verdicts are `supported` (zero false positives, no evidence on
  miss-catching). The named next step: an evidence-swap perturbation —
  re-run the judge on a memo whose citations are deliberately shuffled to
  not support the claims, and check it flags them. Costs a handful of
  metered calls; design is in `docs/judge-meta-eval.md`.
