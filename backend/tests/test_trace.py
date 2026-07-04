import json

from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder


def test_recorder_appends_jsonl_and_memory(tmp_path):
    rec = TraceRecorder(run_dir=tmp_path)
    rec.emit(TraceEvent(type="tool_call", agent="planner", payload={"tool": "calc"}))
    rec.emit(TraceEvent(type="tool_result", agent="planner", payload={"ok": True}, tokens=12))
    lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["type"] == "tool_call"
    assert first["agent"] == "planner"
    assert "ts" in first
    assert len(rec.events) == 2


def test_event_type_is_validated():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TraceEvent(type="not_a_type", agent="x", payload={})


def test_cost_ledger_accumulates_per_agent():
    ledger = CostLedger()
    ledger.add("planner", prompt_tokens=100, completion_tokens=20)
    ledger.add("planner", prompt_tokens=50, completion_tokens=10)
    ledger.add("analyst", prompt_tokens=200, completion_tokens=80)
    s = ledger.summary()
    assert s["planner"] == {"prompt_tokens": 150, "completion_tokens": 30, "calls": 2}
    assert s["analyst"]["calls"] == 1
    assert ledger.total_tokens() == 460
