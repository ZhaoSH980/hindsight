# Hindsight D3 — API + Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the proven D2 pipeline over a FastAPI + WebSocket API and build the three showcase pages (Research Studio with the "Reveal the future" moment, Trace Explorer, Eval Dashboard) in a dark quant-terminal React frontend, bilingual EN/中, tolerant of failed runs, ending with an English README skeleton.

**Architecture:** The API is a thin read-mostly layer over existing artifacts: Store rows, run-dir files (`memo.md`/`claims.json`/`scores.json`/`trace.jsonl`), frozen `bars.json` snapshots. Live streaming = tailing `trace.jsonl` over WebSocket (the same file replays recorded runs — one code path for live and replay). Run/suite execution happens in background threads; the POST pre-registers a `queued` row so status/WS never 404. The sandbox is untouched: `/api/cases/{id}/bars` is a display-only endpoint (spec §5 note) — masking the future is the FRONTEND's job.

**Tech Stack:** backend adds `fastapi` + `uvicorn[standard]` (runtime) and `httpx` (dev, TestClient). Frontend: React 18 + Vite + TypeScript + Tailwind CSS v3 + react-router-dom + Recharts. No state library, no react-query (YAGNI).

**Working directory:** repo root `F:/AIProjects/my_show/hindsight`, branch `d1-foundation`. Baseline: tag `d2-complete`, **141 tests green**. Venv `backend/.venv`; Node 22 / npm 10 available.

**Reference docs:** spec §5 (endpoints + event protocol), §6 (pages), §8 (WS fallback); D1 plan's "**D3 carryover (current)**" list (thread-bound sqlite; failed-run tolerance; `.get("outcome")`; strict `<` snapshot boundary untouchable; citation nits → D4).

**Quota note:** ALL D3 development runs use `--offline`/replay or fake executors — zero metered calls needed. Live runs only if a demo rehearsal explicitly wants a fresh one.

**Test-count note:** counts below assume the 141 baseline; trust arithmetic over literals if review fixes add tests mid-execution (D2 precedent).

## File structure (created/modified this plan)

```
backend/
├── pyproject.toml                    # MOD: + fastapi, uvicorn; dev + httpx
├── hindsight/llm/recording.py       # MOD: thread-safe (lock + check_same_thread=False)
├── hindsight/agents/orchestrator.py # MOD: optional run_id param (pre-registration)
├── hindsight/eval/suite.py          # MOD: optional suite_id param
├── hindsight/api/__init__.py        # NEW (empty)
├── hindsight/api/app.py             # NEW: create_app factory + CORS + static mount
├── hindsight/api/deps.py            # NEW: AppState (root, store, runs_root, executor hooks)
├── hindsight/api/routes_cases.py    # NEW
├── hindsight/api/routes_runs.py     # NEW (list/detail/trace + POST run + WS stream)
├── hindsight/api/routes_eval.py     # NEW (suites, leaderboard, experiences)
└── tests/test_api_*.py              # NEW: cases/runs/stream/eval TestClient suites
frontend/                             # NEW: Vite React TS app
├── package.json  vite.config.ts  tailwind.config.js  postcss.config.js
├── index.html  src/main.tsx  src/index.css  src/App.tsx
├── src/lib/{api.ts, types.ts, i18n.tsx, format.ts, useRunStream.ts}
├── src/components/{PriceChart.tsx, ClaimCard.tsx, EventRow.tsx,
│                   CalibrationChart.tsx, ScoreCards.tsx, AttributionBadge.tsx}
└── src/pages/{Studio.tsx, TraceExplorer.tsx, EvalDashboard.tsx}
.claude/launch.json                   # NEW: backend + frontend dev servers
README.md                             # NEW (English skeleton; D4 finalizes)
```

---

### Task 1: RecordingLLMClient thread safety (carryover ⑨)

**Files:**
- Modify: `backend/hindsight/llm/recording.py`
- Modify: `backend/tests/test_replay.py` (2 new tests)

- [ ] **Step 1: Write the failing tests** — append to `backend/tests/test_replay.py`:

```python
def test_chat_usable_from_worker_thread(tmp_path):
    import threading

    c = RecordingLLMClient(
        transport=lambda r: fake_response("t"),
        db_path=tmp_path / "db.sqlite",
        model="m1",
    )
    errors: list[Exception] = []

    def work():
        try:
            c.chat(messages=[{"role": "user", "content": "from-thread"}])
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    t = threading.Thread(target=work)
    t.start()
    t.join()
    assert errors == []


def test_concurrent_chats_all_recorded(tmp_path):
    import threading

    calls = []

    def transport(request):
        calls.append(request)
        return fake_response("x")

    c = RecordingLLMClient(
        transport=transport, db_path=tmp_path / "db.sqlite", model="m1"
    )
    threads = [
        threading.Thread(
            target=lambda i=i: c.chat(messages=[{"role": "user", "content": f"q{i}"}])
        )
        for i in range(8)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(calls) == 8  # all distinct requests reached the transport, none crashed
```

- [ ] **Step 2: Run to verify the first test fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_replay.py -q`
Expected: `test_chat_usable_from_worker_thread` FAILS (`sqlite3.ProgrammingError: SQLite objects created in a thread...`).

- [ ] **Step 3: Implement** — in `backend/hindsight/llm/recording.py`: add `import threading`; in `__init__`: `self._conn = sqlite3.connect(db_path, check_same_thread=False)` and `self._lock = threading.Lock()`; in `chat()`, wrap BOTH database touchpoints:

```python
        with self._lock:
            row = self._conn.execute(
                "SELECT response_json FROM llm_calls WHERE hash = ?", (key,)
            ).fetchone()
