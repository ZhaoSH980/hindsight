# Research memo

## Background
NVDA enters its May 28 FY26Q1 earnings report with shares at $132.64, having rallied roughly 19% off April lows. Hyperscaler capex commitments totaling over $300 billion for 2025 underpin demand, while the H20 China export ban introduces up to $5.5B in charges and lost recurring revenue. Blackwell ramp is the fastest in NVIDIA's history at $11B in Q4 FY25, but gross margins are transitioning down from the mid-70s.

## Bull case
The four largest hyperscalers have collectively committed well over $300 billion in 2025 capex, with Meta even raising its guidance, confirming that AI infrastructure demand has not blinked. Blackwell revenue hit $11 billion in its first quarter — the fastest product ramp in NVIDIA's history — and a Q2 guide near or above ~$45 billion despite the lost China business would demonstrate that Blackwell demand more than covers the H20 hole.

## Bear case
The H20 export license requirement removes NVIDIA's only meaningful China AI accelerator and triggers up to $5.5B in charges, while China represented roughly $17B (13%) of FY25 revenue. Gross margins are guided down to 71% non-GAAP from the mid-70s as costlier Blackwell systems ramp, and TD Cowen's lease checks suggest Microsoft walked away from roughly 2 GW of data-center capacity — an early indicator that capex digestion risk could materialize in fiscal 2027 estimates that embed continued hypergrowth.

## Conclusion
The fundamental setup is net positive for the near-term print: hyperscaler budgets are intact, Blackwell is ramping at record speed, and consensus revenue of $43.3B appears achievable. However, the H20 overhang, gross-margin compression, and concentration risk create meaningful two-sided uncertainty around the report. I expect a modest positive drift over a 20-day horizon as Blackwell demand evidence accumulates, but with elevated volatility around the earnings event itself.

## Claims
- `c1` [direction, 20d, conf 0.55] NVDA closes at least 3% above the as-of price of $132.64 on the 20th trading day after as-of -> **ungradable** (horizon-end return +8.54% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.4] NVDA's 20-trading-day return lands between +3% and +12% -> **ungradable** (horizon-end return +8.54% vs [3.0, 12.0])
- `c3` [volatility, 5d, conf 0.6] NVDA's realized daily log-return volatility over the 5 trading days ending on the 5th trading day after as-of ranks above the 80th percentile of same-length rolling windows from the prior 252 trading days -> **ungradable** (realized vol 0.02449 vs p80 0.04555 (above))
