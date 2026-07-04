"""SEC EDGAR one-click document import for the case wizard.

EDGAR is the one automatable corpus source whose dates cannot lie: the
filing date is stamped by the SEC itself — exactly the property an
anti-lookahead corpus needs. News still has to be curated by hand.

All network access goes through an injectable `http_get` so tests never
touch the internet. URLs are always rebuilt server-side from validated
parts (accession number, document name) — no client-supplied URLs.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from html.parser import HTMLParser
from typing import Callable
from urllib.request import Request, urlopen

# SEC fair-access policy requires "Company Name AdminContact@domain" in the UA;
# override with HINDSIGHT_EDGAR_UA if you deploy this yourself
_UA = os.environ.get(
    "HINDSIGHT_EDGAR_UA",
    "Hindsight eval harness zhaochenghao980@gmail.com",
)
_TIMEOUT = 30

_ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_DOCNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")

HttpGet = Callable[[str], bytes]


def default_http_get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": _UA, "Accept-Encoding": "identity"})
    with urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310 - sec.gov URLs built server-side
        return resp.read()


class _TextExtractor(HTMLParser):
    """Tag-stripping text extraction good enough for iXBRL filing documents."""

    _SKIP = {"script", "style", "head", "title", "ix:header", "ix:hidden"}
    _BREAK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "table", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
        if tag in self._BREAK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def html_to_text(html: str, max_chars: int = 40000) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts)
    # leftover iXBRL context ids concatenate into giant space-less tokens — drop them
    text = re.sub(r"\S{80,}", " ", text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text[:max_chars]


def lookup_cik(ticker: str, http_get: HttpGet = default_http_get) -> int | None:
    data = json.loads(http_get("https://www.sec.gov/files/company_tickers.json"))
    t = ticker.strip().upper()
    for row in data.values():
        if row.get("ticker") == t:
            return int(row["cik_str"])
    return None


def list_filings(
    ticker: str,
    before: date,
    forms: tuple[str, ...] = ("10-K", "10-Q", "8-K"),
    limit: int = 10,
    http_get: HttpGet = default_http_get,
) -> list[dict]:
    """Most recent filings of the given forms filed on or before `before`."""
    cik = lookup_cik(ticker, http_get)
    if cik is None:
        raise ValueError(f"ticker {ticker!r} not found on SEC EDGAR")
    sub = json.loads(http_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    recent = sub.get("filings", {}).get("recent", {})
    out: list[dict] = []
    rows = zip(
        recent.get("form", []),
        recent.get("filingDate", []),
        recent.get("accessionNumber", []),
        recent.get("primaryDocument", []),
    )
    for form, filed, accession, document in rows:  # EDGAR sorts newest-first
        if form not in forms or not document:
            continue
        if date.fromisoformat(filed) > before:
            continue
        out.append(
            {"cik": cik, "form": form, "filed": filed, "accession": accession, "document": document}
        )
        if len(out) >= limit:
            break
    return out


def _pick_document(index_json: bytes, primary: str, form: str) -> str:
    """8-K primary docs are iXBRL cover pages; the substance (press release)
    lives in an ex99 exhibit. Prefer that when present."""
    if not form.startswith("8-K"):
        return primary
    try:
        items = json.loads(index_json).get("directory", {}).get("item", [])
    except (json.JSONDecodeError, AttributeError):
        return primary
    exhibits = [
        f for f in items
        if str(f.get("name", "")).lower().endswith((".htm", ".html"))
        and ("ex99" in str(f.get("name", "")).lower() or "press" in str(f.get("name", "")).lower())
    ]
    if not exhibits:
        return primary
    best = max(exhibits, key=lambda f: int(f.get("size") or 0))
    name = str(best["name"])
    return name if _DOCNAME_RE.match(name) else primary


def fetch_filing(
    ticker: str,
    cik: int,
    accession: str,
    document: str,
    form: str,
    filed: str,
    max_chars: int = 40000,
    http_get: HttpGet = default_http_get,
) -> dict:
    """Fetch one filing document and shape it as a wizard-ready doc draft.

    URLs are rebuilt here from strictly validated parts — client input can
    only ever point inside sec.gov's archive tree.
    """
    if not _ACCESSION_RE.match(accession):
        raise ValueError(f"malformed accession number {accession!r}")
    if not _DOCNAME_RE.match(document):
        raise ValueError(f"malformed document name {document!r}")
    date.fromisoformat(filed)  # raises on garbage
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"
    if form.startswith("8-K"):
        try:
            document = _pick_document(http_get(f"{base}/index.json"), document, form)
        except Exception:  # noqa: BLE001 - index lookup is best-effort, primary doc still works
            pass
    url = f"{base}/{document}"
    raw = http_get(url)
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("cp1252", errors="replace")
    text = html_to_text(html, max_chars)
    if len(text) < 100:
        raise ValueError(f"filing {accession} produced no usable text")
    return {
        "title": f"{ticker.upper()} {form} (filed {filed})",
        "published_at": filed,
        "source": f"SEC EDGAR {form}",
        "url": url,
        "doc_type": "filing",
        "text": text,
    }
