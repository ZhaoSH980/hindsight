# Research memo

## Background
NVDA enters its May 28 FY26Q1 earnings report with shares at $132.64, having rallied ~37% from their April 8 tariff-driven lows. Hyperscalers collectively signaled over $300B in 2025 AI capex, and Blackwell generated $11B in its first quarter — the fastest ramp in NVIDIA's history. However, the H20 export-license requirement triggered up to $5.5B in charges and removed most China data-center revenue, while gross margins are pressured during the Blackwell transition and analyst EPS estimates show unusually wide dispersion around H20 accounting treatment.

## Bull case
The combined hyperscaler capex commitments of $300B+ for 2025, with Meta even raising its outlook, confirm demand-side strength through at least this fiscal year. Blackwell's $11B debut quarter and the top four cloud providers ordering 3.6 million GPUs in 2025 versus 1.3 million Hopper units at peak demonstrate accelerating adoption. A Q2 guide near or above ~$45B despite the full loss of China revenue would prove Blackwell demand is more than offsetting the H20 hole, while gross margins are guided to recover to the mid-70s as yields mature.

## Bear case
The H20 ban removed roughly $17B in annual China revenue (~13% of total) and saddled the quarter with up to $5.5B in charges. Gross margins are declining from the mid-70s to ~71% during the Blackwell transition, and the GB300 changeover later this year adds further mix risk. TD Cowen's finding that Microsoft walked away from ~2GW of data-center projects, combined with DeepSeek's demonstration that algorithmic efficiency can reduce compute requirements, suggests the capex digestion risk may materialize in fiscal 2027 estimates that currently embed continued hypergrowth.

## Conclusion
The fundamental setup is net positive for the near-term print: hyperscaler capex is confirmed, Blackwell is ramping at record pace, and consensus revenue of $43.3B appears achievable. However, the H20 charge creates accounting noise, the Q2 guide is the true swing factor, and the stock has already rallied 37% from April lows, limiting upside surprise potential. We expect a modestly positive reaction if the Q2 guide clears ~$45B, but see elevated risk of a pullback if China-revenue loss or gross-margin commentary disappoints.

## Claims
- `c1` [direction, 5d, conf 0.55] NVDA closes at least 3% above the as-of price on the 5th trading day after as-of (capturing the May 28 earnings reaction) -> **ungradable** (horizon-end return +1.73% vs up 3.0%)
- `c2` [magnitude, 5d, conf 0.4] NVDA's 5-trading-day return lands between -7% and +2%, capturing a downside or muted reaction to earnings -> **ungradable** (horizon-end return +1.73% vs [-7.0, 2.0])
- `c3` [volatility, 5d, conf 0.7] NVDA's realized daily log-return volatility over the 5 trading days surrounding earnings falls in the top 20% of same-length rolling windows from the prior year -> **ungradable** (realized vol 0.02449 vs p80 0.04555 (above))
