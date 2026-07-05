# Research memo

## Background
GOOGL closed at $305.32 on 2026-02-13, down roughly 11% from its late-January peak near $343 following its Q4 2025 earnings release on February 4. The company reported strong fundamentals—18% revenue growth to $113.8B, Google Cloud accelerating to 48% growth, and EPS up 31% to $2.82—but the stock has been in a sharp pullback for nine straight sessions. The 10-K filed February 5 highlights significant risk factors including advertising concentration (>70% of revenue), AI-driven competitive disruption, and escalating regulatory.

## Bull case
Alphabet's Q4 2025 results demonstrate accelerating growth across all segments, with consolidated revenues up 18% and Google Cloud growing 48% to $17.7B with operating income more than doubling to $5.3B. The company generated $73.3B in TTM free cash flow and exceeded $400B in annual revenue for the first time, suggesting the post-earnings selloff is overdone relative to fundamental improvement. The $157.7B Cloud revenue backlog provides strong forward visibility.

## Bear case
The 10-K explicitly warns that AI is 'quickly reshaping the advertising industry' with 'no assurance that we will adapt effectively,' while over 70% of revenue remains concentrated in online advertising. Other Bets operating losses widened sharply to $3.6B in Q4 (from $1.2B prior year), driven by a $2.1B Waymo compensation charge, and Alphabet-level activities losses nearly doubled. The stock's 11% decline over nine sessions since earnings suggests the market is pricing in structural concerns about competitive threats and margin pressure from rising AI investments.

## Conclusion
The sharp post-earnings decline of ~11% over nine trading days appears overdone relative to the strong fundamental results, but the 10-K's risk factors around AI disruption and advertising concentration provide legitimate concerns. With the stock now near the bottom of its recent range and RSI-like conditions suggesting oversold territory, a modest bounce is probable over a 20-40 day horizon, though the magnitude is uncertain given competitive and regulatory headwinds.

## Claims
- `c1` [direction, 20d, conf 0.55] GOOGL closes at least 3% above the as-of price ($305.32) on the 20th trading day after 2026-02-13 -> **miss** (horizon-end return +0.02% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.4] GOOGL's 20-trading-day return lands between +3% and +10% -> **miss** (horizon-end return +0.02% vs [3.0, 10.0])
- `c3` [volatility, 40d, conf 0.58] GOOGL's realized daily log-return volatility over the 40-trading-day horizon is above the 60th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.01946 vs p60 0.01957 (above))
