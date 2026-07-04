from datetime import date

from hindsight.agents.researcher import EvidenceManager, estimate_tokens
from hindsight.data.models import Chunk, ScoredChunk
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder


def sc(cid: str, score: float, text: str = "word " * 100) -> ScoredChunk:
    return ScoredChunk(
        chunk=Chunk(
            chunk_id=cid, doc_id=cid, title=cid,
            published_at=date(2025, 5, 1), text=text,
        ),
        score=score,
    )


def test_dedupe_keeps_best_score():
    em = EvidenceManager(context_budget=100000)
    em.add_results([sc("a::000", 1.0)])
    em.add_results([sc("a::000", 3.0), sc("b::000", 2.0)])
    bundle = em.bundle()
    assert [c.chunk_id for c in bundle] == ["a::000", "b::000"]  # sorted by score desc


def test_bundle_respects_budget_and_emits_trim(tmp_path):
    text = "x" * 400  # ~100 tokens each
    em = EvidenceManager(context_budget=250)
    em.add_results([sc("a::000", 3.0, text), sc("b::000", 2.0, text), sc("c::000", 1.0, text)])
    rec = TraceRecorder(run_dir=tmp_path)
    bundle = em.bundle(trace=rec)
    assert [c.chunk_id for c in bundle] == ["a::000", "b::000"]
    trims = [e for e in rec.events if e.type == "context_trim"]
    assert len(trims) == 1
    assert trims[0].payload["chunk_id"] == "c::000"


def test_bundle_always_keeps_at_least_one():
    em = EvidenceManager(context_budget=1)
    em.add_results([sc("a::000", 1.0, "x" * 4000)])
    assert len(em.bundle()) == 1


def test_corpus_tool_feeds_sink():
    from hindsight.rag.bm25_retriever import BM25Retriever
    from hindsight.sandbox.audit import AuditLog
    from hindsight.sandbox.gate import SandboxedCorpus
    from hindsight.tools.corpus_search import make_corpus_tool

    chunk = Chunk(
        chunk_id="a::000", doc_id="a", title="t",
        published_at=date(2025, 5, 1), text="nvidia data center demand",
    )
    corpus = SandboxedCorpus(
        BM25Retriever([chunk]), as_of=date(2025, 5, 22), audit=AuditLog()
    )
    em = EvidenceManager(context_budget=100000)
    spec = make_corpus_tool(corpus, evidence_sink=em)
    spec.fn(query="nvidia demand")
    assert em.chunk_ids() == {"a::000"}
