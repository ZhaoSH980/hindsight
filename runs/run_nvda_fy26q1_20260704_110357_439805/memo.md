# Research memo

## Background
NVDA enters its FY26Q1 earnings report on May 28, 2025 with shares at $132.64, having rallied ~37% from their April 8 tariff-driven lows near $96. The stock has nearly recovered to its January highs as hyperscaler capex commentary from MSFT, GOOG, META, and AMZN confirmed 2025 AI infrastructure budgets exceeding $300 billion combined. Key overhangs include the H20 China export-license hit (up to $5.5B charge), Blackwell gross-margin transition dynamics, and the question of whether Q2 guidance can absorb a full quarter of lost China revenue.

## Bull case
Hyperscaler capex is intact and accelerating — Meta even raised its 2025 outlook to $64-72B — and Microsoft explicitly stated AI capacity remains supply-constrained with demand ahead of supply. Blackwell is the fastest product ramp in NVIDIA's history at $11B in Q4 FY25, and the top four cloud providers ordered 3.6M Blackwell GPUs versus 1.3M Hopper at peak. If Q2 guidance comes in near or above ~$45B despite the lost H20 China business, it confirms Blackwell demand more than covers the China hole, validating the bull thesis that AI compute demand is accelerating rather than digesting.

## Bear case
The H20 export ban removes roughly $17B in annual China revenue (~13% of FY25 total), and the up-to-$5.5B charge creates significant EPS dispersion. Gross margins are guided down to 71% non-GAAP from the mid-70s as Blackwell ramp costs bite, with recovery promised only later in the fiscal year. Data-center lease checks showed Microsoft walking away from ~2GW of capacity and AWS pausing some negotiations, while DeepSeek's efficiency breakthrough raises the risk that algorithmic progress weakens the mapping from AI demand to GPU units — risks that point toward a fiscal 2027 digestion phase even if the May 28 print itself doesn't miss.

## Conclusion
The setup into May 28 is asymmetric but largely de-risked on the demand side: hyperscaler budgets are confirmed, Blackwell is ramping, and the H20 charge is already flagged. The most likely outcome is an in-line to modest beat with Q2 guidance that calms China-loss fears, supporting a modest positive drift over 40 trading days. However, the stock's 37% rally from April lows means much of the good news is priced in, capping upside magnitude while gross-margin and lease-check concerns limit conviction.

## Claims
- `c1` [direction, 5d, conf 0.55] NVDA closes at least 3% above the as-of price ($132.64) on the 5th trading day after as-of, capturing the immediate earnings reaction window -> **miss** (horizon-end return +1.73% vs up 3.0%)
- `c2` [magnitude, 5d, conf 0.4] NVDA's 5-trading-day return lands between +3% and +12%, reflecting a positive but measured earnings reaction given the stock's recent rally -> **miss** (horizon-end return +1.73% vs [3.0, 12.0])
- `c3` [direction, 40d, conf 0.5] NVDA closes at least 5% above the as-of price on the 40th trading day after as-of, reflecting sustained post-earnings strength as Blackwell ramp and confirmed capex budgets dominate the narrative -> **hit** (horizon-end return +25.76% vs up 5.0%)
- `c4` [volatility, 5d, conf 0.7] NVDA's realized daily log-return volatility over the 5-trading-day window ending on the 5th trading day after as-of ranks above the 80th percentile of same-length rolling windows from the prior 252 days, reflecting elevated earnings-event turbulence -> **miss** (realized vol 0.02449 vs p80 0.04555 (above))
