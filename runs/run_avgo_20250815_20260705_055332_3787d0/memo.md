# Research memo

## Background
Broadcom (AVGO) has rallied approximately 22% over the two months leading into August 15, 2025, closing at $304.11. The company's most recent SEC filings show strong fundamental momentum: Q2 FY2025 revenue grew 20% YoY to $15.0 billion, AI semiconductor revenue grew 46% YoY to over $4.4 billion, and management guided Q3 revenue to approximately $15.8 billion (+21% YoY) with AI revenue accelerating to $5.1 billion. The company generated record free cash flow of $6.4 billion and returned $7.0 billion to shareholders through dividends and buybacks.

## Bull case
Broadcom's AI semiconductor revenue is accelerating — management guided Q3 AI revenue to $5.1 billion, up from $4.4 billion in Q2, marking ten consecutive quarters of growth. With consolidated revenue guidance of $15.8 billion (+21% YoY), adjusted EBITDA margins of at least 66%, and record free cash flow of $6.4 billion supporting $4.2 billion in share repurchases, the fundamental trajectory supports continued price appreciation. The stock's 22% rally over two months reflects strong momentum entering the back half of fiscal 2025.

## Bear case
AVGO has already rallied ~22% in two months, creating potential for a near-term pullback as the price has moved from $249 to $304 in a relatively short period. The company carries significant indebtedness — total debt principal outstanding of $69.4 billion as of May 4, 2025, including $3.9 billion in commercial paper — which the 10-Q explicitly flags as a risk factor requiring sufficient cash flows to service. The stock also pulled back 1.6% on August 15 from $308.97 to $304.12, potentially signaling exhaustion of the recent rally.

## Conclusion
AVGO's fundamentals are strong with accelerating AI revenue and robust cash generation, but the stock's rapid 22% two-month advance creates meaningful short-term pullback risk. Over a 40-trading-day horizon, the fundamental trajectory likely supports prices modestly above current levels, though the extended run-up suggests limited upside in the near term and potential for volatility as the market digests recent gains.

## Claims
- `c1` [direction, 40d, conf 0.55] AVGO closes at least 3% above the as-of price ($304.11) on the 40th trading day after 2025-08-15 -> **hit** (horizon-end return +16.64% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.4] AVGO's 40-trading-day return lands between +3% and +12% -> **miss** (horizon-end return +16.64% vs [3.0, 12.0])
- `c3` [volatility, 20d, conf 0.5] AVGO's realized daily log-return volatility over the next 20 trading days is above the 60th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.03339 vs p60 0.03620 (above))
