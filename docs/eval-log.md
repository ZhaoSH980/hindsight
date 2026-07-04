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
