# Research memo

## Background
Microsoft reported strong fiscal Q2 2026 results on January 28, 2026, with revenue of $81.3B (+17% Y/Y) and Azure growth of 39%, yet the stock has fallen ~15.5% over the trailing two months to $399.54 as of February 13, 2026. The decline accelerated sharply after the earnings release, with shares dropping from ~$479 to ~$400 in just over two weeks, suggesting the market is focused on the $7.6B negative OpenAI investment adjustment and potential AI capex concerns rather than headline beats.

## Bull case
Microsoft's fundamentals remain exceptionally strong: Q2 FY2026 revenue grew 17% to $81.3B, operating income grew 21% to $38.3B, and commercial RPO surged 110% to $625B, signaling massive forward revenue visibility. The stock's 15% decline over two months — and particularly the ~16% post-earnings drop — appears overdone relative to the accelerating cloud and AI demand evidenced by Azure's 39% growth and Microsoft Cloud surpassing $50B in quarterly revenue. On a non-GAAP basis excluding OpenAI valuation impacts, net income grew 23% and EPS grew 24%, indicating the underlying business is thriving.

## Bear case
The market's sharp sell-off after earnings — despite a top- and bottom-line beat — signals deep concern about the sustainability and returns on Microsoft's massive AI investments, as the 8-K itself warns of 'significant investments in products and services that may not achieve expected returns.' The GAAP net income figure was inflated by a $7.6B positive OpenAI valuation adjustment that masked weaker underlying non-GAAP growth, and the Intelligent Cloud segment's cost of revenue surged 44% Y/Y ($9.4B to $13.6B), suggesting margin pressure from AI infrastructure buildout. More Personal Computing revenue declined 3% Y/Y, showing not all segments are participating in growth.

## Conclusion
Microsoft's post-earnings sell-off appears disconnected from the fundamental strength shown in its Q2 FY2026 results, particularly the 110% surge in commercial RPO to $625B and 39% Azure growth. However, the severity and persistence of the decline — 16% in two weeks despite a clear earnings beat — suggests the market is pricing in structural concerns about AI investment returns and cost escalation that cannot be dismissed. A modest rebound from oversold levels is the most probable near-term outcome, but confidence is tempered by the clear bearish momentum.

## Claims
- `c1` [direction, 20d, conf 0.45] MSFT closes at least 5% above the as-of price ($399.54) on the 20th trading day after 2026-02-13 -> **miss** (horizon-end return -0.11% vs up 5.0%)
- `c2` [magnitude, 20d, conf 0.35] MSFT's 20-trading-day return lands between +5% and +15% -> **miss** (horizon-end return -0.11% vs [5.0, 15.0])
- `c3` [volatility, 40d, conf 0.55] MSFT's realized daily log-return volatility over the next 40 trading days falls below the 80th percentile of the prior 252-day rolling windows, indicating calmer price action than the recent turbulent period -> **hit** (realized vol 0.01519 vs p80 0.02191 (below))
