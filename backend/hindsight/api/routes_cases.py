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
