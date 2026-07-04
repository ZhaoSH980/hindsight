import json
import threading
import time

from fastapi.testclient import TestClient

from hindsight.api.app import create_app
from hindsight.store.db import Store


def fake_executor_factory(root):
    """Simulates a run: writes trace lines over ~0.5s then marks done."""

    def execute(case_id: str, config: dict, run_id: str) -> None:
        store = Store(root / "hindsight.db")
        run_dir = root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        trace = run_dir / "trace.jsonl"

        def work():
            store.upsert_run(run_id, case_id, "{}", "running")
            with trace.open("a", encoding="utf-8", newline="\n") as f:
                for i in range(3):
                    f.write(json.dumps({"type": "plan_step", "agent": "planner",
                                        "payload": {"step": i}, "tokens": 0, "ts": "t"}) + "\n")
                    f.flush()
                    time.sleep(0.1)
            store.upsert_run(run_id, case_id, "{}", "done", scores_json="{}")

        threading.Thread(target=work, daemon=True).start()

    return execute


def test_post_run_returns_id_and_streams(api_root):
    app = create_app(repo_root=api_root)
    app.state.hindsight.run_executor = fake_executor_factory(api_root)
    client = TestClient(app)

    r = client.post("/api/runs", json={"case_id": "fixture_case"})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    assert run_id

    # queued row visible immediately (no race)
    assert client.get(f"/api/runs/{run_id}").json()["status"] in ("queued", "running", "done")

    events = []
    with client.websocket_connect(f"/api/runs/{run_id}/stream") as ws:
        while True:
            msg = json.loads(ws.receive_text())
            events.append(msg)
            if msg["type"] == "status":
                break
    types = [e["type"] for e in events]
    assert types.count("plan_step") == 3
    assert events[-1] == {"type": "status", "payload": {"status": "done"}}


def test_post_run_unknown_case_404(api_root):
    app = create_app(repo_root=api_root)
    app.state.hindsight.run_executor = fake_executor_factory(api_root)
    client = TestClient(app)
    assert client.post("/api/runs", json={"case_id": "nope"}).status_code == 404


def test_ws_unknown_run_id_closes_immediately(api_root):
    app = create_app(repo_root=api_root)
    client = TestClient(app)
    with client.websocket_connect("/api/runs/bogus_run/stream") as ws:
        msg = json.loads(ws.receive_text())
        assert msg["type"] == "error"
        assert "bogus_run" in msg["payload"]["detail"]
