import json

from fastapi.testclient import TestClient

from hindsight.api.app import create_app
from hindsight.store.db import Store


def seed_run(root, run_id, status, with_memo: bool):
    store = Store(root / "hindsight.db")
    scores = {"outcome": {"hit_rate": 1.0}} if with_memo else {"status": "failed_validation"}
    store.upsert_run(run_id, "fixture_case", '{"model":"m"}', status, scores_json=json.dumps(scores))
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "trace.jsonl").write_text(
        '{"type": "plan_step", "agent": "planner", "payload": {}, "tokens": 1, "ts": "t"}\n',
        encoding="utf-8",
    )
    (run_dir / "scores.json").write_text(json.dumps(scores), encoding="utf-8")
    if with_memo:
        (run_dir / "memo.md").write_text("# memo", encoding="utf-8")
        (run_dir / "claims.json").write_text('[{"claim_id": "c1", "status": "hit"}]', encoding="utf-8")


def test_list_and_detail_success_run(api_root):
    seed_run(api_root, "r_ok", "done", with_memo=True)
    client = TestClient(create_app(repo_root=api_root))
    runs = client.get("/api/runs").json()
    assert [r["run_id"] for r in runs] == ["r_ok"]
    assert runs[0]["scores"]["outcome"]["hit_rate"] == 1.0
    detail = client.get("/api/runs/r_ok").json()
    assert detail["memo_md"] == "# memo"
    assert detail["claims"][0]["status"] == "hit"


def test_failed_run_detail_is_graceful(api_root):
    seed_run(api_root, "r_fail", "failed", with_memo=False)
    client = TestClient(create_app(repo_root=api_root))
    detail = client.get("/api/runs/r_fail").json()
    assert detail["status"] == "failed"
    assert detail["memo_md"] is None
    assert detail["claims"] == []
    assert detail["scores"]["status"] == "failed_validation"


def test_trace_endpoint_parses_jsonl(api_root):
    seed_run(api_root, "r_ok", "done", with_memo=True)
    client = TestClient(create_app(repo_root=api_root))
    events = client.get("/api/runs/r_ok/trace").json()
    assert events[0]["type"] == "plan_step"


def test_trace_tolerates_truncated_tail(api_root):
    seed_run(api_root, "r_crash", "failed", with_memo=False)
    trace = api_root / "runs" / "r_crash" / "trace.jsonl"
    with trace.open("a", encoding="utf-8", newline="\n") as f:
        f.write('{"type": "tool_call", "agent": "planner", "payload": {}, "tokens": 0, "ts": "t"}\n')
        f.write('{"type": "tool_result", "agent": "pla')  # truncated mid-write
    client = TestClient(create_app(repo_root=api_root))
    events = client.get("/api/runs/r_crash/trace").json()
    assert [e["type"] for e in events] == ["plan_step", "tool_call"]


def test_unknown_run_404(api_root):
    client = TestClient(create_app(repo_root=api_root))
    assert client.get("/api/runs/nope").status_code == 404
    assert client.get("/api/runs/nope/trace").status_code == 404


def test_start_run_validates_at_the_door(api_root):
    """Bad language / max_steps / traversal case_id must 422 before any run
    row exists — not birth a row that crashes in the background."""
    client = TestClient(create_app(repo_root=api_root))
    for payload in (
        {"case_id": "fixture_case", "language": "fr"},
        {"case_id": "fixture_case", "max_steps": 0},
        {"case_id": "fixture_case", "max_steps": 33},
        {"case_id": "../evil", "language": "en"},
    ):
        r = client.post("/api/runs", json=payload)
        assert r.status_code == 422, payload
    assert client.get("/api/runs").json() == []
