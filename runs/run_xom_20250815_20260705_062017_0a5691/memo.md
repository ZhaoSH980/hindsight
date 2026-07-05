# Research memo

## Background
XOM closed at $104.16 on August 15, 2025, down roughly 4.4% over the prior two months as crude oil prices softened and refining margins remained under pressure. Second-quarter 2025 earnings of $7.1 billion declined from $7.7 billion in Q1, driven by lower crude and natural gas realizations, though the company continued aggressive share repurchases of ~$5 billion per quarter. The 10-Q filed August 4 highlights tariff uncertainty and volatile trade conditions as ongoing risks to the business outlook.

## Bull case
ExxonMobil's advantaged volume growth from Permian and Guyana continues to deliver record production levels, with 2Q25 marking the highest second-quarter output since the Exxon-Mobil merger. The company has commenced start-up of six of ten key projects expected to improve earnings power by more than $3 billion in 2026 at constant prices and margins, while returning $9.2 billion to shareholders in Q2 alone, on pace for $20 billion in annual repurchases.

## Bear case
Earnings declined $631 million sequentially from Q1 to Q2 2025 due to weaker crude and natural gas realizations, and YTD earnings of $14.8 billion are down $2.7 billion versus the first half of 2024. Chemical margins remain at bottom-of-cycle conditions, global refining margins are below their 10-year historical range, and the 10-Q explicitly flags a volatile global trade environment with highly uncertain tariff risks that could further pressure commodity prices and demand.

## Conclusion
XOM faces near-term headwinds from weakening crude realizations, below-cycle refining and chemical margins, and tariff-driven macro uncertainty that have already pushed the stock down over 4% in two months. While structural cost savings, advantaged volume growth, and massive shareholder returns provide a floor, the deteriorating commodity price environment is likely to keep shares under pressure over the next several weeks. A modest recovery is plausible if oil prices stabilize, but the risk-reward skews slightly negative given the earnings momentum deterioration.

## Claims
- `c1` [direction, 20d, conf 0.45] XOM closes at least 3% below the as-of price of $104.16 on the 20th trading day after August 15, 2025 -> **miss** (horizon-end return +5.50% vs down 3.0%)
- `c2` [magnitude, 20d, conf 0.35] XOM's 20-trading-day return falls between -8% and -3% -> **miss** (horizon-end return +5.50% vs [-8.0, -3.0])
- `c3` [volatility, 40d, conf 0.55] XOM's realized daily log-return volatility over the 40-trading-day horizon window falls above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01208 vs p60 0.01430 (above))
