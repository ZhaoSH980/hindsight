"""Critic: three-layer memo validation with feedback-retry (spec §3.1).

Layer 1: JSON + pydantic schema. Layer 2: mechanical consistency (evidence
ids exist, ticker matches, horizon within the case window). Layer 3: one
LLM semantic check. Failures feed back to the Analyst, max 2 retries; a
structurally-valid memo that never passes layer 3 is returned unverified.
"""
from __future__ import annotations

import json

from pydantic import ValidationError

from hindsight.agents.analyst import render_evidence, run_analyst
from hindsight.agents.prompts import CRITIC_SEMANTIC_SYSTEM
from hindsight.data.models import CaseMeta, Chunk
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import Memo
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder

MAX_RETRIES = 2


def strip_fence(text: str) -> str:
    """Extract the JSON payload from an LLM reply: tolerates ```json fences
    (with or without a space/language tag), prose before/after the fence,
    and bare prose around a top-level JSON object."""
    text = text.strip()
    if "```" in text:
        start = text.find("```")
        rest = text[start + 3 :].lstrip()
        if rest[:4].lower() == "json":
            rest = rest[4:]
        end = rest.find("```")
        if end != -1:
            rest = rest[:end]
        return rest.strip()
    if not text.startswith("{") and "{" in text and text.rfind("}") > text.find("{"):
        return text[text.find("{") : text.rfind("}") + 1]
    return text


def structural_check(
    raw: str, valid_evidence_ids: set[str], case: CaseMeta
) -> tuple[Memo | None, list[str]]:
    try:
        memo = Memo.model_validate_json(strip_fence(raw))
    except (ValidationError, ValueError) as exc:
        return None, [f"schema: {str(exc)[:800]}"]
    errors: list[str] = []
    for claim in memo.claims:
        if claim.ticker != case.ticker:
            errors.append(f"claim {claim.claim_id}: ticker {claim.ticker} != case ticker {case.ticker}")
        if claim.horizon_days > case.outcome_window_days:
            errors.append(
                f"claim {claim.claim_id}: horizon {claim.horizon_days} exceeds case window {case.outcome_window_days}"
            )
        for eid in claim.evidence:
            if eid not in valid_evidence_ids:
                errors.append(f"claim {claim.claim_id}: unknown evidence id {eid}")
    return (memo, errors) if not errors else (None, errors)


def semantic_check(
    llm: RecordingLLMClient,
    memo: Memo,
    evidence_chunks: list[Chunk],
    temperature: float,
    ledger: CostLedger,
) -> tuple[bool, list[str]]:
    user = (
        "Memo JSON:\n" + memo.model_dump_json() + "\n\nCited evidence:\n"
        + render_evidence(evidence_chunks)
    )
    resp = llm.chat(
        messages=[
            {"role": "system", "content": CRITIC_SEMANTIC_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    usage = resp.get("usage") or {}
    ledger.add("critic", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    text = strip_fence(resp["choices"][0]["message"].get("content") or "")
    try:
        verdict = json.loads(text)
        return bool(verdict.get("ok")), [str(p) for p in verdict.get("problems", [])]
    except (json.JSONDecodeError, AttributeError):
        # fail CLOSED: an unreviewable verdict consumes a retry; repeated
        # failures leave the memo marked unverified instead of silently passing
        return False, [
            "semantic review could not parse its verdict; regenerate the memo "
            "JSON exactly (unchanged if you believe it is correct)"
        ]


def produce_memo(
    llm: RecordingLLMClient,
    evidence_chunks: list[Chunk],
    case: CaseMeta,
    market_summary: str,
    temperature: float,
    trace: TraceRecorder,
    ledger: CostLedger,
) -> tuple[Memo | None, bool]:
    valid_ids = {c.chunk_id for c in evidence_chunks}
    feedback: str | None = None
    last_structurally_valid: Memo | None = None
    for attempt in range(1 + MAX_RETRIES):
        raw = run_analyst(
            llm, evidence_chunks, case, market_summary, temperature, ledger, feedback
        )
        memo, errors = structural_check(raw, valid_ids, case)
        if memo is None:
            trace.emit(
                TraceEvent(
                    type="validation",
                    agent="critic",
                    payload={"attempt": attempt, "layer": "structural", "errors": errors[:6]},
                )
            )
            feedback = f"(attempt {attempt + 1}) " + "\n".join(errors[:6])
            continue
        last_structurally_valid = memo
        ok, problems = semantic_check(llm, memo, evidence_chunks, temperature, ledger)
        trace.emit(
            TraceEvent(
                type="validation",
                agent="critic",
                payload={"attempt": attempt, "layer": "semantic", "ok": ok, "problems": problems[:6]},
            )
        )
        if ok:
            return memo, False
        feedback = f"(attempt {attempt + 1}) " + "\n".join(problems[:6])
    return last_structurally_valid, True  # unverified (or None if never structural)
