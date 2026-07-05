# Research memo

## Background
Apple reported a record June quarter with $94.0B in revenue (up 10% YoY) and diluted EPS of $1.57 (up 12% YoY), driven by iPhone (+13%), Mac (+15%), and Services (+13%) growth. The stock rallied sharply from an August 1 close of $201.58 to $230.94 by August 15, a ~14.6% surge in two weeks. However, the 10-Q highlights ongoing tariff risks, declining Products gross margin percentage (34.5% vs. 35.3% prior year), and weakness in Wearables and iPad categories.

## Bull case
Apple's Q3 results demonstrate broad-based revenue strength across all geographic segments and record iPhone, Mac, and Services revenue, with Services gross margin reaching 75.6% and total revenue growing 10% YoY. The installed base hit an all-time high, and Services revenue reached a new all-time high of $27.4B, providing a durable high-margin recurring revenue stream that supports continued earnings growth and multiple expansion.

## Bear case
The 10-Q explicitly warns that tariffs are pressuring Products gross margin (down to 34.5% from 35.3% YoY) and that gross margins will be 'subject to volatility and downward pressure.' Section 232 semiconductor investigations and ongoing U.S.-China tariff escalation pose material risks to Apple's supply chain and pricing. Wearables revenue declined 9% and iPad fell 8% YoY, and the stock's ~14.6% two-week rally leaves limited room for upside surprise.

## Conclusion
Apple's fundamentals are strong with record revenue and EPS growth, but the rapid ~14.6% price appreciation over two weeks has likely front-run much of the positive news. Tariff uncertainty and Products gross margin compression create downside risk, while the high-margin Services trajectory supports the structural bull case. Over a 40-trading-day horizon, the risk-reward appears balanced with modest downside bias given the extended short-term rally and tariff overhang.

## Claims
- `c1` [direction, 20d, conf 0.55] AAPL closes at least 3% below the as-of price of $230.94 on the 20th trading day after as-of -> **miss** (horizon-end return +2.21% vs down 3.0%)
- `c2` [magnitude, 20d, conf 0.35] AAPL's 20-trading-day return lands between -10% and -3% -> **miss** (horizon-end return +2.21% vs [-10.0, -3.0])
- `c3` [volatility, 40d, conf 0.58] AAPL's realized daily log-return volatility over the 40-trading-day window is above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01520 vs p60 0.01691 (above))
