# Research memo

## Background
AMD's stock surged roughly 40% from mid-June through mid-August 2025, closing at $177.51 on August 15. The rally followed a strong Q2 2025 earnings report on August 5 showing record revenue of $7.7 billion (up 32% YoY), driven by record Client revenue and Data Center growth. However, Q2 GAAP results were pressured by an $800 million inventory charge from U.S. export restrictions on MI308 GPU shipments to China, and Data Center segment swung to a $155 million operating loss from $743 million a year ago.

## Bull case
AMD guided Q3 2025 revenue to approximately $8.7 billion (plus or minus $300 million), representing ~28% YoY growth and ~13% sequential growth, with non-GAAP gross margin expected at ~54% — excluding any MI308 China revenue. Management emphasized robust demand across the AI portfolio and the upcoming ramp of MI350 series accelerators, positioning AMD for significant second-half growth. Client and Gaming segment revenue surged 69% YoY to a record $3.6 billion, and the company generated record free cash flow of $1.2 billion in Q2.

## Bear case
The $800 million MI308 export control charge caused GAAP gross margin to collapse to 40% (from 49% a year ago) and pushed the Data Center segment into a $155 million operating loss, reversing the $743 million profit from Q2 2024. Non-GAAP operating income fell 29% YoY to $897 million, and non-GAAP EPS dropped 30% to $0.48. The stock's 40% rally in two months has likely priced in much of the optimistic outlook, and any further export control headwinds or AI ramp delays could trigger a sharp pullback.

## Conclusion
AMD's fundamentals show genuine momentum in Client/Gaming and a credible AI growth narrative with MI350 ramping, but the export control overhang and the stock's rapid 40% appreciation create meaningful downside risk near current levels. The Q3 guidance of ~$8.7 billion at 54% non-GAAP gross margin is strong, yet much of this appears already reflected in the price after the post-earnings rally. I expect AMD to remain volatile with a slight downward drift over the next 40 trading days as the market digests the run-up and awaits proof of MI350 execution.

## Claims
- `c1` [direction, 20d, conf 0.45] AMD closes at least 5% below the as-of price ($177.51) on the 20th trading day after as-of -> **hit** (horizon-end return -9.21% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.35] AMD's 20-trading-day return lands between -15% and -5% -> **hit** (horizon-end return -9.21% vs [-15.0, -5.0])
- `c3` [volatility, 40d, conf 0.55] AMD's realized daily log-return volatility over the 40-trading-day window is above the 70th percentile of same-length rolling windows from the prior 252 trading days -> **hit** (realized vol 0.04488 vs p70 0.02840 (above))
