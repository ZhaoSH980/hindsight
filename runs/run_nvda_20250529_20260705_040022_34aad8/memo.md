# Research memo

## Background
NVIDIA reported FY26Q1 revenue of $44.1B, beating the ~$43.3B consensus, with Data Center revenue up 73% YoY. The Q2 guide of $45.0B (±2%) absorbs an ~$8B H20 revenue loss from China export controls yet still implies sequential growth, signaling Blackwell demand is more than offsetting the China hole. Hyperscaler capex commitments exceeding $300B combined for 2025 underpin the demand picture, though the stock has already rallied ~28% from its April 3 lows into the print.

## Bull case
The $45B Q2 guide despite losing ~$8B in H20 revenue is the single most powerful signal: it means ex-China, underlying demand is accelerating fast enough to grow sequentially even with a massive headwind removed. Blackwell is the fastest product ramp in NVIDIA's history at $11B in Q4 FY25, and with four hyperscalers committing $300B+ in 2025 capex, the demand visibility extends through fiscal 2026. Gross margins ex-H20 hit 71.3% and are guided to 72.0% in Q2, with management targeting mid-70s by year-end as Blackwell yields improve — confirming the transition is de-risking.

## Bear case
The H20 situation permanently removes ~$17B in annual China revenue (13% of FY25 total), and the $4.5B charge plus $2.5B in lost shipments compressed GAAP gross margin to 60.5% from 73.0% sequentially. More structurally, TD Cowen's lease checks found Microsoft walked away from ~2GW of data-center capacity, AWS paused lease negotiations, and DeepSeek's efficiency breakthrough raises the risk that algorithmic progress weakens the mapping from AI demand to GPU units — risks that compound against FY27 estimates embedding continued hypergrowth.

## Conclusion
The post-earnings setup favors upside drift: the Q2 guide confirms Blackwell demand covers the China hole with room to spare, hyperscaler capex is intact, and the H20 charge is now a known, bounded quantity rather than an overhang. The stock's 28% run into the print creates some near-term consolidation risk, but the fundamental trajectory — accelerating ex-China revenue, recovering gross margins, and a product ramp still in early innings — supports further upside over a 30-40 day horizon.

## Claims
- `c1` [direction, 20d, conf 0.58] NVDA closes at least 3% above the as-of price of $138.99 on the 20th trading day after May 29, 2025 -> **hit** (horizon-end return +13.34% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.45] NVDA's 20-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +13.34% vs [3.0, 12.0])
- `c3` [direction, 35d, conf 0.55] NVDA closes at least 5% above the as-of price of $138.99 on the 35th trading day after May 29, 2025 -> **hit** (horizon-end return +23.14% vs up 5.0%)
- `c4` [volatility, 40d, conf 0.52] NVDA's realized daily log-return volatility over the 40 trading days after May 29, 2025 falls below the 60th percentile of same-length rolling windows from the prior 252 trading days -> **hit** (realized vol 0.01653 vs p60 0.04244 (below))
