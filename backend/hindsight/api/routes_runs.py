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
