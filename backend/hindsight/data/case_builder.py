"""Create a new case dataset from user-supplied metadata and documents.

The corpus is the product's soul: every document must genuinely predate the
as-of date, or the time sandbox is guarding an already-poisoned well. This
builder enforces what CAN be checked mechanically (dates, structure, a
round-trip load) — the truthfulness of the text itself remains the author's
responsibility and is called out in the UI.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from hindsight.data.cases import MIN_CORPUS_DOCS, load_case
from hindsight.data.models import Bar

# lookback must cover the grader's needs: ~252 trading days of history for the
# volatility percentile plus the baseline hunt (orchestrator fetches as_of-800d)
_LOOKBACK_DAYS = 800
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_]{2,48}$")
# digit-leading symbols are real markets (0700.HK, 600519.SS) — allow them
_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,9}$")


class BarsFetcher(Protocol):
    def __call__(self, ticker: str, start: date, end: date) -> list[Bar]: ...


class NewDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    published_at: date
    source: str = Field(default="user-supplied", max_length=100)
    url: str = Field(default="", max_length=500)
    doc_type: str = Field(default="news", max_length=32)
    # floor: a corpus of one-liners defeats retrieval; ceiling: comfortably
    # above the EDGAR importer's 40k cap, but no request-body bombs
    text: str = Field(min_length=100, max_length=60_000)


class NewCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    as_of: date
    outcome_window_days: int = Field(default=40, gt=0, le=250)
    title: str = Field(min_length=3, max_length=200)
    title_zh: str = ""
    description: str = Field(min_length=10, max_length=2000)
    description_zh: str = ""
    tags: list[str] = Field(default_factory=list, max_length=8)
    docs: list[NewDoc] = Field(min_length=MIN_CORPUS_DOCS, max_length=40)

    @field_validator("ticker")
    @classmethod
    def _ticker_shape(cls, v: str) -> str:
        v = v.strip().upper()
        if not _TICKER_RE.match(v):
            raise ValueError(f"ticker {v!r} must look like a market symbol (A-Z, 0-9, ., -)")
        return v

    @field_validator("tags")
    @classmethod
    def _tag_shape(cls, v: list[str]) -> list[str]:
        return [t.strip().lower()[:24] for t in v if t.strip()]


class CaseBuildError(ValueError):
    """User-fixable problem with the submitted case (maps to HTTP 400)."""


def _slugify(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:limit] or "doc"


def derive_case_id(datasets_root: Path, ticker: str, as_of: date) -> str:
    base = f"{_slugify(ticker)}_{as_of.strftime('%Y%m%d')}"
    case_id = base
    n = 2
    while (datasets_root / case_id).exists():
        case_id = f"{base}_{n}"
        n += 1
    return case_id


def _claim_case_dir(datasets_root: Path, ticker: str, as_of: date) -> tuple[str, Path]:
    """Atomically reserve a case directory: mkdir itself is the claim, so two
    concurrent requests for the same ticker+date can never share (or destroy)
    one directory — the loser just gets the next suffix."""
    base = f"{_slugify(ticker)}_{as_of.strftime('%Y%m%d')}"
    case_id = base
    n = 2
    while True:
        case_dir = datasets_root / case_id
        try:
            (case_dir / "docs").mkdir(parents=True)
            return case_id, case_dir
        except FileExistsError:
            case_id = f"{base}_{n}"
            n += 1


def _doc_markdown(doc: NewDoc) -> str:
    # frontmatter fields mirror rag/ingest.load_documents expectations
    def esc(s: str) -> str:
        # backslash would start a YAML escape inside double quotes — neutralize
        return s.replace("\\", "/").replace("\n", " ").replace('"', "'").strip()

    return (
        "---\n"
        f'title: "{esc(doc.title)}"\n'
        f'source: "{esc(doc.source)}"\n'
        f"published_at: {doc.published_at.isoformat()}\n"
        f'url: "{esc(doc.url)}"\n'
        f'doc_type: "{esc(doc.doc_type)}"\n'
        "---\n\n"
        f"{doc.text.strip()}\n"
    )


def build_case(
    datasets_root: Path,
    req: NewCaseRequest,
    bars_fetcher: BarsFetcher | None = None,
    today: Callable[[], date] = date.today,
) -> dict:
    """Validate, fetch bars, and write datasets/<case_id>/. Returns a summary.

    All-or-nothing: any failure removes the partially written directory.
    """
    if req.as_of >= today():
        raise CaseBuildError(
            f"as_of {req.as_of.isoformat()} is not in the past — "
            "the future has to exist before it can grade anything"
        )

    late = [d for d in req.docs if d.published_at > req.as_of]
    if late:
        names = ", ".join(f"{d.title!r} ({d.published_at.isoformat()})" for d in late[:5])
        raise CaseBuildError(
            f"{len(late)} document(s) are published AFTER the as-of date: {names}. "
            "Documents from the future would poison the sandbox at the source."
        )

    if bars_fetcher is None:
        from hindsight.data.market_source import YFinanceSource

        bars_fetcher = YFinanceSource().get_bars

    start = req.as_of - timedelta(days=_LOOKBACK_DAYS)
    # calendar buffer over trading days so the grader can find the window end
    end = min(today(), req.as_of + timedelta(days=req.outcome_window_days * 2 + 30))
    bars = bars_fetcher(req.ticker, start, end)
    if not bars:
        raise CaseBuildError(f"no market data returned for {req.ticker!r} — check the symbol")
    if not any(b.date <= req.as_of for b in bars):
        raise CaseBuildError(f"market data for {req.ticker!r} has no bar on or before as_of")
    bars_after = sum(1 for b in bars if b.date > req.as_of)

    case_id, case_dir = _claim_case_dir(datasets_root, req.ticker, req.as_of)
    try:
        meta = {
            "case_id": case_id,
            "title": req.title,
            "title_zh": req.title_zh,
            "ticker": req.ticker,
            "as_of": req.as_of.isoformat(),
            "outcome_window_days": req.outcome_window_days,
            "description": req.description,
            "description_zh": req.description_zh,
            "tags": req.tags,
        }
        (case_dir / "meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        bars_payload = {
            "ticker": req.ticker,
            "auto_adjust": True,
            "source": "case-wizard",
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "bars": [
                {
                    "date": b.date.isoformat(),
                    "open": b.open,
                    "high": b.high,
                    "low": b.low,
                    "close": b.close,
                    "volume": b.volume,
                }
                for b in bars
            ],
        }
        (case_dir / "bars.json").write_text(
            json.dumps(bars_payload, indent=1), encoding="utf-8", newline="\n"
        )
        for i, doc in enumerate(req.docs):
            name = f"{i + 1:02d}_{_slugify(doc.title)}.md"
            (case_dir / "docs" / name).write_text(
                _doc_markdown(doc), encoding="utf-8", newline="\n"
            )

        # the real gate: the case must load exactly like the curated ones
        loaded = load_case(case_dir)
    except CaseBuildError:
        shutil.rmtree(case_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(case_dir, ignore_errors=True)
        raise CaseBuildError(f"case failed to load after writing: {exc}") from exc

    window_open = bars_after < req.outcome_window_days
    return {
        "case_id": case_id,
        "n_docs": len(loaded.documents),
        "n_chunks": len(loaded.chunks),
        "n_bars": len(bars),
        "bars_after_as_of": bars_after,
        # claims may grade as ungradable until the window fully closes
        "outcome_window_still_open": window_open,
    }
