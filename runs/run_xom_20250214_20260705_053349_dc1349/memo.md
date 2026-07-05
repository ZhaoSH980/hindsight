# Research memo

## Background
ExxonMobil reported full-year 2024 earnings of $33.7 billion, down from $36.0 billion in 2023, pressured by weaker refining margins and lower natural gas prices despite record production from Guyana and Permian assets. The stock traded around $103.94 as of February 14, 2025, having recovered from a late-January dip below $102 but remaining below its mid-January peak near $107. The company generated $55 billion in operating cash flow and continued aggressive shareholder returns, including over $19 billion in share repurchases for 2024.

## Bull case
XOM's advantaged volume growth from Guyana and Permian (including Pioneer), record high-value product sales, and $12.1 billion in cumulative structural cost savings provide a durable earnings floor. With $34.4 billion in free cash flow, industry-leading return on capital employed of 12.7%, and sustained shareholder distributions exceeding $26 billion, the stock has strong fundamental support near current levels.

## Bear case
Energy Products earnings collapsed from $12.1 billion in 2023 to $4.0 billion in 2024 due to significantly weaker industry refining margins, and fourth-quarter Energy Products earnings fell to just $402 million. This margin deterioration, combined with higher depreciation and maintenance expenses from 2025 project start-ups, suggests near-term earnings pressure could weigh on the stock.

## Conclusion
XOM appears range-bound near $104 with mixed fundamental signals: strong upstream growth and cash returns are offset by sharp downstream margin compression. Over a 40-trading-day horizon, the stock is likely to drift modestly lower as refining margin headwinds persist against a backdrop of already-soft Q4 results. Volatility is expected to remain within normal ranges given the stock's stable trading pattern.

## Claims
- `c1` [direction, 40d, conf 0.38] XOM closes at least 3% below the as-of price on the 40th trading day after as-of -> **hit** (horizon-end return -4.48% vs down 3.0%)
- `c2` [magnitude, 40d, conf 0.33] XOM's 40-trading-day return lands between -8% and -1% -> **hit** (horizon-end return -4.48% vs [-8.0, -1.0])
- `c3` [volatility, 20d, conf 0.55] XOM's realized daily log-return volatility over the next 20 trading days falls below the 60th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.01632 vs p60 0.01212 (below))
