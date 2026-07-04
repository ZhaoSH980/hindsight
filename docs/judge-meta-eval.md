# Judge meta-evaluation: grounding verdicts vs. independent re-read

> **Provenance — read this first.** Labels in this document were produced by the Claude
> coordinator's agent re-reading each cited evidence chunk; they are intended for author
> review — relabel any row you disagree with; the agreement rate recomputes trivially
> (agree-count / 26). These are NOT independent human labels until the author has reviewed
> them. The labeling criterion mirrors the judge's rubric: *does the cited text genuinely
> support the claim's thesis/direction?* (Evidence can never prove a future return band;
> a claim is "supported" when the chunks it cites genuinely back its direction and framing.)

## How the entries were recovered

The judge's per-claim `grounding` list is not persisted in `scores.json` (only the
aggregate `grounding_rate` is). The full entries were recovered from the recorded LLM
calls in `llm_calls.sqlite`: the 13 rows whose request contains the judge system prompt
("You are the process judge") were parsed — request side into the memo (claim ids,
statements, cited chunk ids) plus the verbatim evidence excerpts the judge saw; response
side (fences stripped) into the `JudgeReport` shape of `backend/hindsight/eval/judge.py`.
Each judge call was paired to its run(s) by exact match of (claim_id, statement,
evidence ids) against the run's `claims.json`.

Independent labels were made against the evidence text **as the judge saw it** (recovered
from the recorded requests — relevant because two corpus docs were edited by the D4
citation-hygiene fix after the early runs), cross-checked against full chunk texts
re-derived from `datasets/*/docs` via `backend/hindsight/rag/chunker.py` (excerpts shown
to the judge are truncated at 1,200 chars per chunk).

## Run inventory and deduplication

