# Research memo

## Background
Microsoft reported strong Q2 FY2025 results on January 29, 2025, with revenue of $69.6 billion (+12% Y/Y) and operating income of $31.7 billion (+17% Y/Y), driven by Azure growth of 31% and Microsoft Cloud revenue of $40.9 billion (+21%). Despite these fundamentals, MSFT shares have declined ~9.6% over the 42 trading days leading up to February 14, 2025, closing at $403.64. The sell-off accelerated after the earnings report, with the stock falling from $437 to $403 in the subsequent two weeks, suggesting investor concerns about AI capex intensity and valuation despite the AI business surpassing a $13 billion annual revenue run rate.

## Bull case
Microsoft's Q2 FY2025 results demonstrate robust cloud and AI momentum, with Azure growing 31% Y/Y and the AI business reaching a $13 billion annual revenue run rate, up 175% year-over-year. Microsoft Cloud revenue of $40.9 billion growing at 21% provides a durable, high-margin revenue base, and the company returned $9.7 billion to shareholders through dividends and buybacks. The post-earnings sell-off of roughly 8% may be an overreaction to near-term capex concerns, creating a potential mean-reversion opportunity given the strong fundamental trajectory.

## Bear case
The market's negative reaction to Microsoft's earnings—driving the stock from $437 to $403 in just two weeks despite beating on revenue and earnings—signals deep investor concern about the sustainability of AI-driven growth relative to massive infrastructure spending. Amy Hood's emphasis on 'continued investments in our cloud and AI infrastructure' suggests margin pressure ahead, and the More Personal Computing segment being 'relatively unchanged' year-over-year indicates weakness outside of cloud. The persistent downtrend with no sign of stabilization suggests further downside is possible.

## Conclusion
Microsoft's fundamentals remain strong with 12% revenue growth and 31% Azure growth, but the market's sharp negative reaction post-earnings signals concerns about AI capex intensity that are unlikely to resolve within a 40-trading-day horizon. The persistent downtrend and failure to bounce meaningfully off the $404 level suggest the stock may remain under pressure or trade sideways near current levels rather than rebound sharply. I expect MSFT to struggle to recover more than 3% above the as-of price within 20 trading days, with downside risk persisting over the full 40-day window.

## Claims
- `c1` [direction, 20d, conf 0.62] MSFT closes less than 3% above the as-of price on the 20th trading day after as-of -> **hit** (horizon-end return -4.64% vs down 3.0%)
- `c2` [magnitude, 20d, conf 0.58] MSFT's 20-trading-day return lands between -8% and +3% -> **hit** (horizon-end return -4.64% vs [-8.0, 3.0])
- `c3` [direction, 40d, conf 0.55] MSFT closes at least 2% below the as-of price on the 40th trading day after as-of -> **hit** (horizon-end return -4.86% vs down 2.0%)
- `c4` [volatility, 40d, conf 0.6] MSFT's realized daily log-return volatility over 40 trading days is above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.02191 vs p60 0.01337 (above))
