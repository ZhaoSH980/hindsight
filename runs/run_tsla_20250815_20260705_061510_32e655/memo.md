# Research memo

## Background
Tesla's Q2 2025 10-Q (filed July 24, 2025) reveals a company in transition: total revenue fell 11.8% YoY to $22.5B, automotive sales declined 14.9% to $15.8B, and net income dropped 16.0% to $1.19B, though energy storage revenue grew and operating cash flow improved to $4.7B for the first half. The stock has been volatile around the $300-340 range since late June, closing at $330.56 on August 15. The recently enacted OBBBA legislation introduces uncertainty around regulatory credit sales and tax provisions that could materially impact future results.

## Bull case
Tesla's energy generation and storage segment is gaining traction with deferred revenue growing from $1.77B to $2.10B and $10.38B in unsatisfied performance obligations, while operating cash flow strengthened to $4.7B for H1 2025 from $3.85B a year prior. The company also holds $36.8B in cash and short-term investments, providing substantial financial flexibility to weather automotive headwinds and invest in growth initiatives like FSD, where deferred revenue grew to $3.75B.

## Bear case
The core automotive business is deteriorating: automotive sales fell $2.74B YoY in Q2, income from operations dropped 42.5% to $923M, and inventory swelled to $14.57B from $12.02B at year-end, signaling demand softness. The OBBBA legislation explicitly threatens loss of certain regulatory credit sales and changes to product costs, which could further pressure margins in a business already seeing gross profit decline 15.3% YoY.

## Conclusion
Tesla faces near-term headwinds from declining automotive revenue, rising inventory, and legislative uncertainty around regulatory credits, but its energy segment growth, strong cash position, and FSD deferred revenue provide a credible offset. The stock's recent recovery to $330 from July lows near $294 suggests the market is pricing in a balanced view. Over a 40-trading-day horizon, modest downside appears more likely than upside given the fundamental deterioration, but volatility is expected to remain elevated.

## Claims
- `c1` [direction, 40d, conf 0.38] TSLA closes at least 5% below the as-of price of $330.56 on the 40th trading day after August 15, 2025 -> **miss** (horizon-end return +31.87% vs down 5.0%)
- `c2` [magnitude, 40d, conf 0.25] TSLA's 40-trading-day return lands between -10% and -5% -> **miss** (horizon-end return +31.87% vs [-10.0, -5.0])
- `c3` [volatility, 20d, conf 0.42] TSLA's realized daily log-return volatility over the next 20 trading days exceeds the 75th percentile of its prior 252-day rolling windows -> **miss** (realized vol 0.02823 vs p75 0.05146 (above))
- `c4` [direction, 10d, conf 0.28] TSLA closes at least 3% above the as-of price of $330.56 on the 10th trading day after August 15, 2025 -> **miss** (horizon-end return +1.00% vs up 3.0%)
