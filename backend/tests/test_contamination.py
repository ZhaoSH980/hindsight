from datetime import date

from llm_stubs import ScriptedTransport, content_response

from hindsight.eval.contamination import run_contamination_probe
from hindsight.llm.recording import RecordingLLMClient
from hindsight.trace.cost_ledger import CostLedger


def test_probe_is_hash_stable(tmp_path):
    transport = ScriptedTransport([content_response("I recall that...")])
    llm = RecordingLLMClient(
        transport=transport, db_path=tmp_path / "llm.sqlite", model="m1"
    )
    ledger = CostLedger()
    t1 = run_contamination_probe(llm, "NVDA", date(2025, 5, 22), ledger)
    t2 = run_contamination_probe(llm, "NVDA", date(2025, 5, 22), ledger)
    assert t1 == t2 == "I recall that..."
    assert len(transport.requests) == 1  # second call replayed from cache
