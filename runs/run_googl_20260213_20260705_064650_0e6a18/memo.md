# Research memo

## Background
GOOGL closed at $305.32 on February 13, 2026, down roughly 11% from its late-January peak near $343 following its Q4 2025 earnings release on February 4. The company reported strong fundamentals: Q4 revenue grew 18% YoY to $113.8 billion, Google Cloud accelerated to 48% growth, and EPS rose 31% to $2.82. However, Alphabet-level unallocated costs surged to $5.9 billion from $2.8 billion year-over-year, driven by shared AI R&D and a $2.1 billion Waymo employee compensation charge, pressuring operating leverage.

## Bull case
Alphabet's Q4 2025 results demonstrated accelerating revenue growth (18% YoY, up from 12% in Q4 2024), with Google Cloud growing 48% to $17.7 billion and a $157.7 billion revenue backlog primarily tied to Cloud. YouTube surpassed $60 billion in annual revenue, Search grew 17%, and net income increased 30%. The post-earnings selloff of ~11% from peak prices may overreact to cost concerns, creating a value entry point given the fundamental strength.

## Bear case
Alphabet-level unallocated costs more than doubled from $2.8 billion to $5.9 billion year-over-year, driven by escalating AI R&D spending and the $2.1 billion Waymo compensation charge, with the Waymo investment round reaching $16 billion. Other Bets operating losses widened to $3.6 billion from $1.2 billion. These rising investments in AI and autonomous driving create uncertainty around future margin expansion, and the stock's recent sharp decline from $343 to $305 may reflect sustained pressure rather than a temporary dip.

## Conclusion
GOOGL presents a mixed picture: exceptional top-line growth and Cloud acceleration are tempered by rapidly rising unallocated AI costs and widening Other Bets losses. The recent ~11% pullback from late-January highs could offer a tactical bounce opportunity given strong fundamentals, but elevated cost trajectories and the stock's downward momentum warrant caution. I expect modest recovery over the next 30-40 trading days but with moderate confidence given ongoing spending pressures.

## Claims
- `c1` [direction, 20d, conf 0.55] GOOGL closes at least 3% above the as-of price on the 20th trading day after as-of -> **miss** (horizon-end return +0.02% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.42] GOOGL's 20-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +0.02% vs [3.0, 12.0])
- `c3` [direction, 40d, conf 0.5] GOOGL closes at least 5% above the as-of price on the 40th trading day after as-of -> **hit** (horizon-end return +8.97% vs up 5.0%)
- `c4` [volatility, 40d, conf 0.45] GOOGL's 40-trading-day realized daily log-return volatility falls below the 60th percentile of the prior 252-day rolling windows -> **hit** (realized vol 0.01946 vs p60 0.01957 (below))
