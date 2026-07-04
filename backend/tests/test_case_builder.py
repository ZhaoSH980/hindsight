"""Case wizard: build_case validation, filesystem safety, and the API route."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from hindsight.api.app import create_app
from hindsight.data.case_builder import (
    CaseBuildError,
    NewCaseRequest,
    build_case,
    derive_case_id,
)
from hindsight.data.models import Bar


def fake_bars(ticker: str, start: date, end: date) -> list[Bar]:
    return [
        Bar(date=date(2025, 5, 20), open=1, high=1, low=1, close=1.0, volume=1),
        Bar(date=date(2025, 5, 21), open=1, high=1, low=1, close=1.1, volume=1),
        Bar(date=date(2025, 5, 22), open=1, high=1, low=1, close=1.2, volume=1),
        Bar(date=date(2025, 6, 20), open=1, high=1, low=1, close=2.0, volume=1),
    ]


DOC = {
    "title": "pre-earnings guidance note",
    "published_at": "2025-05-01",
    "source": "fixture",
    "text": "nvidia guidance strong, data center demand robust, capex cycle intact " * 3,
}
DOC2 = {
    "title": "bearish take on valuation",
    "published_at": "2025-05-10",
    "source": "fixture",
    "text": "valuation stretched, china export controls weigh on outlook, margins peaking " * 3,
}


def make_req(**over) -> NewCaseRequest:
    payload = {
        "ticker": "nvda",
        "as_of": "2025-05-22",
        "outcome_window_days": 20,
        "title": "NVDA test case",
        "description": "a case created by the wizard tests",
        "tags": ["Test ", ""],
        "docs": [DOC, DOC2],
        **over,
    }
    return NewCaseRequest.model_validate(payload)


def test_happy_path_builds_loadable_case(tmp_path):
    res = build_case(tmp_path, make_req(), bars_fetcher=fake_bars,
                     today=lambda: date(2026, 7, 5))
    case_dir = tmp_path / res["case_id"]
    assert res["case_id"] == "nvda_20250522"
    assert (case_dir / "meta.json").exists()
    assert (case_dir / "bars.json").exists()
    assert res["n_docs"] == 2 and res["n_bars"] == 4 and res["bars_after_as_of"] == 1
    assert res["outcome_window_still_open"] is True  # only 1 bar after as_of < 20
    # ticker normalized, tags cleaned
    import json

    meta = json.loads((case_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["ticker"] == "NVDA"
    assert meta["tags"] == ["test"]


def test_future_doc_rejected_and_nothing_written(tmp_path):
    bad_doc = {**DOC2, "published_at": "2025-05-23"}
    with pytest.raises(CaseBuildError, match="AFTER the as-of date"):
        build_case(tmp_path, make_req(docs=[DOC, bad_doc]), bars_fetcher=fake_bars,
                   today=lambda: date(2026, 7, 5))
    assert list(tmp_path.iterdir()) == []


def test_as_of_must_be_past(tmp_path):
    with pytest.raises(CaseBuildError, match="not in the past"):
        build_case(tmp_path, make_req(), bars_fetcher=fake_bars,
                   today=lambda: date(2025, 5, 22))


def test_duplicate_case_id_gets_suffix(tmp_path):
    kwargs = dict(bars_fetcher=fake_bars, today=lambda: date(2026, 7, 5))
    first = build_case(tmp_path, make_req(), **kwargs)
    second = build_case(tmp_path, make_req(), **kwargs)
    assert first["case_id"] == "nvda_20250522"
    assert second["case_id"] == "nvda_20250522_2"


def test_ticker_cannot_smuggle_a_path(tmp_path):
    with pytest.raises(ValueError):
        make_req(ticker="../evil")
    # derive_case_id only ever emits slug characters
    assert derive_case_id(tmp_path, "BRK.B", date(2025, 5, 22)) == "brk_b_20250522"


def test_bars_must_cover_as_of(tmp_path):
    def late_bars(ticker, start, end):
        return [Bar(date=date(2025, 6, 1), open=1, high=1, low=1, close=1, volume=1)]

    with pytest.raises(CaseBuildError, match="on or before as_of"):
        build_case(tmp_path, make_req(), bars_fetcher=late_bars,
                   today=lambda: date(2026, 7, 5))


def test_min_docs_enforced():
    with pytest.raises(ValueError):
        make_req(docs=[DOC])


# ---------- API route ----------

def test_post_cases_roundtrip(api_root):
    app = create_app(repo_root=api_root)
    app.state.hindsight.bars_fetcher = fake_bars
    client = TestClient(app)

    payload = {
        "ticker": "NVDA",
        "as_of": "2025-05-22",
        "outcome_window_days": 20,
        "title": "Wizard case",
        "description": "created through the API in a test",
        "docs": [DOC, DOC2],
    }
    r = client.post("/api/cases", json=payload)
    assert r.status_code == 200, r.text
    case_id = r.json()["case_id"]

    listed = {c["case_id"] for c in client.get("/api/cases").json()}
    assert case_id in listed
    bars = client.get(f"/api/cases/{case_id}/bars").json()
    assert len(bars["bars"]) == 4


def test_post_cases_rejects_future_doc(api_root):
    app = create_app(repo_root=api_root)
    app.state.hindsight.bars_fetcher = fake_bars
    client = TestClient(app)
    bad = {**DOC2, "published_at": "2026-01-01"}
    r = client.post("/api/cases", json={
        "ticker": "NVDA", "as_of": "2025-05-22", "title": "Bad case",
        "description": "future doc must be rejected", "docs": [DOC, bad],
    })
    assert r.status_code == 400
    assert "AFTER the as-of date" in r.json()["detail"]


def test_post_cases_blocked_offline(api_root, monkeypatch):
    monkeypatch.setenv("HINDSIGHT_OFFLINE", "1")
    app = create_app(repo_root=api_root)
    client = TestClient(app)
    r = client.post("/api/cases", json={
        "ticker": "NVDA", "as_of": "2025-05-22", "title": "Offline case",
        "description": "should be refused offline", "docs": [DOC, DOC2],
    })
    assert r.status_code == 400
    assert "offline" in r.json()["detail"]


def test_concurrent_creation_never_shares_a_directory(tmp_path):
    """Two simultaneous builds of the same ticker+date must land in two
    distinct directories — mkdir is the atomic claim (TOCTOU regression)."""
    import threading

    results, errors = [], []

    def create():
        try:
            results.append(build_case(tmp_path, make_req(), bars_fetcher=fake_bars,
                                      today=lambda: date(2026, 7, 5)))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=create) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    ids = {r["case_id"] for r in results}
    assert len(ids) == 2
    for cid in ids:
        assert (tmp_path / cid / "meta.json").exists()


def test_backslash_in_title_survives_frontmatter():
    req = make_req(docs=[{**DOC, "title": r"smart\dumb money note"}, DOC2])
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        res = build_case(Path(td), req, bars_fetcher=fake_bars,
                         today=lambda: date(2026, 7, 5))
        assert res["n_docs"] == 2  # round-trip load passed -> YAML stayed valid


def test_digit_leading_tickers_accepted():
    assert make_req(ticker="0700.HK").ticker == "0700.HK"
    assert make_req(ticker="600519.SS").ticker == "600519.SS"


def test_oversized_doc_rejected():
    with pytest.raises(ValueError):
        make_req(docs=[DOC, {**DOC2, "text": "x" * 60_001}])
