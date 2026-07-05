# Research memo

## Background
JPMorgan Chase closed at $301.01 on February 13, 2026, down roughly 5% over the prior two months after peaking near $333 in early January. The bank reported full-year 2025 record managed revenue of $185.6 billion, net income of $57.0 billion, and ROTCE of 20%, yet Q4 2025 net income fell 27% quarter-over-quarter to $13.0 billion, driven partly by a $2.2 billion provision increase tied to the Apple credit card portfolio forward purchase commitment. The 10-K filed on the as-of date and the January earnings 8-Ks constitute the available evidence set.

## Bull case
JPM's fundamental franchise remains exceptionally strong: record revenue for the eighth consecutive year at $185.6 billion, ROTCE of 20%, CET1 capital ratio of 14.5%, and book value per share of $127. The stock has sold off from $333 to $301 — over 9% — despite these results, potentially creating a value entry point. The Apple card portfolio acquisition signals strategic growth in card services, and the firm's fortress balance sheet with $4.4 trillion in assets provides a durable earnings base.

## Bear case
Q4 2025 results showed significant deterioration: net income fell 27% QoQ to $13.0 billion, income before tax expense dropped 26% QoQ, and the Apple card commitment added $2.2 billion to provisions while reducing the CET1 ratio by approximately 25 basis points. CCB net income fell 27% QoQ and 19% YoY, and the provision for credit losses surged 37% QoQ and 77% YoY to $4.66 billion. The stock's persistent decline from $333 to $301 suggests the market is pricing in these headwinds rather than discounting them.

## Conclusion
JPM presents a mixed picture: strong full-year fundamentals and capital position contrast with deteriorating quarterly trends and elevated credit costs from the Apple card commitment. The recent ~5% pullback from the as-of window's starting point may offer partial mean-reversion upside, but the Q4 earnings weakness and rising provisions create genuine downside risk. I expect modest recovery over a 30-trading-day horizon but with elevated volatility given competing forces.

## Claims
- `c1` [direction, 30d, conf 0.45] JPM closes at least 3% above the as-of price of $301.01 on the 30th trading day after 2026-02-13 -> **miss** (horizon-end return -6.21% vs up 3.0%)
- `c2` [magnitude, 30d, conf 0.35] JPM's 30-trading-day return lands between +3% and +12% -> **miss** (horizon-end return -6.21% vs [3.0, 12.0])
- `c3` [volatility, 20d, conf 0.55] JPM's realized daily log-return volatility over the 20 trading days after as-of is above the 70th percentile of the prior 252-day rolling windows -> **miss** (realized vol 0.01424 vs p70 0.01614 (above))
