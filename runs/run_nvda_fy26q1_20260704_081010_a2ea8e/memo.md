# Research memo

## Background
NVDA enters its FY26Q1 earnings report on May 28 with shares at $132.64, having rallied roughly 18% off April lows on the back of reaffirmed hyperscaler capex totaling over $300 billion for 2025. The H20 China export-license requirement disclosed April 15 creates up to $5.5 billion in charges and removes the primary China data-center revenue stream, while Blackwell ramp momentum ($11B in Q4 FY25) and robust hyperscaler demand provide offsetting tailwinds. Consensus revenue sits near $43.3B versus the $43.0B guide, with EPS dispersion wide due to H20 charge treatment uncertainty.

## Bull case
The four largest hyperscalers collectively reaffirmed over $300 billion of 2025 capex with Meta even raising its outlook, and Microsoft explicitly stated AI capacity remains supply-constrained with demand ahead of supply. Blackwell is the fastest product ramp in NVIDIA's history at $11B in its first quarter, and a Q2 guide near or above $45B despite the lost China business would confirm Blackwell demand is more than covering the H20 hole. The stock has already recovered sharply from April lows, suggesting the market is pricing in a constructive outcome.

## Bear case
The H20 export ban removes roughly $17 billion in annual China revenue (13% of FY25 total) and introduces up to $5.5B in charges, while the AI Diffusion rule's May 15 compliance date adds further policy uncertainty. Gross margins are guided down to 71% from the mid-70s as Blackwell systems carry higher costs, and TD Cowen's lease checks found Microsoft walked away from roughly 2 GW of data-center capacity — an early indicator that capex digestion risk could materialize in FY2027 estimates that currently embed continued hypergrowth. Customer concentration is striking, with multiple direct customers repeatedly crossing 10% of revenue.

## Conclusion
The setup into May 28 earnings is genuinely two-sided: hyperscaler demand is confirmed and Blackwell is ramping faster than any prior NVIDIA architecture, but the H20 ban, gross-margin compression, and emerging capex digestion signals create real downside risk. With the stock having rallied 18% in five weeks, much of the good news is priced in, leaving the reaction asymmetrically sensitive to the Q2 guide and H20 accounting clarity. I expect a positive but volatile outcome, with modest upside more likely than a sharp sell-off given the demand visibility from hyperscaler commentary.

## Claims
- `c1` [direction, 5d, conf 0.52] NVDA closes at least 3% above the as-of price ($132.64) on the 5th trading day after May 22, capturing the earnings reaction -> **miss** (horizon-end return +1.73% vs up 3.0%)
- `c2` [magnitude, 5d, conf 0.4] NVDA's 5-trading-day return lands between +3% and +12%, consistent with a positive but not extreme earnings reaction -> **miss** (horizon-end return +1.73% vs [3.0, 12.0])
- `c3` [volatility, 5d, conf 0.68] NVDA's realized daily log-return volatility over the 5 trading days following the as-of date falls above the 70th percentile of same-length rolling windows from the prior 252 days, reflecting elevated earnings-event turbulence -> **miss** (realized vol 0.02449 vs p70 0.03657 (above))
- `c4` [direction, 20d, conf 0.45] NVDA closes at least 5% above the as-of price on the 20th trading day after May 22, reflecting sustained post-earnings strength as Blackwell demand and hyperscaler capex visibility dominate -> **hit** (horizon-end return +8.54% vs up 5.0%)
