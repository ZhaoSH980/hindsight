"""market_data tool: adjusted price history up to as_of, with derived stats."""
from __future__ import annotations

import json
from datetime import date, timedelta

from hindsight.sandbox.errors import LookaheadError
from hindsight.sandbox.gate import SandboxedMarketData
from hindsight.tools.registry import ToolSpec


def make_market_tool(market: SandboxedMarketData, ticker: str) -> ToolSpec:
    def price_history(lookback_days: int = 60) -> str:
        end = market.as_of
        start = end - timedelta(days=lookback_days)
        try:
            bars = market.get_bars(ticker, start, end)
        except LookaheadError as exc:  # defensive; end==as_of never triggers it
            return json.dumps({"error": str(exc)})
        if not bars:
            return json.dumps({"error": f"no bars for {ticker} in window"})
        closes = [b.close for b in bars]
        pct = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0.0
        return json.dumps(
            {
                "ticker": ticker,
                "as_of": end.isoformat(),
                "bars": [
                    {"date": b.date.isoformat(), "close": round(b.close, 4)}
                    for b in bars
                ],
                "window_return_pct": round(pct, 2),
                "last_close": round(closes[-1], 4),
            }
        )

    return ToolSpec(
        name="price_history",
        description=(
            f"Daily adjusted closes for {ticker} ending at the as_of date. "
            "Data after as_of does not exist for this run."
        ),
        parameters={
            "type": "object",
            "properties": {
                "lookback_days": {"type": "integer", "default": 60},
            },
            "required": [],
        },
        fn=price_history,
    )
