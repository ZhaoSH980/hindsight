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
- `c1` [direction, 20d, conf 0.5] NVDA closes at least 1% above the as-of price on the 20th trading day after as-of (naive baseline) -> **hit** (horizon-end return +8.54% vs up 1.0%)
- `c2` [direction, 5d, conf 0.5] NVDA closes at least 1% above the as-of price on the 5th trading day after as-of (naive baseline) -> **hit** (horizon-end return +1.73% vs up 1.0%)
- `c3` [volatility, 20d, conf 0.5] NVDA's realized volatility over the 20 trading days after as-of is above its median (naive baseline) -> **miss** (realized vol 0.01669 vs p50 0.04264 (above))
