"""as_of information gates. All agent-facing data access goes through here."""
from __future__ import annotations

from datetime import date

from hindsight.data.market_source import MarketDataSource
from hindsight.data.models import Bar, ScoredChunk
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.errors import LookaheadError


class SandboxedCorpus:
    def __init__(self, retriever: BM25Retriever, as_of: date, audit: AuditLog):
        self._retriever = retriever
        self.as_of = as_of
        self.audit = audit

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        results = self._retriever.search(query, as_of=self.as_of, top_k=top_k)
        self.audit.record(
            tool="corpus_search",
            params={"query": query, "top_k": top_k},
            data_max_date=max((s.chunk.published_at for s in results), default=None),
        )
        return results


class SandboxedMarketData:
    def __init__(self, source: MarketDataSource, as_of: date, audit: AuditLog):
        self._source = source
        self.as_of = as_of
        self.audit = audit

    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        if end > self.as_of:
            self.audit.record(
                tool="market_data",
                params={"ticker": ticker, "start": str(start), "end": str(end)},
                note="DENIED lookahead",
            )
            raise LookaheadError(
                f"requested bars up to {end}, but as_of is {self.as_of}"
            )
        bars = self._source.get_bars(ticker, start, end)
        self.audit.record(
            tool="market_data",
            params={"ticker": ticker, "start": str(start), "end": str(end)},
            data_max_date=max((b.date for b in bars), default=None),
        )
        return bars
