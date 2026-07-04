import json
from datetime import date

from llm_stubs import ScriptedTransport, content_response

from hindsight.agents.critic import produce_memo, structural_check
from hindsight.data.models import CaseMeta, Chunk
from hindsight.llm.recording import RecordingLLMClient
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.recorder import TraceRecorder

META = CaseMeta(
    case_id="c", title="T", ticker="NVDA",
    as_of=date(2025, 5, 22), outcome_window_days=40,
)

CHUNK = Chunk(
    chunk_id="a::000", doc_id="a", title="t",
    published_at=date(2025, 5, 1), text="nvidia demand strong",
)

VALID_MEMO = json.dumps(
    {
        "background": "b",
        "bull_case": "+",
        "bear_case": "-",
        "conclusion": "up",
        "claims": [
            {
                "claim_id": "c1",
                "statement": "NVDA closes >=5% above the as-of price on the 20th trading day",
                "type": "direction",
                "ticker": "NVDA",
                "horizon_days": 20,
                "prediction": {"direction": "up", "threshold_pct": 5.0},
                "confidence": 0.6,
                "evidence": ["a::000"],
            }
        ],
    }
)

SEMANTIC_OK = json.dumps({"ok": True, "problems": []})
SEMANTIC_BAD = json.dumps({"ok": False, "problems": ["claim not falsifiable"]})


def run_loop(responses, tmp_path):
    transport = ScriptedTransport(responses)
    llm = RecordingLLMClient(
        transport=transport, db_path=tmp_path / "llm.sqlite", model="m1"
    )
    memo, unverified = produce_memo(
        llm=llm,
        evidence_chunks=[CHUNK],
        case=META,
        market_summary="{}",
        temperature=0.0,
        trace=TraceRecorder(run_dir=tmp_path),
        ledger=CostLedger(),
    )
    return memo, unverified, transport


def test_happy_path(tmp_path):
    memo, unverified, t = run_loop(
        [content_response(VALID_MEMO), content_response(SEMANTIC_OK)], tmp_path
    )
    assert memo is not None and not unverified
    assert memo.claims[0].claim_id == "c1"
    assert len(t.requests) == 2  # analyst + semantic critic


def test_structural_failure_retries_with_feedback(tmp_path):
    memo, unverified, t = run_loop(
        [
            content_response("{not json at all"),
            content_response(VALID_MEMO),
            content_response(SEMANTIC_OK),
        ],
        tmp_path,
    )
    assert memo is not None and not unverified
    retry_messages = t.requests[1]["messages"]
    assert any("failed validation" in (m.get("content") or "") for m in retry_messages)


def test_unknown_evidence_id_caught_mechanically():
    bad = json.loads(VALID_MEMO)
    bad["claims"][0]["evidence"] = ["ghost::000"]
    memo, errors = structural_check(json.dumps(bad), {"a::000"}, META)
    assert memo is None
    assert any("ghost::000" in e for e in errors)


def test_horizon_over_window_caught_mechanically():
    bad = json.loads(VALID_MEMO)
    bad["claims"][0]["horizon_days"] = 99
    memo, errors = structural_check(json.dumps(bad), {"a::000"}, META)
    assert memo is None
    assert any("horizon" in e for e in errors)


def test_semantic_failure_then_exhaustion_marks_unverified(tmp_path):
    memo, unverified, t = run_loop(
        [
            content_response(VALID_MEMO),
            content_response(SEMANTIC_BAD),
            content_response(VALID_MEMO.replace('"c1"', '"c2"')),
            content_response(SEMANTIC_BAD),
            content_response(VALID_MEMO.replace('"c1"', '"c3"')),
            content_response(SEMANTIC_BAD),
        ],
        tmp_path,
    )
    assert memo is not None
    assert unverified is True


def test_markdown_fenced_json_is_accepted(tmp_path):
    fenced = "```json\n" + VALID_MEMO + "\n```"
    memo, unverified, t = run_loop(
        [content_response(fenced), content_response(SEMANTIC_OK)], tmp_path
    )
    assert memo is not None and not unverified


def test_unparseable_critic_consumes_retry_and_degrades(tmp_path):
    memo, unverified, t = run_loop(
        [
            content_response(VALID_MEMO),
            content_response("I think it looks fine!"),
            content_response(VALID_MEMO),
            content_response("still prose"),
            content_response(VALID_MEMO),
            content_response("nope"),
        ],
        tmp_path,
    )
    assert memo is not None
    assert unverified is True  # gate fails CLOSED, not open


def test_fence_with_space_and_prose_wrapping(tmp_path):
    wrapped = (
        "Sure! Here is the memo:\n``` json\n" + VALID_MEMO + "\n```\nHope this helps."
    )
    memo, unverified, t = run_loop(
        [content_response(wrapped), content_response(SEMANTIC_OK)], tmp_path
    )
    assert memo is not None and not unverified


def test_bare_prose_around_json(tmp_path):
    wrapped = "Here is the JSON you asked for: " + VALID_MEMO + " Let me know!"
    memo, unverified, t = run_loop(
        [content_response(wrapped), content_response(SEMANTIC_OK)], tmp_path
    )
    assert memo is not None and not unverified


def test_structural_exhaustion_returns_none(tmp_path):
    memo, unverified, t = run_loop([content_response("{broken")] * 3, tmp_path)
    assert memo is None
    assert unverified is True
