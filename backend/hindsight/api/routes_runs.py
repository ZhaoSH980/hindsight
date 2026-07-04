"""Run read endpoints. Failed runs are first-class: memo_md may be null and
claims empty — the frontend renders a 'validation failed' state, never a 404."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

import asyncio
import threading

from typing import Literal

from fastapi import WebSocket
from pydantic import BaseModel, Field

from hindsight.agents.orchestrator import _new_run_id


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


class StartRunRequest(BaseModel):
    # mirror RunConfig's constraints here so bad requests 422 at the door
    # instead of birthing a run row that instantly crashes in the background
    case_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    memory_on: bool = False
    max_steps: int = Field(default=8, gt=0, le=32)
    language: Literal["en", "zh"] = "en"


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
    config = {"memory_on": body.memory_on, "max_steps": body.max_steps, "language": body.language}
    state.store.upsert_run(run_id, body.case_id, json.dumps(config), "queued")
    executor = state.run_executor or _default_executor(state)
    executor(body.case_id, config, run_id)
    return {"run_id": run_id}


@router.websocket("/api/runs/{run_id}/stream")
async def stream_run(ws: WebSocket, run_id: str):
    await ws.accept()
    state = ws.app.state.hindsight
    rows = [r for r in state.store.get_runs() if r["run_id"] == run_id]
    if not rows:
        await ws.send_text(json.dumps({"type": "error", "payload": {"detail": f"unknown run {run_id}"}}))
        await ws.close(code=4404)
        return
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
        # invariant executors must uphold: terminal status is upserted AFTER the last trace line
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
