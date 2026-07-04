"""Parametric-memory contamination probe (spec §3.2 known limitation).

Asks the model directly what it knows about the ticker AFTER as_of. The
answer is stored per run and surfaced on the Eval Dashboard as a case-level
contamination indicator. Deterministic prompt + temperature 0 means the
recording layer collapses repeat probes into a single real API call.
"""
from __future__ import annotations

from datetime import date

from hindsight.agents.prompts import PROBE_PROMPT
from hindsight.llm.recording import RecordingLLMClient
from hindsight.trace.cost_ledger import CostLedger


def run_contamination_probe(
    llm: RecordingLLMClient, ticker: str, as_of: date, ledger: CostLedger
) -> str:
    resp = llm.chat(
        messages=[
            {
                "role": "user",
                "content": PROBE_PROMPT.format(ticker=ticker, as_of=as_of.isoformat()),
            }
        ],
        temperature=0.0,
    )
    usage = resp.get("usage") or {}
    ledger.add("probe", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    return resp["choices"][0]["message"].get("content") or ""
