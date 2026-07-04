import json
from datetime import date

from llm_stubs import ScriptedTransport, content_response

from hindsight.data.models import Chunk
from hindsight.eval.judge import judge_scores, run_judge
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import Claim, ClaimType, GradeStatus, Memo
from hindsight.trace.cost_ledger import CostLedger


def make_memo():
    return Memo(
        background="b", bull_case="+", bear_case="-", conclusion="up",
        claims=[
            Claim(
                claim_id="c1", statement="s", type=ClaimType.direction, ticker="N",
                horizon_days=5, prediction={"direction": "up", "threshold_pct": 5.0},
                confidence=0.6, evidence=["a::000"],
            )
        ],
    )


CHUNKS = {
    "a::000": Chunk(
        chunk_id="a::000", doc_id="a", title="t",
        published_at=date(2025, 5, 1), text="evidence text",
    )
}

VALID_REPORT = json.dumps(
    {
        "grounding": [{"claim_id": "c1", "supported": True, "comment": "ok"}],
        "reasoning_consistency": 4,
        "retrieval_sufficiency": 3,
        "attributions": [{"claim_id": "c1", "attribution": "reasonable_but_wrong"}],
    }
)


def run(responses, tmp_path):
    llm = RecordingLLMClient(
        transport=ScriptedTransport(responses),
        db_path=tmp_path / "llm.sqlite",
        model="m1",
    )
    memo = make_memo()
    graded = [GradedClaim(memo.claims[0], GradeStatus.miss, -1.0, "missed")]
    return run_judge(llm, memo, graded, CHUNKS, temperature=0.0, ledger=CostLedger())


def test_valid_report_parses(tmp_path):
    report = run([content_response(VALID_REPORT)], tmp_path)
    assert report is not None
    assert report.reasoning_consistency == 4
    assert report.attributions[0].attribution == "reasonable_but_wrong"


def test_invalid_then_retry_succeeds(tmp_path):
    report = run(
        [content_response("{broken"), content_response(VALID_REPORT)], tmp_path
    )
    assert report is not None


def test_two_failures_returns_none(tmp_path):
    report = run(
        [content_response("{broken"), content_response("also broken")], tmp_path
    )
    assert report is None


def test_judge_scores_math():
    from hindsight.eval.judge import ClaimGrounding, JudgeReport

    report = JudgeReport(
        grounding=[
            ClaimGrounding(claim_id="c1", supported=True),
            ClaimGrounding(claim_id="c2", supported=False),
        ],
        reasoning_consistency=5,
        retrieval_sufficiency=2,
        attributions=[],
    )
    scores = judge_scores(report)
    assert scores["grounding_rate"] == 0.5
    assert scores["judge_failed"] is False
    assert judge_scores(None)["judge_failed"] is True
