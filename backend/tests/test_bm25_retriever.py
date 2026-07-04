from datetime import date

from hindsight.data.models import Chunk
from hindsight.rag.bm25_retriever import BM25Retriever


def make_chunk(cid: str, text: str, published: date) -> Chunk:
    return Chunk(
        chunk_id=cid,
        doc_id=cid.split("::")[0],
        title=cid,
        published_at=published,
        text=text,
    )


CORPUS = [
    make_chunk("a::000", "nvidia data center revenue beat expectations", date(2025, 2, 27)),
    make_chunk("b::000", "tesla delivery numbers missed estimates badly", date(2025, 3, 5)),
    make_chunk("c::000", "nvidia blackwell supply chain ramping fast", date(2025, 4, 10)),
    make_chunk("d::000", "macro semis outlook mixed on tariffs", date(2025, 4, 20)),
    make_chunk("future::000", "nvidia earnings results smashed records", date(2025, 5, 28)),
]


def test_relevant_chunk_ranks_first():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia data center revenue", as_of=date(2025, 5, 22), top_k=3)
    assert results[0].chunk.chunk_id == "a::000"
    assert results[0].score > 0


def test_future_chunks_never_returned():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia earnings results", as_of=date(2025, 5, 22), top_k=5)
    ids = [s.chunk.chunk_id for s in results]
    assert "future::000" not in ids


def test_as_of_boundary_is_inclusive():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia earnings results", as_of=date(2025, 5, 28), top_k=5)
    ids = [s.chunk.chunk_id for s in results]
    assert "future::000" in ids


def test_empty_when_nothing_visible():
    r = BM25Retriever(CORPUS)
    assert r.search("anything", as_of=date(2024, 1, 1), top_k=3) == []


def test_top_k_respected():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia", as_of=date(2025, 5, 22), top_k=2)
    assert len(results) <= 2


def test_non_positive_top_k_treated_as_one():
    r = BM25Retriever(CORPUS)
    assert len(r.search("nvidia", as_of=date(2025, 5, 22), top_k=0)) == 1
    assert len(r.search("nvidia", as_of=date(2025, 5, 22), top_k=-3)) == 1


def test_zero_score_fallback_returns_single_visible_chunk():
    r = BM25Retriever(CORPUS[:2])
    results = r.search("zzz qqq", as_of=date(2025, 5, 22), top_k=3)
    assert len(results) == 1
    assert results[0].chunk.published_at <= date(2025, 5, 22)
