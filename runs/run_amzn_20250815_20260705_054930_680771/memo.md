# Research memo

## Background
Amazon reported strong Q2 2025 results on July 31, with net sales up 13% to $167.7B and operating income rising to $19.2B from $14.7B a year prior. AWS grew 17.5% YoY to $30.9B, and the company guided Q3 net sales to $174-179.5B (10-13% growth). Despite the earnings beat, the stock dropped sharply from $234.11 on July 31 to $214.75 on August 1, before partially recovering to $231.03 by August 15.

## Bull case
Amazon's Q2 results demonstrate accelerating revenue growth (13% vs. 9% in Q1) with expanding operating margins across all three segments, particularly North America (7.5% operating margin vs. 5.8% prior year) and International (4.1% vs. 0.9%). Q3 guidance implies continued top-line acceleration to 10-13% growth, and the stock has already recovered most of its post-earnings drop, suggesting the market is digesting the strong results favorably.

## Bear case
The post-earnings sell-off from $234 to $214.75 on August 1 signals investor concern despite the beat, likely driven by heavy AI capital expenditure requirements noted in the April letter — AI chips are 'much more expensive than CPU chips' and capital is deployed upfront before monetization. AWS growth decelerated slightly from 17% to 17.5% QoQ but the massive capex cycle could pressure free cash flow, and Q3 operating income guidance of $15.5-20.5B is wide, with the midpoint below Q2's $19.2B, suggesting potential margin compression ahead.

## Conclusion
Amazon's fundamentals remain strong with accelerating revenue and expanding margins, but the post-earnings volatility and wide Q3 operating income guidance range reflect genuine uncertainty about capex intensity and near-term margin trajectory. The stock's rapid recovery to $231 suggests the market ultimately favors the bull case, but the sharp August 1 drop demonstrates fragility. Over a 40-trading-day horizon, modest upside appears more likely than further downside given the fundamental momentum, though volatility is expected to remain elevated.

## Claims
- `c1` [direction, 40d, conf 0.55] AMZN closes at least 3% above the as-of price of $231.03 on the 40th trading day after August 15, 2025 -> **miss** (horizon-end return -4.74% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.42] AMZN's 40-trading-day return falls between +3% and +12% -> **miss** (horizon-end return -4.74% vs [3.0, 12.0])
- `c3` [volatility, 20d, conf 0.58] AMZN's realized daily log-return volatility over the 20 trading days following August 15, 2025 exceeds the 70th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.01707 vs p70 0.02036 (above))
