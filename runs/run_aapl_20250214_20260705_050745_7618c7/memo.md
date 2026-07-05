# Research memo

## Background
Apple reported record fiscal Q1 2025 revenue of $124.3 billion (up 4% YoY) and record diluted EPS of $2.40 (up 10% YoY) on January 30, 2025, with Services reaching an all-time high of $26.3 billion. However, iPhone revenue was essentially flat year-over-year and Greater China net sales declined 11%, reflecting ongoing competitive and macroeconomic headwinds. The stock has been volatile, declining roughly 2.5% over the prior ~40 trading days to close at $243.31 on February 14, 2025.

## Bull case
Apple's record Q1 revenue and EPS, combined with 14% Services growth and an all-time-high installed base across all geographic segments, demonstrate the durability of its ecosystem and monetization potential. The expansion of Apple Intelligence to more languages in April 2025 could serve as a catalyst for an upgrade cycle, while Mac (+16%) and iPad (+15%) growth show product-line diversification beyond iPhone.

## Bear case
iPhone revenue was flat year-over-year at $69.1 billion and Greater China net sales fell 11%, signaling weakness in Apple's largest product category and a key growth market. The 10-K highlights substantial risks from concentrated manufacturing in China mainland and exposure to tariffs, trade restrictions, and geopolitical tensions that could materially disrupt the supply chain and compress margins.

## Conclusion
Apple's fundamentals remain strong with record revenue and EPS, but flat iPhone sales and declining Greater China revenue temper the near-term outlook. The stock's recent recovery from late-January lows suggests the market is pricing in a balanced scenario, leaving limited upside catalysts within a 40-trading-day horizon absent new product or macro developments. Geopolitical and tariff risks add downside uncertainty that could cap gains.

## Claims
- `c1` [direction, 20d, conf 0.55] AAPL closes at or above its as-of price (no decline) on the 20th trading day after as-of -> **miss** (horizon-end return -12.51% vs up 0.5%)
- `c2` [magnitude, 20d, conf 0.38] AAPL's 20-trading-day return lands between +1% and +8% -> **miss** (horizon-end return -12.51% vs [1.0, 8.0])
- `c3` [volatility, 40d, conf 0.45] AAPL's realized daily log-return volatility over the next 40 trading days falls below the 50th percentile of the prior ~252-day rolling windows -> **miss** (realized vol 0.03600 vs p50 0.01447 (below))
- `c4` [direction, 40d, conf 0.58] AAPL closes no more than 5% below its as-of price on the 40th trading day after as-of -> **miss** (horizon-end return -17.20% vs up 0.5%)