11 run directories are committed under `runs/`. One
(`run_nvda_fy26q1_20260704_075320_922d45`) is a crashed partial with only a trace and no
scores — excluded. The remaining **10 scored runs** (6 pre-suite D2/D3-era + 4 suite
runs; the D4 plan's "8 total" estimate undercounted the pre-suite era by two) map onto
**7 unique judge reports**, because byte-identical runs replay the identical judge
request from the recording cache and therefore share one judge response:

| Report | Run(s) | Case | Judge response shared? |
|---|---|---|---|
| R1 | `run_nvda_fy26q1_20260704_074410_b3e722` | NVDA | no |
| R2 | `run_nvda_fy26q1_20260704_075823_3fdb4f` | NVDA | no |
| R3 | `run_nvda_fy26q1_20260704_080442_ce7ca0` + `run_nvda_fy26q1_20260704_081010_a2ea8e` | NVDA | yes — identical memo, one judge call replayed by both |
| R4 | `run_smci_case3_20260704_082812_622419` + `run_smci_case3_20260704_083129_603736` | SMCI | yes — identical memo, shared |
| R5 | `run_smci_case3_20260704_105922_28a79f` (suite base) + `run_smci_case3_20260704_110057_faa55c` (suite memory) | SMCI | yes — on SMCI no experience cards pass the time gate, so the memory config reduced to base and replayed it byte-identically |
| R6 | `run_nvda_fy26q1_20260704_110057_5107e6` (suite base) | NVDA | no |
| R7 | `run_nvda_fy26q1_20260704_110357_439805` (suite memory) | NVDA | no — lesson lines changed the planner brief, hence a different memo and a fresh judge call |

Each shared judge response is counted **once** below. R1 has 3 claims, R2 has 3, R3–R7
have 4 each: **26 unique grounding entries** — above the spec's 10-entry floor, so no
shortfall to report.

Retry note: 6 of the 7 reports took two LLM calls (hence `judge.calls = 2` in most
`scores.json` cost blocks). In every retry pair the first response failed schema
validation for the same benign reason — the model added an extra `comment` field inside
`attributions`, which the strict (`extra="forbid"`) `JudgeReport` schema rejects — and
the second attempt validated. The grounding verdicts were identical across both attempts
in all six pairs; the labels below are against the validated (effective) reports.

## The table

Verdict/label vocabulary: `sup` = supported (cited evidence genuinely backs the claim's
thesis), `not-sup` = not supported. Every judge verdict in every report is `sup`
(consistent with `grounding_rate: 1.0` in all ten `scores.json` files).

| # | Report | Claim | Statement (gist) | Cited evidence (gist) | Judge | Label | Agree? | Rationale (one line) |
|---|---|---|---|---|---|---|---|---|
| 1 | R1 | c1 | NVDA ≥3% above as-of at day 5 (earnings reaction) | hyperscaler_capex::000/001 (budgets intact, >$300B), blackwell_ramp::000 (3.6M GPU orders), analyst_preview::000 | sup | sup | yes | Cited demand-side chunks genuinely back a bullish reaction thesis; note the judge's comment also invokes the "$11B debut", which is in the memo text but not in c1's cited chunks — verdict unaffected. |
| 2 | R1 | c2 | 5-day return in [−7%, +2%] (muted/downside scenario) | h20_export_restriction::000 ($5.5B charge, ~$17B China), ai_capex_skeptic::000 (pre-fix text: 2GW walk-away, DeepSeek), q4_fy25_recap::001 (margin guide down, −8.5% on last print), analyst_preview::000 | sup | sup | yes | The bear-side chunks cited genuinely support a muted-to-down scenario; correctly marshaled for the claim's direction. |
| 3 | R1 | c3 | 5-day realized vol in top 20% of prior-year windows | analyst_preview::000 (unusually wide EPS dispersion), h20::000/001 (charge size open, license questions), q4_fy25_recap::001 | sup | sup | yes | Wide estimate dispersion plus unresolved binary questions is exactly the evidence an elevated-event-vol claim needs. |
| 4 | R2 | c1 | NVDA ≥3% above $132.64 at day 20 | hyperscaler_capex::000/001, blackwell_ramp::001 ($11B quarter, fastest ramp), analyst_preview::000 (~$45B guide watermark) | sup | sup | yes | Demand and ramp chunks directly support the constructive 20-day thesis. |
| 5 | R2 | c2 | 20-day return in [+3%, +12%] | hyperscaler_capex::001, blackwell_ramp::001, analyst_preview::000, q4_fy25_recap::000 (record revenue) | sup | sup | yes | Cited chunks back the positive direction; the band itself is calibration, not an evidence question. |
| 6 | R2 | c3 | 5-day vol > p80 of prior 252-day windows | h20::000/001 (indefinite license, $5.5B), analyst_preview::000 (wide dispersion) | sup | sup | yes | Same event-uncertainty evidence pattern as row 3; genuinely supportive. |
| 7 | R3 | c1 | NVDA ≥3% above ($132.64) at day 5 | hyperscaler_capex::000/001, blackwell_ramp::001, analyst_preview::000 | sup | sup | yes | Bullish demand chunks match the bullish claim. |
| 8 | R3 | c2 | 5-day return in [+3%, +12%] (positive, not extreme) | hyperscaler_capex::000, blackwell_ramp::001, analyst_preview::000, q4_fy25_recap::001 (margin headwind) | sup | sup | yes | Demand strength plus a cited headwind chunk is coherent grounding for a bounded-positive claim. |
| 9 | R3 | c3 | 5-day vol > p70 (earnings turbulence) | analyst_preview::000, h20::000/001, ai_capex_skeptic::001 (pre-fix text: H20 ban, customer concentration) | sup | sup | yes | Multiple documented uncertainty sources support the elevated-vol thesis. |
| 10 | R3 | c4 | ≥5% above at day 20 (sustained Blackwell/capex strength) | hyperscaler_capex::001, blackwell_ramp::000/001, analyst_preview::000 | sup | sup | yes | The cited GTC-order and capex chunks are precisely the claim's stated drivers. |
| 11 | R4 | c1 | SMCI ≥5% below $51.11 at day 20 | bear_view_margins_governance::000/001 (pre-fix text: JPM Underweight $23, EY resignation), 10k_filed_compliance::000 (adverse ICFR opinion, DOJ/SEC subpoenas) | sup | sup | yes | Bear chunks genuinely support downside; the compliance chunk's caveat paragraph carries the bear-relevant content even though its headline event is positive. Judge's "90% rally" is imprecise (chunk says "more than doubled"), verdict unaffected. |
| 12 | R4 | c2 | 20-day return in [−15%, −5%] | same bear set as row 11 | sup | sup | yes | Direction genuinely evidenced; the realized −27.5% overshot the band, but grounding judges the citation, not the outcome. |
| 13 | R4 | c3 | 40-day vol > p70 | bear_view::000, bull_thesis_turnaround::000, 10k_filed::000, accounting_saga_recap::000 (−19%, −12%, −33% single-day moves) | sup | sup | yes | Opposing bull/bear signals plus a documented history of violent moves genuinely support a high-vol claim. |
| 14 | R4 | c4 | ≥10% above at day 40 (bull scenario) | bull_thesis::000/001 (overhang cleared, Loop $70 PT), hyperscaler_capex_macro::000 ($320B capex), blackwell_dlc_production::000 | sup | sup | yes | All four chunks are on-thesis bull evidence for the hedged upside scenario. |
| 15 | R5 | c1 | SMCI ≥5% above at day 20 (re-rating momentum) | bull_thesis::000/001, 10k_filed::000, blackwell_dlc_production::000 | sup | sup | yes | Compliance-cleared and production chunks genuinely back the re-rating thesis (outcome was a miss; grounding still valid). |
| 16 | R5 | c2 | 20-day return in [−10%, +4%] (pullback as concerns reassert) | bear_view::000/001 (post-fix text: JPM $35-from-$23, still Underweight), q2_fy25_update::000 (FY25 guidance cut), 10k_filed::000 | sup | sup | yes | Margin/governance chunks genuinely support a cautious pullback band. |
| 17 | R5 | c3 | ≥8% below at day 40 (relief rally fades) | bear_view::000/001, 10k_filed::000, q2_fy25_update::000 | sup | sup | yes | Same bear set legitimately extends to the longer-horizon downside claim. |
| 18 | R5 | c4 | 40-day vol > p80 (probes + rally turbulence) | 10k_filed::000 (open DOJ/SEC), bear_view::001, accounting_saga_recap::000, hyperscaler_capex_macro::000 (DeepSeek repricing day) | sup | sup | yes | Probe overhang plus documented violent history support high vol; the capex-macro chunk is the weakest citation (mostly demand-side) but its DeepSeek-crash passage is vol-relevant. |
| 19 | R6 | c1 | NVDA ≥3% above at day 5 | hyperscaler_capex::000/001, blackwell_ramp::000/001, analyst_preview::000 | sup | sup | yes | Demand and ramp chunks (here including the $11B chunk, actually cited) back the bullish reaction claim. |
| 20 | R6 | c2 | 5-day return in [+3%, +12%] | hyperscaler_capex::000/001, blackwell_ramp::000, analyst_preview::000 | sup | sup | yes | Same bullish evidence set supports a modest-positive band. |
| 21 | R6 | c3 | 5-day vol > p80 | h20::000, analyst_preview::000, ai_capex_skeptic::001 (post-fix text), q4_fy25_recap::001 (−8.5% on prior print) | sup | sup | yes | Charge uncertainty, dispersion, and a large prior earnings move genuinely support elevated vol. |
| 22 | R6 | c4 | ≥5% above at day 20 | hyperscaler_capex::001, blackwell_ramp::000/001, amd_competition::001 ("unlikely to cap the Blackwell ramp") | sup | sup | yes | The AMD chunk explicitly concludes NVIDIA's ramp is not capped — legitimate support for the longer bullish claim. |
| 23 | R7 | c1 | NVDA ≥3% above $132.64 at day 5 | hyperscaler_capex::000/001, analyst_preview::000, blackwell_ramp::000 | sup | sup | yes | On-thesis demand evidence for the bullish reaction claim. |
| 24 | R7 | c2 | 5-day return in [+3%, +12%] (measured positive, post-rally) | hyperscaler_capex::000, analyst_preview::000, blackwell_ramp::001, q4_fy25_recap::001 | sup | sup | yes | Demand-vs-headwind tension backs a measured-positive band; minor nuance: the "recent rally" framing sits oddly beside blackwell_ramp::001's "shares have lagged" line, but no cited text contradicts the claim's direction. |
| 25 | R7 | c3 | ≥5% above at day 40 (sustained strength) | hyperscaler_capex::001, blackwell_ramp::000, analyst_preview::000, amd_competition::001 | sup | sup | yes | Capex persistence, ramp trajectory, and the AMD moat chunk genuinely support the 40-day bullish claim (this one hit: +25.8%). |
| 26 | R7 | c4 | 5-day vol > p80 (earnings turbulence) | h20::000, analyst_preview::000, ai_capex_skeptic::000 (post-fix text incl. Wells Fargo/AWS lease checks) | sup | sup | yes | Charge dispersion plus macro-uncertainty chunks genuinely support the elevated-vol claim. |

## Agreement rate

**26 / 26 = 100%** (labels as shipped; recompute after author review).

## Honest caveats

- **The verdict distribution is one-sided.** The judge said `supported` on all 26 entries,
  and the re-read agrees each time. That means this meta-eval confirms the judge produced
  **no false positives** on this data, but it provides **zero evidence** about the judge's
  ability to catch an ungrounded claim — there is not a single negative instance to test
  against. This is a property of the pipeline, not leniency: the analyst is constrained to
  cite retrieved chunk ids and the critic gate rejects memos with evidence problems before
  the judge ever sees them, so weakly-grounded claims rarely survive to judging. A
  deliberate perturbation test (feeding the judge a memo with swapped or irrelevant
  evidence ids) would be the natural next step and is noted in future work.
- **All claims here are scenario-hedged forecasts.** Several memos carry mutually opposing
  claims (e.g. R4 c1 bearish / c4 bullish; R5 c1 bullish / c3 bearish). Grounding is
  judged per claim, so both sides can legitimately be `supported` — the re-read applied
  the same per-claim standard.
- **The judge sees more than the cited chunks.** It receives the full memo JSON and
  outcome lines, and its comments occasionally blend memo narrative with cited evidence
  (row 1's "$11B debut") or round numbers loosely (row 11's "90% rally"). Neither instance
  changed a verdict, but comment text should not be read as strictly evidence-derived.
- **Evidence excerpts are truncated at 1,200 chars** in the judge prompt; labels were
  made primarily against the same truncated view (with full chunks consulted for context),
  so judge and labeler saw the same load-bearing text.
- **Corpus drift between eras.** The D4 citation-hygiene fix (commit `67e9d39`) edited
  `ai_capex_skeptic.md` and `bear_view_margins_governance.md` after the six pre-suite runs.
  R1/R3/R4 were therefore judged against the pre-fix chunk text (e.g. R4's chunks still
  carried JPMorgan's $23 target; the post-fix text has the $35-from-$23 raise), and the
  labels for those rows were made against that same pre-fix text as recovered from the
  recorded requests — not against today's corpus.
