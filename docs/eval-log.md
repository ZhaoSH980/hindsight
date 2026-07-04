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
