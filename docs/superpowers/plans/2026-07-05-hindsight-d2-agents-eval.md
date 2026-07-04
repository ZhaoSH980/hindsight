# Hindsight D2 — Agents + Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete research pipeline (four-agent orchestration with a native-function-calling ReAct planner), the three-track evaluation engine (outcome grader per spec §3.3, LLM judge with failure attribution, cost ledger wiring), the time-gated experience library, the contamination probe, and the EvalSuite runner — ending with a real recorded end-to-end run on the NVDA case and a validated case-3 (SMCI) candidate.

**Architecture:** Deterministic orchestrator state machine; the LLM's freedom is confined to single decisions inside each stage. Planner = bounded ReAct over native `tools` (probe-decided, see docs/eval-log.md). Researcher = deterministic evidence manager (no LLM). All LLM traffic flows through the D1 record/replay client wrapped in a 429-aware retry transport. Grading runs deliberately OUTSIDE the sandbox (evaluation is entitled to realized data; the boundary is the orchestrator). Experience cards pass a three-constraint time gate before reaching the planner.

**Tech Stack:** unchanged from D1 (Python 3.11+/3.13, pydantic v2, rank-bm25, sqlite3, openai SDK; pytest; no new dependencies).

**Working directory:** repo root `F:/AIProjects/my_show/hindsight`, branch `d1-foundation` (continue on it). Venv: `backend/.venv` (Git Bash: `backend/.venv/Scripts/python`). Baseline: tag `d1-complete`, 60 tests passing.

**Reference docs:** spec `docs/superpowers/specs/2026-07-04-hindsight-design.md` (§3.1-3.6, §4.3-4.4, §8, §10-D2); D1 plan carryover list (all 11 items are folded into Tasks 1, 2, 5, 9, 11, 12 below); probe results `docs/eval-log.md`.

**Test-count drift note:** review fixes during execution added 2 extra tests beyond this plan's originals (Task 2: broken-`__str__` guard; Task 3: time-gate boundary). Every "Expected: N passed" from Task 4 onward therefore runs **+2** versus the number printed in the task body. Trust the arithmetic (previous suite total + this task's new tests), not the stale literal.

**Sanctioned spec notes baked into this plan:** Researcher is deterministic (spec §4.2 amended); claims/trace live in run-dir files, no separate SQLite tables (spec §4.3 amended); `audit` trace events are forwarded sandbox `AuditEntry`s (spec §5 amended).

**LLM call budget per live run:** probe 1 + planner ≤8 + analyst 1-3 + critic-semantic 1-3 + judge 1-2 ≈ 12-17 calls. xf-yun throttles bursts (429 code 11210 after ~4 rapid calls) — the retry transport (Task 1) absorbs this; the recording layer makes re-runs free.

## File structure (created/modified this plan)

```
backend/hindsight/
├── llm/retry.py                 # NEW: 429-aware retry transport wrapper
├── llm/recording.py             # MOD: float-coerce temperature
├── trace/recorder.py            # MOD: newline="\n"
├── tools/registry.py            # MOD: + safe_call()
├── tools/corpus_search.py       # MOD: excerpt "..." marker; evidence_sink param
├── store/__init__.py            # NEW (empty)
├── store/db.py                  # NEW: runs + experiences tables (thread-safe)
├── agents/__init__.py           # NEW (empty)
├── agents/prompts.py            # NEW: all system prompts + brief builders
├── agents/researcher.py         # NEW: EvidenceManager (deterministic)
├── agents/planner.py            # NEW: bounded ReAct loop + FINISH_TOOL
├── agents/analyst.py            # NEW: memo generation call
├── agents/critic.py             # NEW: 3-layer validation loop
├── agents/orchestrator.py       # NEW: the state machine + run persistence
├── eval/__init__.py             # NEW (empty)
├── eval/outcome_grader.py       # NEW: spec §3.3 rules 1-6 + aggregates
├── eval/judge.py                # NEW: process scores + failure attribution
├── eval/contamination.py       # NEW: parametric-memory probe
├── eval/suite.py                # NEW: EvalSuite runner
├── memory/__init__.py           # NEW (empty)
├── memory/experience.py         # NEW: cards, builder, time-gated retriever
└── cli.py                       # MOD: + run, + suite subcommands
backend/tests/
├── llm_stubs.py                 # NEW: ScriptedTransport + response builders
├── test_retry.py  test_store.py  test_prompts.py  test_researcher.py
├── test_planner.py  test_critic_loop.py  test_grader.py  test_judge.py
├── test_contamination.py  test_experience.py  test_orchestrator.py  test_suite.py
├── test_replay.py test_trace.py test_tools.py test_sandbox_leakage.py   # MOD: additions
datasets/smci_case3/             # NEW (Task 15): meta.json, bars.json, docs/*.md
runs/                            # NEW: committed recorded runs (Task 14/15)
docs/eval-log.md                 # MOD: prompt-iteration + case-3 entries
```

---

### Task 1: LLM hardening batch (retry transport, replay-key coercion, recorder newline)

Carryover items ⑤⑥⑧⑩⑪ + the TraceRecorder append-across-instances test.

**Files:**
- Create: `backend/hindsight/llm/retry.py`
- Modify: `backend/hindsight/llm/recording.py` (one line in `chat`)
- Modify: `backend/hindsight/trace/recorder.py` (one line in `emit`)
- Create: `backend/tests/test_retry.py`
- Modify: `backend/tests/test_replay.py` (3 new tests)
- Modify: `backend/tests/test_trace.py` (2 new tests)

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_retry.py`:

```python
import pytest

from hindsight.llm.retry import GENERIC_WAITS, RATE_LIMIT_WAITS, with_retry


class RateLimitError(Exception):
    """Name-matched by the retry wrapper (mirrors openai.RateLimitError)."""


def make_flaky(fail_times: int, exc_factory):
    state = {"calls": 0}

    def transport(request):
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc_factory()
        return {"ok": True, "calls": state["calls"]}

    return transport, state


