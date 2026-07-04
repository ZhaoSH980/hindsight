import json
from datetime import date

from llm_stubs import ScriptedTransport, content_response, tool_call_response

from hindsight.agents.planner import FINISH_TOOL, run_planner
from hindsight.data.models import Chunk
from hindsight.llm.recording import RecordingLLMClient
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.gate import SandboxedCorpus
from hindsight.tools.corpus_search import make_corpus_tool
from hindsight.tools.registry import ToolRegistry
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.recorder import TraceRecorder


def make_registry():
    chunk = Chunk(
        chunk_id="a::000", doc_id="a", title="t",
        published_at=date(2025, 5, 1), text="nvidia data center demand strong",
    )
    corpus = SandboxedCorpus(
        BM25Retriever([chunk]), as_of=date(2025, 5, 22), audit=AuditLog()
    )
    reg = ToolRegistry()
    reg.register(make_corpus_tool(corpus))
    reg.register(FINISH_TOOL)
    return reg


def run(transport, tmp_path, max_steps=8):
    llm = RecordingLLMClient(
        transport=transport, db_path=tmp_path / "llm.sqlite", model="m1"
    )
    trace = TraceRecorder(run_dir=tmp_path)
    ledger = CostLedger()
    run_planner(
        llm=llm, registry=make_registry(), user_brief="brief",
        max_steps=max_steps, temperature=0.0, trace=trace, ledger=ledger,
    )
    return trace, ledger, transport


def test_planner_searches_then_finishes(tmp_path):
    transport = ScriptedTransport(
        [
            tool_call_response("corpus_search", {"query": "nvidia demand"}),
            tool_call_response("finish_research", {"reason": "enough"}),
        ]
    )
    trace, ledger, transport = run(transport, tmp_path)
    assert len(transport.requests) == 2
    types = [e.type for e in trace.events]
    assert types.count("plan_step") == 2
    assert types.count("tool_call") == 2
    assert types.count("tool_result") == 2
    assert ledger.summary()["planner"]["calls"] == 2
    # second request must carry the tool result message back to the model
    roles = [m["role"] for m in transport.requests[1]["messages"]]
    assert roles.count("tool") == 1


def test_planner_stops_at_max_steps(tmp_path):
    transport = ScriptedTransport(
        [tool_call_response("corpus_search", {"query": f"q{i}"}, call_id=f"c{i}") for i in range(3)]
    )
    trace, ledger, transport = run(transport, tmp_path, max_steps=3)
    assert len(transport.requests) == 3  # capped, never a 4th call


def test_prose_answer_ends_loop(tmp_path):
    transport = ScriptedTransport([content_response("I have enough already.")])
    trace, ledger, transport = run(transport, tmp_path)
    assert len(transport.requests) == 1
    assert [e.type for e in trace.events].count("plan_step") == 1


def test_unparseable_arguments_survive(tmp_path):
    bad = tool_call_response("corpus_search", {})
    bad["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = "{not json"
    transport = ScriptedTransport(
        [bad, tool_call_response("finish_research", {"reason": "done"}, call_id="c2")]
    )
    trace, ledger, transport = run(transport, tmp_path)
    results = [e for e in trace.events if e.type == "tool_result"]
    assert "error" in results[0].payload["result"]
