"""Analyst: one LLM call turning the evidence bundle into a memo JSON."""
from __future__ import annotations

from hindsight.agents.prompts import ANALYST_SYSTEM, analyst_user_prompt
from hindsight.data.models import CaseMeta, Chunk
from hindsight.llm.recording import RecordingLLMClient
from hindsight.trace.cost_ledger import CostLedger

_EVIDENCE_CHARS = 1500


def render_evidence(chunks: list[Chunk]) -> str:
    return "\n\n".join(
        f"[{c.chunk_id}] ({c.published_at.isoformat()}) {c.title}\n{c.text[:_EVIDENCE_CHARS]}"
        for c in chunks
    )


def run_analyst(
    llm: RecordingLLMClient,
    evidence_chunks: list[Chunk],
    case: CaseMeta,
    market_summary: str,
    temperature: float,
    ledger: CostLedger,
    feedback: str | None = None,
    language: str = "en",
) -> str:
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM},
        {
            "role": "user",
            "content": analyst_user_prompt(
                case, render_evidence(evidence_chunks), market_summary, language
            ),
        },
    ]
    if feedback:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous memo failed validation:\n"
                    + feedback
                    + "\nReturn the corrected JSON only."
                ),
            }
        )
    resp = llm.chat(messages=messages, temperature=temperature)
    usage = resp.get("usage") or {}
    ledger.add("analyst", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    return resp["choices"][0]["message"].get("content") or ""
