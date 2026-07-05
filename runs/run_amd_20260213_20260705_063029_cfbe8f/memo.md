# Research memo

## Background
AMD reported record Q4 2025 revenue of $10.3 billion on February 3, 2026, with Data Center segment revenue reaching $5.4 billion (up 39% YoY) and full-year revenue of $34.6 billion. The stock surged from $242 to $259 in the days following earnings but then collapsed sharply, falling to $192.50 by February 5 before partially recovering to $207.32 by February 13. The company guided Q1 2026 revenue to approximately $9.8 billion (up ~32% YoY) with ~55% non-GAAP gross margin, and announced a major multiyear partnership with OpenAI to deploy 6 gigawatts of AMD GPUs.

## Bull case
AMD's fundamental trajectory is exceptionally strong: record Q4 revenue of $10.3 billion, Data Center revenue up 39% YoY to $5.4 billion, full-year Data Center revenue of $16.6 billion up 32%, and a landmark OpenAI partnership for 6 GW of GPU deployment starting with MI450 series. The Q1 2026 guide of $9.8 billion represents 32% YoY growth, and management emphasized 'strong momentum' entering 2026. The MI308 inventory reserve reversal of $360 million plus $390 million in China sales demonstrates an incremental revenue catalyst. After the sharp post-earnings sell-off from $259 to $192, the stock has already begun recovering, suggesting the drawdown may have been an overshoot.

## Bear case
The stock lost nearly 26% of its value in a single session (from $242 to $200 on February 4) despite beating earnings, suggesting the market is deeply skeptical of the valuation or forward outlook. Q1 2026 guidance implies a ~5% sequential revenue decline from Q4's $10.3 billion, and the $100 million MI308 China revenue contribution is modest relative to the $390 million seen in Q4. The Embedded segment declined 3% for the full year, and the MI308 export control situation has created significant earnings volatility, with $800 million in inventory charges earlier in 2025 partially offset by Q4 reserve reversals that inflate reported margins.

## Conclusion
AMD's fundamentals are robust with record revenue, strong Data Center growth, and a transformative OpenAI partnership, but the violent post-earnings price action signals significant market concern about valuation and the sustainability of growth. The partial recovery to $207 suggests the initial sell-off was overdone, but elevated volatility is likely to persist as investors reconcile strong fundamentals against a rich valuation. Over a 40-day horizon, the stock appears more likely than not to recover further from depressed levels, but with considerable uncertainty.

## Claims
- `c1` [direction, 40d, conf 0.55] AMD closes at least 5% above the as-of price of $207.32 on the 40th trading day after 2026-02-13 -> **hit** (horizon-end return +23.03% vs up 5.0%)
- `c2` [magnitude, 40d, conf 0.42] AMD's 40-trading-day return lands between +5% and +20% -> **miss** (horizon-end return +23.03% vs [5.0, 20.0])
- `c3` [volatility, 20d, conf 0.6] AMD's realized daily log-return volatility over the 20 trading days after 2026-02-13 is above the 80th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.03251 vs p80 0.04829 (above))
