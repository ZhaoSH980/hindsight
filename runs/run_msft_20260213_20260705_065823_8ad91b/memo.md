# Research memo

## Background
Microsoft reported strong Q2 FY2026 results on January 28, 2026, with revenue of $81.3B (+17% YoY) and operating income of $38.3B (+21% YoY), driven by Azure growth of 39% and Microsoft Cloud surpassing $50B in quarterly revenue. Despite these fundamentals, MSFT shares have sold off sharply, falling 15.5% over the 42 trading days ending February 13, 2026, closing at $399.54. The decline accelerated notably after the earnings release, with the stock dropping from ~$479 to ~$400 in the subsequent two weeks.

## Bull case
Microsoft's Q2 FY2026 results demonstrate exceptional operational strength: revenue grew 17% to $81.3B, operating income grew 21% to $38.3B, and Azure grew 39% YoY, with management explicitly stating they exceeded expectations across revenue, operating income, and EPS. The stock has already corrected 15.5% from recent highs, potentially creating a value opportunity for a company generating $80B+ in operating cash flow over six months and aggressively repurchasing shares ($7.4B in Q2 alone).

## Bear case
The post-earnings selloff is deeply concerning: despite beating expectations and delivering strong Q2 results on January 28, the stock collapsed from $479 to $400 in just 12 trading days, suggesting the market is pricing in fundamental concerns about the sustainability of AI-driven growth, competitive pressures, or capital expenditure intensity. The 10-Q reveals additions to property and equipment nearly doubled to $29.9B in Q2 from $15.8B prior year, signaling massive capex that may pressure future returns.

## Conclusion
Microsoft's fundamentals remain robust with 17% revenue growth and strong cloud/AI momentum, but the severe post-earnings selloff signals market concern about factors not fully captured in the filings, likely related to AI investment intensity and competitive risks. The magnitude of the decline suggests near-term oversold conditions, but the market's rejection of strong results warrants caution. I expect a modest recovery from oversold levels but with elevated volatility as the market digests the disconnect between fundamentals and price action.

## Claims
- `c1` [direction, 20d, conf 0.55] MSFT closes at least 3% above the as-of price ($399.54) on the 20th trading day after as-of -> **miss** (horizon-end return -0.11% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.4] MSFT's 20-trading-day return lands between +3% and +12% -> **miss** (horizon-end return -0.11% vs [3.0, 12.0])
- `c3` [direction, 40d, conf 0.5] MSFT closes at least 5% above the as-of price on the 40th trading day after as-of -> **miss** (horizon-end return -1.82% vs up 5.0%)
- `c4` [volatility, 20d, conf 0.6] Realized daily log-return volatility for MSFT over the 20-trading-day window is above the 80th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.01394 vs p80 0.01694 (above))
