# Research memo

## Background
Amazon reported strong Q4 2024 results on February 6, 2025, with net sales up 10% to $187.8B and operating income surging to $21.2B from $13.2B year-over-year. AWS continued its 19% growth trajectory with $28.8B in quarterly revenue and $10.6B in operating income. However, Q1 2025 guidance was mixed—net sales growth of 5-9% reflects an unusually large $2.1B FX headwind and a Leap Year comparison impact, while operating income guidance of $14.0-18.0B brackets the prior year's $15.3B. The stock closed at $228.68 on February 14, 2025, down 1.82% over the prior ~40 trading days, having sold off from a late-January peak near $238.

## Bull case
Amazon's Q4 results demonstrate accelerating profitability across all segments—North America operating margin reached 8.0% (up from 6.1% in Q4 2023), International swung from a loss to $1.3B operating income, and AWS operating income grew 47% year-over-year. Full-year 2024 operating income nearly doubled to $68.6B from $36.9B, with operating cash flow TTM at $115.9B. The Q1 2025 operating income midpoint of $16.0B still represents solid profitability despite FX headwinds, and the Leap Year and FX impacts are transient. With the stock having pulled back ~4% from its post-earnings peak, strong fundamentals could support a recovery.

## Bear case
Q1 2025 net sales guidance of 5-9% growth represents a meaningful deceleration from Q4's 10% and the full year's 11%, driven by a $2.1B FX headwind (150 bps) and the absence of Leap Year benefit (~$1.5B in Q1 2024). Operating income guidance of $14.0-18.0B is wide and its midpoint of $16.0B is only modestly above Q1 2024's $15.3B, suggesting profit growth may be flattening sequentially. Capex is surging—TTM property and equipment purchases reached $77.7B, up 61% year-over-year—which could pressure free cash flow, which already declined from $52.97B TTM in Q2 2024 to $38.2B TTM in Q4 2024. The stock's recent decline and elevated volatility around earnings suggest the market is questioning the growth-investment trade-off.

## Conclusion
Amazon's fundamentals remain strong with accelerating margins and robust AWS growth, but Q1 2025 guidance signals a temporary growth deceleration from FX and calendar effects alongside surging capital expenditures that are compressing free cash flow. The stock's recent pullback partially reflects these concerns, creating a balanced risk-reward setup over a 40-day horizon. I expect AMZN to trade roughly flat to modestly higher as the market digests the transient nature of Q1 headwinds, with elevated volatility persisting near term.

## Claims
- `c1` [direction, 40d, conf 0.45] AMZN closes at least 2% above the as-of price ($228.68) on the 40th trading day after as-of -> **miss** (horizon-end return -20.36% vs up 2.0%)
- `c2` [magnitude, 40d, conf 0.5] AMZN's 40-trading-day return lands between -3% and +5% -> **miss** (horizon-end return -20.36% vs [-3.0, 5.0])
- `c3` [volatility, 20d, conf 0.55] AMZN's realized daily log-return volatility over the next 20 trading days is above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.01809 vs p60 0.01710 (above))
