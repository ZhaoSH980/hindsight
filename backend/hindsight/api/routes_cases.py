"""Case listing + display-only bars (spec §5: the sandbox gates AGENT access;
this endpoint feeds the frontend chart, which does its own as_of masking)."""
from __future__ import annotations

import json
import os
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from hindsight.data import edgar
from hindsight.data.case_builder import (
    CaseBuildError,
    CaseExistsError,
    NewCaseRequest,
    build_case,
)

router = APIRouter()


def _require_online() -> None:
    if os.environ.get("HINDSIGHT_OFFLINE", "") == "1":
        raise HTTPException(
            status_code=400,
            detail="offline mode has no network access — start the server online for this",
        )


@router.get("/api/cases")
def list_cases(request: Request):
    state = request.app.state.hindsight
    cases = []
    if state.datasets.exists():
        for meta_path in sorted(state.datasets.glob("*/meta.json")):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue  # a stray/broken case dir must not 500 the whole list
            meta["n_docs"] = len(list((meta_path.parent / "docs").glob("*.md")))
            cases.append(meta)
    return cases


@router.post("/api/cases")
def create_case(body: NewCaseRequest, request: Request):
    state = request.app.state.hindsight
    _require_online()
    fetcher = getattr(state, "bars_fetcher", None)  # test seam; None -> yfinance
    try:
        result = build_case(state.datasets, body, bars_fetcher=fetcher)
    except CaseExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CaseBuildError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # yfinance/network failures -> upstream error, not a 500
        raise HTTPException(status_code=502, detail=f"market data fetch failed: {exc}") from exc
    return result


@router.get("/api/edgar/filings")
def edgar_filings(ticker: str, before: str, request: Request):
    """Most recent SEC filings for a ticker, filed on or before `before`."""
    state = request.app.state.hindsight
    _require_online()
    http_get = getattr(state, "edgar_http", None) or edgar.default_http_get
    try:
        before_d = date.fromisoformat(before)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"bad date {before!r}") from exc
    try:
        return edgar.list_filings(ticker, before_d, http_get=http_get)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"EDGAR request failed: {exc}") from exc


class EdgarFetchRequest(BaseModel):
    ticker: str
    cik: int
    accession: str
    document: str
    form: str
    filed: str


@router.post("/api/edgar/fetch")
def edgar_fetch(body: EdgarFetchRequest, request: Request):
    """Fetch one filing as a wizard-ready document draft."""
    state = request.app.state.hindsight
    _require_online()
    http_get = getattr(state, "edgar_http", None) or edgar.default_http_get
    try:
        return edgar.fetch_filing(
            body.ticker, body.cik, body.accession, body.document, body.form, body.filed,
            http_get=http_get,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"EDGAR request failed: {exc}") from exc


@router.get("/api/cases/{case_id}/bars")
def case_bars(case_id: str, request: Request):
    state = request.app.state.hindsight
    bars_path = state.datasets / case_id / "bars.json"
    if not bars_path.exists():
        raise HTTPException(status_code=404, detail=f"unknown case {case_id}")
    payload = json.loads(bars_path.read_text(encoding="utf-8"))
    return {"ticker": payload["ticker"], "bars": payload["bars"]}
