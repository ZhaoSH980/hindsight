"""Time-filtered BM25 retrieval.

Filter-then-index: visible chunks are selected by published_at <= as_of
BEFORE the BM25 index is built, so corpus statistics (IDF) never observe
future documents. Rebuilding per query is fine at our corpus sizes
(hundreds of chunks).

Note: BM25Okapi IDF can zero out terms present in ~half the corpus when
the corpus is tiny (2-3 chunks). Case datasets enforce a minimum corpus
size instead of patching the scorer.
"""
from __future__ import annotations

import re
from datetime import date

from rank_bm25 import BM25Okapi

from hindsight.data.models import Chunk, ScoredChunk

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class BM25Retriever:
    def __init__(self, chunks: list[Chunk]):
        self._chunks = list(chunks)

    def search(self, query: str, as_of: date, top_k: int = 5) -> list[ScoredChunk]:
        top_k = max(1, top_k)
        visible = [c for c in self._chunks if c.published_at <= as_of]
        if not visible:
            return []
        index = BM25Okapi([_tokenize(c.text) for c in visible])
        scores = index.get_scores(_tokenize(query))
        ranked = sorted(zip(visible, scores), key=lambda p: p[1], reverse=True)
        return [
            ScoredChunk(chunk=c, score=float(s)) for c, s in ranked[:top_k] if s > 0
        ] or [ScoredChunk(chunk=c, score=float(s)) for c, s in ranked[: min(top_k, 1)]]