```
and
```python
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO llm_calls VALUES (?, ?, ?, ?)",
                (
                    key,
                    json.dumps(request, ensure_ascii=False),
                    json.dumps(response, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
            self._conn.commit()
```
(The transport call stays OUTSIDE the lock — concurrent runs must not serialize their network waits.)

- [ ] **Step 4: Run tests** — full suite expect `143 passed`.
- [ ] **Step 5: Commit** — `fix(d3): thread-safe recording client for server use`

---

### Task 2: API skeleton + cases endpoints

**Files:**
- Modify: `backend/pyproject.toml` (deps)
- Create: `backend/hindsight/api/__init__.py` (empty), `backend/hindsight/api/deps.py`, `backend/hindsight/api/app.py`, `backend/hindsight/api/routes_cases.py`
- Test: `backend/tests/test_api_cases.py` (+ shared fixture in `backend/tests/conftest.py`)

- [ ] **Step 1: Add dependencies** — in `backend/pyproject.toml` `[project].dependencies` append `"fastapi>=0.111"` and `"uvicorn[standard]>=0.30"`; in `[project.optional-dependencies].dev` append `"httpx>=0.27"`. Then `cd backend && .venv/Scripts/python -m pip install -q -e ".[dev]"`.

- [ ] **Step 2: Add the shared API fixture** — append to `backend/tests/conftest.py`:

```python
@pytest.fixture
def api_root(case_dir, tmp_path) -> Path:
    """A fake repo root: datasets/<case>, empty runs/, fresh hindsight.db."""
    import shutil

    root = tmp_path / "approot"
    (root / "datasets").mkdir(parents=True)
    shutil.copytree(case_dir, root / "datasets" / case_dir.name)
    (root / "runs").mkdir()
    return root
```

(`Path` is already imported in conftest.)

- [ ] **Step 3: Write the failing tests** — `backend/tests/test_api_cases.py`:

```python
from fastapi.testclient import TestClient

from hindsight.api.app import create_app


def client_for(root):
    return TestClient(create_app(repo_root=root))


def test_list_cases(api_root):
    client = client_for(api_root)
    r = client.get("/api/cases")
    assert r.status_code == 200
    cases = r.json()
    assert len(cases) == 1
    c = cases[0]
    assert c["case_id"] == "fixture_case"
    assert c["ticker"] == "NVDA"
    assert c["as_of"] == "2025-05-22"
    assert c["n_docs"] == 2


def test_case_bars_full_window(api_root):
    client = client_for(api_root)
    r = client.get("/api/cases/fixture_case/bars")
    assert r.status_code == 200
    payload = r.json()
    assert payload["ticker"] == "NVDA"
    dates = [b["date"] for b in payload["bars"]]
    assert "2025-06-20" in dates  # display endpoint returns the FUTURE too (spec §5)


def test_unknown_case_404(api_root):
    client = client_for(api_root)
    assert client.get("/api/cases/nope/bars").status_code == 404
```

- [ ] **Step 4: Run to verify failure** — `ModuleNotFoundError: hindsight.api`.

- [ ] **Step 5: Implement.** `backend/hindsight/api/deps.py`:

```python
"""Application state shared by all routers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from hindsight.store.db import Store

_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class AppState:
    root: Path
    store: Store
    run_executor: Callable[..., Any] | None = None    # tests inject; None = real
    suite_executor: Callable[..., Any] | None = None

    @property
    def datasets(self) -> Path:
        return self.root / "datasets"

    @property
    def runs_root(self) -> Path:
        return self.root / "runs"


def make_state(repo_root: Path | None = None) -> AppState:
    root = Path(repo_root) if repo_root else _REPO_ROOT
    return AppState(root=root, store=Store(root / "hindsight.db"))
```

`backend/hindsight/api/routes_cases.py`:

```python
"""Case listing + display-only bars (spec §5: the sandbox gates AGENT access;
this endpoint feeds the frontend chart, which does its own as_of masking)."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/api/cases")
def list_cases(request: Request):
    state = request.app.state.hindsight
    cases = []
    if state.datasets.exists():
        for meta_path in sorted(state.datasets.glob("*/meta.json")):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["n_docs"] = len(list((meta_path.parent / "docs").glob("*.md")))
            cases.append(meta)
    return cases


@router.get("/api/cases/{case_id}/bars")
def case_bars(case_id: str, request: Request):
    state = request.app.state.hindsight
    bars_path = state.datasets / case_id / "bars.json"
    if not bars_path.exists():
        raise HTTPException(status_code=404, detail=f"unknown case {case_id}")
    payload = json.loads(bars_path.read_text(encoding="utf-8"))
    return {"ticker": payload["ticker"], "bars": payload["bars"]}
```

`backend/hindsight/api/app.py`:

```python
"""FastAPI app factory. `app` at module level serves uvicorn:
    backend/.venv/Scripts/python -m uvicorn hindsight.api.app:app --port 8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hindsight.api.deps import make_state


def create_app(repo_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Hindsight API")
    app.state.hindsight = make_state(repo_root)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    from hindsight.api.routes_cases import router as cases_router

    app.include_router(cases_router)

    dist = app.state.hindsight.root / "frontend" / "dist"
    if dist.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
```

(Task 3/4/5 append their routers to `create_app` — each later task adds its own `include_router` line ABOVE the static mount.)

- [ ] **Step 6: Run tests** — expect `146 passed` (143 + 3).
- [ ] **Step 7: Commit** — `feat(d3): fastapi skeleton with case endpoints`

---

### Task 3: Run read endpoints (list / detail / trace) with failed-run tolerance

**Files:**
- Create: `backend/hindsight/api/routes_runs.py` (read endpoints only; Task 4 adds POST/WS)
- Modify: `backend/hindsight/api/app.py` (include router)
- Test: `backend/tests/test_api_runs.py`

- [ ] **Step 1: Write the failing tests** — `backend/tests/test_api_runs.py`:

```python
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


def test_unknown_run_404(api_root):
    client = TestClient(create_app(repo_root=api_root))
    assert client.get("/api/runs/nope").status_code == 404
    assert client.get("/api/runs/nope/trace").status_code == 404
```

- [ ] **Step 2: Verify failure** — 404s/ModuleNotFound as appropriate.

- [ ] **Step 3: Implement** `backend/hindsight/api/routes_runs.py`:

```python
"""Run read endpoints. Failed runs are first-class: memo_md may be null and
claims empty — the frontend renders a 'validation failed' state, never a 404."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def _row_to_summary(row: dict) -> dict:
    return {
        "run_id": row["run_id"],
        "case_id": row["case_id"],
        "suite_id": row["suite_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "config": json.loads(row["config_json"]) if row["config_json"] else {},
        "scores": json.loads(row["scores_json"]) if row["scores_json"] else None,
    }


def _get_row(state, run_id: str) -> dict:
    rows = [r for r in state.store.get_runs() if r["run_id"] == run_id]
    if not rows:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    return rows[0]


@router.get("/api/runs")
def list_runs(request: Request):
    state = request.app.state.hindsight
    return [_row_to_summary(r) for r in state.store.get_runs()]


@router.get("/api/runs/{run_id}")
def run_detail(run_id: str, request: Request):
    state = request.app.state.hindsight
    row = _get_row(state, run_id)
    run_dir = state.runs_root / run_id
    memo = run_dir / "memo.md"
    claims = run_dir / "claims.json"
    detail = _row_to_summary(row)
    detail["memo_md"] = memo.read_text(encoding="utf-8") if memo.exists() else None
    detail["claims"] = (
        json.loads(claims.read_text(encoding="utf-8")) if claims.exists() else []
    )
    return detail


@router.get("/api/runs/{run_id}/trace")
def run_trace(run_id: str, request: Request):
    state = request.app.state.hindsight
    _get_row(state, run_id)
    trace = state.runs_root / run_id / "trace.jsonl"
    if not trace.exists():
        return []
    events = []
    for line in trace.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # truncated tail from a crash-mid-write; drop, never 500
    return events
```

In `app.py`, after the cases router include, add:

```python
    from hindsight.api.routes_runs import router as runs_router

    app.include_router(runs_router)
```

- [ ] **Step 4: Run tests** — expect `150 passed` (146 + 4).
- [ ] **Step 5: Commit** — `feat(d3): run read endpoints with failed-run tolerance`

---

### Task 4: Run execution (POST) + WebSocket stream

The POST pre-registers a `queued` row (so status/WS never race a 404), then executes in a background thread. The WS handler tails `trace.jsonl` — one code path streams live runs AND replays recorded ones.

**Files:**
- Modify: `backend/hindsight/agents/orchestrator.py` (optional `run_id` param — sanctioned signature extension)
- Modify: `backend/hindsight/api/routes_runs.py` (POST + WS)
- Test: `backend/tests/test_api_stream.py`

- [ ] **Step 1: Orchestrator pre-registration support.** In `run_research`, extend the signature with `run_id: str | None = None` (keyword-only section, after `suite_started_at`) and replace the internal assignment with:

```python
    run_id = run_id or _new_run_id(case.meta.case_id)
```

Add a regression test to `backend/tests/test_orchestrator.py`:

```python
def test_run_id_can_be_preassigned(case_dir, tmp_path):
    llm = RecordingLLMClient(
        transport=ScriptedTransport(SCRIPT),
        db_path=tmp_path / "llm.sqlite",
        model="m1",
    )
    result = run_research(
        case_dir=case_dir,
        config=RunConfig(model="m1"),
        llm=llm,
        store=Store(tmp_path / "h.db"),
        runs_root=tmp_path / "runs",
        run_id="run_preassigned_001",
    )
    assert result.run_id == "run_preassigned_001"
    assert result.run_dir.name == "run_preassigned_001"
```

(Note: `SCRIPT` responses will partially replay from this test's fresh db — they are all new requests here, so all 6 are consumed normally.)

- [ ] **Step 2: Write the failing stream tests** — `backend/tests/test_api_stream.py`:

```python
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
```

- [ ] **Step 3: Verify failure** — POST route missing (405/404), then implement.

- [ ] **Step 4: Implement** — append to `backend/hindsight/api/routes_runs.py`:

```python
import asyncio
import threading

from fastapi import WebSocket
from pydantic import BaseModel

from hindsight.agents.orchestrator import _new_run_id


class StartRunRequest(BaseModel):
    case_id: str
    memory_on: bool = False
    max_steps: int = 8


def _default_executor(state):
    """Real executor: env-configured LLM, retry transport, record mode."""

    def execute(case_id: str, config: dict, run_id: str) -> None:
        from hindsight.agents.orchestrator import run_research
        from hindsight.llm.client import LLMConfig, openai_transport
        from hindsight.llm.recording import RecordingLLMClient
        from hindsight.llm.retry import with_retry
        from hindsight.schemas import RunConfig

        cfg = LLMConfig.from_env()
        llm = RecordingLLMClient(
            transport=with_retry(openai_transport(cfg)),
            db_path=state.root / "llm_calls.sqlite",
            model=cfg.model,
        )

        def work():
            try:
                run_research(
                    case_dir=state.datasets / case_id,
                    config=RunConfig(model=cfg.model, **config),
                    llm=llm,
                    store=state.store,
                    runs_root=state.runs_root,
                    run_id=run_id,
                )
            except Exception as exc:  # noqa: BLE001 - background thread must not die silently
                state.store.upsert_run(run_id, case_id, json.dumps(config), "failed",
                                       scores_json=json.dumps({"status": "crashed", "error": str(exc)[:500]}))

        threading.Thread(target=work, daemon=True).start()

    return execute


@router.post("/api/runs")
def start_run(body: StartRunRequest, request: Request):
    state = request.app.state.hindsight
    if not (state.datasets / body.case_id / "meta.json").exists():
        raise HTTPException(status_code=404, detail=f"unknown case {body.case_id}")
    run_id = _new_run_id(body.case_id)
    config = {"memory_on": body.memory_on, "max_steps": body.max_steps}
    state.store.upsert_run(run_id, body.case_id, json.dumps(config), "queued")
    executor = state.run_executor or _default_executor(state)
    executor(body.case_id, config, run_id)
    return {"run_id": run_id}


@router.websocket("/api/runs/{run_id}/stream")
async def stream_run(ws: WebSocket, run_id: str):
    await ws.accept()
    state = ws.app.state.hindsight
    trace = state.runs_root / run_id / "trace.jsonl"
    sent = 0
    for _ in range(1500):  # ~10 min ceiling at 0.4s
        if trace.exists():
            lines = trace.read_text(encoding="utf-8").splitlines()
            for line in lines[sent:]:
                if line.strip():
                    await ws.send_text(line)
            sent = len(lines)
        rows = [r for r in state.store.get_runs() if r["run_id"] == run_id]
        status = rows[0]["status"] if rows else "unknown"
        if status in ("done", "failed") :
            # drain any lines written between the read above and the status flip
            if trace.exists():
                lines = trace.read_text(encoding="utf-8").splitlines()
                for line in lines[sent:]:
                    if line.strip():
                        await ws.send_text(line)
                sent = len(lines)
            await ws.send_text(json.dumps({"type": "status", "payload": {"status": status}}))
            break
        await asyncio.sleep(0.4)
    await ws.close()
```

- [ ] **Step 5: Run tests** — expect `153 passed` (150 + 1 orchestrator regression + 2 stream tests).
- [ ] **Step 6: Commit** — `feat(d3): run execution endpoint and websocket trace streaming`

---

### Task 5: Suites, leaderboard, experiences endpoints

**Files:**
- Modify: `backend/hindsight/eval/suite.py` (optional `suite_id` param — sanctioned)
- Create: `backend/hindsight/api/routes_eval.py`
- Modify: `backend/hindsight/api/app.py` (include router)
- Test: `backend/tests/test_api_eval.py`

- [ ] **Step 1: suite.py pre-registration** — extend `run_suite` signature with `suite_id: str | None = None` and use `suite_id = suite_id or f"suite_{uuid.uuid4().hex[:8]}"`. Add a one-assert regression test to `backend/tests/test_suite.py` (preassigned id round-trips into the summary file name and return value).

- [ ] **Step 2: Write the failing tests** — `backend/tests/test_api_eval.py`:

```python
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
```

- [ ] **Step 3: Implement** `backend/hindsight/api/routes_eval.py`:

```python
"""Suite launch/status, leaderboard, experience browsing.

Leaderboard reads only what exists: failed runs carry no "outcome" key
(D3 carryover) — every read goes through .get()."""
from __future__ import annotations

import json
import threading
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class StartSuiteRequest(BaseModel):
    case_ids: list[str]
    presets: list[str] = ["base", "memory"]


def _default_suite_executor(state):
    def execute(case_ids: list[str], presets: list[str], suite_id: str) -> None:
        from hindsight.eval.suite import PRESETS, run_suite
        from hindsight.llm.client import LLMConfig, openai_transport
        from hindsight.llm.recording import RecordingLLMClient
        from hindsight.llm.retry import with_retry

        cfg = LLMConfig.from_env()
        llm = RecordingLLMClient(
            transport=with_retry(openai_transport(cfg)),
            db_path=state.root / "llm_calls.sqlite",
            model=cfg.model,
        )
        configs = {name: PRESETS[name].model_copy(update={"model": cfg.model}) for name in presets}

        def work():
            run_suite(
                [state.datasets / cid for cid in case_ids],
                configs,
                llm=llm,
                store=state.store,
                runs_root=state.runs_root,
                suite_id=suite_id,
            )

        threading.Thread(target=work, daemon=True).start()

    return execute


@router.post("/api/eval/suites")
def start_suite(body: StartSuiteRequest, request: Request):
    state = request.app.state.hindsight
    for cid in body.case_ids:
        if not (state.datasets / cid / "meta.json").exists():
            raise HTTPException(status_code=404, detail=f"unknown case {cid}")
    suite_id = f"suite_{uuid.uuid4().hex[:8]}"
    executor = state.suite_executor or _default_suite_executor(state)
    executor(body.case_ids, body.presets, suite_id)
    return {"suite_id": suite_id}


@router.get("/api/eval/suites/{suite_id}")
def suite_status(suite_id: str, request: Request):
    state = request.app.state.hindsight
    runs = state.store.get_runs(suite_id=suite_id)
    summary_path = state.runs_root / "suites" / f"{suite_id}.json"
    summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.exists()
        else None
    )
    return {"suite_id": suite_id, "runs": runs, "summary": summary}


@router.get("/api/leaderboard")
def leaderboard(suite_id: str, request: Request):
    state = request.app.state.hindsight
    summary_path = state.runs_root / "suites" / f"{suite_id}.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail=f"unknown suite {suite_id}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    cases: dict = {}
    for case_name, per_config in summary.get("results", {}).items():
        cases[case_name] = {}
        for config_name, scores in per_config.items():
            outcome = (scores or {}).get("outcome") or {}
            process = (scores or {}).get("process") or {}
            cases[case_name][config_name] = {
                "hit_rate": outcome.get("hit_rate"),
                "brier": outcome.get("brier"),
                "grounding_rate": process.get("grounding_rate"),
                "status": (scores or {}).get("status", "ok"),
            }
    return {"suite_id": suite_id, "configs": summary.get("configs", []), "cases": cases}


@router.get("/api/experiences")
def experiences(request: Request):
    state = request.app.state.hindsight
    rows = state.store.query_experiences("9999-12-31", exclude_case_id="__none__")
    return [json.loads(r["card_json"]) for r in rows]
```

Include the router in `app.py` (above the static mount).

- [ ] **Step 4: Run tests** — expect all green (153-ish + 4; report the real count).
- [ ] **Step 5: Commit** — `feat(d3): suite, leaderboard, and experience endpoints`

---

### Task 6: Frontend scaffold (Vite + React + TS + Tailwind, dark quant theme, i18n, API client)

No pytest here. Acceptance = `npm install` clean, `npm run dev` renders the shell with nav + language toggle, `npm run build` exits 0.

**Files (all NEW under `frontend/`):** `package.json`, `vite.config.ts`, `tailwind.config.js`, `postcss.config.js`, `index.html`, `src/main.tsx`, `src/index.css`, `src/App.tsx`, `src/lib/types.ts`, `src/lib/api.ts`, `src/lib/i18n.tsx`, `src/lib/format.ts`.

- [ ] **Step 1: Scaffold.** `cd F:/AIProjects/my_show/hindsight && npm create vite@latest frontend -- --template react-ts` (accept defaults), then `cd frontend && npm install && npm install react-router-dom recharts && npm install -D tailwindcss@3 postcss autoprefixer && npx tailwindcss init -p`.

- [ ] **Step 2: Theme + config.** `tailwind.config.js`:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#070a0f", 900: "#0a0e14", 800: "#11161f", 700: "#1a2230", 600: "#27324a" },
        line: { DEFAULT: "#1f2937" },
        up: "#22c55e",
        down: "#ef4444",
        accent: "#38bdf8",
        amber: "#f59e0b",
        muted: "#8b98ad",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
```

`vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true, ws: true },
    },
  },
});
```

`src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-ink-900 text-slate-200 antialiased;
}

.panel {
  @apply bg-ink-800 border border-line rounded-lg;
}

.num {
  @apply font-mono tabular-nums;
}
```

- [ ] **Step 3: Types + API client.** `src/lib/types.ts`:

```ts
export interface CaseMeta {
  case_id: string;
  title: string;
  ticker: string;
  as_of: string;
  outcome_window_days: number;
  description: string;
  tags: string[];
  n_docs: number;
}

export interface Bar { date: string; open: number; high: number; low: number; close: number; volume: number }

export interface Claim {
  claim_id: string;
  statement: string;
  type: "direction" | "magnitude" | "volatility";
  ticker: string;
  horizon_days: number;
  prediction: Record<string, unknown>;
  confidence: number;
  evidence: string[];
  status?: "hit" | "miss" | "ungradable";
  realized_return_pct?: number | null;
  detail?: string;
}

export interface RunSummary {
  run_id: string;
  case_id: string;
  suite_id: string | null;
  status: string;
  created_at: string;
  config: Record<string, unknown>;
  scores: Scores | null;
}

export interface Scores {
  status?: string;
  outcome?: { n_claims: number; n_gradable: number; n_hit: number; hit_rate: number | null; brier: number | null; calibration: CalBucket[] };
  process?: { judge_failed: boolean; grounding_rate?: number | null; reasoning_consistency?: number; retrieval_sufficiency?: number; attributions?: Record<string, string> };
  cost?: Record<string, { prompt_tokens: number; completion_tokens: number; calls: number }>;
  contamination_probe?: string;
  unverified?: boolean;
}

export interface RunDetail extends RunSummary { memo_md: string | null; claims: Claim[] }

export interface TraceEvent { type: string; agent: string; payload: Record<string, unknown>; tokens: number; ts: string }
```

`src/lib/api.ts`:

```ts
import type { Bar, CaseMeta, RunDetail, RunSummary, TraceEvent } from "./types";

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

export const api = {
  cases: () => get<CaseMeta[]>("/api/cases"),
  bars: (caseId: string) => get<{ ticker: string; bars: Bar[] }>(`/api/cases/${caseId}/bars`),
  runs: () => get<RunSummary[]>("/api/runs"),
  run: (runId: string) => get<RunDetail>(`/api/runs/${runId}`),
  trace: (runId: string) => get<TraceEvent[]>(`/api/runs/${runId}/trace`),
  startRun: async (caseId: string, memoryOn: boolean, maxSteps: number) => {
    const r = await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: caseId, memory_on: memoryOn, max_steps: maxSteps }),
    });
    if (!r.ok) throw new Error(`start run failed: ${r.status}`);
    return (await r.json()) as { run_id: string };
  },
};
```

- [ ] **Step 4: i18n.** `src/lib/i18n.tsx` — context provider + dict; ALL UI strings route through `t()`:

```tsx
import { createContext, useContext, useState, type ReactNode } from "react";

const dict = {
  en: {
    studio: "Research Studio", trace: "Trace Explorer", evals: "Eval Dashboard",
    run: "Run research", running: "Running…", reveal: "Reveal the future",
    revealed: "Future revealed", memory: "Experience memory", maxSteps: "Max steps",
    claims: "Claims", memo: "Research memo", hit: "HIT", miss: "MISS",
    ungradable: "UNGRADABLE", failed: "Validation failed — no memo was produced",
    unverified: "Unverified: the semantic critic never approved this memo; claims are not scored",
    probe: "Contamination probe", calibration: "Calibration", costs: "Token costs",
    auditLog: "Sandbox audit log", allEvents: "All events", asOf: "as-of",
    theFuture: "the future does not exist yet",
  },
  zh: {
    studio: "研究台", trace: "轨迹回放", evals: "评估看板",
    run: "开始研究", running: "运行中…", reveal: "揭示未来",
    revealed: "未来已揭示", memory: "经验记忆", maxSteps: "最大步数",
    claims: "可证伪声明", memo: "研究备忘录", hit: "命中", miss: "未中",
    ungradable: "不可评分", failed: "校验失败——未产出备忘录",
    unverified: "未验证：语义审查未通过，声明不计分",
    probe: "污染探针", calibration: "校准", costs: "Token 成本",
    auditLog: "沙箱审计日志", allEvents: "全部事件", asOf: "研究基准日",
    theFuture: "未来尚不存在",
  },
} as const;

type Lang = keyof typeof dict;
type Key = keyof (typeof dict)["en"];

const LangCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (k: Key) => string }>(
  { lang: "en", setLang: () => {}, t: (k) => k }
);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");
  const t = (k: Key) => dict[lang][k];
  return <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>;
}

export const useLang = () => useContext(LangCtx);
```

- [ ] **Step 5: Shell.** `src/App.tsx`: `BrowserRouter` + top nav (brand "HINDSIGHT" in mono + three `NavLink`s using `t()` + EN/中 toggle button) + `<Routes>` for `/` (Studio), `/runs/:runId/trace` (TraceExplorer), `/runs/:runId` (EvalDashboard). Pages are stubs (`<div>...</div>`) in this task. `src/lib/format.ts`: `pct(x: number | null | undefined)`, `num(x)`, `shortId(runId)` helpers.

- [ ] **Step 6: Verify.** `npm run dev` → shell renders at :5173, toggle switches nav labels EN/中. `npm run build` exits 0. Report both.
- [ ] **Step 7: Commit** — `feat(d3): frontend scaffold with dark quant theme and i18n` (commit `frontend/` except `node_modules/` — ensure repo-root `.gitignore` already covers `node_modules/` and `frontend/dist/`; it does since D1).

---

### Task 7: Research Studio page (the demo centerpiece)

**Files:** `src/lib/useRunStream.ts`, `src/components/PriceChart.tsx`, `src/components/ClaimCard.tsx`, `src/pages/Studio.tsx` (+ App.tsx route swap).

- [ ] **Step 1: the stream hook** — `src/lib/useRunStream.ts` (full code, WS with poll fallback per spec §8):

```ts
import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { TraceEvent } from "./types";

export function useRunStream(runId: string | null) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<string>("idle");
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    if (!runId) return;
    setEvents([]);
    setStatus("running");
    let closed = false;

    const startPolling = () => {
      if (pollRef.current) return;
      pollRef.current = window.setInterval(async () => {
        try {
          const [trace, detail] = await Promise.all([api.trace(runId), api.run(runId)]);
          setEvents(trace);
          if (detail.status === "done" || detail.status === "failed") {
            setStatus(detail.status);
            if (pollRef.current) window.clearInterval(pollRef.current);
          }
        } catch { /* keep polling */ }
      }, 1500);
    };

    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/api/runs/${runId}/stream`);
    ws.onmessage = (m) => {
      const evt = JSON.parse(m.data);
      if (evt.type === "status") {
        setStatus(evt.payload.status);
        ws.close();
      } else {
        setEvents((prev) => [...prev, evt]);
      }
    };
    ws.onerror = () => { if (!closed) startPolling(); };
    ws.onclose = () => { if (!closed && status === "running") startPolling(); };

    return () => {
      closed = true;
      ws.close();
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [runId]);

  return { events, status };
}
```

- [ ] **Step 2: the chart** — `src/components/PriceChart.tsx` (full code; the mask/reveal is THE demo moment):

```tsx
import {
  Area, ComposedChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { useLang } from "../lib/i18n";
import type { Bar } from "../lib/types";

interface Props { bars: Bar[]; asOf: string; revealed: boolean }

export function PriceChart({ bars, asOf, revealed }: Props) {
  const { t } = useLang();
  const data = bars.map((b) => ({
    date: b.date,
    past: b.date <= asOf ? b.close : null,
    future: b.date >= asOf ? (revealed ? b.close : null) : null,
  }));
  return (
    <div className="panel p-3 h-72 relative">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <XAxis dataKey="date" tick={{ fill: "#8b98ad", fontSize: 10 }} minTickGap={40} />
          <YAxis domain={["auto", "auto"]} tick={{ fill: "#8b98ad", fontSize: 10 }} width={48} />
          <Tooltip
            contentStyle={{ background: "#11161f", border: "1px solid #1f2937" }}
            labelStyle={{ color: "#8b98ad" }}
          />
          <ReferenceLine x={asOf} stroke="#f59e0b" strokeDasharray="4 4"
            label={{ value: `${t("asOf")} ${asOf}`, fill: "#f59e0b", fontSize: 10, position: "insideTopRight" }} />
          <Area dataKey="past" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.08} strokeWidth={1.5} dot={false} isAnimationActive={false} />
          <Area dataKey="future" stroke="#22c55e" fill="#22c55e" fillOpacity={0.08} strokeWidth={1.5} dot={false} isAnimationActive={true} animationDuration={1200} />
        </ComposedChart>
      </ResponsiveContainer>
      {!revealed && (
        <div className="absolute inset-y-0 right-0 w-[38%] bg-gradient-to-r from-transparent to-ink-950/90 flex items-center justify-end pr-4 pointer-events-none">
          <span className="text-muted text-xs font-mono rotate-0">{t("theFuture")}</span>
        </div>
      )}
    </div>
  );
}
```

(The masked-region width is cosmetic; the data itself carries `future: null` until reveal — the chart cannot leak what it was never given.)

- [ ] **Step 3: claim cards** — `src/components/ClaimCard.tsx`: bordered card per claim; BEFORE reveal show type badge, statement, horizon, confidence bar (`w-[{conf*100}%]` accent), evidence chunk ids as pills; AFTER reveal add status chip (`hit`→up green / `miss`→down red / `ungradable`→muted) + `realized_return_pct` + `detail` line. Full code left to the implementer; acceptance below governs.

- [ ] **Step 4: page assembly** — `src/pages/Studio.tsx` must implement:
  1. Load `api.cases()` on mount; case selector (card list with ticker/title/as_of/tags); selecting loads `api.bars(caseId)`.
  2. Config row: memory toggle, max-steps number input (default 8), Run button (`t("run")`); disabled while running.
  3. `PriceChart` with `revealed=false` initially; reveal state resets when a new case/run starts.
  4. Start run → `api.startRun` → `useRunStream(runId)`; right-hand live feed renders events as compact rows (icon by type: plan_step 🧭 tool_call 🔧 tool_result 📄 validation 🛡 audit 🔍 score 🏁 — use text glyphs, mono font); auto-scroll to bottom.
  5. On `status === "done"`: fetch `api.run(runId)`; render memo (`memo_md` in a `<pre className="whitespace-pre-wrap">` or a minimal md renderer — plain pre is acceptable for D3), claim cards, and the **Reveal the future** button (accent, prominent). Clicking sets `revealed=true` → chart future series animates in, claim cards show statuses. If `scores.unverified` → amber banner `t("unverified")`.
  6. On `status === "failed"`: red banner `t("failed")`; no memo section; link to trace page.
  7. Every visible string through `t()`.

- [ ] **Step 5: manual acceptance** (run backend `uvicorn hindsight.api.app:app --port 8000` from repo root with the venv + `npm run dev`; use the COMMITTED recorded runs — start a run with `HINDSIGHT_OFFLINE=1` env on the backend so the executor replays instantly, zero quota):
  - [ ] case cards render for nvda_fy26q1 + smci_case3
  - [ ] chart masks the future; amber as-of line labeled
  - [ ] starting a run streams events live into the feed
  - [ ] memo + claims render on completion; reveal animates the future series and flips claim chips
  - [ ] failed-run banner path verified (temporarily point at a seeded failed run or assert via the Eval page)
  - [ ] EN/中 toggle flips every label on the page
- [ ] **Step 6: Commit** — `feat(d3): research studio with reveal-the-future flow`

---

### Task 8: Trace Explorer page

**Files:** `src/components/EventRow.tsx`, `src/pages/TraceExplorer.tsx`.

- [ ] Must implement:
  1. Route `/runs/:runId/trace`; loads `api.trace(runId)` + `api.run(runId)`.
  2. Run header: run_id (mono), case, status chip, created_at, config summary.
  3. Filter bar: All / plan_step / tool_call+tool_result / validation / audit / score+context_trim (toggle pills, counts shown).
  4. Event list: `EventRow` = left color rail by type (accent=plan, sky=tool, amber=validation, red=DENIED audit note, green=score), agent tag, compact one-line summary (e.g. tool name + truncated args), expandable `<pre>` with pretty-printed payload JSON; tokens shown when > 0.
  5. Audit events render the sandbox fields (tool/params/data_max_date/note) — a `DENIED lookahead` note gets a red highlight (this is a demo talking point).
  6. Cost footer: per-agent table from `scores.cost` (calls / prompt / completion tokens, mono).
  7. i18n via `t()`; graceful when trace is empty (failed early).
- [ ] Manual acceptance: open the committed NVDA record run's trace — all event types visible, filters work, DENIED audit visible if present, payloads expand.
- [ ] Commit — `feat(d3): trace explorer with audit view and cost footer`

---

### Task 9: Eval Dashboard page

**Files:** `src/components/{ScoreCards.tsx, CalibrationChart.tsx, AttributionBadge.tsx}`, `src/pages/EvalDashboard.tsx`.

- [ ] `CalibrationChart` (full code):

```tsx
import {
  CartesianGrid, ReferenceLine, Scatter, ScatterChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

interface Bucket { lo: number; hi: number; n: number; avg_confidence: number | null; hit_rate: number | null }

export function CalibrationChart({ buckets }: { buckets: Bucket[] }) {
  const pts = buckets
    .filter((b) => b.n > 0 && b.avg_confidence !== null && b.hit_rate !== null)
    .map((b) => ({ x: b.avg_confidence, y: b.hit_rate, n: b.n }));
  return (
    <div className="panel p-3 h-64">
      <ResponsiveContainer>
        <ScatterChart margin={{ top: 10, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
          <XAxis type="number" dataKey="x" domain={[0, 1]} tick={{ fill: "#8b98ad", fontSize: 10 }}
            label={{ value: "confidence", fill: "#8b98ad", fontSize: 10, position: "insideBottom", offset: -2 }} />
          <YAxis type="number" dataKey="y" domain={[0, 1]} tick={{ fill: "#8b98ad", fontSize: 10 }} width={36}
            label={{ value: "hit rate", fill: "#8b98ad", fontSize: 10, angle: -90, position: "insideLeft" }} />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#8b98ad" strokeDasharray="4 4" />
          <Tooltip contentStyle={{ background: "#11161f", border: "1px solid #1f2937" }}
            formatter={(v: number) => v.toFixed(2)} />
          <Scatter data={pts} fill="#38bdf8" shape={(p: any) => (
            <g>
              <circle cx={p.cx} cy={p.cy} r={4 + Math.min(p.payload.n, 6)} fill="#38bdf8" fillOpacity={0.7} />
              <text x={p.cx} y={p.cy - 10} fill="#8b98ad" fontSize={9} textAnchor="middle">n={p.payload.n}</text>
            </g>
          )} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] Must implement (page):
  1. Route `/runs/:runId`; run picker (recent runs from `api.runs()`) when navigated bare.
  2. `ScoreCards`: hit rate, Brier, grounding rate, reasoning/retrieval (1-5), total tokens (num, mono, colored by polarity where meaningful; show "—" for null, NEVER crash on missing keys — failed runs have `scores.status` only).
  3. `CalibrationChart` from `scores.outcome.calibration` (skip section entirely if absent).
  4. Claims table: id / type / statement / horizon / confidence / status chip / realized % / `AttributionBadge` (only for misses; three enum values with distinct hues: evidence_missing=amber, misread_evidence=red, reasonable_but_wrong=sky — the "why it behaves as it does" column).
  5. Contamination probe: collapsible panel rendering `scores.contamination_probe` text.
  6. Banners: failed (red, from status) / unverified (amber).
  7. i18n throughout.
- [ ] Manual acceptance: NVDA record run shows 4 claims / 1 hit / attribution badges on misses / calibration points with n labels; SMCI run shows its shapes; a seeded failed run renders banners without crashing.
- [ ] Commit — `feat(d3): eval dashboard with calibration and attribution views`

---

### Task 10: README skeleton + launch config + D3 wrap-up

**Files:** Create `README.md` (repo root), `.claude/launch.json`; verify everything.

- [ ] **Step 1: README skeleton** (English; D4 adds banner/GIF/中文版/methodology深度)。 Sections, in order: title + one-line tagline ("A time-travel evaluation harness for deep research agents — every claim it makes is falsifiable against realized market data"); badges row (CI placeholder); **Why** (3 sentences: deep-research evals are subjective; finance gives ground truth; Hindsight runs agents as-of a past date, grades them with hindsight); **How it works** (mermaid flowchart: sandbox → agents → grading → experience loop); **Quick start** (uvicorn + npm dev + `HINDSIGHT_OFFLINE=1` replay demo of the committed runs — zero API key needed for the demo path); **The three anti-lookahead channels** (docs/bars/memory, one line each + pointer to the 11 leakage tests); **Evaluation** (three tracks tables + the NVDA/SMCI headline numbers with the honest small-sample framing); **Repo map**; **Known limitations** (parametric memory contamination + probe, small-N statistics, judge self-preference — one line each, pointing to docs); link to `docs/design-decisions.md` and `docs/eval-log.md`.

- [ ] **Step 2: `.claude/launch.json`**:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "backend",
      "runtimeExecutable": "backend/.venv/Scripts/python",
      "runtimeArgs": ["-m", "uvicorn", "hindsight.api.app:app", "--port", "8000"],
      "port": 8000
    },
    {
      "name": "frontend",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev", "--prefix", "frontend"],
      "port": 5173
    }
  ]
}
```

- [ ] **Step 2b: SPA fallback (T2-review carryover)** — `StaticFiles(html=True)` serves `index.html` only at `/`; direct navigation/refresh on client routes (e.g. `/runs/xyz`) 404s. In `app.py`, replace the static mount with a mount plus a catch-all: keep the mount for `/assets`, and add

```python
        from fastapi.responses import FileResponse

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str):
            return FileResponse(dist / "index.html")
