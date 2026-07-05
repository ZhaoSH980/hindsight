# Research memo

## Background
ExxonMobil's stock has declined approximately 4.4% over the two months leading into August 15, 2025, closing at $104.16. The company's most recent 10-Q (filed August 4) and 8-K (filed August 1) show year-to-date earnings of $14.8 billion, down from $17.5 billion in the first half of 2024, driven by weaker crude prices and declining refining margins. Despite these headwinds, XOM generated $24.5 billion in operating cash flow and distributed $18.4 billion to shareholders year-to-date, while advancing major projects like Fawley and Strathcona.

## Bull case
XOM continues to generate massive free cash flow ($14.2 billion YTD) and is executing on its $20 billion annual share repurchase program, having already repurchased approximately 40% of Pioneer shares issued. Structural cost savings reached $1.4 billion YTD with a path to $18 billion cumulative by 2030, and advantaged volume growth from the Permian and Guyana is partially offsetting margin weakness. New project start-ups (Fawley Hydrofiner, Strathcona Renewable Diesel, China Chemical Complex) are coming online, which should support higher-value product yields and earnings recovery.

## Bear case
Year-to-date earnings fell from $17.5 billion to $14.8 billion as weaker crude prices and declining industry refining margins more than offset volume growth and cost savings. Energy Products earnings dropped sharply (1Q25 $827M vs $1.4B prior year; 2Q25 $1.4B but YTD still down $129M), and Chemical Products earnings collapsed from $785M to $273 million year-over-year in 1Q25. The stock's persistent downtrend from $111 in mid-July to $104 in mid-August suggests the market is pricing in continued margin pressure with no clear catalyst for reversal.

## Conclusion
XOM faces near-term earnings pressure from weaker refining and chemical margins, but its robust free cash flow generation, aggressive shareholder returns, and project start-ups provide a floor. The stock's recent decline to $104 likely overdiscounts near-term margin weakness, suggesting a modest recovery is probable over a 40-trading-day horizon, though volatility may remain elevated as the market digests conflicting signals on commodity prices and margin trends.

## Claims
- `c1` [direction, 40d, conf 0.55] XOM closes at least 3% above the as-of price of $104.16 on the 40th trading day after August 15, 2025 -> **hit** (horizon-end return +5.40% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.4] XOM's 40-trading-day return lands between +3% and +10% -> **hit** (horizon-end return +5.40% vs [3.0, 10.0])
- `c3` [volatility, 20d, conf 0.58] XOM's realized daily log-return volatility over the next 20 trading days falls above the 60th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.01110 vs p60 0.01462 (above))
