# Research memo

## Background
JPMorgan Chase stock has risen approximately 8% over the two months ending August 15, 2025, closing at $286.32. The bank's Q2 2025 10-Q reports net income of $15.0 billion with an ROE of 18% and ROTCE of 21%, though results were down 17% YoY due to the absence of a $7.9 billion Visa share gain from the prior year. A new $50 billion share repurchase program was authorized effective July 1, 2025, replacing the prior $30 billion program.

## Bull case
JPM's core franchise remains exceptionally strong with CIB Markets revenue up 15%, AWM assets under management up 18% to $4.3 trillion, and TBVPS growing 11% to $103.40. The newly authorized $50 billion buyback program provides meaningful capital return support, and CET1 capital ratios of 15.1% provide ample cushion above regulatory minimums.

## Bear case
Credit costs are rising meaningfully, with net charge-offs up to $2.4 billion in Q2 2025 from $2.2 billion prior year, driven by Card Services where the net charge-off rate reached 3.40%. The allowance for credit losses grew to $28.3 billion with coverage ratios ticking up, and nonperforming assets rose to $10.5 billion from $8.4 billion a year ago, signaling potential deterioration in consumer credit quality.

## Conclusion
JPM presents a mixed picture: strong capital return dynamics and franchise momentum are offset by deteriorating consumer credit and the absence of the prior-year Visa gain tailwind. Over a 40-trading-day horizon, the stock appears range-bound with modest upside potential supported by buyback execution, but credit deterioration trends warrant caution. The balance of factors suggests a slight positive drift rather than a sharp move in either direction.

## Claims
- `c1` [direction, 40d, conf 0.45] JPM closes at least 2% above the as-of price of $286.32 on the 40th trading day after 2025-08-15 -> **hit** (horizon-end return +6.53% vs up 2.0%)
- `c2` [magnitude, 40d, conf 0.55] JPM's 40-trading-day return falls between -3% and +5% -> **miss** (horizon-end return +6.53% vs [-3.0, 5.0])
- `c3` [volatility, 40d, conf 0.5] JPM's realized daily log-return volatility over the 40-trading-day window after 2025-08-15 falls below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.01001 vs p60 0.01733 (below))
