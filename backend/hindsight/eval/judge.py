"""Process judge: grounding, consistency, sufficiency + failure attribution.

The judge sees the A-track outcomes (spec §3.4: outcome grader runs first)
so it can attribute every miss to evidence_missing / misread_evidence /
reasonable_but_wrong — the sharpest answer to "why did it behave that way".
Self-preference caveat documented in the methodology doc, not here.
"""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from hindsight.agents.critic import strip_fence
from hindsight.agents.prompts import JUDGE_SYSTEM
from hindsight.data.models import Chunk
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import Memo
from hindsight.trace.cost_ledger import CostLedger


class ClaimGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    supported: bool
    comment: str = ""


class Attribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    attribution: Literal["evidence_missing", "misread_evidence", "reasonable_but_wrong"]


class JudgeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grounding: list[ClaimGrounding]
    reasoning_consistency: int = Field(ge=1, le=5)
    retrieval_sufficiency: int = Field(ge=1, le=5)
    attributions: list[Attribution] = Field(default_factory=list)


def _outcome_lines(graded: list[GradedClaim]) -> str:
    return "\n".join(
        f"- {g.claim.claim_id}: {g.status.value}"
        + (f" (realized {g.realized_return_pct:+.2f}%)" if g.realized_return_pct is not None else "")
        + f" — {g.detail}"
        for g in graded
    )


def _evidence_lines(memo: Memo, evidence_map: dict[str, Chunk]) -> str:
    cited = {eid for c in memo.claims for eid in c.evidence}
    blocks = []
    for eid in sorted(cited):
        chunk = evidence_map.get(eid)
        if chunk is not None:
            blocks.append(f"[{eid}] {chunk.text[:1200]}")
    return "\n\n".join(blocks)


def run_judge(
    llm: RecordingLLMClient,
    memo: Memo,
    graded: list[GradedClaim],
    evidence_map: dict[str, Chunk],
    temperature: float,
    ledger: CostLedger,
) -> JudgeReport | None:
    user = (
        "Memo JSON:\n" + memo.model_dump_json()
        + "\n\nClaim outcomes:\n" + _outcome_lines(graded)
        + "\n\nCited evidence:\n" + _evidence_lines(memo, evidence_map)
    )
    feedback = ""
    for _ in range(2):
        resp = llm.chat(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": user + feedback},
            ],
            temperature=temperature,
        )
        usage = resp.get("usage") or {}
        ledger.add("judge", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        text = strip_fence(resp["choices"][0]["message"].get("content") or "")
        try:
            return JudgeReport.model_validate_json(text)
        except (ValidationError, ValueError) as exc:
            feedback = f"\n\nYour previous reply was invalid ({str(exc)[:300]}). Return ONLY the JSON object."
    return None


def judge_scores(report: JudgeReport | None) -> dict:
    if report is None:
        return {"judge_failed": True}
    total = len(report.grounding)
    supported = sum(1 for g in report.grounding if g.supported)
    return {
        "judge_failed": False,
        "grounding_rate": supported / total if total else None,
        "reasoning_consistency": report.reasoning_consistency,
        "retrieval_sufficiency": report.retrieval_sufficiency,
        "attributions": {a.claim_id: a.attribution for a in report.attributions},
    }
