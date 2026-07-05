# Research memo

## Background
naive baseline — no research was performed

## Bull case
naive baseline — no research was performed

## Bear case
naive baseline — no research was performed

## Conclusion
naive baseline — no research was performed

## Claims
- `c1` [direction, 20d, conf 0.5] META closes at least 1% above the as-of price on the 20th trading day after as-of (naive baseline) -> **miss** (horizon-end return -17.81% vs up 1.0%)
- `c2` [direction, 5d, conf 0.5] META closes at least 1% above the as-of price on the 5th trading day after as-of (naive baseline) -> **miss** (horizon-end return -9.30% vs up 1.0%)
- `c3` [volatility, 20d, conf 0.5] META's realized volatility over the 20 trading days after as-of is above its median (naive baseline) -> **hit** (realized vol 0.02365 vs p50 0.01717 (above))
