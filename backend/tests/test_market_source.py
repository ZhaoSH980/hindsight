import json
from datetime import date

import pytest

from hindsight.data.market_source import FrozenBarsSource

BARS = {
    "ticker": "NVDA",
    "auto_adjust": True,
    "fetched_at": "2026-07-04T12:00:00",
    "bars": [
        {"date": "2025-05-20", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
        {"date": "2025-05-21", "open": 1.5, "high": 2.5, "low": 1, "close": 2.0, "volume": 110},
        {"date": "2025-05-22", "open": 2.0, "high": 3.0, "low": 1.5, "close": 2.5, "volume": 120},
    ],
}


@pytest.fixture
def source(tmp_path):
    p = tmp_path / "bars.json"
    p.write_text(json.dumps(BARS), encoding="utf-8")
    return FrozenBarsSource(p)


def test_range_filter_inclusive(source):
    bars = source.get_bars("NVDA", date(2025, 5, 21), date(2025, 5, 22))
    assert [b.date.isoformat() for b in bars] == ["2025-05-21", "2025-05-22"]
    assert bars[0].close == 2.0


def test_unknown_ticker_raises(source):
    with pytest.raises(ValueError, match="TSLA"):
        source.get_bars("TSLA", date(2025, 5, 20), date(2025, 5, 22))


def test_bars_sorted_by_date(source):
    bars = source.get_bars("NVDA", date(2025, 1, 1), date(2026, 1, 1))
    assert [b.date for b in bars] == sorted(b.date for b in bars)


def test_yfinance_source_flattens_and_inclusive_end(monkeypatch):
    import pandas as pd
    import yfinance as yf

    from hindsight.data.market_source import YFinanceSource

    captured = {}

    def fake_download(ticker, start, end, progress, auto_adjust):
        captured["end"] = end
        idx = pd.DatetimeIndex([pd.Timestamp("2025-05-21"), pd.Timestamp("2025-05-22")])
        cols = pd.MultiIndex.from_product(
            [["Open", "High", "Low", "Close", "Volume"], [ticker]]
        )
        return pd.DataFrame(
            [[1, 2, 0.5, 1.5, 100], [1.5, 2.5, 1, 2.0, 110]], index=idx, columns=cols
        )

    monkeypatch.setattr(yf, "download", fake_download)
    bars = YFinanceSource().get_bars("NVDA", date(2025, 5, 21), date(2025, 5, 22))
    assert captured["end"] == "2025-05-23"
    assert [b.date.isoformat() for b in bars] == ["2025-05-21", "2025-05-22"]
    assert bars[0].close == 1.5