def test_rate_limit_retries_with_long_waits():
    sleeps = []
    transport, state = make_flaky(2, lambda: RateLimitError("429 code 11210"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    assert wrapped({"m": 1})["ok"] is True
    assert state["calls"] == 3
    assert sleeps == [RATE_LIMIT_WAITS[0], RATE_LIMIT_WAITS[1]]


def test_generic_error_uses_expo_backoff():
    sleeps = []
    transport, state = make_flaky(2, lambda: ConnectionError("boom"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    assert wrapped({"m": 1})["ok"] is True
    assert sleeps == [GENERIC_WAITS[0], GENERIC_WAITS[1]]


def test_exhaustion_reraises():
    sleeps = []
    transport, _ = make_flaky(99, lambda: RateLimitError("429"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    with pytest.raises(RateLimitError):
        wrapped({"m": 1})
    assert sleeps == list(RATE_LIMIT_WAITS)


def test_429_in_message_counts_as_rate_limit():
    sleeps = []
    transport, _ = make_flaky(1, lambda: RuntimeError("HTTP 429 too many requests"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    assert wrapped({"m": 1})["ok"] is True
    assert sleeps == [RATE_LIMIT_WAITS[0]]
```

Append to `backend/tests/test_replay.py`:

```python
def test_temperature_int_float_same_key(tmp_path):
    calls = []

    def transport(request):
        calls.append(request)
        return fake_response("t")

    c = RecordingLLMClient(transport=transport, db_path=tmp_path / "db.sqlite", model="m1")
    c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0)
    c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0.0)
    assert len(calls) == 1


def test_cjk_content_replays_equal(tmp_path):
    db = tmp_path / "db.sqlite"
    c1 = RecordingLLMClient(
        transport=lambda r: fake_response("英伟达数据中心需求强劲，Blackwell 供不应求。"),
        db_path=db,
        model="m1",
    )
    r1 = c1.chat(messages=[{"role": "user", "content": "中文测试 ± émojis 🚀"}])
    c2 = RecordingLLMClient(
        transport=lambda r: (_ for _ in ()).throw(AssertionError("offline")),
        db_path=db,
        model="m1",
        offline=True,
    )
    r2 = c2.chat(messages=[{"role": "user", "content": "中文测试 ± émojis 🚀"}])
    assert r2 == r1


def test_tools_order_changes_key(tmp_path):
    calls = []

    def transport(request):
        calls.append(request)
        return fake_response(f"call-{len(calls)}")

    c = RecordingLLMClient(transport=transport, db_path=tmp_path / "db.sqlite", model="m1")
    tools_a = [{"name": "search"}, {"name": "calc"}]
    tools_b = [{"name": "calc"}, {"name": "search"}]
    c.chat(messages=[{"role": "user", "content": "hi"}], tools=tools_a)
    c.chat(messages=[{"role": "user", "content": "hi"}], tools=tools_b)
    assert len(calls) == 2
```

Append to `backend/tests/test_trace.py`:

```python
def test_recorder_appends_across_instances(tmp_path):
    TraceRecorder(run_dir=tmp_path).emit(
        TraceEvent(type="plan_step", agent="a", payload={})
    )
    TraceRecorder(run_dir=tmp_path).emit(
        TraceEvent(type="plan_step", agent="b", payload={})
    )
    lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert [json.loads(l)["agent"] for l in lines] == ["a", "b"]


def test_trace_file_uses_lf_only(tmp_path):
    rec = TraceRecorder(run_dir=tmp_path)
    rec.emit(TraceEvent(type="plan_step", agent="a", payload={"x": "中文"}))
    raw = (tmp_path / "trace.jsonl").read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_retry.py tests/test_replay.py tests/test_trace.py -q`
Expected: FAIL — `ModuleNotFoundError: hindsight.llm.retry`, plus the replay/trace additions failing (`2 calls`, `\r\n` present).

- [ ] **Step 3: Write `backend/hindsight/llm/retry.py`**

```python
"""Transport retry wrapper: long waits on 429, exponential backoff otherwise.

xf-yun MaaS throttles bursts (~4 rapid calls -> 429 code 11210, see
docs/eval-log.md). Rate-limit waits are deliberately long; generic errors
get a short exponential ladder. Exhaustion re-raises the last exception.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from hindsight.llm.client import Transport

RATE_LIMIT_WAITS = (15.0, 30.0, 60.0)
GENERIC_WAITS = (2.0, 4.0, 8.0)


def _is_rate_limit(exc: Exception) -> bool:
    if type(exc).__name__ == "RateLimitError":
        return True
    text = str(exc)
    return "429" in text or "11210" in text


def with_retry(
    transport: Transport,
    sleep: Callable[[float], None] = time.sleep,
) -> Transport:
    def send(request: dict[str, Any]) -> dict[str, Any]:
        rate_i = 0
        generic_i = 0
        while True:
            try:
                return transport(request)
            except Exception as exc:  # noqa: BLE001 - classified below, re-raised on exhaustion
                if _is_rate_limit(exc):
                    if rate_i >= len(RATE_LIMIT_WAITS):
                        raise
                    sleep(RATE_LIMIT_WAITS[rate_i])
                    rate_i += 1
                else:
                    if generic_i >= len(GENERIC_WAITS):
                        raise
                    sleep(GENERIC_WAITS[generic_i])
                    generic_i += 1

    return send
```

- [ ] **Step 4: Apply the two one-line modifications**

In `backend/hindsight/llm/recording.py`, at the top of `chat()` (before building `request`), add:

```python
        temperature = float(temperature)  # int/float must hash to the same replay key
```

In `backend/hindsight/trace/recorder.py`, change the `open` call in `emit` to:

```python
        with self._path.open("a", encoding="utf-8", newline="\n") as f:
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `69 passed` (60 existing + 4 retry + 3 replay + 2 trace).

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/llm backend/hindsight/trace/recorder.py backend/tests/test_retry.py backend/tests/test_replay.py backend/tests/test_trace.py
git commit -m "feat(d2): 429-aware retry transport; replay-key and trace hardening"
```

---

### Task 2: safe_call dispatch boundary + excerpt truncation marker

Carryover items ①②: any tool failure becomes error JSON the ReAct loop can read; truncated excerpts signal truncation.

**Files:**
- Modify: `backend/hindsight/tools/registry.py` (add `safe_call`)
- Modify: `backend/hindsight/tools/corpus_search.py` (marker)
- Modify: `backend/tests/test_tools.py` (5 new tests)

- [ ] **Step 1: Write the failing tests** — append to `backend/tests/test_tools.py`:

```python
def test_safe_call_overflow_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "calc", {"expression": "9**9**9"})
    assert "OverflowError" in json.loads(out)["error"]


def test_safe_call_recursion_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "calc", {"expression": "+".join(["1"] * 5000)})
    payload = json.loads(out)
    assert "error" in payload or "value" in payload  # deep-parse limits vary; must not raise


def test_safe_call_bad_kwargs_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "corpus_search", {"query": "x", "evil": "y"})
    assert "TypeError" in json.loads(out)["error"]


def test_safe_call_unknown_tool_returns_error_json(registry):
    from hindsight.tools.registry import safe_call

    out = safe_call(registry, "nope", {})
    assert "KeyError" in json.loads(out)["error"]


def test_excerpt_truncation_marker(registry):
    from datetime import date as _date

    from hindsight.rag.bm25_retriever import BM25Retriever
    from hindsight.sandbox.audit import AuditLog
    from hindsight.sandbox.gate import SandboxedCorpus
    from hindsight.tools.corpus_search import make_corpus_tool

    long_chunk = Chunk(
        chunk_id="long::000",
        doc_id="long",
        title="long doc",
        published_at=_date(2025, 5, 1),
        text="nvidia " * 200,  # 1400 chars > 700
    )
    corpus = SandboxedCorpus(BM25Retriever([long_chunk]), as_of=AS_OF, audit=AuditLog())
    spec = make_corpus_tool(corpus)
    payload = json.loads(spec.fn(query="nvidia"))
    excerpt = payload["results"][0]["excerpt"]
    assert excerpt.endswith("...")
    assert len(excerpt) == 700 + 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_tools.py -q`
Expected: FAIL — `ImportError: cannot import name 'safe_call'`.

- [ ] **Step 3: Implement**

In `backend/hindsight/tools/registry.py`, add `import json` at the top and this function at module level (below the class):

```python
def safe_call(registry: ToolRegistry, name: str, args: dict[str, Any]) -> str:
    """LLM-facing dispatch: any failure becomes error JSON the model can read.

    The ReAct loop must never die on a malformed tool call (OverflowError,
    RecursionError, TypeError from unexpected kwargs, unknown tool, ...).
    """
    try:
        return registry.call(name, args)
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all at the LLM boundary
        try:
            msg = str(exc)
        except Exception:  # noqa: BLE001 - even __str__ can be broken
            msg = "<unprintable exception>"
        return json.dumps({"error": f"{type(exc).__name__}: {msg}"})
```

In `backend/hindsight/tools/corpus_search.py`, replace the excerpt line inside the results mapping with:

```python
                        "excerpt": s.chunk.text[:_EXCERPT_CHARS]
                        + ("..." if len(s.chunk.text) > _EXCERPT_CHARS else ""),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `74 passed` (69 + 5).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/tools backend/tests/test_tools.py
git commit -m "feat(d2): safe_call LLM dispatch boundary; excerpt truncation marker"
```

---

### Task 3: SQLite store (runs + experiences)

**Files:**
- Create: `backend/hindsight/store/__init__.py` (empty)
- Create: `backend/hindsight/store/db.py`
- Test: `backend/tests/test_store.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_store.py`:

```python
from hindsight.store.db import Store


def test_run_upsert_and_get(tmp_path):
    s = Store(tmp_path / "h.db")
    s.upsert_run("r1", "case_a", '{"model":"m"}', "running")
    s.upsert_run("r1", "case_a", '{"model":"m"}', "done", scores_json='{"hit_rate":1.0}')
    rows = s.get_runs()
    assert len(rows) == 1
    assert rows[0]["run_id"] == "r1"
    assert rows[0]["status"] == "done"
    assert rows[0]["scores_json"] == '{"hit_rate":1.0}'


def test_runs_filter_by_suite(tmp_path):
    s = Store(tmp_path / "h.db")
    s.upsert_run("r1", "c", "{}", "done", suite_id="s1")
    s.upsert_run("r2", "c", "{}", "done", suite_id="s2")
    assert [r["run_id"] for r in s.get_runs(suite_id="s1")] == ["r1"]


def test_experience_time_gate_and_leave_one_out(tmp_path):
    s = Store(tmp_path / "h.db")
    s.insert_experience("e1", "case_a", "r1", "2025-03-01", "2025-04-15", "NVDA earnings", "{}")
    s.insert_experience("e2", "case_b", "r2", "2025-05-01", "2025-06-30", "TSLA delivery", "{}")
    s.insert_experience("e3", "case_c", "r3", "2025-02-01", "2025-03-10", "SMCI filing", "{}")

    rows = s.query_experiences(as_of="2025-05-22", exclude_case_id="case_c")
    ids = {r["exp_id"] for r in rows}
    assert ids == {"e1"}  # e2 window not closed by as_of; e3 excluded (same case)


def test_experience_created_before_snapshot(tmp_path):
    s = Store(tmp_path / "h.db")
    s.insert_experience("e1", "case_a", "r1", "2025-03-01", "2025-04-15", "NVDA", "{}")
    future = "9999-01-01T00:00:00+00:00"
    past = "2000-01-01T00:00:00+00:00"
    assert s.query_experiences("2025-05-22", "other", created_before=future)
    assert s.query_experiences("2025-05-22", "other", created_before=past) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_store.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/store/db.py`**

```python
"""SQLite store for run summaries and experience cards.

Thread-safe from birth (check_same_thread=False + lock) because D3's
FastAPI threadpool will share it. Claims and traces are NOT stored here —
run-dir files are authoritative for details (spec §4.3).
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS runs ("
                " run_id TEXT PRIMARY KEY, case_id TEXT NOT NULL,"
                " suite_id TEXT, config_json TEXT NOT NULL,"
                " status TEXT NOT NULL, scores_json TEXT,"
                " created_at TEXT NOT NULL)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS experiences ("
                " exp_id TEXT PRIMARY KEY, source_case_id TEXT NOT NULL,"
                " source_run_id TEXT NOT NULL, as_of TEXT NOT NULL,"
                " outcome_window_end TEXT NOT NULL, features_text TEXT NOT NULL,"
                " card_json TEXT NOT NULL, created_at TEXT NOT NULL)"
            )
            self._conn.commit()

    def upsert_run(
        self,
        run_id: str,
        case_id: str,
        config_json: str,
        status: str,
        scores_json: str | None = None,
        suite_id: str | None = None,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(run_id) DO UPDATE SET"
                " status=excluded.status, scores_json=excluded.scores_json",
                (run_id, case_id, suite_id, config_json, status, scores_json, now_iso()),
            )
            self._conn.commit()

    def get_runs(self, suite_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if suite_id is None:
                rows = self._conn.execute("SELECT * FROM runs ORDER BY created_at").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM runs WHERE suite_id = ? ORDER BY created_at", (suite_id,)
                ).fetchall()
        return [dict(r) for r in rows]

    def insert_experience(
        self,
        exp_id: str,
        source_case_id: str,
        source_run_id: str,
        as_of: str,
        outcome_window_end: str,
        features_text: str,
        card_json: str,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO experiences VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    exp_id,
                    source_case_id,
                    source_run_id,
                    as_of,
                    outcome_window_end,
                    features_text,
                    card_json,
                    now_iso(),
                ),
            )
            self._conn.commit()

    def query_experiences(
        self,
        as_of: str,
        exclude_case_id: str,
        created_before: str | None = None,
    ) -> list[dict[str, Any]]:
        """Time-gated candidates (spec §3.5): window closed by as_of, never the
        same case, optionally only cards existing before a suite snapshot."""
        sql = (
            "SELECT * FROM experiences"
            " WHERE outcome_window_end <= ? AND source_case_id != ?"
        )
        params: list[Any] = [as_of, exclude_case_id]
        if created_before is not None:
            sql += " AND created_at < ?"
            params.append(created_before)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `78 passed` (74 + 4).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/store backend/tests/test_store.py
git commit -m "feat(d2): sqlite store for runs and time-gated experiences"
```

---

### Task 4: Agent prompts module

All prompts are English (spec §4.2). They are versioned code: every later edit is an eval-log entry (spec §3.4 留痕).

**Files:**
- Create: `backend/hindsight/agents/__init__.py` (empty)
- Create: `backend/hindsight/agents/prompts.py`
- Test: `backend/tests/test_prompts.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_prompts.py`:

```python
from datetime import date

from hindsight.agents import prompts
from hindsight.data.models import CaseMeta


def make_meta():
    return CaseMeta(
        case_id="c",
        title="T",
        ticker="NVDA",
        as_of=date(2025, 5, 22),
        outcome_window_days=40,
        description="desc",
    )


def test_analyst_prompt_names_schema_essentials():
    text = prompts.ANALYST_SYSTEM
    for token in ('"claims"', '"direction"', '"magnitude"', '"volatility"',
                  '"confidence"', '"evidence"', '"horizon_days"'):
        assert token in text


def test_judge_prompt_names_attribution_enum():
    for token in ("evidence_missing", "misread_evidence", "reasonable_but_wrong"):
        assert token in prompts.JUDGE_SYSTEM


def test_case_brief_carries_asof_and_horizon_cap():
    brief = prompts.case_brief(make_meta())
    assert "2025-05-22" in brief
    assert "40" in brief
    assert "NVDA" in brief
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_prompts.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/agents/prompts.py`** (create empty `agents/__init__.py` too)

```python
"""System prompts and brief builders. Prompts are versioned code:
every edit gets a before/after entry in docs/eval-log.md."""
from __future__ import annotations

from hindsight.data.models import CaseMeta

PLANNER_SYSTEM = """\
You are the research planner of Hindsight, an evaluation-driven equity research system.
You research one ticker AS OF a historical date. Information published after the as-of \
date does not exist for you; tools enforce this.
Work in steps. Think briefly about what you still need, then call ONE tool at a time. \
Use focused keyword queries (3-6 words). Before finishing, make sure your evidence covers:
- the most recent reported results and forward guidance,
- the main demand/supply drivers,
- at least one credible bearish angle or risk,
- recent price action (use price_history).
When coverage is sufficient (typically 4-6 tool calls), call finish_research with a \
one-line reason. Never invent facts that tools did not return.
"""

ANALYST_SYSTEM = """\
You are the research analyst of Hindsight. Using ONLY the evidence provided, write a \
structured research memo as a single JSON object — no markdown fences, no prose outside JSON.

Schema (all fields required):
{
  "background": "2-4 sentences of market context",
  "bull_case": "the strongest bullish argument, grounded in evidence",
  "bear_case": "the strongest bearish argument, grounded in evidence",
  "conclusion": "your synthesized view in 2-3 sentences",
  "claims": [
    {
      "claim_id": "c1",
      "statement": "objectively checkable statement about the stock price",
      "type": "direction" | "magnitude" | "volatility",
      "ticker": "<the case ticker>",
      "horizon_days": <int, trading days, within the allowed horizon>,
      "prediction":
        {"direction": "up"|"down", "threshold_pct": <float > 0>}            // type=direction
        | {"low_pct": <float>, "high_pct": <float>}                          // type=magnitude
        | {"relation": "above"|"below", "percentile": <0..100>}              // type=volatility
      ,
      "confidence": <float 0..1, your honest probability that the claim comes true>,
      "evidence": ["<chunk_id>", ...]
    }
  ]
}

Rules:
- 2 to 4 claims; at least one "direction" claim.
- Every claim cites at least one evidence chunk_id from the provided evidence blocks.
- direction semantics: at-horizon-end — the claim is judged on the closing price of the \
Nth trading day after the as-of date, not on any intraday path.
- magnitude semantics: uses the same horizon-end return r as direction; the claim is a \
hit iff r*100 falls inside [low_pct, high_pct] (closed interval). It is NOT a price \
range over the period.
- volatility semantics: the realized daily log-return volatility over your claim's \
horizon window is compared against same-length rolling windows from the prior ~252 \
trading days; "above" percentile p predicts unusually turbulent price action for this \
stock, "below" predicts unusually calm.
- confidence is used for calibration scoring (Brier). Do not inflate it.
Example claim: {"claim_id": "c1", "statement": "NVDA closes >=5% above the as-of price \
on the 20th trading day after as-of", "type": "direction", "ticker": "NVDA", \
"horizon_days": 20, "prediction": {"direction": "up", "threshold_pct": 5.0}, \
"confidence": 0.62, "evidence": ["q4_recap::001"]}
Example magnitude claim: {"claim_id": "c2", "statement": "NVDA's 20-trading-day \
return lands between -2% and +8%", "type": "magnitude", "ticker": "NVDA", \
"horizon_days": 20, "prediction": {"low_pct": -2.0, "high_pct": 8.0}, \
"confidence": 0.55, "evidence": ["q4_recap::001"]}
"""

CRITIC_SEMANTIC_SYSTEM = """\
You are the memo critic of Hindsight. You receive a research memo (JSON) and the evidence \
excerpts its claims cite. Return ONLY a JSON object: {"ok": true|false, "problems": ["..."]}.
Mark ok=false when any of the following holds:
- a claim is not objectively checkable against daily closing prices within its horizon,
- a cited evidence excerpt does not actually support its claim,
- the conclusion contradicts the direction of the claims.
List each problem as one short actionable sentence. If everything is sound, return \
{"ok": true, "problems": []}.
"""

JUDGE_SYSTEM = """\
You are the process judge of Hindsight. You receive: a research memo (JSON), the evidence \
excerpts it cited, and the OUTCOME of each claim (hit / miss / ungradable, with realized \
returns). Judge the PROCESS, not the luck. Return ONLY a JSON object:
{
  "grounding": [{"claim_id": "...", "supported": true|false, "comment": "..."}],
  "reasoning_consistency": <1-5>,
  "retrieval_sufficiency": <1-5>,
  "attributions": [{"claim_id": "...", "attribution": "evidence_missing" | "misread_evidence" | "reasonable_but_wrong"}]
}
Rules:
- grounding: one entry per claim — does its cited evidence genuinely support the statement?
- attributions: one entry for EVERY claim whose outcome is miss, and only those. \
evidence_missing = the corpus contained (or the planner should have sought) contrary \
signals that were never retrieved; misread_evidence = retrieved evidence was \
misinterpreted; reasonable_but_wrong = the process was sound and the market simply \
moved against the claim.
- reasoning_consistency: does the memo's logic hang together (5 = airtight)?
- retrieval_sufficiency: did the research cover the angles that mattered (5 = complete)?
"""

PROBE_PROMPT = """\
Knowledge check (answer from memory only, no tools): what do you know about what \
happened to {ticker} — its stock price and major business events — AFTER {as_of}? \
If you know specifics, state them with dates. If you do not know, say so plainly.\
"""


def case_brief(meta: CaseMeta) -> str:
    return (
        f"Research task: {meta.title}\n"
        f"Ticker: {meta.ticker}\n"
        f"As-of date: {meta.as_of.isoformat()} (information after this date does not exist)\n"
        f"Context: {meta.description}\n"
        f"Claims horizon limit: {meta.outcome_window_days} trading days.\n"
    )


def experience_block(rendered_cards: str) -> str:
    if not rendered_cards:
        return ""
    return (
        "\nLessons from previously graded research (older cases whose outcomes are "
        "already known as of your research date):\n" + rendered_cards + "\n"
    )


def analyst_user_prompt(meta: CaseMeta, evidence_text: str, market_summary: str) -> str:
    return (
        case_brief(meta)
        + f"\nMarket snapshot (price_history tool output):\n{market_summary}\n"
        + f"\nEvidence blocks (cite chunk_ids exactly as shown):\n{evidence_text}\n"
        + "\nWrite the memo JSON now."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `81 passed` (78 + 3).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/agents backend/tests/test_prompts.py
git commit -m "feat(d2): agent prompts module"
```

---

### Task 5: EvidenceManager (the deterministic Researcher) + corpus tool sink

Spec §3.6 context_budget semantics (trim lowest-score first, emit `context_trim`) and §3.1's Researcher stage. Queries come from the Planner's tool calls; this stage owns evidence dedup and budget.

**Files:**
- Create: `backend/hindsight/agents/researcher.py`
- Modify: `backend/hindsight/tools/corpus_search.py` (optional `evidence_sink` param)
- Test: `backend/tests/test_researcher.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_researcher.py`:

```python
from datetime import date

from hindsight.agents.researcher import EvidenceManager, estimate_tokens
from hindsight.data.models import Chunk, ScoredChunk
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder


def sc(cid: str, score: float, text: str = "word " * 100) -> ScoredChunk:
    return ScoredChunk(
        chunk=Chunk(
            chunk_id=cid, doc_id=cid, title=cid,
            published_at=date(2025, 5, 1), text=text,
        ),
        score=score,
    )


def test_dedupe_keeps_best_score():
    em = EvidenceManager(context_budget=100000)
    em.add_results([sc("a::000", 1.0)])
    em.add_results([sc("a::000", 3.0), sc("b::000", 2.0)])
    bundle = em.bundle()
    assert [c.chunk_id for c in bundle] == ["a::000", "b::000"]  # sorted by score desc


def test_bundle_respects_budget_and_emits_trim(tmp_path):
    text = "x" * 400  # ~100 tokens each
    em = EvidenceManager(context_budget=250)
    em.add_results([sc("a::000", 3.0, text), sc("b::000", 2.0, text), sc("c::000", 1.0, text)])
    rec = TraceRecorder(run_dir=tmp_path)
    bundle = em.bundle(trace=rec)
    assert [c.chunk_id for c in bundle] == ["a::000", "b::000"]
    trims = [e for e in rec.events if e.type == "context_trim"]
    assert len(trims) == 1
    assert trims[0].payload["chunk_id"] == "c::000"


def test_bundle_always_keeps_at_least_one():
    em = EvidenceManager(context_budget=1)
    em.add_results([sc("a::000", 1.0, "x" * 4000)])
    assert len(em.bundle()) == 1


def test_corpus_tool_feeds_sink():
    from hindsight.rag.bm25_retriever import BM25Retriever
    from hindsight.sandbox.audit import AuditLog
    from hindsight.sandbox.gate import SandboxedCorpus
    from hindsight.tools.corpus_search import make_corpus_tool

    chunk = Chunk(
        chunk_id="a::000", doc_id="a", title="t",
        published_at=date(2025, 5, 1), text="nvidia data center demand",
    )
    corpus = SandboxedCorpus(
        BM25Retriever([chunk]), as_of=date(2025, 5, 22), audit=AuditLog()
    )
    em = EvidenceManager(context_budget=100000)
    spec = make_corpus_tool(corpus, evidence_sink=em)
    spec.fn(query="nvidia demand")
    assert em.chunk_ids() == {"a::000"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_researcher.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/agents/researcher.py`**

```python
"""Evidence manager — the deterministic 'Researcher' stage.

Deliberately non-LLM: search queries come from the Planner's tool calls;
this stage owns evidence dedup and context_budget trimming (spec §3.6).
The failure mode it isolates is retrieval coverage, which is measured by
the judge's retrieval_sufficiency score, not by an extra LLM role.
"""
from __future__ import annotations

from hindsight.data.models import Chunk, ScoredChunk
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class EvidenceManager:
    def __init__(self, context_budget: int):
        self._budget = context_budget
        self._best: dict[str, ScoredChunk] = {}

    def add_results(self, results: list[ScoredChunk]) -> None:
        for s in results:
            cur = self._best.get(s.chunk.chunk_id)
            if cur is None or s.score > cur.score:
                self._best[s.chunk.chunk_id] = s

    def chunk_ids(self) -> set[str]:
        return set(self._best)

    def evidence_map(self) -> dict[str, Chunk]:
        return {cid: s.chunk for cid, s in self._best.items()}

    def bundle(self, trace: TraceRecorder | None = None) -> list[Chunk]:
        """Greedy best-fit packing in descending score order: each chunk is kept
        iff it fits the remaining budget. A lower-scored small chunk can survive
        where a pricier higher-scored one didn't (score-density beats strict
        rank truncation). Caveat: a single oversized top-ranked chunk can
        consume the whole budget and starve smaller lower-ranked chunks.
        Every dropped chunk emits a context_trim event."""
        ranked = sorted(self._best.values(), key=lambda s: s.score, reverse=True)
        kept: list[Chunk] = []
        used = 0
        for s in ranked:
            cost = estimate_tokens(s.chunk.text)
            if kept and used + cost > self._budget:
                if trace is not None:
                    trace.emit(
                        TraceEvent(
                            type="context_trim",
                            agent="researcher",
                            payload={
                                "chunk_id": s.chunk.chunk_id,
                                "score": round(s.score, 3),
                                "reason": f"context_budget {self._budget} exceeded",
                            },
                        )
                    )
                continue
            kept.append(s.chunk)
            used += cost
        return kept
```

- [ ] **Step 4: Modify `backend/hindsight/tools/corpus_search.py`**

Change the factory signature and add the sink hook (two edits):

```python
def make_corpus_tool(corpus: SandboxedCorpus, evidence_sink=None) -> ToolSpec:
    def corpus_search(query: str, top_k: int = 5) -> str:
        results = corpus.search(query, top_k=top_k)
        if evidence_sink is not None:
            evidence_sink.add_results(results)
        ...  # rest unchanged
```

(`evidence_sink` is duck-typed — anything with `add_results(list[ScoredChunk])`; no import needed, no cycle.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `85 passed` (81 + 4).

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/agents/researcher.py backend/hindsight/tools/corpus_search.py backend/tests/test_researcher.py
git commit -m "feat(d2): evidence manager with context-budget trimming"
```

---

### Task 6: Planner (bounded ReAct, native function calling) + test stubs

**Files:**
- Create: `backend/tests/llm_stubs.py` (shared scripted-transport helpers, not a test file)
- Create: `backend/hindsight/agents/planner.py`
- Test: `backend/tests/test_planner.py`

- [ ] **Step 1: Write `backend/tests/llm_stubs.py`**

```python
"""Scripted fake LLM transports for agent tests. No network, ever."""
from __future__ import annotations

import json


def content_response(text: str, prompt_tokens: int = 50, completion_tokens: int = 20) -> dict:
    return {
        "choices": [
            {"message": {"role": "assistant", "content": text, "tool_calls": None}}
        ],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def tool_call_response(name: str, args: dict, call_id: str = "call_1") -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": json.dumps(args)},
                        }
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 10},
    }


class ScriptedTransport:
    """Returns queued responses in order; records every request it received."""

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, request: dict) -> dict:
        self.requests.append(request)
        if not self._responses:
            raise AssertionError("ScriptedTransport exhausted — unexpected extra LLM call")
        return self._responses.pop(0)
```

- [ ] **Step 2: Write the failing tests**

`backend/tests/test_planner.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_planner.py -q`
Expected: FAIL — `ModuleNotFoundError: hindsight.agents.planner`

- [ ] **Step 4: Write `backend/hindsight/agents/planner.py`**

```python
"""Bounded ReAct planner: native function calling, deterministic dispatch.

The loop is a plain for-range — the LLM decides WHAT to call, never HOW
often the loop spins (spec §3.1: determinism over autonomy)."""
from __future__ import annotations

import json
from typing import Any

from hindsight.agents.prompts import PLANNER_SYSTEM
from hindsight.llm.recording import RecordingLLMClient
from hindsight.tools.registry import ToolRegistry, ToolSpec, safe_call
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder

FINISH_TOOL = ToolSpec(
    name="finish_research",
    description="Call when the gathered evidence is sufficient to write the memo.",
    parameters={
        "type": "object",
        "properties": {"reason": {"type": "string"}},
        "required": ["reason"],
    },
    fn=lambda reason="done": json.dumps({"ok": True, "reason": reason}),
)


def run_planner(
    llm: RecordingLLMClient,
    registry: ToolRegistry,
    user_brief: str,
    max_steps: int,
    temperature: float,
    trace: TraceRecorder,
    ledger: CostLedger,
) -> None:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": user_brief},
    ]
    tools = registry.openai_specs()
    for step in range(max_steps):
        # list(messages): freeze this request's view — the live list keeps growing
        # and passing it by reference would alias recorded requests to the final state
        resp = llm.chat(messages=list(messages), tools=tools, temperature=temperature)
        usage = resp.get("usage") or {}
        ledger.add(
            "planner", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        )
        msg = resp["choices"][0]["message"]
        calls = msg.get("tool_calls") or []
        trace.emit(
            TraceEvent(
                type="plan_step",
                agent="planner",
                payload={
                    "step": step,
                    "thought": msg.get("content") or "",
                    "n_tool_calls": len(calls),
                },
                tokens=usage.get("completion_tokens", 0),
            )
        )
        if not calls:
            break  # model answered in prose; planning ends
        messages.append(
            {"role": "assistant", "content": msg.get("content"), "tool_calls": calls}
        )
        finished = False
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError as exc:
                args = {}
                result = json.dumps({"error": f"unparseable arguments: {exc}"})
            else:
                result = safe_call(registry, name, args)
            trace.emit(
                TraceEvent(
                    type="tool_call", agent="planner", payload={"tool": name, "args": args}
                )
            )
            trace.emit(
                TraceEvent(
                    type="tool_result",
                    agent="planner",
                    payload={"tool": name, "result": result[:2000]},
                )
            )
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": result}
            )
            if name == "finish_research":
                finished = True
        if finished:
            break
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `89 passed` (85 + 4).

- [ ] **Step 6: Commit**

```bash
git add backend/tests/llm_stubs.py backend/hindsight/agents/planner.py backend/tests/test_planner.py
git commit -m "feat(d2): bounded ReAct planner with native function calling"
```

---

### Task 7: Analyst + Critic three-layer validation loop

Spec §3.1 Critic: ① schema (pydantic) → ② mechanical consistency → ③ semantic LLM check; failures feed back to the Analyst, ≤2 retries, then `unverified`.

> Review-driven additions beyond this section's blocks (repo is authoritative): `test_critic_loop.py` carries 5 extra tests (fail-closed unparseable critic, fence-with-space/prose wrapping, bare-prose JSON, structural exhaustion, retry-request uniqueness); `critic.py` includes the fail-closed except branch, robust `strip_fence`, and attempt-prefixed feedback shown in the amended blocks below.

**Files:**
- Create: `backend/hindsight/agents/analyst.py`
- Create: `backend/hindsight/agents/critic.py`
- Test: `backend/tests/test_critic_loop.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_critic_loop.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_critic_loop.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/agents/analyst.py`**

```python
"""Analyst: one LLM call turning the evidence bundle into a memo JSON."""
from __future__ import annotations

from hindsight.agents.prompts import ANALYST_SYSTEM, analyst_user_prompt
from hindsight.data.models import CaseMeta, Chunk
from hindsight.llm.recording import RecordingLLMClient
from hindsight.trace.cost_ledger import CostLedger

_EVIDENCE_CHARS = 1500


def render_evidence(chunks: list[Chunk]) -> str:
    return "\n\n".join(
        f"[{c.chunk_id}] ({c.published_at.isoformat()}) {c.title}\n{c.text[:_EVIDENCE_CHARS]}"
        for c in chunks
    )


def run_analyst(
    llm: RecordingLLMClient,
    evidence_chunks: list[Chunk],
    case: CaseMeta,
    market_summary: str,
    temperature: float,
    ledger: CostLedger,
    feedback: str | None = None,
) -> str:
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM},
        {
            "role": "user",
            "content": analyst_user_prompt(case, render_evidence(evidence_chunks), market_summary),
        },
    ]
    if feedback:
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous memo failed validation:\n"
                    + feedback
                    + "\nReturn the corrected JSON only."
                ),
            }
        )
    resp = llm.chat(messages=messages, temperature=temperature)
    usage = resp.get("usage") or {}
    ledger.add("analyst", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    return resp["choices"][0]["message"].get("content") or ""
```

- [ ] **Step 4: Write `backend/hindsight/agents/critic.py`**

```python
"""Critic: three-layer memo validation with feedback-retry (spec §3.1).

Layer 1: JSON + pydantic schema. Layer 2: mechanical consistency (evidence
ids exist, ticker matches, horizon within the case window). Layer 3: one
LLM semantic check. Failures feed back to the Analyst, max 2 retries; a
structurally-valid memo that never passes layer 3 is returned unverified.
"""
from __future__ import annotations

import json

from pydantic import ValidationError

from hindsight.agents.analyst import render_evidence, run_analyst
from hindsight.agents.prompts import CRITIC_SEMANTIC_SYSTEM
from hindsight.data.models import CaseMeta, Chunk
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import Memo
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder

MAX_RETRIES = 2


def strip_fence(text: str) -> str:
    """Extract the JSON payload from an LLM reply: tolerates ```json fences
    (with or without a space/language tag), prose before/after the fence,
    and bare prose around a top-level JSON object."""
    text = text.strip()
    if "```" in text:
        start = text.find("```")
        rest = text[start + 3 :].lstrip()
        if rest[:4].lower() == "json":
            rest = rest[4:]
        end = rest.find("```")
        if end != -1:
            rest = rest[:end]
        return rest.strip()
    if not text.startswith("{") and "{" in text and text.rfind("}") > text.find("{"):
        return text[text.find("{") : text.rfind("}") + 1]
    return text


def structural_check(
    raw: str, valid_evidence_ids: set[str], case: CaseMeta
) -> tuple[Memo | None, list[str]]:
    try:
        memo = Memo.model_validate_json(strip_fence(raw))
    except (ValidationError, ValueError) as exc:
        return None, [f"schema: {str(exc)[:800]}"]
    errors: list[str] = []
    for claim in memo.claims:
        if claim.ticker != case.ticker:
            errors.append(f"claim {claim.claim_id}: ticker {claim.ticker} != case ticker {case.ticker}")
        if claim.horizon_days > case.outcome_window_days:
            errors.append(
                f"claim {claim.claim_id}: horizon {claim.horizon_days} exceeds case window {case.outcome_window_days}"
            )
        for eid in claim.evidence:
            if eid not in valid_evidence_ids:
                errors.append(f"claim {claim.claim_id}: unknown evidence id {eid}")
    return (memo, errors) if not errors else (None, errors)


def semantic_check(
    llm: RecordingLLMClient,
    memo: Memo,
    evidence_chunks: list[Chunk],
    temperature: float,
    ledger: CostLedger,
) -> tuple[bool, list[str]]:
    user = (
        "Memo JSON:\n" + memo.model_dump_json() + "\n\nCited evidence:\n"
        + render_evidence(evidence_chunks)
    )
    resp = llm.chat(
        messages=[
            {"role": "system", "content": CRITIC_SEMANTIC_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    usage = resp.get("usage") or {}
    ledger.add("critic", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    text = strip_fence(resp["choices"][0]["message"].get("content") or "")
    try:
        verdict = json.loads(text)
        return bool(verdict.get("ok")), [str(p) for p in verdict.get("problems", [])]
    except (json.JSONDecodeError, AttributeError):
        # fail CLOSED: an unreviewable verdict consumes a retry; repeated
        # failures leave the memo marked unverified instead of silently passing
        return False, [
            "semantic review could not parse its verdict; regenerate the memo "
            "JSON exactly (unchanged if you believe it is correct)"
        ]


def produce_memo(
    llm: RecordingLLMClient,
    evidence_chunks: list[Chunk],
    case: CaseMeta,
    market_summary: str,
    temperature: float,
    trace: TraceRecorder,
    ledger: CostLedger,
) -> tuple[Memo | None, bool]:
    valid_ids = {c.chunk_id for c in evidence_chunks}
    feedback: str | None = None
    last_structurally_valid: Memo | None = None
    for attempt in range(1 + MAX_RETRIES):
        raw = run_analyst(
            llm, evidence_chunks, case, market_summary, temperature, ledger, feedback
        )
        memo, errors = structural_check(raw, valid_ids, case)
        if memo is None:
            trace.emit(
                TraceEvent(
                    type="validation",
                    agent="critic",
                    payload={"attempt": attempt, "layer": "structural", "errors": errors[:6]},
                )
            )
            feedback = f"(attempt {attempt + 1}) " + "\n".join(errors[:6])
            continue
        last_structurally_valid = memo
        ok, problems = semantic_check(llm, memo, evidence_chunks, temperature, ledger)
        trace.emit(
            TraceEvent(
                type="validation",
                agent="critic",
                payload={"attempt": attempt, "layer": "semantic", "ok": ok, "problems": problems[:6]},
            )
        )
        if ok:
            return memo, False
        feedback = f"(attempt {attempt + 1}) " + "\n".join(problems[:6])
    return last_structurally_valid, True  # unverified (or None if never structural)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `95 passed` (89 + 6).

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/agents/analyst.py backend/hindsight/agents/critic.py backend/tests/test_critic_loop.py
git commit -m "feat(d2): analyst and three-layer critic validation loop"
```

---

### Task 8: Outcome grader (spec §3.3 rules 1-6)

Pure functions, no LLM, no sandbox — grading is entitled to realized data; the module docstring says so explicitly (interview talking point).

**Files:**
- Create: `backend/hindsight/eval/__init__.py` (empty)
- Create: `backend/hindsight/eval/outcome_grader.py`
- Test: `backend/tests/test_grader.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_grader.py`:

```python
import math
from datetime import date, timedelta

from hindsight.data.models import Bar
from hindsight.eval.outcome_grader import GradedClaim, aggregate, grade_claim
from hindsight.schemas import Claim, ClaimType, GradeStatus


def make_bars(closes: list[float], start: date = date(2025, 5, 1)) -> list[Bar]:
    return [
        Bar(date=start + timedelta(days=i), open=c, high=c, low=c, close=c, volume=1)
        for i, c in enumerate(closes)
    ]


def direction_claim(threshold=5.0, horizon=2, direction="up", confidence=0.7):
    return Claim(
        claim_id="c1",
        statement="s",
        type=ClaimType.direction,
        ticker="NVDA",
        horizon_days=horizon,
        prediction={"direction": direction, "threshold_pct": threshold},
        confidence=confidence,
        evidence=["e::000"],
    )


AS_OF = date(2025, 5, 3)  # bars[2] is the baseline (start + 2 days)


def test_direction_up_hit_at_exact_threshold():
    bars = make_bars([100, 100, 100, 102, 105.0])  # baseline 100, horizon 2 -> 105
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.hit  # r == threshold -> hit (rule 3: >=)
    assert math.isclose(g.realized_return_pct, 5.0)


def test_direction_up_miss_below_threshold():
    bars = make_bars([100, 100, 100, 102, 104.9])
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.miss


def test_direction_down_hit():
    bars = make_bars([100, 100, 100, 96, 94.0])
    g = grade_claim(direction_claim(direction="down", threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.hit


def test_at_horizon_end_not_path_touch():
    # touches +6% intraday path at bar 3 but ends at +1% -> miss (rule 3)
    bars = make_bars([100, 100, 100, 106, 101.0])
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.miss


def test_nontrading_asof_uses_prior_close():
    bars = make_bars([100, 100, 100, 102, 105.0])
    weekend = AS_OF + timedelta(hours=0)  # same day; simulate gap by removing bar
    bars_gap = [b for b in bars if b.date != AS_OF]  # as_of date itself has no bar
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars_gap, AS_OF)
    # baseline falls back to bars[1] (100); horizon counts bars after it: 102 then 105
    assert g.status == GradeStatus.hit


def test_horizon_beyond_data_is_ungradable():
    bars = make_bars([100, 100, 100, 102])
    g = grade_claim(direction_claim(horizon=5), bars, AS_OF)
    assert g.status == GradeStatus.ungradable


def test_no_baseline_is_ungradable():
    bars = make_bars([100, 100], start=date(2025, 6, 1))  # all after as_of
    g = grade_claim(direction_claim(), bars, AS_OF)
    assert g.status == GradeStatus.ungradable


def test_magnitude_interval_closed_endpoints():
    bars = make_bars([100, 100, 100, 102, 108.0])
    claim = Claim(
        claim_id="m1", statement="s", type=ClaimType.magnitude, ticker="NVDA",
        horizon_days=2, prediction={"low_pct": 2.0, "high_pct": 8.0},
        confidence=0.5, evidence=["e::000"],
    )
    assert grade_claim(claim, bars, AS_OF).status == GradeStatus.hit  # 8.0 == high -> hit
    bars_out = make_bars([100, 100, 100, 102, 108.1])
    assert grade_claim(claim, bars_out, AS_OF).status == GradeStatus.miss


def test_split_adjusted_series_grades_smoothly():
    # A 10:1 split inside the outcome window: the frozen snapshot is
    # auto-adjusted so closes are continuous — grading must NOT see -90%.
    bars = make_bars([100, 100, 100, 101, 103.0])  # adjusted series, split invisible
    g = grade_claim(direction_claim(threshold=2.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.hit
    assert g.realized_return_pct > 0


def test_volatility_above_hits_in_high_vol_window():
    import random

    rng = random.Random(7)
    quiet = [100.0]
    for _ in range(300):
        quiet.append(quiet[-1] * (1 + rng.uniform(-0.002, 0.002)))
    wild = [quiet[-1]]
    for _ in range(10):
        wild.append(wild[-1] * (1 + rng.uniform(-0.08, 0.08)))
    closes = quiet + wild[1:]
    bars = make_bars(closes, start=date(2024, 6, 1))
    as_of = bars[300].date
    claim = Claim(
        claim_id="v1", statement="s", type=ClaimType.volatility, ticker="NVDA",
        horizon_days=10, prediction={"relation": "above", "percentile": 90},
        confidence=0.6, evidence=["e::000"],
    )
    assert grade_claim(claim, bars, as_of).status == GradeStatus.hit


def test_volatility_insufficient_history_ungradable():
    bars = make_bars([100.0] * 15)
    claim = Claim(
        claim_id="v1", statement="s", type=ClaimType.volatility, ticker="NVDA",
        horizon_days=3, prediction={"relation": "above", "percentile": 80},
        confidence=0.6, evidence=["e::000"],
    )
    assert grade_claim(claim, bars, bars[5].date).status == GradeStatus.ungradable


def test_aggregate_brier_and_calibration():
    graded = [
        GradedClaim(direction_claim(confidence=0.9), GradeStatus.hit, 6.0, ""),
        GradedClaim(direction_claim(confidence=0.9), GradeStatus.miss, 1.0, ""),
        GradedClaim(direction_claim(confidence=0.1), GradeStatus.miss, -1.0, ""),
        GradedClaim(direction_claim(confidence=0.5), GradeStatus.ungradable, None, ""),
    ]
    agg = aggregate(graded)
    assert agg["n_claims"] == 4
    assert agg["n_gradable"] == 3
    assert math.isclose(agg["hit_rate"], 1 / 3)
    expected_brier = ((0.9 - 1) ** 2 + (0.9 - 0) ** 2 + (0.1 - 0) ** 2) / 3
    assert math.isclose(agg["brier"], expected_brier)
    buckets = {(b["lo"], b["hi"]): b for b in agg["calibration"]}
    assert buckets[(0.8, 1.0)]["n"] == 2
    assert math.isclose(buckets[(0.8, 1.0)]["hit_rate"], 0.5)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_grader.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/eval/outcome_grader.py`** (create empty `eval/__init__.py` too)

```python
"""Outcome grader: mechanical claim judgment per spec §3.3 rules 1-6.

Runs deliberately OUTSIDE the time sandbox — evaluation is entitled to
realized data. The boundary is the orchestrator: agents never see this
module's inputs. Pure functions; no LLM, no I/O.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from hindsight.data.models import Bar
from hindsight.schemas import (
    Claim,
    DirectionPrediction,
    GradeStatus,
    MagnitudePrediction,
    VolatilityPrediction,
)

MIN_VOL_SAMPLES = 20
HISTORY_BARS = 252


@dataclass
class GradedClaim:
    claim: Claim
    status: GradeStatus
    realized_return_pct: float | None
    detail: str


def _baseline_index(bars: list[Bar], as_of: date) -> int | None:
    """Rule 1: baseline P0 = last close at or before as_of."""
    idx = None
    for i, b in enumerate(bars):
        if b.date <= as_of:
            idx = i
        else:
            break
    return idx


def _std_log_returns(closes: list[float]) -> float:
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0]
    if not rets:
        return 0.0
    mean = sum(rets) / len(rets)
    return math.sqrt(sum((r - mean) ** 2 for r in rets) / len(rets))


def _percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    k = (len(xs) - 1) * p / 100
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def grade_claim(claim: Claim, bars: list[Bar], as_of: date) -> GradedClaim:
    bars = sorted(bars, key=lambda b: b.date)  # defensive: grading correctness must not depend on a caller three modules away keeping bars sorted
    i0 = _baseline_index(bars, as_of)
    if i0 is None:
        return GradedClaim(claim, GradeStatus.ungradable, None, "no baseline bar at or before as_of")
    p0 = bars[i0].close
    hi = i0 + claim.horizon_days  # rule 2: Nth bar after the baseline bar
    if hi >= len(bars):
        return GradedClaim(
            claim,
            GradeStatus.ungradable,
            None,
            f"bars cover {len(bars) - 1 - i0} trading days after as_of; horizon {claim.horizon_days}",
        )
    r = bars[hi].close / p0 - 1
    pct = r * 100
    pred = claim.prediction
    if isinstance(pred, DirectionPrediction):
        # rule 3: at-horizon-end, >= for up, <= -threshold for down.
        # Boundary comparisons use math.isclose first: pct is derived from
        # bars[hi].close / p0 - 1, and binary floats mean an exact-percent
        # baseline (e.g. a 108.0/100 close) can land a few ULPs off the
        # threshold (8.000000000000007 instead of 8.0). Without the
        # tolerance, a claim landing exactly on its stated threshold is
        # spuriously graded a miss depending on rounding direction, which
        # would contradict the ">=" / closed-interval semantics rule 3/4
        # promise. abs_tol=1e-9 pp is far below any real price-derived
        # difference, so it never masks a genuine miss.
        if pred.direction == "up":
            threshold = pred.threshold_pct / 100
            hit = r >= threshold or math.isclose(r, threshold, abs_tol=1e-9)
        else:
            threshold = -pred.threshold_pct / 100
            hit = r <= threshold or math.isclose(r, threshold, abs_tol=1e-9)
        return GradedClaim(
            claim,
            GradeStatus.hit if hit else GradeStatus.miss,
            pct,
            f"horizon-end return {pct:+.2f}% vs {pred.direction} {pred.threshold_pct}%",
        )
    if isinstance(pred, MagnitudePrediction):
        # rule 4: closed interval [low_pct, high_pct] — same float-boundary
        # tolerance as rule 3 (see comment above) applied to both endpoints.
        hit = (pred.low_pct <= pct <= pred.high_pct) or math.isclose(
            pct, pred.low_pct, abs_tol=1e-9
        ) or math.isclose(pct, pred.high_pct, abs_tol=1e-9)
        # NOTE: rule 3 compares in ratio-space, rule 4 in pct-space (100x scale
        # difference in effective tolerance). Verified harmless: real float noise
        # tops out ~3e-14 in ratio space, >1000x below the tighter bound.
        return GradedClaim(
            claim,
            GradeStatus.hit if hit else GradeStatus.miss,
            pct,
            f"horizon-end return {pct:+.2f}% vs [{pred.low_pct}, {pred.high_pct}]",
        )
    assert isinstance(pred, VolatilityPrediction)
    # rule 5: realized window std of log returns vs rolling same-length windows
    window = [b.close for b in bars[i0 : hi + 1]]
    realized = _std_log_returns(window)
    history = [b.close for b in bars[: i0 + 1]][-(HISTORY_BARS + 1) :]
    n = claim.horizon_days
    samples = [
        _std_log_returns(history[j : j + n + 1]) for j in range(len(history) - n)
    ]
    if len(samples) < MIN_VOL_SAMPLES:
        return GradedClaim(claim, GradeStatus.ungradable, pct, "insufficient history for volatility percentile")
    threshold = _percentile(samples, pred.percentile)
    hit = realized > threshold if pred.relation == "above" else realized < threshold
    return GradedClaim(
        claim,
        GradeStatus.hit if hit else GradeStatus.miss,
        pct,
        f"realized vol {realized:.5f} vs p{pred.percentile:g} {threshold:.5f} ({pred.relation})",
    )


def grade_claims(claims: list[Claim], bars: list[Bar], as_of: date) -> list[GradedClaim]:
    return [grade_claim(c, bars, as_of) for c in claims]


_BUCKETS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]


def aggregate(graded: list[GradedClaim]) -> dict:
    gradable = [g for g in graded if g.status != GradeStatus.ungradable]
    hits = [g for g in gradable if g.status == GradeStatus.hit]
    brier = (
        sum(
            (g.claim.confidence - (1.0 if g.status == GradeStatus.hit else 0.0)) ** 2
            for g in gradable
        )
        / len(gradable)
        if gradable
        else None
    )
    calibration = []
    for lo, hi in _BUCKETS:
        inb = [
            g
            for g in gradable
            if (lo <= g.claim.confidence < hi) or (hi == 1.0 and g.claim.confidence == 1.0)
        ]
        calibration.append(
            {
                "lo": lo,
                "hi": hi,
                "n": len(inb),
                "avg_confidence": sum(g.claim.confidence for g in inb) / len(inb) if inb else None,
                "hit_rate": (
                    sum(1 for g in inb if g.status == GradeStatus.hit) / len(inb) if inb else None
                ),
            }
        )
    return {
        "n_claims": len(graded),
        "n_gradable": len(gradable),
        "n_hit": len(hits),
        "hit_rate": len(hits) / len(gradable) if gradable else None,
        "brier": brier,
        "calibration": calibration,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `107 passed` (95 + 12).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/eval backend/tests/test_grader.py
git commit -m "feat(d2): outcome grader implementing spec 3.3 grading semantics"
```

---

### Task 9: LLM judge + failure attribution

Spec §3.4-B: judge receives A-track outcomes; attribution enum for every missed claim; usage extracted with explicit keys (carryover ⑦).

**Files:**
- Create: `backend/hindsight/eval/judge.py`
- Test: `backend/tests/test_judge.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_judge.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_judge.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/eval/judge.py`**

```python
"""Process judge: grounding, consistency, sufficiency + failure attribution.

The judge sees the A-track outcomes (spec §3.4: outcome grader runs first)
so it can attribute every miss to evidence_missing / misread_evidence /
reasonable_but_wrong — the sharpest answer to "why did it behave that way".
Self-preference caveat documented in the methodology doc, not here.
"""
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from hindsight.agents.critic import strip_fence
from hindsight.agents.prompts import JUDGE_SYSTEM
from hindsight.data.models import Chunk
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import Memo
from hindsight.trace.cost_ledger import CostLedger


class ClaimGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    supported: bool
    comment: str = ""


class Attribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    attribution: Literal["evidence_missing", "misread_evidence", "reasonable_but_wrong"]


class JudgeReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grounding: list[ClaimGrounding]
    reasoning_consistency: int = Field(ge=1, le=5)
    retrieval_sufficiency: int = Field(ge=1, le=5)
    attributions: list[Attribution] = Field(default_factory=list)


def _outcome_lines(graded: list[GradedClaim]) -> str:
    return "\n".join(
        f"- {g.claim.claim_id}: {g.status.value}"
        + (f" (realized {g.realized_return_pct:+.2f}%)" if g.realized_return_pct is not None else "")
        + f" — {g.detail}"
        for g in graded
    )


def _evidence_lines(memo: Memo, evidence_map: dict[str, Chunk]) -> str:
    cited = {eid for c in memo.claims for eid in c.evidence}
    blocks = []
    for eid in sorted(cited):
        chunk = evidence_map.get(eid)
        if chunk is not None:
            blocks.append(f"[{eid}] {chunk.text[:1200]}")
    return "\n\n".join(blocks)


def run_judge(
    llm: RecordingLLMClient,
    memo: Memo,
    graded: list[GradedClaim],
    evidence_map: dict[str, Chunk],
    temperature: float,
    ledger: CostLedger,
) -> JudgeReport | None:
    user = (
        "Memo JSON:\n" + memo.model_dump_json()
        + "\n\nClaim outcomes:\n" + _outcome_lines(graded)
        + "\n\nCited evidence:\n" + _evidence_lines(memo, evidence_map)
    )
    feedback = ""
    for _ in range(2):
        resp = llm.chat(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": user + feedback},
            ],
            temperature=temperature,
        )
        usage = resp.get("usage") or {}
        ledger.add("judge", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        text = strip_fence(resp["choices"][0]["message"].get("content") or "")
        try:
            return JudgeReport.model_validate_json(text)
        except (ValidationError, ValueError) as exc:
            feedback = f"\n\nYour previous reply was invalid ({str(exc)[:300]}). Return ONLY the JSON object."
    return None


def judge_scores(report: JudgeReport | None) -> dict:
    if report is None:
        return {"judge_failed": True}
    total = len(report.grounding)
    supported = sum(1 for g in report.grounding if g.supported)
    return {
        "judge_failed": False,
        "grounding_rate": supported / total if total else None,
        "reasoning_consistency": report.reasoning_consistency,
        "retrieval_sufficiency": report.retrieval_sufficiency,
        "attributions": {a.claim_id: a.attribution for a in report.attributions},
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `111 passed` (107 + 4).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/eval/judge.py backend/tests/test_judge.py
git commit -m "feat(d2): LLM judge with grounding scores and failure attribution"
```

---

### Task 10: Contamination probe

Spec §3.2(b): one hash-stable LLM call per (ticker, as_of) asking what the model already knows about the future. Stored, displayed, never used by agents.

**Files:**
- Create: `backend/hindsight/eval/contamination.py`
- Test: `backend/tests/test_contamination.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_contamination.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_contamination.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/eval/contamination.py`**

```python
"""Parametric-memory contamination probe (spec §3.2 known limitation).

Asks the model directly what it knows about the ticker AFTER as_of. The
answer is stored per run and surfaced on the Eval Dashboard as a case-level
contamination indicator. Deterministic prompt + temperature 0 means the
recording layer collapses repeat probes into a single real API call.
"""
from __future__ import annotations

from datetime import date

from hindsight.agents.prompts import PROBE_PROMPT
from hindsight.llm.recording import RecordingLLMClient
from hindsight.trace.cost_ledger import CostLedger


def run_contamination_probe(
    llm: RecordingLLMClient, ticker: str, as_of: date, ledger: CostLedger
) -> str:
    resp = llm.chat(
        messages=[
            {
                "role": "user",
                "content": PROBE_PROMPT.format(ticker=ticker, as_of=as_of.isoformat()),
            }
        ],
        temperature=0.0,
    )
    usage = resp.get("usage") or {}
    ledger.add("probe", usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    return resp["choices"][0]["message"].get("content") or ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `112 passed` (111 + 1).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/eval/contamination.py backend/tests/test_contamination.py
git commit -m "feat(d2): parametric-memory contamination probe"
```

---

### Task 11: Experience library (cards, builder, time-gated retriever) + memory-channel leakage tests

Spec §3.5 in full: write-always, `memory_on` gates reads only, three hard retrieval constraints, BM25 over feature text, structured lesson.

**Files:**
- Create: `backend/hindsight/memory/__init__.py` (empty)
- Create: `backend/hindsight/memory/experience.py`
- Test: `backend/tests/test_experience.py`
- Modify: `backend/tests/test_sandbox_leakage.py` (memory-channel section)

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_experience.py`:

```python
import json
from datetime import date

from hindsight.data.models import CaseMeta
from hindsight.eval.judge import Attribution, ClaimGrounding, JudgeReport
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.memory.experience import (
    ExperienceCard,
    ExperienceRetriever,
    build_card,
    render_cards,
)
from hindsight.schemas import Claim, ClaimType, GradeStatus
from hindsight.store.db import Store


def make_graded(status=GradeStatus.miss):
    claim = Claim(
        claim_id="c1", statement="NVDA up 5% in 20d", type=ClaimType.direction,
        ticker="NVDA", horizon_days=20,
        prediction={"direction": "up", "threshold_pct": 5.0},
        confidence=0.8, evidence=["a::000"],
    )
    return GradedClaim(claim, status, -2.0 if status == GradeStatus.miss else 6.0, "d")


def make_report():
    return JudgeReport(
        grounding=[ClaimGrounding(claim_id="c1", supported=True)],
        reasoning_consistency=4,
        retrieval_sufficiency=3,
        attributions=[Attribution(claim_id="c1", attribution="misread_evidence")],
    )


META = CaseMeta(
    case_id="case_a", title="NVDA earnings", ticker="NVDA",
    as_of=date(2025, 3, 1), outcome_window_days=20, tags=["earnings"],
)


def test_build_card_carries_lesson_and_window():
    card = build_card(META, "r1", [make_graded()], make_report(), date(2025, 4, 15))
    assert card.source_case_id == "case_a"
    assert card.outcome_window_end == date(2025, 4, 15)
    assert card.lesson_attribution == "misread_evidence"
    assert "NVDA" in card.features_text
    assert card.outcomes["c1"]["status"] == "miss"


def test_build_card_all_hits_lesson():
    card = build_card(
        META, "r1", [make_graded(GradeStatus.hit)], make_report(), date(2025, 4, 15)
    )
    assert card.lesson_attribution is None
    assert "held" in card.lesson_text


def test_retriever_ranks_by_similarity(tmp_path):
    store = Store(tmp_path / "h.db")
    r = ExperienceRetriever(store)
    for i, (case_id, feats) in enumerate(
        [("c_nvda", "NVDA earnings semis ai-capex"),
         ("c_tsla", "TSLA delivery autos"),
         ("c_smci", "SMCI filing servers")]
    ):
        card = build_card(
            CaseMeta(case_id=case_id, title=feats, ticker=feats.split()[0],
                     as_of=date(2025, 1, 1), outcome_window_days=5),
            f"r{i}", [make_graded()], make_report(), date(2025, 2, 1),
        )
        r.write(card)
    got = r.retrieve("NVDA earnings ai", as_of=date(2025, 5, 22),
                     exclude_case_id="other", top_k=1)
    assert got[0].source_case_id == "c_nvda"


def test_render_cards_mentions_lesson(tmp_path):
    card = build_card(META, "r1", [make_graded()], make_report(), date(2025, 4, 15))
    text = render_cards([card])
    assert "misread_evidence" in text
    assert "NVDA" in text
```

Append to `backend/tests/test_sandbox_leakage.py` (memory channel — spec §9 third channel):

```python
def _write_exp(store, case_id, as_of, window_end, feats="NVDA earnings"):
    from hindsight.memory.experience import ExperienceCard

    card = ExperienceCard(
        exp_id=f"e_{case_id}_{window_end}",
        source_case_id=case_id,
        source_run_id="r",
        as_of=as_of,
        outcome_window_end=window_end,
        features_text=feats,
        strategy_summary="s",
        outcomes={},
        lesson_text="l",
    )
    store.insert_experience(
        card.exp_id, card.source_case_id, card.source_run_id,
        card.as_of.isoformat(), card.outcome_window_end.isoformat(),
        card.features_text, card.model_dump_json(),
    )


def test_memory_channel_hides_unclosed_windows(tmp_path):
    from hindsight.memory.experience import ExperienceRetriever
    from hindsight.store.db import Store

    store = Store(tmp_path / "h.db")
    _write_exp(store, "old_case", date(2025, 2, 1), date(2025, 3, 1))
    _write_exp(store, "recent_case", date(2025, 5, 1), date(2025, 6, 30))  # window open at as_of
    got = ExperienceRetriever(store).retrieve(
        "NVDA earnings", as_of=AS_OF, exclude_case_id="current"
    )
    assert {c.source_case_id for c in got} == {"old_case"}


def test_memory_channel_leave_one_out(tmp_path):
    from hindsight.memory.experience import ExperienceRetriever
    from hindsight.store.db import Store

    store = Store(tmp_path / "h.db")
    _write_exp(store, "current", date(2025, 2, 1), date(2025, 3, 1))
    got = ExperienceRetriever(store).retrieve(
        "NVDA earnings", as_of=AS_OF, exclude_case_id="current"
    )
    assert got == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_experience.py tests/test_sandbox_leakage.py -q`
Expected: FAIL — `ModuleNotFoundError: hindsight.memory.experience`

- [ ] **Step 3: Write `backend/hindsight/memory/experience.py`** (create empty `memory/__init__.py` too)

```python
"""Experience library: cross-run Reflexion with a time gate (spec §3.5).

Write-always; RunConfig.memory_on gates READS only. Retrieval enforces
three hard constraints (in SQL, Store.query_experiences): the source run's
outcome window closed at or before the new run's as_of; never the same
case (leave-one-out); optionally only cards existing before a suite
snapshot. BM25 ranking happens only over candidates that pass the gate.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from hindsight.data.models import CaseMeta
from hindsight.eval.judge import JudgeReport
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.rag.bm25_retriever import _tokenize
from hindsight.schemas import GradeStatus
from hindsight.store.db import Store

from rank_bm25 import BM25Okapi


class ExperienceCard(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exp_id: str
    source_case_id: str
    source_run_id: str
    as_of: date
    outcome_window_end: date
    features_text: str
    strategy_summary: str
    outcomes: dict[str, Any]
    lesson_attribution: str | None = None
    lesson_text: str = ""


def build_card(
    case: CaseMeta,
    run_id: str,
    graded: list[GradedClaim],
    report: JudgeReport | None,
    outcome_window_end: date,
) -> ExperienceCard:
    outcomes = {
        g.claim.claim_id: {
            "status": g.status.value,
            "statement": g.claim.statement,
            "confidence": g.claim.confidence,
        }
        for g in graded
    }
    misses = [g for g in graded if g.status == GradeStatus.miss]
    attribution: str | None = None
    if misses and report is not None and report.attributions:
        counts = Counter(a.attribution for a in report.attributions)
        attribution = counts.most_common(1)[0][0]
    if not misses:
        lesson = "Calibration held: graded claims came true at the stated confidence."
    elif attribution:
        lesson = f"Missed claims were mostly {attribution}; adjust research accordingly."
    else:
        lesson = "Claims missed; no attribution available."
    return ExperienceCard(
        exp_id=f"exp_{run_id}",
        source_case_id=case.case_id,
        source_run_id=run_id,
        as_of=case.as_of,
        outcome_window_end=outcome_window_end,
        features_text=f"{case.ticker} {' '.join(case.tags)} {case.title}",
        strategy_summary=f"{len(graded)} claims, "
        f"{sum(1 for g in graded if g.status == GradeStatus.hit)} hit",
        outcomes=outcomes,
        lesson_attribution=attribution,
        lesson_text=lesson,
    )


class ExperienceRetriever:
    def __init__(self, store: Store):
        self._store = store

    def write(self, card: ExperienceCard) -> None:
        self._store.insert_experience(
            card.exp_id,
            card.source_case_id,
            card.source_run_id,
            card.as_of.isoformat(),
            card.outcome_window_end.isoformat(),
            card.features_text,
            card.model_dump_json(),
        )

    def retrieve(
        self,
        features_text: str,
        as_of: date,
        exclude_case_id: str,
        created_before: str | None = None,
        top_k: int = 3,
    ) -> list[ExperienceCard]:
        rows = self._store.query_experiences(
            as_of.isoformat(), exclude_case_id, created_before
        )
        if not rows:
            return []
        cards = [ExperienceCard(**json.loads(r["card_json"])) for r in rows]
        index = BM25Okapi([_tokenize(c.features_text) for c in cards])
        scores = index.get_scores(_tokenize(features_text))
        ranked = sorted(zip(cards, scores), key=lambda p: p[1], reverse=True)
        return [c for c, _ in ranked[: max(1, top_k)]]


def render_cards(cards: list[ExperienceCard]) -> str:
    blocks = []
    for c in cards:
        hits = sum(1 for o in c.outcomes.values() if o.get("status") == "hit")
        blocks.append(
            f"- [{c.source_case_id}] {c.features_text} — {c.strategy_summary} "
            f"({hits}/{len(c.outcomes)} claims hit). Lesson"
            + (f" ({c.lesson_attribution})" if c.lesson_attribution else "")
            + f": {c.lesson_text}"
        )
    return "\n".join(blocks)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `118 passed` (112 + 4 experience + 2 leakage).

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/memory backend/tests/test_experience.py backend/tests/test_sandbox_leakage.py
git commit -m "feat(d2): time-gated experience library with memory-channel leakage tests"
```

---

### Task 12: Orchestrator + run persistence + CLI `run`

The deterministic state machine (spec §3.1): probe → experience → planner → evidence bundle → analyst/critic → grade (outside sandbox) → judge → experience write → persist. Forwards sandbox audit entries into the trace as `audit` events (spec §5).

**Files:**
- Create: `backend/hindsight/agents/orchestrator.py`
- Modify: `backend/hindsight/cli.py` (add `run` subcommand)
- Test: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_orchestrator.py`:

```python
import json
from datetime import date

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_orchestrator.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/agents/orchestrator.py`**

```python
"""The run orchestrator: a deterministic state machine around the agents.

Stage order: contamination probe -> experience retrieval (memory_on) ->
planner (bounded ReAct) -> evidence bundle -> analyst/critic loop ->
outcome grading -> judge -> experience write (always) -> persistence.

Grading reads bars DIRECTLY from the case's frozen snapshot, bypassing the
sandbox on purpose: evaluation is entitled to realized data. Agents never
receive anything derived from that read.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from hindsight.agents.critic import produce_memo
from hindsight.agents.planner import FINISH_TOOL, run_planner
from hindsight.agents.prompts import case_brief, experience_block
from hindsight.agents.researcher import EvidenceManager
from hindsight.data.cases import load_case
from hindsight.eval.contamination import run_contamination_probe
from hindsight.eval.judge import judge_scores, run_judge
from hindsight.eval.outcome_grader import GradedClaim, aggregate, grade_claims
from hindsight.llm.recording import RecordingLLMClient
from hindsight.memory.experience import ExperienceRetriever, build_card, render_cards
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.gate import SandboxedCorpus, SandboxedMarketData
from hindsight.schemas import GradeStatus, Memo, RunConfig
from hindsight.store.db import Store
from hindsight.tools.calc import make_calc_tool
from hindsight.tools.corpus_search import make_corpus_tool
from hindsight.tools.market_data import make_market_tool
from hindsight.tools.registry import ToolRegistry, safe_call
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder

FAR_FUTURE = date(2100, 1, 1)


@dataclass
class RunResult:
    run_id: str
    memo: Memo | None
    scores: dict
    unverified: bool
    run_dir: Path


def _new_run_id(case_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"run_{case_id}_{stamp}_{uuid.uuid4().hex[:6]}"


def _forward_audit(trace: TraceRecorder, audit: AuditLog, start: int) -> int:
    for entry in audit.entries[start:]:
        trace.emit(
            TraceEvent(type="audit", agent="sandbox", payload=entry.model_dump(mode="json"))
        )
    return len(audit.entries)


def _memo_markdown(memo: Memo, graded: list[GradedClaim]) -> str:
    status = {g.claim.claim_id: g for g in graded}
    lines = [
        "# Research memo",
        "",
        "## Background",
        memo.background,
        "",
        "## Bull case",
        memo.bull_case,
        "",
        "## Bear case",
        memo.bear_case,
        "",
        "## Conclusion",
        memo.conclusion,
        "",
        "## Claims",
    ]
    for c in memo.claims:
        g = status.get(c.claim_id)
        verdict = f" -> **{g.status.value}** ({g.detail})" if g else ""
        lines.append(
            f"- `{c.claim_id}` [{c.type.value}, {c.horizon_days}d, conf {c.confidence}] "
            f"{c.statement}{verdict}"
        )
    return "\n".join(lines) + "\n"


def run_research(
    case_dir: Path,
    config: RunConfig,
    *,
    llm: RecordingLLMClient,
    store: Store,
    runs_root: Path,
    suite_id: str | None = None,
    suite_started_at: str | None = None,
) -> RunResult:
    case = load_case(Path(case_dir))
    as_of = case.meta.as_of
    run_id = _new_run_id(case.meta.case_id)
    run_dir = Path(runs_root) / run_id
    trace = TraceRecorder(run_dir=run_dir)
    ledger = CostLedger()
    audit = AuditLog()
    audit_seen = 0

    store.upsert_run(run_id, case.meta.case_id, config.model_dump_json(), "running", suite_id=suite_id)

    corpus = SandboxedCorpus(BM25Retriever(case.chunks), as_of=as_of, audit=audit)
    market = SandboxedMarketData(case.bars_source, as_of=as_of, audit=audit)
    evidence = EvidenceManager(config.context_budget)
    registry = ToolRegistry()
    registry.register(make_corpus_tool(corpus, evidence_sink=evidence))
    registry.register(make_market_tool(market, case.meta.ticker))
    registry.register(make_calc_tool())
    registry.register(FINISH_TOOL)

    probe_text = run_contamination_probe(llm, case.meta.ticker, as_of, ledger)

    cards = []
    if config.memory_on:
        retriever = ExperienceRetriever(store)
        cards = retriever.retrieve(
            f"{case.meta.ticker} {' '.join(case.meta.tags)} {case.meta.title}",
            as_of=as_of,
            exclude_case_id=case.meta.case_id,
            created_before=suite_started_at,
        )
    brief = case_brief(case.meta) + experience_block(render_cards(cards))

    temperature = float(config.temperature)
    run_planner(
        llm=llm, registry=registry, user_brief=brief,
        max_steps=config.max_steps, temperature=temperature,
        trace=trace, ledger=ledger,
    )
    audit_seen = _forward_audit(trace, audit, audit_seen)

    bundle = evidence.bundle(trace)
    market_summary = safe_call(registry, "price_history", {"lookback_days": 60})
    audit_seen = _forward_audit(trace, audit, audit_seen)

    memo, unverified = produce_memo(
        llm, bundle, case.meta, market_summary, temperature, trace, ledger
    )
    if memo is None:
        scores = {"status": "failed_validation", "cost": ledger.summary(),
                  "contamination_probe": probe_text[:2000]}
        (run_dir / "scores.json").write_text(json.dumps(scores, indent=1), encoding="utf-8")
        store.upsert_run(run_id, case.meta.case_id, config.model_dump_json(), "failed",
                         scores_json=json.dumps(scores), suite_id=suite_id)
        return RunResult(run_id, None, scores, True, run_dir)

    # ---- evaluation side: deliberately outside the sandbox ----
    bars = case.bars_source.get_bars(case.meta.ticker, as_of - timedelta(days=800), FAR_FUTURE)
    graded = grade_claims(memo.claims, bars, as_of)
    if unverified:
        for g in graded:
            g.status = GradeStatus.ungradable  # unverified memo claims never score
    agg = aggregate(graded)
    report = run_judge(llm, memo, graded, evidence.evidence_map(), temperature, ledger)
    jscores = judge_scores(report)

    baseline = max((i for i, b in enumerate(bars) if b.date <= as_of), default=None)
    if baseline is None:
        window_end = as_of
    else:
        end_i = min(baseline + case.meta.outcome_window_days, len(bars) - 1)
        window_end = bars[end_i].date
    card = build_card(case.meta, run_id, graded, report, window_end)
    ExperienceRetriever(store).write(card)  # write-always (spec §3.5)

    scores = {
        "outcome": agg,
        "process": jscores,
        "cost": ledger.summary(),
        "contamination_probe": probe_text[:2000],
        "unverified": unverified,
    }
    trace.emit(TraceEvent(type="score", agent="eval", payload={"outcome": agg, "process": jscores}))
    audit_seen = _forward_audit(trace, audit, audit_seen)

    (run_dir / "memo.md").write_text(_memo_markdown(memo, graded), encoding="utf-8", newline="\n")
    (run_dir / "claims.json").write_text(
        json.dumps(
            [
                {
                    **g.claim.model_dump(mode="json"),
                    "status": g.status.value,
                    "realized_return_pct": g.realized_return_pct,
                    "detail": g.detail,
                }
                for g in graded
            ],
            indent=1,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (run_dir / "scores.json").write_text(json.dumps(scores, indent=1), encoding="utf-8", newline="\n")
    store.upsert_run(run_id, case.meta.case_id, config.model_dump_json(), "done",
                     scores_json=json.dumps(scores), suite_id=suite_id)
    return RunResult(run_id, memo, scores, unverified, run_dir)
```

- [ ] **Step 4: Add the CLI `run` subcommand** — in `backend/hindsight/cli.py`, extend `main()`'s subparsers and dispatch:

```python
    pr = sub.add_parser("run", help="full research run against a case")
    pr.add_argument("--case", required=True)
    pr.add_argument("--memory", action="store_true")
    pr.add_argument("--max-steps", type=int, default=8)
    pr.add_argument("--runs-root", default="runs")
    pr.add_argument("--db", default="hindsight.db")
    pr.add_argument("--offline", action="store_true")
```

and the dispatch branch:

```python
    if args.command == "run":
        from hindsight.agents.orchestrator import run_research
        from hindsight.llm.client import LLMConfig, openai_transport
        from hindsight.llm.recording import RecordingLLMClient
        from hindsight.llm.retry import with_retry
        from hindsight.schemas import RunConfig
        from hindsight.store.db import Store

        cfg = LLMConfig.from_env()
        llm = RecordingLLMClient(
            transport=with_retry(openai_transport(cfg)),
            db_path=Path("llm_calls.sqlite"),
            model=cfg.model,
            offline=True if args.offline else None,
        )
        result = run_research(
            case_dir=Path(args.case),
            config=RunConfig(model=cfg.model, memory_on=args.memory, max_steps=args.max_steps),
            llm=llm,
            store=Store(Path(args.db)),
            runs_root=Path(args.runs_root),
        )
        print(f"run {result.run_id} -> {result.run_dir}")
        print(json.dumps(result.scores, indent=1, ensure_ascii=False))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `120 passed` (118 + 2).

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/agents/orchestrator.py backend/hindsight/cli.py backend/tests/test_orchestrator.py
git commit -m "feat(d2): run orchestrator with persistence and CLI run command"
```

---

### Task 13: EvalSuite runner + CLI `suite`

Spec §3.4/§3.5: N cases × M configs, cases ordered by as_of ascending, one snapshot taken before any run so in-suite experience writes are invisible to all suite runs.

**Files:**
- Create: `backend/hindsight/eval/suite.py`
- Modify: `backend/hindsight/cli.py` (add `suite` subcommand)
- Test: `backend/tests/test_suite.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_suite.py`:

```python
import json
from pathlib import Path

from hindsight.eval.suite import PRESETS, run_suite
from hindsight.schemas import RunConfig
from hindsight.store.db import Store


def test_suite_passes_one_snapshot_and_orders_cases(case_dir, tmp_path):
    calls = []

    def fake_run(case_dir, config, *, llm, store, runs_root, suite_id, suite_started_at):
        calls.append(
            {"case": Path(case_dir).name, "config": config.model_dump(),
             "suite_id": suite_id, "snap": suite_started_at}
        )

        class R:
            scores = {"outcome": {"hit_rate": 1.0}}
            run_id = f"r{len(calls)}"

        return R()

    store = Store(tmp_path / "h.db")
    suite_id = run_suite(
        [case_dir],
        {"base": RunConfig(model="m"), "memory": RunConfig(model="m", memory_on=True)},
        llm=None,
        store=store,
        runs_root=tmp_path / "runs",
        run_fn=fake_run,
    )
    assert len(calls) == 2  # 1 case x 2 configs
    snaps = {c["snap"] for c in calls}
    assert len(snaps) == 1 and None not in snaps  # single shared snapshot
    assert {c["suite_id"] for c in calls} == {suite_id}
    summary = json.loads(
        (tmp_path / "runs" / "suites" / f"{suite_id}.json").read_text(encoding="utf-8")
    )
    assert summary["configs"] == ["base", "memory"]
    assert summary["results"]["fixture_case"]["base"]["outcome"]["hit_rate"] == 1.0


def test_presets_exist():
    assert set(PRESETS) == {"base", "memory", "tight"}
    assert PRESETS["memory"].memory_on is True
    assert PRESETS["tight"].context_budget == 2000
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_suite.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/eval/suite.py`**

```python
"""EvalSuite: N cases x M configs with a single experience snapshot.

Cases run in as_of ascending order (spec §3.5: later cases may legally use
earlier cases' experience — but only cards that existed BEFORE the suite
started, so config comparisons stay order-independent)."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Callable

from hindsight.agents.orchestrator import run_research
from hindsight.data.cases import load_case
from hindsight.schemas import RunConfig
from hindsight.store.db import Store, now_iso

PRESETS: dict[str, RunConfig] = {
    "base": RunConfig(),
    "memory": RunConfig(memory_on=True),
    "tight": RunConfig(memory_on=True, context_budget=2000),
}


def run_suite(
    case_dirs: list[Path],
    configs: dict[str, RunConfig],
    *,
    llm: Any,
    store: Store,
    runs_root: Path,
    run_fn: Callable[..., Any] = run_research,
) -> str:
    suite_id = f"suite_{uuid.uuid4().hex[:8]}"
    suite_started_at = now_iso()  # single snapshot BEFORE any run
    ordered = sorted(case_dirs, key=lambda d: load_case(Path(d)).meta.as_of)
    results: dict[str, dict[str, Any]] = {}
    for case_dir in ordered:
        case_name = Path(case_dir).name
        results[case_name] = {}
        for config_name, config in configs.items():
            result = run_fn(
                case_dir,
                config,
                llm=llm,
                store=store,
                runs_root=runs_root,
                suite_id=suite_id,
                suite_started_at=suite_started_at,
            )
            results[case_name][config_name] = result.scores
    summary = {
        "suite_id": suite_id,
        "started_at": suite_started_at,
        "cases": [Path(d).name for d in ordered],
        "configs": list(configs),
        "results": results,
    }
    out = Path(runs_root) / "suites" / f"{suite_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return suite_id
```

- [ ] **Step 4: Add the CLI `suite` subcommand** in `backend/hindsight/cli.py`:

```python
    ps = sub.add_parser("suite", help="run an eval suite: cases x config presets")
    ps.add_argument("--cases", required=True, help="comma-separated dataset dirs")
    ps.add_argument("--presets", default="base,memory")
    ps.add_argument("--runs-root", default="runs")
    ps.add_argument("--db", default="hindsight.db")
    ps.add_argument("--offline", action="store_true")
```

dispatch branch (mirrors `run`, building the llm once):

```python
    if args.command == "suite":
        from hindsight.eval.suite import PRESETS, run_suite
        from hindsight.llm.client import LLMConfig, openai_transport
        from hindsight.llm.recording import RecordingLLMClient
        from hindsight.llm.retry import with_retry
        from hindsight.store.db import Store

        cfg = LLMConfig.from_env()
        llm = RecordingLLMClient(
            transport=with_retry(openai_transport(cfg)),
            db_path=Path("llm_calls.sqlite"),
            model=cfg.model,
            offline=True if args.offline else None,
        )
        configs = {}
        for name in args.presets.split(","):
            preset = PRESETS[name.strip()]
            configs[name.strip()] = preset.model_copy(update={"model": cfg.model})
        suite_id = run_suite(
            [Path(p.strip()) for p in args.cases.split(",")],
            configs,
            llm=llm,
            store=Store(Path(args.db)),
            runs_root=Path(args.runs_root),
        )
        print(f"suite {suite_id} complete -> {Path(args.runs_root) / 'suites' / (suite_id + '.json')}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `122 passed` (120 + 2).

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/eval/suite.py backend/hindsight/cli.py backend/tests/test_suite.py
git commit -m "feat(d2): eval suite runner with shared experience snapshot"
```

---

### Task 14: Live end-to-end run on the NVDA case (real API — quota-aware)

**No new code.** This is the first real firing of the whole pipeline. Budget: ≤3 full live runs (~50 metered calls) before pausing for guidance. The recording layer makes every repeat free.

- [ ] **Step 1: Live run (record mode)**

Run from repo root: `backend/.venv/Scripts/python -m hindsight.cli run --case datasets/nvda_fy26q1`
Watch for: 429 pauses are normal (retry transport waits 15-60s); a full run takes several minutes.

- [ ] **Step 2: Inspect quality**

Read `runs/<run_id>/memo.md` and `scores.json`. Acceptance bar:
- memo has ≥2 claims, at least one `direction`, all citing real chunk ids
- ≥1 claim graded hit or miss (not everything ungradable)
- judge report parsed (`process.judge_failed == false`)
- trace.jsonl contains plan_step/tool_call/validation/score/audit events

- [ ] **Step 3: Iterate if broken (evaluation-driven, logged)**

If the analyst emits invalid JSON repeatedly or the planner never searches: adjust ONE prompt in `agents/prompts.py`, append a dated entry to `docs/eval-log.md` (what changed, scores before/after), re-run. Repeat ≤3 total live runs. If still broken after 3, STOP and report BLOCKED with the failure transcripts.

- [ ] **Step 4: Offline replay proof**

Run: `backend/.venv/Scripts/python -m hindsight.cli run --case datasets/nvda_fy26q1 --offline`
Expected: completes WITHOUT network using replayed responses (new run_id, same memo content). This is the interview offline-demo guarantee.

- [ ] **Step 5: Commit the artifacts**

```bash
git add runs llm_calls.sqlite hindsight.db docs/eval-log.md backend/hindsight/agents/prompts.py
git commit -m "feat(d2): first live NVDA run recorded; offline replay verified"
```

(Include `prompts.py` only if Step 3 changed it. The sqlite files contain prompts/responses — no key material; committing them IS the offline-demo mechanism.)

---

### Task 15: Case 3 (SMCI candidate) rough corpus + falsification validation

Spec §4.1 case 3: an event where the contemporaneous bullish narrative was falsified within 20-40 trading days. SMCI is the initial candidate; the curator VERIFIES with real data and may swap tickers. Facts must be verified via WebSearch (interview credibility). English docs, 6-8 of them, no long-document requirement (that's case 1's job).

- [ ] **Step 1: Research the candidate window (WebSearch)**

Establish SMCI's 2025 timeline: the Feb 2025 delayed-filing resolution rally, guidance claims, subsequent drawdowns. Pick an `as_of` where: (a) the prior 60-90 days' public narrative was predominantly bullish; (b) the following 20-40 trading days falsified it (drawdown ≥15% or clear thesis break). Verify with actual price data BEFORE authoring: run a quick yfinance query via the venv. If SMCI offers no such window, pick an alternative ticker that does (document why in eval-log).

- [ ] **Step 2: Author the dataset**

`datasets/smci_case3/meta.json` (same schema as nvda case; `outcome_window_days` 20-40 matching the falsification window; tags e.g. `["turnaround", "servers", "ai-capex"]`) + 6-8 docs under `docs/` (frontmatter identical to case 1; every doc dated ≤ as_of except ONE deliberate future doc stating what actually happened). Same authoring rules: facts as known at publication date, real URLs, numbers verified.

- [ ] **Step 3: Freeze bars + integrity test**

Run the freeze script for a window covering as_of −120d to as_of + outcome window + buffer. Copy `backend/tests/test_nvda_case.py` to `backend/tests/test_smci_case.py`, adapt CASE_DIR/ticker/as_of/doc count (≥6), DROP the long-document test (case 1 covers it). Run: expect 3 tests passing (`125 passed` total).

- [ ] **Step 4: Falsification validation run (real API)**

`backend/.venv/Scripts/python -m hindsight.cli run --case datasets/smci_case3`
Validation bar (spec: "选候选→跑→验证失败形态"): the memo's bullish-leaning claims should grade mostly `miss` — that's the point of this case. Record in `docs/eval-log.md`: as_of chosen, claims/hits/misses, whether the failure shape holds. If the agent is bearish and hits instead — that's also acceptable showcase material (note it); the case requirement is that NARRATIVE-FOLLOWING claims get falsified, which the calibration chart will surface.

- [ ] **Step 5: Commit**

```bash
git add datasets/smci_case3 backend/tests/test_smci_case.py runs llm_calls.sqlite hindsight.db docs/eval-log.md
git commit -m "feat(d2): SMCI falsification case with validated failure shape"
```

---

### Task 16: D2 wrap-up verification

- [ ] **Step 1: Full suite** — `cd backend && .venv/Scripts/python -m pytest -q` → expect `125 passed` (or the exact count after Task 15's test file; report the real number).
- [ ] **Step 2: Security scan** — `git log -p --all | grep -cE "0aece327|MDMyOTc3"` → must print `0`.
- [ ] **Step 3: Exit criteria** (all must pass; report each):
  - CLI `run` works live AND offline on nvda_fy26q1
  - Two committed cases load; leakage tests cover documents + bars + memory channels
  - `docs/eval-log.md` has: probe entry (D1), ≥1 prompt-iteration or live-run entry, case-3 validation entry
  - `runs/` contains ≥2 committed recorded runs replayable offline
- [ ] **Step 4: Update the D1 plan's carryover list** — mark items ①-⑪ done (they are implemented by Tasks 1-13); refresh the D3 list (RecordingLLMClient thread-bound sqlite — note `Store` already ships `check_same_thread=False`+lock but serializes all reads through one coarse lock, acceptable for demo traffic; FastAPI + WS; frontend pages; suite paired-delta rendering).
- [ ] **Step 5: Commit and tag**

```bash
git add -A && git commit -m "chore(d2): day-2 wrap-up"
git tag d2-complete
```

---

## Execution notes

- Same conventions as D1: subagent per task, spec-then-quality review, sanctioned deviations amend this plan file first.
- Tasks 14-15 make real API calls (authorized; ≤3 live runs each). All other tasks are network-free.
- Deviation rule for LLM-behavior surprises: if the real model's response SHAPE differs from the stubs (e.g. tool_calls field variants), fix the parsing layer, add a regression test mirroring the real shape, and note it in eval-log.

