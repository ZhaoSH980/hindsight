# Research memo

## Background
AMZN closed at $198.79 on 2026-02-13, down ~10.7% over the prior 41 trading days, with the decline accelerating sharply after its Q4 2025 earnings release on February 5. The 8-K filed that day revealed Q4 net sales of $213.4B (up 14% YoY) and AWS growth of 24%, but Q1 2026 operating income guidance of $16.5–$21.5B (vs. $18.4B in Q1 2025) disappointed, partly due to ~$1B in higher Amazon Leo costs and investments in quick commerce. Management also announced plans for ~$200B in 2026 capex, while free cash flow fell to $11.2B TTM from $38.2B the prior year, driven by a $50.7B YoY increase in property and equipment purchases primarily for AI investments.

## Bull case
Despite the sharp post-earnings selloff, Amazon's Q4 results showed genuine operational strength: AWS grew 24% (its fastest in 13 quarters), advertising grew 22%, and Q4 operating income excluding special charges would have been $27.4B. The Q1 2026 revenue guidance of $173.5–$178.5B implies 11–15% YoY growth, and the operating income midpoint of $19B is only modestly below Q1 2025's $18.4B despite massive investment headwinds, suggesting the underlying business ex-investments is still accelerating. With the stock already down ~10.7% in the measured window and ~20% from its late-January peak near $247, much of the near-term disappointment may be priced in.

## Bear case
The Q1 2026 operating income guidance midpoint of $19B barely exceeds Q1 2025's $18.4B despite 11–15% revenue growth, reflecting severe margin compression from ~$1B in Amazon Leo costs, quick commerce investments, and sharper international pricing. Free cash flow collapsed to $11.2B TTM from $38.2B, and management plans ~$200B in 2026 capex—a staggering increase that could take years to generate returns. The 10-K explicitly warns that investments in AI and new technologies 'may not meet our expectations' and could be written down, while the stock's rapid descent from $247 to $199 in under a month signals that institutional selling pressure remains intense and may not be exhausted.

## Conclusion
The post-earnings selloff has been severe and may be overdone in the near term given Amazon's strong AWS and advertising momentum, but the massive capex ramp and margin compression from new investments create genuine uncertainty about near-term earnings power. I expect the stock to find a floor and partially recover over the next 20–40 trading days as oversold conditions stabilize, though the magnitude of any rebound is likely to be modest given the overhang of investment concerns. The risk of further downside appears lower than the probability of at least a partial mean-reversion bounce from deeply oversold levels.

## Claims
- `c1` [direction, 20d, conf 0.55] AMZN closes at least 3% above the as-of price of $198.79 on the 20th trading day after 2026-02-13 -> **hit** (horizon-end return +6.51% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.4] AMZN's 20-trading-day return lands between +3% and +12% -> **hit** (horizon-end return +6.51% vs [3.0, 12.0])
- `c3` [volatility, 20d, conf 0.5] AMZN's realized daily log-return volatility over the 20 trading days after 2026-02-13 falls below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.01601 vs p60 0.02038 (below))
- `c4` [direction, 40d, conf 0.52] AMZN closes at least 5% above the as-of price of $198.79 on the 40th trading day after 2026-02-13 -> **hit** (horizon-end return +25.27% vs up 5.0%)
