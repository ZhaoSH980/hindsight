# Research memo

## Background
Amazon reported strong Q2 2025 results on July 31, with net sales up 13% to $167.7B and operating income of $19.2B, beating prior-year figures. AWS continued its steady 17.5% growth trajectory while North America and International segments showed accelerating profitability. However, the stock dropped sharply from $234.11 on July 31 to $214.75 on August 1 following the earnings release, before partially recovering to $231.03 by August 15. Q3 2025 guidance projected net sales of $174-179.5B (10-13% growth) and operating income of $15.5-20.5B, with the wide operating income range reflecting substantial uncertainty including tariff and macro risks.

## Bull case
Amazon's Q2 results demonstrated accelerating profitability across all three segments, with North America operating income up 48% Y/Y, International up 448% Y/Y, and consolidated operating margin expanding meaningfully. The Q3 sales guidance midpoint of ~$176.75B implies continued double-digit revenue growth, and management's aggressive AI infrastructure investment positions AWS to capture outsized demand as AI workloads scale. The stock's recovery from the August 1 post-earnings dip to $214.75 back to $231.03 by August 15 suggests the market is digesting the results favorably.

## Bear case
The post-earnings drop from $234.11 to $214.75 on August 1 signals investor concern about the Q3 guidance, particularly the wide operating income range of $15.5-20.5B which brackets below Q3 2024's $17.4B at the low end. Heavy AI capital expenditure requirements, as highlighted in the April letter, create near-term margin pressure with monetization lagging investment. The guidance itself flags substantial uncertainty from tariffs, trade policies, recessionary fears, and geopolitical conditions that could compress margins and demand.

## Conclusion
Amazon's fundamentals remain strong with accelerating profitability and steady AWS growth, but the wide Q3 operating income guidance range and macro uncertainties create meaningful downside risk. The stock's rapid recovery from the August 1 selloff suggests resilience, yet the elevated volatility around earnings indicates the market remains uncertain about near-term trajectory. We expect AMZN to trade in a relatively stable range near current levels with moderate upside bias over the next 40 trading days, supported by fundamental strength but capped by macro and capex concerns.

## Claims
- `c1` [direction, 20d, conf 0.58] AMZN closes at or above the as-of price of $231.03 on the 20th trading day after August 15, 2025 -> **hit** (horizon-end return +0.17% vs up 0.01%)
- `c2` [magnitude, 20d, conf 0.52] AMZN's 20-trading-day return falls between -3% and +6% -> **hit** (horizon-end return +0.17% vs [-3.0, 6.0])
- `c3` [volatility, 40d, conf 0.55] AMZN's realized daily log-return volatility over the 40-trading-day window is below the 60th percentile of same-length rolling windows from the prior 252 trading days -> **hit** (realized vol 0.01676 vs p60 0.01892 (below))
