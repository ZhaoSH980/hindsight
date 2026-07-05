# Research memo

## Background
JPMorgan Chase reported Q2 2025 net income of $15.0 billion (EPS $5.24), with ROTCE of 21% and a CET1 capital ratio of 15.1%. The stock has risen ~8% over the past two months to $286.32 as of August 15, 2025. The firm authorized a new $50 billion share repurchase program effective July 1, 2025, replacing the prior $30 billion program, while TBVPS grew 11% year-over-year to $103.40. Credit costs are rising modestly, with net charge-offs up to $2.4 billion in Q2, predominantly in Card Services.

## Bull case
JPM's robust capital position (CET1 ratio of 15.1%, well above regulatory minimums) and the newly authorized $50 billion buyback program provide strong support for shareholder returns. TBVPS grew 11% YoY to $103.40, and the firm maintains a 21% ROTCE, signaling efficient capital deployment. With $970 billion in HQLA and ~$1.5 trillion in total liquidity sources, JPM has ample capacity to weather volatility while continuing aggressive capital return.

## Bear case
Net charge-offs rose to $2.4 billion in Q2 2025 (up $179 million YoY), with the Card Services net charge-off rate at 3.40%, and nonperforming assets increased to $10.5 billion from $8.4 billion a year ago. Total net revenue declined 11% YoY, largely due to the absence of the prior-year $7.9 billion Visa share gain, and the allowance for loan losses coverage ratio ticked up to 1.85% from 1.81%. Rising consumer credit deterioration could pressure future earnings.

## Conclusion
JPM's fundamentals remain strong with best-in-class capital ratios, robust liquidity, and a significant new buyback authorization that should provide a floor for the stock. However, rising credit costs in Card Services and the absence of the prior-year Visa gain create headwinds to revenue growth. Over a 40-trading-day horizon, the stock is likely to trade in a relatively tight range with modest upside bias, supported by capital return momentum but capped by credit normalization concerns.

## Claims
- `c1` [direction, 40d, conf 0.45] JPM closes at least 2% above the as-of price of $286.32 on the 40th trading day after August 15, 2025 -> **hit** (horizon-end return +6.53% vs up 2.0%)
- `c2` [magnitude, 40d, conf 0.5] JPM's 40-trading-day return lands between -3% and +5% -> **miss** (horizon-end return +6.53% vs [-3.0, 5.0])
- `c3` [volatility, 40d, conf 0.55] JPM's realized daily log-return volatility over 40 trading days falls below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.01001 vs p60 0.01733 (below))
