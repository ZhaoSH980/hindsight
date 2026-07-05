# Research memo

## Background
Apple reported record June-quarter revenue of $94.0 billion (up 10% YoY) and EPS of $1.57 (up 12% YoY) on July 31, 2025, with iPhone revenue hitting $44.6 billion and Services reaching an all-time high of $27.4 billion. The stock rallied sharply into mid-August, rising ~16.9% over the prior two months to close at $230.94 on August 15. However, the 10-Q explicitly flags tariff uncertainty as a material risk to gross margins and supply chain, with Products gross margin percentage already declining YoY due to tariffs and product mix.

## Bull case
Apple's Q3 2025 results demonstrate broad-based revenue strength across every geographic segment, with total revenue up 10%, iPhone up 13%, Mac up 15%, and Services up 13% year-over-year. Services gross margin percentage expanded to 75.6% from 74.0%, and total gross margin percentage improved to 46.5%, suggesting the Services growth engine continues to drive profitability higher. With an all-time-high installed base across all product categories and Greater China returning to growth (+4% in Q3 after declining 4% over nine months), the fundamental momentum supports further upside.

## Bear case
The 10-Q explicitly warns that tariffs and other trade measures 'can have a material adverse impact on the Company's business, results of operations and financial condition,' and Products gross margin percentage has already declined from 35.3% to 34.5% year-over-year due to tariffs and product mix. The stock's ~17% rally over two months has likely priced in much of the earnings beat, and the company itself states that gross margins 'will be subject to volatility and downward pressure.' iPad and Wearables revenue both declined year-over-year, and the Section 232 semiconductor investigation poses an unresolved overhang.

## Conclusion
Apple's fundamentals are strong with record revenue, expanding Services margins, and broad geographic growth, but the stock has already rallied ~17% in two months, pricing in much of the good news. Tariff risk remains the key uncertainty, already pressuring Products gross margin and explicitly flagged as potentially material. Over a 40-trading-day horizon, the risk-reward appears balanced-to-cautiously-bearish given the rapid recent appreciation and unresolved trade policy headwinds.

## Claims
- `c1` [direction, 20d, conf 0.45] AAPL closes at least 3% below the as-of price of $230.94 on the 20th trading day after August 15, 2025 -> **miss** (horizon-end return +2.21% vs down 3.0%)
- `c2` [magnitude, 20d, conf 0.3] AAPL's 20-trading-day return falls between -3% and -10% -> **miss** (horizon-end return +2.21% vs [-10.0, -3.0])
- `c3` [volatility, 40d, conf 0.4] AAPL's realized daily log-return volatility over the 40 trading days after August 15, 2025 is above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01520 vs p60 0.01691 (above))
- `c4` [direction, 40d, conf 0.38] AAPL closes at least 5% below the as-of price of $230.94 on the 40th trading day after August 15, 2025 -> **miss** (horizon-end return +6.94% vs down 5.0%)
