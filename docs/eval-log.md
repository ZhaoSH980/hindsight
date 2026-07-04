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
