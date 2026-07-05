# Research memo

## Background
AMD delivered record Q4 2024 revenue of $7.7 billion (up 24% YoY) and full-year revenue of $25.8 billion, with Data Center segment revenue nearly doubling to $12.6 billion driven by Instinct GPU and EPYC CPU growth. Despite these results, the stock has declined sharply, falling from ~$129 in early January to $113.10 as of February 14, a ~10.7% drop over the trailing window. The Q1 2025 guidance of ~$7.1 billion implies a ~7% sequential decline, which may be pressuring sentiment. The 10-K was filed on February 5, providing comprehensive risk disclosures alongside the strong financial performance.

## Bull case
AMD's Data Center revenue grew 94% YoY to a record $12.6 billion in 2024, with Instinct accelerator revenue exceeding $5 billion, and Q1 2025 guidance of ~$7.1 billion still represents ~30% YoY growth. The company holds $5.1 billion in cash and short-term investments with only $1.7 billion in total debt, and generated $2.4 billion in free cash flow for the year. After a ~10.7% price decline over the recent window with no fundamental deterioration, the stock may be oversold, and the strong AI/data center momentum could attract buyers at these levels.

## Bear case
AMD's Q1 2025 revenue guidance of ~$7.1 billion represents a ~7% sequential decline from Q4's $7.7 billion, breaking the sequential growth trajectory. Gaming revenue collapsed 59% YoY and Embedded revenue fell 13% YoY, showing weakness beyond the data center narrative. GAAP net income declined 28% YoY in Q4 despite record revenue, and the stock's persistent decline from ~$129 to ~$113 over six weeks suggests the market is pricing in concerns about the sustainability of AI-driven growth and competitive pressures from NVIDIA.

## Conclusion
AMD presents a mixed picture: exceptional data center growth and strong AI momentum are offset by declining Gaming and Embedded segments, a sequential revenue guide-down for Q1 2025, and falling GAAP profitability. The stock's sharp recent decline may create a near-term bounce opportunity, but the sequential guidance break and broader segment weakness warrant caution. Over a 40-day horizon, modest recovery from oversold levels appears more likely than continued decline, though conviction is tempered by the guide-down.

## Claims
- `c1` [direction, 20d, conf 0.45] AMD closes at least 3% above the as-of price of $113.10 on the 20th trading day after 2025-02-14 -> **miss** (horizon-end return -7.52% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.35] AMD's 20-trading-day return lands between 0% and +8% -> **miss** (horizon-end return -7.52% vs [0.0, 8.0])
- `c3` [volatility, 40d, conf 0.55] AMD's realized daily log-return volatility over the 40-trading-day horizon is above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.05007 vs p60 0.02911 (above))
