# Research memo

## Background
NVDA enters its May 28 FY26Q1 earnings report with shares at $132.64, having rallied ~37% from April lows. The investment case is dominated by three forces: hyperscaler capex commitments exceeding $300 billion for 2025, the H20 China export-license requirement carrying up to $5.5 billion in charges, and the Blackwell ramp — already at $11 billion in Q4 FY25 — which is the fastest product ramp in company history. Consensus revenue sits near $43.3 billion, just above the $43.0 billion guide.

## Bull case
The four largest hyperscalers reaffirmed or raised 2025 capex plans totaling well over $300 billion, with Microsoft explicitly stating AI capacity remains supply-constrained. NVIDIA's Blackwell ramp generated $11.0 billion in Q4 FY25 — its fastest ever — and the top four U.S. cloud providers ordered 3.6 million Blackwell GPUs for 2025 versus 1.3 million Hopper GPUs in Hopper's peak year. If Q2 guidance comes near or above ~$45 billion despite the lost China business, it confirms Blackwell demand is more than covering the H20 hole.

## Bear case
The H20 export restriction removes NVIDIA's only meaningful China AI accelerator — a market that billed roughly $17 billion in FY2025 (~13% of revenue) — with up to $5.5 billion in charges hitting Q1. Gross margins are guided down to 71.0% non-GAAP from the mid-70s as costlier Blackwell systems ramp, and TD Cowen's supply-chain work found Microsoft walked away from roughly two gigawatts of data-center leases, an early-moving indicator of potential capex digestion. Customer concentration is striking, with multiple direct customers crossing 10% of revenue.

## Conclusion
The setup into May 28 earnings is asymmetric: hyperscaler demand signals are robust and Blackwell ramp momentum is strong, but the H20 charge and gross-margin compression create real near-term uncertainty. With the stock having rallied 37% off April lows, much of the good news is priced in, raising the bar for an upside surprise. I expect modest positive returns over a 5-day horizon anchored on the print, but with elevated volatility given the wide dispersion in EPS estimates and the binary nature of the Q2 guide.

## Claims
- `c1` [direction, 5d, conf 0.45] NVDA closes at least 3% above the as-of price on the 5th trading day after as-of (capturing the May 28 earnings reaction) -> **miss** (horizon-end return +1.73% vs up 3.0%)
- `c2` [magnitude, 5d, conf 0.35] NVDA's 5-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +1.73% vs [3.0, 12.0])
- `c3` [volatility, 5d, conf 0.6] NVDA's realized daily log-return volatility over the 5 trading days after as-of is above the 80th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.02449 vs p80 0.04555 (above))
- `c4` [direction, 20d, conf 0.4] NVDA closes at least 5% above the as-of price on the 20th trading day after as-of -> **hit** (horizon-end return +8.54% vs up 5.0%)
