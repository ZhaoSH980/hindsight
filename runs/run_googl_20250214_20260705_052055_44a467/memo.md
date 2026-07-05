# Research memo

## Background
GOOGL closed at $184.27 on 2025-02-14, down 5.81% over the prior ~40 trading days despite reporting strong Q4 2024 results on February 4. The sell-off occurred immediately after earnings, with the stock dropping from $205.31 on Feb 4 to $184.38 on Feb 7, and continuing to drift lower. Alphabet announced $75 billion in planned 2025 capex alongside 12% YoY revenue growth and 32% operating margins.

## Bull case
Alphabet's Q4 2024 results demonstrate robust fundamental momentum: revenues grew 12% to $96.5 billion, operating income surged 31% with margin expansion of 5 percentage points to 32%, and EPS rose 31% to $2.15. Google Cloud grew 30% to $12.0 billion, and management expressed confidence about AI-driven opportunities ahead. The post-earnings sell-off of roughly 10% from the Feb 4 close of $205.31 may represent an overshoot relative to these improving fundamentals, creating a potential mean-reversion opportunity.

## Bear case
The market's sharp negative reaction to a fundamentally strong earnings print signals deeper concerns about the $75 billion capex commitment and competitive pressures. The 10-K explicitly warns of 'formidable competition in every aspect of our business' including from AI products and services, and highlights 'heightened regulatory scrutiny' that could affect business practices and financial results. The persistent downward drift from $205 to $184 over eight trading days post-earnings suggests sustained selling pressure rather than a transient reaction.

## Conclusion
GOOGL faces a tension between strong reported financials and a market that is clearly pricing in elevated risk from massive capex spending, competition, and regulation. The post-earnings sell-off has been persistent rather than V-shaped, but the magnitude of the decline relative to the fundamental improvement creates a plausible case for stabilization or partial recovery. I expect moderate upside over a 40-day horizon but with meaningful uncertainty about whether the market re-rates the capex narrative.

## Claims
- `c1` [direction, 40d, conf 0.55] GOOGL closes at least 3% above the as-of price of $184.27 on the 40th trading day after 2025-02-14 -> **miss** (horizon-end return -14.02% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.4] GOOGL's 40-trading-day return lands between +3% and +12% -> **miss** (horizon-end return -14.02% vs [3.0, 12.0])
- `c3` [volatility, 40d, conf 0.45] GOOGL's realized daily log-return volatility over the 40-trading-day horizon falls below the 50th percentile of the prior ~252-day rolling windows -> **miss** (realized vol 0.02570 vs p50 0.01740 (below))
