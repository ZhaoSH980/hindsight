# Research memo

## Background
XOM has rallied approximately 27% from mid-December 2025 to February 13, 2026, reaching $147.45. The company reported full-year 2025 earnings of $28.8 billion, down from $33.7 billion in 2024, reflecting weaker crude prices and chemical margins, partially offset by record upstream production of 4.7 million BOE/d and $37.2 billion in shareholder distributions. Despite declining year-over-year profitability, ExxonMobil highlighted structural cost savings of $15.1 billion cumulative since 2019 and plans for $20 billion in share repurchases through 2026.

## Bull case
ExxonMobil's production reached its highest level in over 40 years at 4.7 million BOE/d, with advantaged assets in the Permian and Guyana hitting annual records and representing 59% of production. The company generated $52.0 billion in operating cash flow, announced $20 billion in planned share repurchases through 2026, and achieved $3.0 billion in structural cost savings in 2025 alone, targeting $20 billion cumulative by 2030. Energy Products earnings rose $3.4 billion year-over-year on stronger refining margins and record throughput, demonstrating diversified earnings resilience.

## Bear case
Full-year earnings fell $4.8 billion from 2024 to 2025, driven by weaker crude realizations, chemical margins that collapsed to $800 million from $2.6 billion, and higher depreciation of $26.0 billion versus $19.0 billion in 2019. Q4 earnings dropped $1.0 billion sequentially, Chemical Products posted a quarterly loss of $281 million, and ROCE declined to 9.3% from 12.7% in 2024. The stock's 27% rally over two months has likely priced in much of the operational improvement, leaving limited upside if crude prices remain soft.

## Conclusion
XOM's recent rally has been driven by strong production growth and shareholder returns, but the fundamental earnings trajectory is declining year-over-year with falling ROCE and weak chemical margins. The stock's sharp appreciation over eight weeks creates meaningful risk of a pullback, particularly given the Q4 sequential earnings decline and soft commodity environment. I expect modest downside or sideways trading over the next 40 trading days as the market digests the mixed results.

## Claims
- `c1` [direction, 20d, conf 0.42] XOM closes at least 3% below the as-of price on the 20th trading day after as-of -> **miss** (horizon-end return +5.91% vs down 3.0%)
- `c2` [magnitude, 20d, conf 0.3] XOM's 20-trading-day return lands between -8% and -3% -> **miss** (horizon-end return +5.91% vs [-8.0, -3.0])
- `c3` [volatility, 40d, conf 0.38] XOM's realized daily log-return volatility over the next 40 trading days will be above the 70th percentile of same-length rolling windows from the prior 252 trading days -> **hit** (realized vol 0.01864 vs p70 0.01448 (above))
