"""Evidence manager — the deterministic 'Researcher' stage.

Deliberately non-LLM: search queries come from the Planner's tool calls;
this stage owns evidence dedup and context_budget trimming (spec §3.6).
The failure mode it isolates is retrieval coverage, which is measured by
the judge's retrieval_sufficiency score, not by an extra LLM role.
"""
from __future__ import annotations

from hindsight.data.models import Chunk, ScoredChunk
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class EvidenceManager:
    def __init__(self, context_budget: int):
        self._budget = context_budget
        self._best: dict[str, ScoredChunk] = {}

    def add_results(self, results: list[ScoredChunk]) -> None:
        for s in results:
            cur = self._best.get(s.chunk.chunk_id)
            if cur is None or s.score > cur.score:
                self._best[s.chunk.chunk_id] = s

    def chunk_ids(self) -> set[str]:
        return set(self._best)

    def evidence_map(self) -> dict[str, Chunk]:
        return {cid: s.chunk for cid, s in self._best.items()}

    def bundle(self, trace: TraceRecorder | None = None) -> list[Chunk]:
        """Highest-score-first selection under the token budget (spec §3.6:
        drop lowest-relevance first). Every dropped chunk emits context_trim."""
        ranked = sorted(self._best.values(), key=lambda s: s.score, reverse=True)
        kept: list[Chunk] = []
        used = 0
        for s in ranked:
            cost = estimate_tokens(s.chunk.text)
            if kept and used + cost > self._budget:
                if trace is not None:
                    trace.emit(
                        TraceEvent(
                            type="context_trim",
                            agent="researcher",
                            payload={
                                "chunk_id": s.chunk.chunk_id,
                                "score": round(s.score, 3),
                                "reason": f"context_budget {self._budget} exceeded",
                            },
                        )
                    )
                continue
            kept.append(s.chunk)
            used += cost
        return kept
