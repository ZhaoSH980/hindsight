# Research memo

## Background
NVDA trades at $132.64 on May 22, 2025, six trading days before its FY26Q1 earnings report on May 28. The stock has rallied roughly 37% off its April 8 tariff-driven lows near $96, recovering as hyperscaler capex commentary confirmed 2025 AI infrastructure budgets remain intact at over $300 billion combined. Key overhangs into the print include the up-to-$5.5 billion H20 China export-control charge, Blackwell ramp execution, and whether Q2 guidance can absorb the full loss of China data-center revenue.

## Bull case
Hyperscaler capex is confirmed at unprecedented levels—Meta raised guidance to $64–72 billion, Alphabet reaffirmed ~$75 billion, Microsoft is on an ~$80 billion pace, and Amazon ~$100 billion—meaning the demand side for AI accelerators did not blink. With Blackwell already generating $11 billion in Q4 FY25 and described as the fastest product ramp in NVIDIA's history, a Q2 guide near or above ~$45 billion despite the lost China business would confirm Blackwell demand is more than covering the H20 hole, validating the rally and opening room for upside to FY2026 estimates.

## Bear case
The H20 export restriction removes roughly $17 billion of annual China data-center revenue (13% of total), with up to $5.5 billion in charges hitting Q1 alone and several billion dollars per quarter of foregone revenue going forward. The bear thesis is not about the May 28 print missing but about FY2027 estimates embedding continued hypergrowth against rising depreciation treadmills for customers, striking customer concentration, and the risk of a capex digestion phase arriving in 2026—any softness in Q2 guidance or gross-margin commentary could trigger a sharp repricing of the growth trajectory.

## Conclusion
The setup into FY26Q1 is asymmetric: consensus revenue near $43.3 billion is only slightly above guidance, and the H20 charge is already flagged, limiting downside surprise on the print itself. The real question is whether Q2 guidance clears ~$45 billion despite the full loss of China revenue—if it does, the Blackwell demand narrative likely pushes NVDA meaningfully higher over the following weeks; if it disappoints, the stock's 37% rally since April lows leaves significant room for a pullback. We lean cautiously bullish but acknowledge elevated event-risk volatility around the report.

## Claims
- `c1` [direction, 20d, conf 0.45] NVDA closes at least 5% above the as-of price of $132.64 on the 20th trading day after as-of (approximately July 23, 2025), reflecting a positive earnings reaction and Blackwell demand confirmation -> **hit** (horizon-end return +8.54% vs up 5.0%)
- `c2` [magnitude, 20d, conf 0.38] NVDA's 20-trading-day return lands between +5% and +20%, consistent with a positive but measured post-earnings drift as Blackwell demand offsets China concerns -> **hit** (horizon-end return +8.54% vs [5.0, 20.0])
- `c3` [volatility, 5d, conf 0.72] NVDA's realized daily log-return volatility over the 5 trading days following the as-of date (spanning the May 28 earnings event) ranks above the 80th percentile of same-length rolling windows from the prior 252 trading days, reflecting elevated event-driven turbulence around the report -> **miss** (realized vol 0.02449 vs p80 0.04555 (above))
- `c4` [direction, 10d, conf 0.35] NVDA closes at least 3% below the as-of price of $132.64 on the 10th trading day after as-of, reflecting downside risk if Q2 guidance disappoints relative to the ~$45 billion threshold needed to offset the China revenue loss -> **miss** (horizon-end return +6.69% vs down 3.0%)
