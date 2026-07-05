# Research memo

## Background
JPMorgan Chase closed at $301.01 on February 13, 2026, down roughly 5% over the prior ~45 trading days from a mid-December peak near $326. The firm filed its 10-K on the as-of date and reported Q4 2025 earnings on January 13, 2026, showing full-year 2025 managed revenue of $185.6 billion (up 3% YoY) and a CET1 capital ratio of 14.5%. The stock's recent pullback coincided with a broader decline from late-January highs around $333 to current levels near $301.

## Bull case
JPM's fundamental franchise remains exceptionally strong, with full-year 2025 net income of $57 billion, ROTCE of 18%, book value per share of $127, and a CET1 ratio of 14.5% supported by $288 billion in CET1 capital and $1.5 trillion in cash and marketable securities. The firm raised $3.3 trillion in credit and capital for clients during 2025, and all three major business segments grew revenue year-over-year (CIB +12%, AWM +12%, CCB +6%). At $301, the stock trades at roughly 2.4x book value and 2.8x tangible book value of $107.56, which is reasonable for a bank generating 18% ROTCE, and the recent ~10% pullback from January highs may present a buying opportunity for a best-in-class franchise.

## Bear case
Q4 2025 results showed sequential deterioration, with net income declining 10% QoQ to $13.0 billion and EPS falling 9% to $4.63, driven by a 37% increase in provision for credit losses to $4.655 billion and an 8% decline in income before tax. The Apple credit card portfolio forward purchase commitment added $2.2 billion to provisions and reduced the CET1 ratio by approximately 25 basis points. CCB net income fell 27% QoQ to $3.642 billion, and the stock has been in a persistent downtrend since mid-January, losing over 9% in three weeks, suggesting the market is pricing in deteriorating credit conditions and slowing momentum.

## Conclusion
JPM presents a mixed picture: best-in-class profitability and capital strength contrast with deteriorating Q4 trends and a sharp recent price decline. The stock's ~10% pullback from January highs creates a potential value entry point given the 18% ROTCE and fortress balance sheet, but near-term credit costs (including the Apple card portfolio impact) and the persistent downtrend warrant caution. Over a 40-trading-day horizon, the risk-reward appears moderately constructive for a mean-reversion bounce from oversold levels, though conviction is tempered by the unclear trajectory of credit costs and the market's bearish near-term stance.

## Claims
- `c1` [direction, 20d, conf 0.45] JPM closes at least 3% above the as-of price ($301.01) on the 20th trading day after 2026-02-13 -> **miss** (horizon-end return -5.42% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.35] JPM's 20-trading-day return lands between +3% and +10% -> **miss** (horizon-end return -5.42% vs [3.0, 10.0])
- `c3` [direction, 40d, conf 0.48] JPM closes at least 5% above the as-of price ($301.01) on the 40th trading day after 2026-02-13 -> **miss** (horizon-end return +3.36% vs up 5.0%)
- `c4` [volatility, 40d, conf 0.4] JPM's realized daily log-return volatility over the 40 trading days after as-of is below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01464 vs p60 0.01392 (below))
