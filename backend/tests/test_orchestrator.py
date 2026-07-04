import json

from llm_stubs import ScriptedTransport, content_response, tool_call_response

from hindsight.agents.orchestrator import run_research
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import RunConfig
from hindsight.store.db import Store

MEMO = json.dumps(
    {
        "background": "b",
        "bull_case": "+",
        "bear_case": "-",
        "conclusion": "up",
        "claims": [
            {
                "claim_id": "c1",
                "statement": "NVDA closes >=5% above the as-of price on the next trading day",
                "type": "direction",
                "ticker": "NVDA",
                "horizon_days": 1,
                "prediction": {"direction": "up", "threshold_pct": 5.0},
                "confidence": 0.7,
                "evidence": ["past::000"],
            }
        ],
    }
)

JUDGE = json.dumps(
    {
        "grounding": [{"claim_id": "c1", "supported": True, "comment": "ok"}],
        "reasoning_consistency": 4,
        "retrieval_sufficiency": 4,
        "attributions": [],
    }
)

SCRIPT = [
    content_response("I do not know anything after that date."),        # probe
    tool_call_response("corpus_search", {"query": "nvidia guidance"}),   # planner 1
    tool_call_response("finish_research", {"reason": "enough"}, "c2"),   # planner 2
    content_response(MEMO),                                              # analyst
    content_response(json.dumps({"ok": True, "problems": []})),          # critic L3
    content_response(JUDGE),                                             # judge
]


def test_e2e_fake_llm(case_dir, tmp_path):
    llm = RecordingLLMClient(
        transport=ScriptedTransport(SCRIPT),
        db_path=tmp_path / "llm.sqlite",
        model="m1",
    )
    store = Store(tmp_path / "h.db")
    result = run_research(
        case_dir=case_dir,
        config=RunConfig(model="m1"),
        llm=llm,
        store=store,
        runs_root=tmp_path / "runs",
    )
    # scores: the fixture bars make horizon-1 return +66.7% -> hit
    assert result.scores["outcome"]["n_hit"] == 1
    assert result.scores["process"]["grounding_rate"] == 1.0
    assert result.scores["cost"]["planner"]["calls"] == 2
    assert "contamination_probe" in result.scores
    # persistence
    run_dir = result.run_dir
    assert (run_dir / "trace.jsonl").exists()
    assert (run_dir / "memo.md").exists()
    claims = json.loads((run_dir / "claims.json").read_text(encoding="utf-8"))
    assert claims[0]["status"] == "hit"
    assert (run_dir / "scores.json").exists()
    # db row + experience written (write-always)
    rows = store.get_runs()
    assert rows[0]["status"] == "done"
    assert store.query_experiences("9999-01-01", exclude_case_id="other")
    # audit events forwarded into trace
    trace_types = [
        json.loads(l)["type"]
        for l in (run_dir / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
    ]
    assert "audit" in trace_types
    assert "score" in trace_types


def test_validation_exhaustion_marks_failed(case_dir, tmp_path):
    # probe(1) + planner prose reply(1) + three broken analyst attempts(3) = 5 responses
    script = (
        [content_response("no post-date knowledge")]
        + [content_response("nope, done planning")]
        + [content_response("{broken")] * 3
    )
    llm = RecordingLLMClient(
        transport=ScriptedTransport(script),
        db_path=tmp_path / "llm.sqlite",
        model="m1",
    )
    store = Store(tmp_path / "h.db")
    result = run_research(
        case_dir=case_dir,
        config=RunConfig(model="m1", max_steps=1),
        llm=llm,
        store=store,
        runs_root=tmp_path / "runs",
    )
    assert result.memo is None
    assert store.get_runs()[0]["status"] == "failed"


SEMANTIC_BAD = json.dumps({"ok": False, "problems": ["not falsifiable"]})


def test_unverified_path_persists_done_with_ungradable(case_dir, tmp_path):
    script = (
        [content_response("no post-date knowledge")]
        + [
            tool_call_response("corpus_search", {"query": "nvidia guidance"}),
            tool_call_response("finish_research", {"reason": "enough"}, "c9"),
        ]
        + [
            content_response(MEMO),
            content_response(SEMANTIC_BAD),
            content_response(MEMO.replace('"c1"', '"c2"')),
            content_response(SEMANTIC_BAD),
            content_response(MEMO.replace('"c1"', '"c3"')),
            content_response(SEMANTIC_BAD),
        ]
        + [content_response(JUDGE)]
    )
    llm = RecordingLLMClient(
        transport=ScriptedTransport(script),
        db_path=tmp_path / "llm.sqlite",
        model="m1",
    )
    store = Store(tmp_path / "h.db")
    result = run_research(
        case_dir=case_dir,
        config=RunConfig(model="m1"),
        llm=llm,
        store=store,
        runs_root=tmp_path / "runs",
    )
    assert result.unverified is True
    assert store.get_runs()[0]["status"] == "done"  # distinct from failed_validation
    claims = json.loads((result.run_dir / "claims.json").read_text(encoding="utf-8"))
    assert claims and all(c["status"] == "ungradable" for c in claims)
    card = json.loads(
        store.query_experiences("9999-01-01", exclude_case_id="other")[0]["card_json"]
    )
    assert "No claims could be graded" in card["lesson_text"]
