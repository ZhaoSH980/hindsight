import json
from datetime import date

import pytest

from hindsight.data.models import Chunk
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.gate import SandboxedCorpus
from hindsight.tools.calc import make_calc_tool
from hindsight.tools.corpus_search import make_corpus_tool
from hindsight.tools.registry import ToolRegistry

AS_OF = date(2025, 5, 22)


@pytest.fixture
def registry():
    chunks = [
        Chunk(
            chunk_id="a::000",
            doc_id="a",
            title="NVDA guidance",
            published_at=date(2025, 5, 1),
            text="nvidia guidance strong data center demand",
        )
    ]
    corpus = SandboxedCorpus(BM25Retriever(chunks), as_of=AS_OF, audit=AuditLog())
    reg = ToolRegistry()
    reg.register(make_corpus_tool(corpus))
    reg.register(make_calc_tool())
    return reg


def test_openai_specs_shape(registry):
    specs = registry.openai_specs()
    names = {s["function"]["name"] for s in specs}
    assert names == {"corpus_search", "calc"}
    assert all(s["type"] == "function" for s in specs)
    assert all("parameters" in s["function"] for s in specs)


def test_dispatch_corpus_search(registry):
    out = registry.call("corpus_search", {"query": "nvidia guidance", "top_k": 3})
    payload = json.loads(out)
    assert payload["results"][0]["chunk_id"] == "a::000"
    assert payload["results"][0]["published_at"] == "2025-05-01"


def test_dispatch_calc(registry):
    out = registry.call("calc", {"expression": "(2.5 - 2.0) / 2.0 * 100"})
    assert json.loads(out)["value"] == pytest.approx(25.0)


def test_calc_rejects_non_arithmetic(registry):
    out = registry.call("calc", {"expression": "__import__('os')"})
    assert "error" in json.loads(out)


def test_unknown_tool_raises(registry):
    with pytest.raises(KeyError):
        registry.call("nope", {})


def test_safe_call_overflow_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "calc", {"expression": "9**9**9"})
    assert "OverflowError" in json.loads(out)["error"]


def test_safe_call_recursion_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "calc", {"expression": "+".join(["1"] * 5000)})
    payload = json.loads(out)
    assert "error" in payload or "value" in payload  # deep-parse limits vary; must not raise


def test_safe_call_bad_kwargs_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "corpus_search", {"query": "x", "evil": "y"})
    assert "TypeError" in json.loads(out)["error"]


def test_safe_call_unknown_tool_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "nope", {})
    assert "KeyError" in json.loads(out)["error"]


def test_excerpt_truncation_marker(registry):
    from datetime import date as _date

    from hindsight.rag.bm25_retriever import BM25Retriever
    from hindsight.sandbox.audit import AuditLog
    from hindsight.sandbox.gate import SandboxedCorpus
    from hindsight.tools.corpus_search import make_corpus_tool

    long_chunk = Chunk(
        chunk_id="long::000",
        doc_id="long",
        title="long doc",
        published_at=_date(2025, 5, 1),
        text="nvidia " * 200,  # 1400 chars > 700
    )
    corpus = SandboxedCorpus(BM25Retriever([long_chunk]), as_of=AS_OF, audit=AuditLog())
    spec = make_corpus_tool(corpus)
    payload = json.loads(spec.fn(query="nvidia"))
    excerpt = payload["results"][0]["excerpt"]
    assert excerpt.endswith("...")
    assert len(excerpt) == 700 + 3
