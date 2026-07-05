# Research memo

## Background
AMD delivered record Q2 2025 revenue of $7.7 billion with Q3 guidance of ~$8.7 billion (+28% YoY), driven by strong EPYC and Ryzen processor sales and an anticipated MI350 ramp. However, U.S. export controls on MI308 GPUs to China caused ~$800 million in inventory charges, pressuring GAAP gross margin to 40% and creating a Data Center segment operating loss of $155 million. The stock has rallied ~40% over the past two months to $177.51 as of August 15, 2025, reflecting optimism about second-half AI accelerator growth and the ZT Systems integration strategy.

## Bull case
AMD's Q3 guidance of ~$8.7 billion in revenue (+28% YoY, +13% sequential) signals strong demand momentum, and management emphasized robust demand across the AI portfolio with the MI350 ramp ahead. Excluding the one-time MI308 export charges, non-GAAP gross margin was 54%, and free cash flow reached $1.18 billion in Q2. The ZT Systems divestiture to Sanmina for $3 billion streamlines operations while retaining AI design expertise, and partnerships with Meta, OpenAI, xAI, Oracle, and Microsoft validate AMD's competitive positioning in AI infrastructure.

## Bear case
The $800 million MI308 inventory charge demonstrates significant geopolitical risk to AMD's China revenue, and the company explicitly excluded any MI308 China shipment revenue from its Q3 outlook pending license review. The Data Center segment posted a $155 million operating loss in Q2, and GAAP gross margin collapsed to 40% from 50% in Q1. With the stock already up 40% in two months, much of the positive outlook may be priced in, and any further export control deterioration or MI350 ramp delays could trigger a sharp pullback.

## Conclusion
AMD's fundamentals are strengthening with record revenue and strong Q3 guidance, but the stock's 40% two-month rally creates elevated expectations and near-term volatility risk. The MI308 export control situation remains an unresolved overhang that could either resolve favorably or worsen. Over a 40-trading-day horizon, the risk-reward appears balanced-to-cautiously-bearish given the extended run-up and geopolitical uncertainty, with modest downside more likely than continued sharp appreciation.

## Claims
- `c1` [direction, 20d, conf 0.45] AMD closes at least 5% below the as-of price of $177.51 on the 20th trading day after August 15, 2025 -> **hit** (horizon-end return -9.21% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.35] AMD's 20-trading-day return falls between -5% and -15% -> **hit** (horizon-end return -9.21% vs [-15.0, -5.0])
- `c3` [volatility, 40d, conf 0.55] AMD's realized daily log-return volatility over the 40-trading-day window after August 15, 2025 exceeds the 70th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.04488 vs p70 0.02840 (above))
- `c4` [direction, 40d, conf 0.5] AMD closes at least 3% below the as-of price of $177.51 on the 40th trading day after August 15, 2025 -> **miss** (horizon-end return +21.92% vs down 3.0%)
