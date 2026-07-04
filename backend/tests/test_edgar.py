"""EDGAR import: parsing, date gating, URL safety, and the API routes."""
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from hindsight.api.app import create_app
from hindsight.data import edgar

TICKERS_JSON = json.dumps(
    {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
).encode()

SUBMISSIONS_JSON = json.dumps(
    {
        "filings": {
            "recent": {
                "form": ["8-K", "4", "10-Q", "8-K"],
                "filingDate": ["2025-05-02", "2025-04-20", "2025-01-31", "2024-11-01"],
                "accessionNumber": [
                    "0000320193-25-000057",
                    "0000320193-25-000044",
                    "0000320193-25-000008",
                    "0000320193-24-000110",
                ],
                "primaryDocument": ["a8k.htm", "form4.xml", "a10q.htm", "old8k.htm"],
            }
        }
    }
).encode()

FILING_HTML = (
    b"<html><head><title>skip me</title><script>garbage()</script></head>"
    b"<body><div>Apple reported quarterly revenue.</div>"
    b"<p>Services set an all-time record. " + b"Detail sentence. " * 20 + b"</p></body></html>"
)


def fake_http(url: str) -> bytes:
    if "company_tickers" in url:
        return TICKERS_JSON
    if "submissions" in url:
        return SUBMISSIONS_JSON
    if "Archives" in url:
        return FILING_HTML
    raise AssertionError(f"unexpected URL {url}")


def test_html_to_text_strips_markup_and_scripts():
    text = edgar.html_to_text(FILING_HTML.decode())
    assert "Apple reported quarterly revenue." in text
    assert "garbage" not in text and "skip me" not in text
    assert "<div>" not in text


def test_list_filings_gates_on_date_and_form():
    rows = edgar.list_filings("aapl", before=date(2025, 4, 15), http_get=fake_http)
    # 2025-05-02 8-K is after the cutoff; form 4 is not requested
    assert [(r["form"], r["filed"]) for r in rows] == [
        ("10-Q", "2025-01-31"),
        ("8-K", "2024-11-01"),
    ]
    assert all(r["cik"] == 320193 for r in rows)


def test_unknown_ticker_raises():
    with pytest.raises(ValueError, match="not found"):
        edgar.list_filings("NOPE", before=date(2025, 1, 1), http_get=fake_http)


def test_fetch_filing_builds_pinned_url_and_doc():
    doc = edgar.fetch_filing(
        "AAPL", 320193, "0000320193-25-000008", "a10q.htm", "10-Q", "2025-01-31",
        http_get=fake_http,
    )
    assert doc["published_at"] == "2025-01-31"
    assert doc["url"].startswith("https://www.sec.gov/Archives/edgar/data/320193/")
    assert doc["doc_type"] == "filing"
    assert "Apple reported quarterly revenue." in doc["text"]


def test_pick_document_prefers_ex99_exhibit_for_8k():
    index = json.dumps({"directory": {"item": [
        {"name": "cover8k.htm", "size": 5000},
        {"name": "a8-kex991.htm", "size": 90000},
        {"name": "a8-kex991small.htm", "size": 100},
        {"name": "chart.jpg", "size": 999999},
    ]}}).encode()
    assert edgar._pick_document(index, "cover8k.htm", "8-K") == "a8-kex991.htm"
    # non-8-K forms keep their primary document
    assert edgar._pick_document(index, "a10q.htm", "10-Q") == "a10q.htm"
    # garbage index falls back to primary
    assert edgar._pick_document(b"<html>", "cover8k.htm", "8-K") == "cover8k.htm"


def test_html_to_text_drops_ixbrl_junk():
    html = "<ix:header><div>aapl:A0.000Notesdue2025Member</div></ix:header><p>Real text.</p>"
    junk_token = "x" * 120
    text = edgar.html_to_text(f"{html}<p>{junk_token}</p>")
    assert "Real text." in text
    assert "Notesdue2025" not in text
    assert junk_token not in text


def test_fetch_filing_rejects_malformed_parts():
    with pytest.raises(ValueError, match="accession"):
        edgar.fetch_filing("AAPL", 1, "../../etc", "a.htm", "8-K", "2025-01-01",
                           http_get=fake_http)
    with pytest.raises(ValueError, match="document"):
        edgar.fetch_filing("AAPL", 1, "0000320193-25-000008", "a/../b.htm", "8-K",
                           "2025-01-01", http_get=fake_http)


# ---------- API routes ----------

def test_edgar_routes_roundtrip(api_root):
    app = create_app(repo_root=api_root)
    app.state.hindsight.edgar_http = fake_http
    client = TestClient(app)

    r = client.get("/api/edgar/filings", params={"ticker": "AAPL", "before": "2025-04-15"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2

    r2 = client.post("/api/edgar/fetch", json={"ticker": "AAPL", **rows[0]})
    assert r2.status_code == 200
    assert r2.json()["published_at"] == "2025-01-31"


def test_edgar_blocked_offline(api_root, monkeypatch):
    monkeypatch.setenv("HINDSIGHT_OFFLINE", "1")
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/api/edgar/filings", params={"ticker": "AAPL", "before": "2025-04-15"})
    assert r.status_code == 400
    assert "offline" in r.json()["detail"]
