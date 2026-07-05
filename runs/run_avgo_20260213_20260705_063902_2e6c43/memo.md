# Research memo

## Background
Broadcom closed at $323.98 on February 13, 2026, down 4.13% over the prior trading week and well off its late-January highs above $353. The company reported record fiscal Q4 2025 revenue of $18.0 billion (up 28% YoY) on December 11, 2025, with AI semiconductor revenue surging 74% YoY, and guided Q1 FY2026 revenue to approximately $19.1 billion. Despite these strong fundamentals, the stock has experienced significant volatility, falling from $353 on January 13 to a low of $306.92 on February 4 before partially recovering.

## Bull case
Broadcom's Q1 FY2026 guidance of $19.1 billion in revenue (28% YoY growth) with AI semiconductor revenue expected to double year-over-year to $8.2 billion provides a strong fundamental catalyst. The company generated $26.9 billion in free cash flow in FY2025 and raised its dividend 10%, signaling management confidence. With the stock trading approximately 8% below its January highs despite record financial results, there is meaningful upside potential if the market re-rates the stock toward its fundamentals.

## Bear case
AVGO has demonstrated significant volatility and a downward trend since mid-January, falling from $353 to $324 in one month despite strong earnings reported in December. The 10-K explicitly warns of risks including cyclicality in the semiconductor industry, customer demand fluctuations, and global economic uncertainty. The stock's 4.13% decline in the most recent week suggests negative momentum that could persist, particularly if macroeconomic concerns or AI sector rotation pressures valuations further.

## Conclusion
Broadcom's fundamentals are exceptionally strong with record revenue, 74% AI growth, and robust free cash flow, but the stock's recent price action shows significant volatility and a pullback from highs. Over a 40-trading-day horizon, the fundamental strength and attractive valuation relative to recent prices provide a moderate bullish bias, though near-term momentum and sector volatility create meaningful downside risk. The most probable outcome is a recovery toward the $330-350 range as the market digests the strong Q1 guidance, but with elevated volatility.

## Claims
- `c1` [direction, 40d, conf 0.55] AVGO closes at least 5% above the as-of price of $323.98 on the 40th trading day after 2026-02-13 -> **hit** (horizon-end return +17.35% vs up 5.0%)
- `c2` [magnitude, 40d, conf 0.45] AVGO's 40-trading-day return lands between +5% and +20% -> **hit** (horizon-end return +17.35% vs [5.0, 20.0])
- `c3` [volatility, 20d, conf 0.6] AVGO's realized daily log-return volatility over the next 20 trading days exceeds the 75th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.02145 vs p75 0.03388 (above))
