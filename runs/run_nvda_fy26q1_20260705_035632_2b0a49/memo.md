# Research memo

## Background
NVDA trades at $132.64 as of May 22, 2025, up ~9.4% over the prior 40 trading days and approaching its January highs, with FY26Q1 earnings scheduled for May 28. The four largest hyperscalers have collectively signaled well over $300 billion in 2025 capex, reinforcing near-term AI accelerator demand, while the H20 China export-license requirement has triggered up to $5.5 billion in charges and removed a meaningful revenue stream. Consensus revenue sits near $43.3 billion against a $43.0 billion guide, with the key variable being whether Blackwell ramp strength offsets the China hole in Q2 guidance.

## Bull case
Hyperscaler capex commitments are unprecedented — Meta raised its 2025 outlook to $64–72 billion, Alphabet reaffirmed ~$75 billion, Microsoft is on pace for ~$80 billion, and Amazon is tracking toward ~$100 billion — collectively implying over $300 billion, meaning the demand side of the AI trade did not blink. Blackwell is already the fastest product ramp in NVIDIA's history at $11 billion in Q4 FY25, with the top four U.S. cloud providers ordering 3.6 million Blackwell GPUs in 2025 versus 1.3 million Hopper GPUs in Hopper's peak year. If the July-quarter guide comes in near or above ~$45 billion despite a full quarter of lost H20 revenue, it would confirm that Blackwell demand is more than covering the China gap, validating the hypergrowth narrative into FY2027.

## Bear case
The H20 export-license requirement has effectively eliminated NVIDIA's China data-center business — roughly $17 billion in FY25 revenue (~13% of total) — with up to $5.5 billion in charges landing in Q1 alone, and management has given no indication licenses will be granted. Gross margins are guided down to 71.0% non-GAAP from the mid-70s as the costlier Blackwell systems ramp, with inventory provisions already creating a 2.3% gross-margin headwind in FY25. Structural risks are accumulating: TD Cowen's supply-chain work found Microsoft walked away from ~2 GW of data-center leases, AWS reportedly paused lease negotiations, DeepSeek demonstrated near-frontier model quality at a fraction of assumed training cost, and the 10-K reveals striking customer concentration with multiple direct customers crossing 10% of revenue — all warning lights that the capex digestion phase could arrive in 2026.

## Conclusion
The setup into May 28 is asymmetric but not one-sided: hyperscaler capex and Blackwell order momentum provide a strong fundamental floor, yet the H20 writedown, gross-margin compression, and accumulating digestion signals create real downside risk if guidance disappoints. The stock's recent 9.4% rally into the print leaves limited margin for error, and the unusually wide EPS dispersion suggests the Street itself is uncertain about the quarter's optics. I expect a modest positive drift over a 40-day horizon as Blackwell demand evidence accumulates, but with elevated volatility around the earnings event itself.

## Claims
- `c1` [direction, 40d, conf 0.55] NVDA closes at least 3% above the as-of price of $132.64 on the 40th trading day after May 22, 2025 -> **hit** (horizon-end return +25.76% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.42] NVDA's 40-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +25.76% vs [3.0, 12.0])
- `c3` [volatility, 40d, conf 0.6] NVDA's realized daily log-return volatility over the 40 trading days after May 22, 2025 ranks above the 70th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01738 vs p70 0.04760 (above))
