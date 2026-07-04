"""Fetch adjusted bars for a case and freeze them to datasets/<case_id>/bars.json.

Usage (from repo root):
    backend/.venv/Scripts/python backend/scripts/freeze_case_bars.py \
        --case datasets/nvda_fy26q1 --start 2025-01-02 --end 2025-08-15

The snapshot is committed to git and never refreshed automatically —
baseline and outcome prices must come from the same fetch (spec §4.1).
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from hindsight.data.market_source import YFinanceSource


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="path to datasets/<case_id>")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args()

    case_dir = Path(args.case)
    meta = json.loads((case_dir / "meta.json").read_text(encoding="utf-8"))
    ticker = meta["ticker"]

    bars = YFinanceSource().get_bars(
        ticker, date.fromisoformat(args.start), date.fromisoformat(args.end)
    )
    payload = {
        "ticker": ticker,
        "auto_adjust": True,
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
    out = case_dir / "bars.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"froze {len(bars)} bars for {ticker} -> {out}")


if __name__ == "__main__":
    main()
