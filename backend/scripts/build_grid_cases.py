"""Build the mechanical case grid: UNIVERSE x GRID_DATES, corpus by rule.

Selection is deliberately mechanical so the statistics downstream mean
something: the universe is 10 liquid large-caps fixed up front, the three
as-of dates form a calendar grid chosen before looking at any outcome, and
each corpus is exactly "the up-to-6 most recent SEC filings before as_of"
via the EDGAR importer — regulator-stamped dates, zero discretionary picks.
(This is the corpus-composition-bias mitigation promised in
docs/evaluation-methodology.md §2.)

Usage (from repo root, online — hits SEC EDGAR + yfinance):
    backend/.venv/Scripts/python backend/scripts/build_grid_cases.py
Idempotent: cases whose directory already exists are skipped.
"""
from __future__ import annotations

import sys
import time
from datetime import date
from pathlib import Path

from hindsight.data import edgar
from hindsight.data.case_builder import NewCaseRequest, build_case, derive_case_id
from hindsight.data.market_source import YFinanceSource

UNIVERSE = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "AVGO", "JPM", "XOM"]
GRID_DATES = [date(2025, 2, 14), date(2025, 8, 15), date(2026, 2, 13)]
OUTCOME_WINDOW = 40
MAX_FILINGS = 6
SEC_SLEEP = 0.4  # stay well under SEC's 10 req/s fair-access ceiling


def cached_http_get():
    cache: dict[str, bytes] = {}

    def get(url: str) -> bytes:
        if url not in cache:
            time.sleep(SEC_SLEEP)
            cache[url] = edgar.default_http_get(url)
        return cache[url]

    return get


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    repo_root = Path(__file__).resolve().parents[2]
    datasets = repo_root / "datasets"
    http_get = cached_http_get()
    bars_fetcher = YFinanceSource().get_bars

    built, skipped, failed = [], [], []
    for ticker in UNIVERSE:
        for as_of in GRID_DATES:
            expected_id = derive_case_id(datasets, ticker, as_of)
            base_id = f"{ticker.lower()}_{as_of.strftime('%Y%m%d')}"
            if expected_id != base_id:
                skipped.append(base_id)  # directory already exists
                print(f"[skip] {base_id} already exists")
                continue
            try:
                filings = edgar.list_filings(
                    ticker, before=as_of, limit=MAX_FILINGS, http_get=http_get
                )
                docs = []
                for f in filings:
                    try:
                        docs.append(
                            edgar.fetch_filing(
                                ticker, f["cik"], f["accession"], f["document"],
                                f["form"], f["filed"], http_get=http_get,
                            )
                        )
                    except Exception as exc:  # noqa: BLE001 - one bad filing != no case
                        print(f"  [warn] {ticker} {f['form']} {f['filed']}: {exc}")
                if len(docs) < 2:
                    failed.append((base_id, f"only {len(docs)} usable filings"))
                    print(f"[fail] {base_id}: only {len(docs)} usable filings")
                    continue
                req = NewCaseRequest(
                    ticker=ticker,
                    as_of=as_of,
                    outcome_window_days=OUTCOME_WINDOW,
                    title=f"{ticker} as of {as_of.isoformat()} (mechanical grid)",
                    title_zh=f"{ticker} 网格案例（基准日 {as_of.isoformat()}）",
                    description=(
                        f"Mechanical grid case: corpus is exactly the {len(docs)} most "
                        f"recent SEC filings before {as_of.isoformat()} via the EDGAR "
                        "importer — no discretionary document picks, no narrative "
                        "authored after the fact. Part of the fixed UNIVERSE x "
                        "GRID_DATES sample built by backend/scripts/build_grid_cases.py."
                    ),
                    description_zh=(
                        f"机械网格案例：语料为基准日 {as_of.isoformat()} 之前最近的 "
                        f"{len(docs)} 份 SEC 申报（EDGAR 导入，日期由监管方盖章），"
                        "无任何人工挑选或事后撰写。由 build_grid_cases.py 按固定的"
                        "股票池 × 日期网格生成。"
                    ),
                    tags=["grid", "mechanical-corpus"],
                    docs=docs,
                )
                result = build_case(datasets, req, bars_fetcher=bars_fetcher)
                built.append(result["case_id"])
                print(f"[ok]   {result['case_id']}: {result['n_docs']} docs, "
                      f"{result['n_bars']} bars, window_open={result['outcome_window_still_open']}")
                time.sleep(1.0)  # be gentle with yfinance too
            except Exception as exc:  # noqa: BLE001 - keep building the rest
                failed.append((base_id, str(exc)[:200]))
                print(f"[fail] {base_id}: {exc}")

    print(f"\nBUILT {len(built)} | SKIPPED {len(skipped)} | FAILED {len(failed)}")
    for cid, why in failed:
        print(f"  failed: {cid} — {why}")


if __name__ == "__main__":
    main()
