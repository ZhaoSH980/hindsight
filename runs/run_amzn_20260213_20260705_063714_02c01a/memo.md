# Research memo

## Background
AMZN closed at $198.79 on 2026-02-13, down 10.67% over the prior ~40 trading days, with the selloff accelerating sharply after its Q4 2025 earnings release on February 5. The decline followed strong Q4 results (14% revenue growth, AWS up 24%) but was accompanied by guidance for Q1 2026 operating income of $16.5–$21.5 billion, potentially below the $18.4 billion posted in Q1 2025, plus disclosure of ~$200 billion in planned 2026 capex and a dramatic free cash flow decline to $11.2 billion from $38.2 billion driven by AI infrastructure investment.

## Bull case
The fundamental business is accelerating: Q4 2025 revenue grew 14% to $213.4 billion, AWS grew 24% (its fastest in 13 quarters) to $35.6 billion, and AWS operating income reached $12.5 billion. Management highlighted a $10 billion annual run-rate in custom chips growing at triple-digit percentages, a massive AWS customer pipeline including OpenAI and Anthropic, and ~$200 billion in unearned AWS performance obligations as of September 2025. The stock has been oversold — down roughly 19% from its January 8 peak of $246.29 to $198.79 — despite these improving fundamentals, suggesting a potential mean-reversion bounce.

## Bear case
The Q1 2026 operating income guidance midpoint of $19.0 billion is only modestly above Q1 2025's $18.4 billion, and the low end of $16.5 billion represents a year-over-year decline, despite 11–15% revenue growth. This margin compression is driven by ~$1 billion in higher Amazon Leo costs, quick commerce investment, and a staggering ~$200 billion planned capex for 2026. Free cash flow already collapsed from $38.2 billion to $11.2 billion in 2025, and the 10-K explicitly warns that revenue growth may not be sustainable and growth rates may decrease. The stock's relentless decline from $247.38 on January 9 to $198.79 on February 13 — with no stabilization — signals institutional selling pressure that may persist.

## Conclusion
AMZN faces a tension between accelerating top-line and AWS momentum on one hand and deteriorating margins and free cash flow on the other, with the market clearly focused on the latter as evidenced by the 19% decline since early January. The planned $200B capex and Q1 guidance suggesting flat-to-down operating income validate near-term bearish concerns, but the severity of the selloff creates conditions for a tactical bounce. I expect continued volatility with a downward bias over the next 40 trading days, though a stabilization bounce is plausible given oversold conditions.

## Claims
- `c1` [direction, 40d, conf 0.45] AMZN closes at least 5% below the as-of price of $198.79 on the 40th trading day after 2026-02-13 -> **miss** (horizon-end return +25.27% vs down 5.0%)
- `c2` [magnitude, 40d, conf 0.35] AMZN's 40-trading-day return lands between -15% and -5% -> **miss** (horizon-end return +25.27% vs [-15.0, -5.0])
- `c3` [volatility, 20d, conf 0.55] AMZN's realized daily log-return volatility over the 20 trading days after 2026-02-13 exceeds the 80th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.01601 vs p80 0.02584 (above))
- `c4` [direction, 10d, conf 0.3] AMZN closes at least 3% above the as-of price of $198.79 on the 10th trading day after 2026-02-13 -> **hit** (horizon-end return +4.83% vs up 3.0%)
