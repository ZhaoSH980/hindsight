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
- `c1` [direction, 20d, conf 0.5] AVGO closes at least 1% above the as-of price on the 20th trading day after as-of (naive baseline) -> **miss** (horizon-end return -0.08% vs up 1.0%)
- `c2` [direction, 5d, conf 0.5] AVGO closes at least 1% above the as-of price on the 5th trading day after as-of (naive baseline) -> **hit** (horizon-end return +1.59% vs up 1.0%)
- `c3` [volatility, 20d, conf 0.5] AVGO's realized volatility over the 20 trading days after as-of is above its median (naive baseline) -> **miss** (realized vol 0.02145 vs p50 0.02736 (above))