```

registered AFTER all API routers (path routes win over the catch-all only if declared earlier — verify `/api/cases` still resolves and `/runs/anything` returns index.html). Also wrap `list_cases`'s per-file `json.loads` in try/except-continue (T2-review resilience note) with one test: a broken meta.json in a stray case dir must not 500 the whole list.

- [ ] **Step 3: Full verification**
  - `cd backend && .venv/Scripts/python -m pytest -q` → report exact count (≈157; trust arithmetic)
  - `cd frontend && npm run build` → exit 0; then confirm `uvicorn hindsight.api.app:app` serves the built frontend at `/` (static mount)
  - Security scan: staged diff free of key material
  - Demo walkthrough (offline): backend with `HINDSIGHT_OFFLINE=1`, replay a run per case through the Studio UI, click through all three pages — record a short checklist of what was seen
- [ ] **Step 4: Commit and tag**

```bash
git add -A && git status --short   # verify nothing unexpected (node_modules/dist must NOT appear)
git commit -m "feat(d3): README skeleton, launch config, day-3 wrap-up"
git tag d3-complete
```

---

## Execution notes

- Same conventions as D1/D2: subagent per task, spec-then-quality review for backend tasks (Tasks 1-5); frontend tasks (6-9) get a single review pass focused on the acceptance checklists + code reading (no byte-diff requirement — the plan specifies infrastructure code exactly but grants latitude on page assembly).
- Frontend development NEVER needs the real API key: run the backend with `HINDSIGHT_OFFLINE=1` and use the committed recorded runs (replay is instant).
- The frontend reviewer should run the dev servers and click through — visual acceptance is the bar, supplemented by reading the diff for i18n coverage and failed-run tolerance.
- **D4 carryover seeded here:** README banner/GIF/中文版; calibration chart polish; leaderboard PAGE (the API exists from Task 5 — the page is D4 scope per spec §10); judge meta-eval labeling; corpus citation nits.
