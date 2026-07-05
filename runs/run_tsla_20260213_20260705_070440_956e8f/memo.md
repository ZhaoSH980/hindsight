# Research memo

## Background
TSLA closed at $417.44 on 2026-02-13, down ~12% over the prior two months from $475.31 on December 15. The company recently filed its FY2025 10-K and Q4 2025 earnings update, reporting $4.4B GAAP operating income for the year and $1.4B in Q4, alongside a 16% YoY decline in Q4 deliveries. Tesla is positioning itself as a physical AI company, with Robotaxi service ramping in Austin, Cybercab and Semi production targeted for 2026, and Optimus production lines being installed.

## Bull case
Tesla's Q4 results showed improving automotive gross margin even excluding regulatory credits, energy storage deployments grew 29% YoY to 14.2 GWh, and FSD subscriptions grew 38% YoY to 1.1 million active users. The Robotaxi service has begun unsupervised operations in Austin with expansion to multiple metros planned for 1H 2026, and Cybercab, Semi, and Megapack 3 are all on schedule for volume production in 2026, potentially catalyzing a re-rating toward the AI and autonomous-driving narrative.

## Bear case
Q4 total deliveries fell 16% YoY to 418,227 and total production declined 5% YoY, signaling weakening core automotive demand. The stock has already dropped over 12% in two months, and the transition from upfront FSD payments to monthly-only subscriptions creates near-term revenue uncertainty. Key growth products—Cybercab, AI5 chips (2027), AI6 chips (2028), and Optimus—remain pre-revenue, meaning the financial burden of AI infrastructure investment is being borne now with monetization still quarters or years away.

## Conclusion
TSLA faces near-term headwinds from declining automotive volumes and a significant stock drawdown, though the company's AI and robotics pipeline provides a credible long-term growth narrative. Over a 40-trading-day horizon, the recent selling pressure and weak delivery trends likely persist, but the stock may find a floor as Q4 earnings details are digested and Robotaxi expansion milestones approach. I expect modest downside risk to persist with elevated volatility given the gap between current automotive fundamentals and future AI monetization expectations.

## Claims
- `c1` [direction, 20d, conf 0.45] TSLA closes at least 5% below the as-of price of $417.44 on the 20th trading day after as-of -> **hit** (horizon-end return -5.24% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.35] TSLA's 20-trading-day return lands between -12% and -5% -> **hit** (horizon-end return -5.24% vs [-12.0, -5.0])
- `c3` [volatility, 40d, conf 0.55] TSLA's realized daily log-return volatility over the 40-trading-day horizon is above the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.02270 vs p60 0.03298 (above))
