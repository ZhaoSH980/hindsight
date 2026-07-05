# Research memo

## Background
Meta reported strong Q2 2025 results on July 30, with revenue of $47.5B (+22% YoY) and operating margin expanding to 43%. The stock surged from ~$693 on July 30 to ~$783 by August 15, a ~13% post-earnings rally. However, the company is guiding to $66-72B in 2025 capex (up ~$30B YoY at midpoint) and expects 2026 expense growth to accelerate above 2025 levels due to infrastructure costs and depreciation.

## Bull case
Meta's advertising business is firing on all cylinders: Q2 ad revenue grew 21% YoY to $46.6B with ad impressions up 11% and price per ad up 9%, demonstrating both volume and pricing power. DAP reached 3.48B (+6% YoY), and the company is aggressively returning capital with $9.76B in Q2 buybacks and $1.33B in dividends. Q3 revenue guidance of $47.5-50.5B implies continued 20%+ growth, and the AI investment cycle is still early, with Meta AI nearing 1 billion monthly actives.

## Bear case
Capex is escalating dramatically—$66-72B in 2025 (up ~$30B YoY) with another year of significant dollar growth expected in 2026—and management explicitly warned that 2026 expense growth will accelerate above 2025's 20-24% rate, driven by a sharp increase in depreciation and infrastructure costs. Free cash flow has already compressed to $8.55B in Q2 (down from $10.33B in Q1) despite $25.6B in operating cash flow, as property and equipment purchases hit $16.5B. Reality Labs losses continue at $4.5B/quarter with no sign of narrowing.

## Conclusion
Meta's post-earnings momentum is supported by exceptional advertising execution and strong Q3 guidance, but the stock has already rallied ~13% in two weeks, pricing in much of the good news. The mounting capex burden and 2026 expense growth acceleration create a genuine risk that FCF compression persists, potentially capping upside. Over a 40-trading-day horizon, modest further gains are plausible but the risk-reward is more balanced than the recent rally suggests.

## Claims
- `c1` [direction, 20d, conf 0.45] META closes at least 3% above the as-of price of $782.66 on the 20th trading day after August 15, 2025 -> **miss** (horizon-end return -2.61% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.35] META's 20-trading-day return falls between +3% and +10% -> **miss** (horizon-end return -2.61% vs [3.0, 10.0])
- `c3` [volatility, 40d, conf 0.48] META's realized daily log-return volatility over the 40 trading days after August 15 falls below the 60th percentile of the prior 252-day rolling windows -> **hit** (realized vol 0.01394 vs p60 0.01980 (below))
