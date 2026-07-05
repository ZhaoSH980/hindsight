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
- `c1` [direction, 20d, conf 0.5] TSLA closes at least 1% above the as-of price on the 20th trading day after as-of (naive baseline) -> **miss** (horizon-end return -5.24% vs up 1.0%)
- `c2` [direction, 5d, conf 0.5] TSLA closes at least 1% above the as-of price on the 5th trading day after as-of (naive baseline) -> **miss** (horizon-end return -4.22% vs up 1.0%)
- `c3` [volatility, 20d, conf 0.5] TSLA's realized volatility over the 20 trading days after as-of is above its median (naive baseline) -> **miss** (realized vol 0.01832 vs p50 0.03128 (above))
