# Research memo

## Background
Apple reported record Q1 FY2026 results on January 29, 2026, with revenue of $143.8 billion (up 16% YoY) and diluted EPS of $2.84 (up 19% YoY), driven by all-time highs in iPhone and Services revenue. Despite these strong fundamentals, the stock has sold off sharply, falling from ~$277 on February 6 to ~$255 on February 13, a one-week decline of roughly 8%. The 10-Q filed January 30 flags ongoing tariff risks, including a Section 232 semiconductor investigation, and management explicitly warns that gross margins will be subject to volatility and downward pressure.

## Bull case
Apple's Q1 FY2026 results demonstrate exceptional fundamental strength: record revenue and EPS, iPhone revenue up 23% YoY to $85.3 billion, Services up 14% to $30 billion, total gross margin expanding 130 basis points to 48.2%, and nearly $54 billion in operating cash flow. The sharp one-week sell-off from ~$277 to ~$255 has created a potentially oversold condition, and the installed base surpassing 2.5 billion active devices provides a durable ecosystem moat that supports long-term revenue visibility.

## Bear case
The 10-Q explicitly warns that gross margins 'will be subject to volatility and downward pressure' due to tariff costs already impacting products, and the Section 232 semiconductor investigation announced January 14, 2026 could impose additional tariffs on products containing semiconductors. R&D expenses surged 32% YoY to $10.9 billion, total operating expenses up 19%, and Mac revenue declined 7%. The stock's 8% one-week decline suggests the market is pricing in these escalating risks, and the price chart shows a pattern of lower highs since early February.

## Conclusion
Apple's fundamentals are genuinely strong with record revenue, EPS, and margin expansion, but the stock's sharp recent decline and management's explicit gross margin warnings suggest the market is increasingly concerned about tariff escalation and rising cost pressures. Over a 20-trading-day horizon, the oversold condition following the ~8% one-week drop creates a reasonable probability of a modest rebound, but tariff overhang and rising operating expenses cap conviction. Over 40 days, the risk-reward appears more balanced as tariff uncertainties may intensify.

## Claims
- `c1` [direction, 20d, conf 0.45] AAPL closes at least 3% above the as-of price of $255.54 on the 20th trading day after February 13, 2026 -> **miss** (horizon-end return -1.16% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.35] AAPL's 20-trading-day return lands between +3% and +10% -> **miss** (horizon-end return -1.16% vs [3.0, 10.0])
- `c3` [volatility, 40d, conf 0.55] AAPL's realized daily log-return volatility over the 40 trading days after as-of is above the 70th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01348 vs p70 0.01656 (above))
