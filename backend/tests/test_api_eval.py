import json

from fastapi.testclient import TestClient

from hindsight.api.app import create_app
from hindsight.store.db import Store


def test_suites_post_and_status(api_root):
    app = create_app(repo_root=api_root)
    calls = {}

    def fake_suite_executor(case_ids, presets, suite_id):
        calls["args"] = (case_ids, presets, suite_id)
        store = Store(api_root / "hindsight.db")
        store.upsert_run("r1", case_ids[0], "{}", "done",
                         scores_json='{"outcome": {"hit_rate": 1.0}}', suite_id=suite_id)
        summary = {"suite_id": suite_id, "configs": presets,
                   "results": {case_ids[0]: {presets[0]: {"outcome": {"hit_rate": 1.0}}}}}
        out = api_root / "runs" / "suites" / f"{suite_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary), encoding="utf-8")

    app.state.hindsight.suite_executor = fake_suite_executor
    client = TestClient(app)

    r = client.post("/api/eval/suites", json={"case_ids": ["fixture_case"], "presets": ["base"]})
    assert r.status_code == 200
    suite_id = r.json()["suite_id"]
    assert calls["args"][2] == suite_id

    status = client.get(f"/api/eval/suites/{suite_id}").json()
    assert status["runs"][0]["run_id"] == "r1"
    assert status["summary"]["suite_id"] == suite_id


def test_leaderboard_reads_summary_and_tolerates_failed(api_root):
    app = create_app(repo_root=api_root)
    client = TestClient(app)
    summary = {
        "suite_id": "s1", "configs": ["base", "memory"],
        "results": {"c": {"base": {"outcome": {"hit_rate": 0.5, "brier": 0.2}},
                          "memory": {"status": "failed_validation"}}},
    }
    out = api_root / "runs" / "suites" / "s1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary), encoding="utf-8")

    board = client.get("/api/leaderboard", params={"suite_id": "s1"}).json()
    row = board["cases"]["c"]
    assert row["base"]["hit_rate"] == 0.5
    assert row["memory"]["hit_rate"] is None  # failed run tolerated, not crashed


def test_experiences_endpoint(api_root):
    store = Store(api_root / "hindsight.db")
    store.insert_experience("e1", "case_a", "r1", "2025-03-01", "2025-04-15",
                            "NVDA earnings", '{"exp_id": "e1", "lesson_text": "l"}')
    client = TestClient(create_app(repo_root=api_root))
    cards = client.get("/api/experiences").json()
    assert cards[0]["exp_id"] == "e1"


def test_suite_executor_crash_writes_sentinel(api_root):
    app = create_app(repo_root=api_root)

    def crashing_executor(case_ids, presets, suite_id):
        import threading

        def work():
            try:
                raise RuntimeError("boom mid-suite")
            except Exception as exc:
                out = api_root / "runs" / "suites" / f"{suite_id}.json"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(
                    json.dumps({"suite_id": suite_id, "status": "crashed", "error": str(exc)}),
                    encoding="utf-8",
                )

        threading.Thread(target=work).start()

    app.state.hindsight.suite_executor = crashing_executor
    client = TestClient(app)
    suite_id = client.post(
        "/api/eval/suites", json={"case_ids": ["fixture_case"], "presets": ["base"]}
    ).json()["suite_id"]
    import time

    time.sleep(0.3)
    status = client.get(f"/api/eval/suites/{suite_id}").json()
    assert status["summary"]["status"] == "crashed"
    assert status["known"] is True


def test_unknown_suite_flagged(api_root):
    client = TestClient(create_app(repo_root=api_root))
    status = client.get("/api/eval/suites/garbage").json()
    assert status["known"] is False
