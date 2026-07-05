# Research memo

## Background
XOM has rallied approximately 27% over the two months leading into the as-of date of February 13, 2026, closing at $147.45 after reporting full-year 2025 earnings of $28.8 billion on January 30. While earnings declined from $33.7 billion in 2024 due to weaker crude realizations and chemical margins, the company highlighted record upstream production of 4.7 million BOE/d, $37.2 billion in shareholder distributions, and $15.1 billion in cumulative structural cost savings. The stock's sharp recent appreciation creates both momentum and mean-reversion risks over the near term.

## Bull case
ExxonMobil's operational execution remains strong, with record Permian and Guyana production, advantaged assets representing 59% of output, and a commitment to repurchase $20 billion of shares through 2026. Energy Products earnings surged $3.4 billion year-over-year on stronger refining margins and record throughput, while the company's structural cost savings program targets $20 billion by 2030. These fundamentals, combined with industry-leading cash flow of $52 billion and a planned investment case presentation on February 20, could sustain positive momentum.

## Bear case
Full-year earnings fell $4.8 billion from 2024, driven by weaker crude prices, declining chemical margins (Chemical Products earnings dropped from $2.6 billion to $800 million), and higher depreciation. Q4 earnings fell $1.0 billion sequentially, and upstream earnings excluding identified items declined from $25.2 billion to $22.2 billion. After a 27% rally in two months, the stock has already priced in much of the operational strength, leaving it vulnerable to profit-taking and any disappointment from the upcoming February 20 investor presentation.

## Conclusion
XOM's recent rally has been driven by strong operational execution and shareholder returns, but the pace of appreciation—27% in two months—creates elevated near-term pullback risk after such a steep run. The fundamental story remains solid with record production and disciplined capital allocation, yet declining earnings and weak chemical margins suggest the stock may have gotten ahead of itself. I expect some consolidation or modest pullback over the next 20-40 trading days as the market digests the rapid move.

## Claims
- `c1` [direction, 20d, conf 0.45] XOM closes at least 3% below the as-of price on the 20th trading day after as-of -> **miss** (horizon-end return +5.91% vs down 3.0%)
- `c2` [magnitude, 20d, conf 0.3] XOM's 20-trading-day return lands between -8% and -3% -> **miss** (horizon-end return +5.91% vs [-8.0, -3.0])
- `c3` [volatility, 40d, conf 0.55] XOM's realized daily log-return volatility over the next 40 trading days is above the 70th percentile of same-length rolling windows from the prior 252 trading days -> **hit** (realized vol 0.01864 vs p70 0.01448 (above))
