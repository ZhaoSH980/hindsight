"""Leakage tests: no code path may return information dated after as_of.

Channels covered here: documents, market bars. The experience-card channel
is added in D2 alongside the experience library (spec §9).
"""
import json
from datetime import date

import pytest

from hindsight.data.market_source import FrozenBarsSource
from hindsight.data.models import Chunk
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.errors import LookaheadError
from hindsight.sandbox.gate import SandboxedCorpus, SandboxedMarketData

AS_OF = date(2025, 5, 22)


def make_chunk(cid: str, text: str, published: date) -> Chunk:
    return Chunk(chunk_id=cid, doc_id=cid, title=cid, published_at=published, text=text)


@pytest.fixture
def corpus():
    chunks = [
        make_chunk("past", "nvidia guidance strong before earnings", date(2025, 5, 1)),
        make_chunk("future", "nvidia earnings smashed records after report", date(2025, 5, 28)),
    ]
    return SandboxedCorpus(BM25Retriever(chunks), as_of=AS_OF, audit=AuditLog())


@pytest.fixture
def market(tmp_path):
    payload = {
        "ticker": "NVDA",
        "auto_adjust": True,
        "fetched_at": "x",
        "bars": [
            {"date": "2025-05-21", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"date": "2025-05-22", "open": 1, "high": 1, "low": 1, "close": 2, "volume": 1},
            {"date": "2025-05-23", "open": 1, "high": 1, "low": 1, "close": 9, "volume": 1},
        ],
    }
    p = tmp_path / "bars.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return SandboxedMarketData(FrozenBarsSource(p), as_of=AS_OF, audit=AuditLog())


def test_corpus_never_returns_future_docs(corpus):
    results = corpus.search("nvidia earnings records report", top_k=5)
    assert results, "past doc should still be retrievable"
    assert all(s.chunk.published_at <= AS_OF for s in results)
    assert all(s.chunk.chunk_id != "future" for s in results)


def test_corpus_writes_audit_entry(corpus):
    corpus.search("nvidia", top_k=2)
    entries = corpus.audit.entries
    assert entries and entries[-1].tool == "corpus_search"
    assert entries[-1].data_max_date is not None
    assert entries[-1].data_max_date <= AS_OF


def test_market_range_ending_after_as_of_raises(market):
    with pytest.raises(LookaheadError):
        market.get_bars("NVDA", date(2025, 5, 21), date(2025, 5, 23))


def test_market_range_up_to_as_of_allowed(market):
    bars = market.get_bars("NVDA", date(2025, 5, 21), AS_OF)
    assert [b.date.isoformat() for b in bars] == ["2025-05-21", "2025-05-22"]
    assert all(b.date <= AS_OF for b in bars)


def test_market_writes_audit_entry(market):
    market.get_bars("NVDA", date(2025, 5, 21), AS_OF)
    entry = market.audit.entries[-1]
    assert entry.tool == "market_data"
    assert entry.data_max_date == AS_OF


def test_denied_market_access_is_audited(market):
    with pytest.raises(LookaheadError):
        market.get_bars("NVDA", date(2025, 5, 21), date(2025, 6, 30))
    entry = market.audit.entries[-1]
    assert entry.note == "DENIED lookahead"


def test_source_error_is_audited(market):
    with pytest.raises(ValueError):
        market.get_bars("TSLA", date(2025, 5, 21), AS_OF)
    entry = market.audit.entries[-1]
    assert entry.tool == "market_data"
    assert entry.note.startswith("ERROR:")


def test_as_of_is_read_only(market, corpus):
    with pytest.raises(AttributeError):
        market.as_of = date(2099, 1, 1)
    with pytest.raises(AttributeError):
        corpus.as_of = date(2099, 1, 1)


def _write_exp(store, case_id, as_of, window_end, feats="NVDA earnings"):
    from hindsight.memory.experience import ExperienceCard

    card = ExperienceCard(
        exp_id=f"e_{case_id}_{window_end}",
        source_case_id=case_id,
        source_run_id="r",
        as_of=as_of,
        outcome_window_end=window_end,
        features_text=feats,
        strategy_summary="s",
        outcomes={},
        lesson_text="l",
    )
    store.insert_experience(
        card.exp_id, card.source_case_id, card.source_run_id,
        card.as_of.isoformat(), card.outcome_window_end.isoformat(),
        card.features_text, card.model_dump_json(),
    )


def test_memory_channel_hides_unclosed_windows(tmp_path):
    from hindsight.memory.experience import ExperienceRetriever
    from hindsight.store.db import Store

    store = Store(tmp_path / "h.db")
    _write_exp(store, "old_case", date(2025, 2, 1), date(2025, 3, 1))
    _write_exp(store, "recent_case", date(2025, 5, 1), date(2025, 6, 30))  # window open at as_of
    got = ExperienceRetriever(store).retrieve(
        "NVDA earnings", as_of=AS_OF, exclude_case_id="current"
    )
    assert {c.source_case_id for c in got} == {"old_case"}


def test_memory_channel_leave_one_out(tmp_path):
    from hindsight.memory.experience import ExperienceRetriever
    from hindsight.store.db import Store

    store = Store(tmp_path / "h.db")
    _write_exp(store, "current", date(2025, 2, 1), date(2025, 3, 1))
    got = ExperienceRetriever(store).retrieve(
        "NVDA earnings", as_of=AS_OF, exclude_case_id="current"
    )
    assert got == []


def test_memory_channel_respects_suite_snapshot(tmp_path):
    from hindsight.memory.experience import ExperienceRetriever
    from hindsight.store.db import Store

    store = Store(tmp_path / "h.db")
    _write_exp(store, "old_case", date(2025, 2, 1), date(2025, 3, 1))
    snapshot_before_write = "2000-01-01T00:00:00+00:00"
    got = ExperienceRetriever(store).retrieve(
        "NVDA earnings", as_of=AS_OF, exclude_case_id="current",
        created_before=snapshot_before_write,
    )
    assert got == []
