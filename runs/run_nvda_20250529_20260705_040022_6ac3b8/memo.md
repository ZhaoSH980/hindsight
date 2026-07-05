# Research memo

## Background
NVIDIA reported FY26Q1 revenue of $44.1B (beating the ~$43.3B consensus) with Data Center revenue up 73% YoY, driven by the Blackwell ramp. The Q2 guide of $45.0B (±2%) absorbs an ~$8B H20 revenue loss from China export controls, yet still implies sequential growth — signaling Blackwell demand is covering the China hole. Hyperscaler 2025 capex is confirmed intact at well over $300B combined, but the stock has already rallied ~28% from its April lows into the print, and the H20 charge and margin compression are known headwinds.

## Bull case
The $45B Q2 guide despite an ~$8B H20 revenue loss is the strongest signal: Blackwell demand is so strong that it absorbs the entire China hit and still grows sequentially. Non-GAAP gross margin ex-H20 was 71.3% in Q1 and guided to 72.0% in Q2, with management targeting a return to the mid-70s by late FY26 as Blackwell yields improve. With hyperscaler capex exceeding $300B for 2025 and Blackwell representing the fastest product ramp in NVIDIA's history at $11B in its first quarter, the demand pipeline is deep and visible.

## Bear case
The stock has already rallied ~28% from April lows into earnings, pricing in much of the good news. The H20 ban permanently removes ~$17B in annual China revenue (13% of FY25 total), and GAAP gross margin has compressed from 78.4% to 60.5% YoY. Structural risks remain: customer concentration with multiple direct customers above 10% of revenue, DeepSeek-style algorithmic efficiency gains that could weaken the AI-demand-to-GPU-units mapping, and lease-check data (TD Cowen) suggesting Microsoft walked away from ~2GW of data-center capacity — an early indicator of potential 2026 capex digestion.

## Conclusion
The setup favors upside drift over a 20-40 trading day horizon. The $45B guide despite the $8B H20 hole is a definitive positive surprise that the market is still absorbing, and the confirmed hyperscaler capex pipeline provides fundamental support. However, the stock's 28% pre-earnings rally and known structural risks cap the magnitude of further near-term gains. A moderate upside move of 3-8% over 20 trading days is the most probable outcome, with volatility likely to remain elevated given the binary nature of AI capex cycle debates.

## Claims
- `c1` [direction, 20d, conf 0.58] NVDA closes at least 3% above the as-of price (138.9952) on the 20th trading day after as-of -> **hit** (horizon-end return +13.34% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.45] NVDA's 20-trading-day return lands between +3% and +10% -> **miss** (horizon-end return +13.34% vs [3.0, 10.0])
- `c3` [volatility, 40d, conf 0.55] NVDA's realized daily log-return volatility over the next 40 trading days falls in the above-60th percentile relative to same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01653 vs p60 0.04244 (above))
- `c4` [direction, 40d, conf 0.52] NVDA closes at least 5% above the as-of price (138.9952) on the 40th trading day after as-of -> **hit** (horizon-end return +26.99% vs up 5.0%)
