# Research memo

## Background
Apple reported record Q1 FY2026 results on January 29, 2026, with revenue of $143.8 billion (up 16% YoY) and diluted EPS of $2.84 (up 19% YoY), driven by all-time highs in iPhone and Services revenue. Despite these strong fundamentals, the stock has sold off sharply, falling from $277.60 on February 6 to $255.54 on February 13 — a 6.6% decline in the most recent window — with the drop accelerating after the ex-dividend date of February 9. The 10-Q filed January 30 highlights tariff risks, including a pending Section 232 semiconductor investigation, and warns that gross margins will be subject to volatility and downward pressure.

## Bull case
Apple's Q1 FY2026 results were exceptionally strong, with iPhone revenue up 23% YoY to $85.3 billion, Greater China revenue surging 38%, total gross margin expanding 130 basis points to 48.2%, and the installed base exceeding 2.5 billion active devices. The company generated nearly $54 billion in operating cash flow and returned almost $32 billion to shareholders. This combination of record revenue, expanding margins, and massive cash generation provides a durable fundamental floor that makes the recent 6.6% selloff look like an overreaction.

## Bear case
The 10-Q explicitly warns that gross margins will be subject to 'volatility and downward pressure,' and tariff risks remain significant — the Section 232 semiconductor investigation results were published January 14, 2026, and further measures could be imposed at any time. R&D expenses surged 32% YoY to $10.9 billion, compressing operating leverage. The stock's sharp drop from $277.60 to $255.54 in the final week suggests the market is pricing in deteriorating forward expectations rather than backward-looking Q1 strength, and the selloff could continue if tariff headlines intensify.

## Conclusion
Apple's fundamentals are genuinely strong with record Q1 revenue, expanding margins, and a 2.5 billion device installed base, but the stock's sharp recent decline signals that the market is focused on forward risks — particularly tariffs, the Section 232 semiconductor investigation, and rising R&D costs. The near-term path likely depends on whether the selloff is an emotional overreaction to be reversed or the start of a tariff-driven de-rating. I lean toward a partial recovery over 40 trading days given the fundamental strength, but with moderate conviction given unresolved tariff overhang.

## Claims
- `c1` [direction, 20d, conf 0.55] AAPL closes at least 3% above the as-of price of $255.54 on the 20th trading day after as-of -> **miss** (horizon-end return -1.16% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.42] AAPL's 20-trading-day return lands between +3% and +12% -> **miss** (horizon-end return -1.16% vs [3.0, 12.0])
- `c3` [volatility, 40d, conf 0.5] AAPL's realized daily log-return volatility over the 40-trading-day horizon window falls below the 60th percentile of same-length rolling windows from the prior 252 trading days -> **hit** (realized vol 0.01348 vs p60 0.01550 (below))
