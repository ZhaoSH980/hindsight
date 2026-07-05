# Research memo

## Background
AMD delivered record Q4 2025 revenue of $10.3 billion and full-year revenue of $34.6 billion, with Data Center segment revenue growing 39% YoY in Q4 to $5.4 billion driven by EPYC CPU strength and Instinct GPU ramp. The stock ran from ~$204 in early January to ~$260 by January 23 before pulling back sharply to ~$192 on February 5, then partially recovering to $207.32 by February 13. The OpenAI strategic partnership for 6 GW of AMD GPUs and the Oracle cloud deployment of 50,000 MI450 GPUs provide a large forward revenue pipeline, but MI450 deployments don't begin until H2 2026.

## Bull case
AMD's record Q4 results, 39% YoY Data Center growth, and multi-year OpenAI partnership for 6 GW of GPU deployments provide a strong fundamental foundation. The stock has already corrected ~20% from its January peak of ~$260 to ~$207, potentially pricing in near-term concerns. With $5.5 billion in free cash flow for 2025 and a massive AI infrastructure pipeline with Oracle and OpenAI, the fundamental trajectory supports a recovery over a 40-trading-day horizon as the post-earnings selloff stabilizes.

## Bear case
The stock's 20%+ plunge from ~$253 on January 22 to ~$192 on February 5 — occurring right after the Q4 earnings release on February 3 — suggests the market was disappointed by something in the report or guidance despite headline beat. The MI450 deployments that underpin the OpenAI and Oracle partnerships don't begin until H2 2026, meaning revenue from these marquee deals won't materialize in the near term. The Embedded segment declined 3% for the full year, and Q3 2025 results excluded any China MI308 revenue, indicating ongoing export-control headwinds.

## Conclusion
AMD's fundamentals are strong with record revenue, accelerating Data Center growth, and a landmark OpenAI partnership, but the sharp post-earnings selloff from $253 to $192 signals market concern about near-term execution or guidance. Over a 40-trading-day horizon, the stock may recover modestly from oversold levels, but the magnitude of the recent decline and the gap between current price and the January peak suggest significant overhead resistance. I expect a modest recovery with elevated volatility as the market digests the OpenAI/Oracle pipeline timeline.

## Claims
- `c1` [direction, 40d, conf 0.55] AMD closes at least 3% above the as-of price of $207.32 on the 40th trading day after 2026-02-13 -> **hit** (horizon-end return +23.03% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.4] AMD's 40-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +23.03% vs [3.0, 12.0])
- `c3` [volatility, 40d, conf 0.6] AMD's realized daily log-return volatility over the 40-trading-day window after 2026-02-13 is above the 70th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.03257 vs p70 0.04575 (above))
