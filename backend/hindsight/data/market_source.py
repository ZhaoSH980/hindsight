"""Market data sources. Runtime always reads frozen snapshots (spec §4.1)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Protocol

from hindsight.data.models import Bar


class MarketDataSource(Protocol):
    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        """Daily adjusted OHLCV bars with start <= bar.date <= end."""
        ...


class FrozenBarsSource:
    """Reads a bars.json snapshot committed under datasets/<case_id>/."""

    def __init__(self, bars_path: Path):
        payload = json.loads(Path(bars_path).read_text(encoding="utf-8"))
        self._ticker: str = payload["ticker"]
        self._bars = sorted(
            (Bar(**b) for b in payload["bars"]), key=lambda b: b.date
        )

    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        if ticker != self._ticker:
            raise ValueError(f"snapshot holds {self._ticker}, not {ticker}")
        return [b for b in self._bars if start <= b.date <= end]


class YFinanceSource:
    """Case-authoring source. Not used at runtime; import stays lazy."""

    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        import yfinance as yf

        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=end.isoformat(),
            progress=False,
            auto_adjust=True,  # explicit: adjusted prices, never rely on defaults
        )
        if df is None or df.empty:
            raise ValueError(f"yfinance returned no data for {ticker}")
        if hasattr(df.columns, "levels"):  # flatten MultiIndex columns
            df.columns = [c[0] for c in df.columns]
        return [
            Bar(
                date=idx.date(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
            for idx, row in df.iterrows()
        ]
