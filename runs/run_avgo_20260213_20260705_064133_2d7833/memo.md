# Research memo

## Background
Broadcom closed at $323.98 on 2026-02-13, down 4.1% over the prior trading week and roughly 7% below its late-January highs near $353. The sell-off comes despite the company's December 11 Q4 FY2025 earnings showing 28% YoY revenue growth to $18.0B, record FY2025 free cash flow of $26.9B, and Q1 FY2026 guidance of $19.1B in revenue with AI semiconductor revenue expected to double YoY to $8.2B. The stock's recent decline suggests the market is weighing near-term risks against strong fundamental momentum.

## Bull case
Broadcom's Q1 FY2026 guidance of $19.1B revenue (28% YoY growth) with AI semiconductor revenue doubling to $8.2B, combined with record FY2025 free cash flow of $26.9B (41% of revenue) and a 10% dividend increase, demonstrates exceptional operational execution and AI-driven growth that should support a price recovery from the recent pullback.

## Bear case
AVGO carries $66.3B in total debt principal with significant near-term maturities ($3.15B short-term debt at FY end vs. $1.4B the prior year), and the stock has already declined ~8% from its January 13 peak of $353 to $324, suggesting the market may be pricing in concerns about customer concentration, semiconductor cyclicality, or AI revenue sustainability that could continue to pressure shares.

## Conclusion
The fundamental picture is strong with AI-driven revenue growth and robust cash generation, but the recent price action indicates meaningful near-term selling pressure. Over a 40-trading-day horizon, the valuation case for a rebound is compelling but tempered by the stock's demonstrated volatility and the market's apparent skepticism despite strong guidance.

## Claims
- `c1` [direction, 40d, conf 0.55] AVGO closes at least 5% above the as-of price of $323.98 on the 40th trading day after 2026-02-13 -> **hit** (horizon-end return +17.35% vs up 5.0%)
- `c2` [magnitude, 40d, conf 0.45] AVGO's 40-trading-day return lands between +5% and +20% -> **hit** (horizon-end return +17.35% vs [5.0, 20.0])
- `c3` [volatility, 20d, conf 0.5] AVGO's realized daily log-return volatility over the next 20 trading days exceeds the 75th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.02145 vs p75 0.03388 (above))
