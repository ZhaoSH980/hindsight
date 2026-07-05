# Research memo

## Background
GOOGL closed at $203.32 on 2025-08-15, up 15.35% over the prior two months, buoyed by a strong Q2 2025 earnings report on July 23 showing 14% revenue growth to $96.4B and 32% Google Cloud growth. The company raised its 2025 capex guidance to ~$85B and reported a $108.2B Cloud revenue backlog, signaling sustained AI infrastructure investment. However, free cash flow fell sharply to $5.3B in Q2 from $18.95B in Q1 due to elevated capex, and ongoing antitrust litigation and regulatory scrutiny remain overhangs.

## Bull case
Alphabet's Q2 2025 results demonstrate robust momentum across all segments, with Google Cloud growing 32% YoY to $13.6B and reaching a >$50B annual revenue run-rate. The $108.2B remaining performance obligation backlog, primarily Cloud-related, provides strong revenue visibility, with ~55% expected to be recognized over 24 months. EPS grew 22% to $2.31 and operating margin held at 32.4% despite a legal settlement charge, showing expense discipline. AI-driven product enhancements like AI Overviews and AI Mode are positively impacting Search, supporting continued double-digit advertising revenue growth.

## Bear case
The massive step-up in capital expenditures to ~$85B for 2025 is pressuring free cash flow, which collapsed to just $5.3B in Q2 2025 from $18.95B in Q1. Property and equipment, net surged to $203.2B from $171.0B at year-end 2024, and long-term debt rose to $23.6B from $10.9B following a $12.5B note issuance in May 2025. This aggressive spending cycle carries execution risk if AI monetization does not scale proportionally. Additionally, ongoing antitrust litigation and heightened regulatory scrutiny could constrain business practices and create financial liabilities.

## Conclusion
GOOGL's fundamentals remain strong with broad-based double-digit growth and a deep Cloud backlog, but the capex cycle is creating a temporary free cash flow trough that could weigh on sentiment near-term. The stock has already rallied 15% in two months, pricing in much of the Q2 beat. Over a 40-trading-day horizon, modest upside is likely if Cloud momentum continues, but the risk-reward is more balanced than the recent rally suggests.

## Claims
- `c1` [direction, 40d, conf 0.55] GOOGL closes at or above 3% above the as-of price of $203.32 on the 40th trading day after 2025-08-15 -> **hit** (horizon-end return +19.85% vs up 3.0%)
- `c2` [magnitude, 40d, conf 0.42] GOOGL's 40-trading-day return lands between 0% and +8% -> **miss** (horizon-end return +19.85% vs [0.0, 8.0])
- `c3` [volatility, 40d, conf 0.58] GOOGL's realized daily log-return volatility over the 40-trading-day horizon falls below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.01916 vs p60 0.02069 (below))
