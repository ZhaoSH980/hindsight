# Research memo

## Background
NVDA reported FY26Q1 revenue of $44.1B (beating the ~$43.3B consensus and $43.0B guide), with data center revenue up 73% YoY. The quarter included a $4.5B H20 charge from the April 9 China export license requirement, though ex-charge non-GAAP gross margin was 71.3% and EPS would have been $0.96. Hyperscaler capex remains intact with Meta, Alphabet, Microsoft, and Amazon collectively guiding ~$300B+ for 2025, and Blackwell is ramping as NVIDIA's fastest product ever. The stock had already rallied ~28% from its April lows into the print, closing at $138.99 on May 29.

## Bull case
The fundamental setup is strong: Blackwell is in volume ramp with hyperscaler demand outstripping supply, Q2 guidance should absorb the full H20 hit yet still show growth (Street preview noted a guide near $45B would confirm Blackwell covers the China hole), and the $4.5B H20 charge is now a known, baked-in headwind. With ex-charge margins at 71.3% and management guiding to mid-70s gross margins later in the fiscal year, the earnings power ex-China is accelerating even as the stock trades well below its January highs.

## Bear case
The H20 ban permanently removes several billion dollars per quarter of China data-center revenue, and the AI Diffusion IFR set for 120-day compliance could impose worldwide licensing on virtually all NVIDIA products. Customer concentration is striking with direct customers repeatedly crossing 10% of revenue, and the capex treadmill for hyperscalers raises the risk of a digestion phase akin to 2019's cloud pause. The stock's 28% rally from April lows into earnings limits upside surprise potential, and FY2027 estimates embedding continued hypergrowth leave room for multiple compression if growth decelerates.

## Conclusion
NVDA's post-earnings setup favors upside drift over a 20-40 trading day horizon. The H20 charge is now fully baked in, Blackwell demand is covering the China revenue hole, and hyperscaler capex commitments provide strong forward visibility. However, the stock's sharp pre-earnings rally and ongoing China export policy uncertainty introduce real near-term volatility risk that could produce choppy price action before a sustained drift higher.

## Claims
- `c1` [direction, 20d, conf 0.58] NVDA closes at least 3% above the as-of price ($138.99) on the 20th trading day after as-of -> **hit** (horizon-end return +13.34% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.42] NVDA's 20-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +13.34% vs [3.0, 12.0])
- `c3` [volatility, 20d, conf 0.55] NVDA's realized daily log-return volatility over the 20 trading days after as-of exceeds the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01692 vs p60 0.03833 (above))
- `c4` [direction, 35d, conf 0.52] NVDA closes at least 5% above the as-of price ($138.99) on the 35th trading day after as-of -> **hit** (horizon-end return +23.14% vs up 5.0%)
