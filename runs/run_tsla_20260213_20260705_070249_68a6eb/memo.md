# Research memo

## Background
TSLA closed at $417.44 on 2026-02-13, down ~12% over the prior ~42 trading days from its December highs near $490. The company filed its FY2025 10-K on January 29, 2026 and a Q4/FY2025 update 8-K on January 28, 2026, revealing Q4 revenue of $24.9B (down 3% YoY), total deliveries of 418,227 (down 16% YoY), and operating margin of 5.7%. Despite declining automotive volumes, Tesla highlighted progress in Robotaxi rollout, FSD subscription growth, energy storage deployment, and AI infrastructure buildout as key strategic catalysts.

## Bull case
Tesla's Q4 update demonstrates meaningful diversification beyond auto sales: energy storage deployed 14.2 GWh (up 29% YoY), FSD subscriptions more than doubled in 2025 to 1.1 million active subscribers, Robotaxi service is expanding to multiple metros in 1H 2026, and the company holds $44.1B in cash. The transition to monthly FSD subscriptions and Robotaxi expansion could unlock recurring revenue streams, while AI5/AI6 chip development targets a 50x performance improvement. These optionality drivers could re-rate the stock upward if investors begin pricing the AI/autonomy platform rather than just vehicle volumes.

## Bear case
Core automotive fundamentals are deteriorating: Q4 total deliveries fell 16% YoY to 418,227, total production declined 5% YoY, 'Other models' deliveries collapsed 51% YoY, and quarterly operating income dropped 11% YoY to $1.4B with only a 5.7% operating margin. The stock has already fallen ~12% in the weeks leading into the as-of date, suggesting the market is digesting these headwinds. With Cybercab and Semi still in tooling phase, Optimus in construction, and AI5/AI6 production not planned until 2027-2028, the near-term financial trajectory remains pressured by declining volumes, tariffs, and rising R&D expenses.

## Conclusion
TSLA faces a tension between deteriorating near-term automotive fundamentals and promising but distant AI/autonomy optionality. The stock's recent ~12% decline partially reflects weak Q4 delivery and margin data, but the 40-day horizon likely captures continued digestion of these headwinds with limited positive catalysts. I expect modest downside or sideways drift as the market weighs declining auto volumes against longer-term Robotaxi and energy growth narratives.

## Claims
- `c1` [direction, 20d, conf 0.38] TSLA closes at least 5% below the as-of price of $417.44 on the 20th trading day after 2026-02-13 -> **hit** (horizon-end return -5.24% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.3] TSLA's 20-trading-day return falls between -10% and -3% -> **hit** (horizon-end return -5.24% vs [-10.0, -3.0])
- `c3` [volatility, 40d, conf 0.55] TSLA's realized daily log-return volatility over the 40-trading-day window after 2026-02-13 falls below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.02270 vs p60 0.03298 (below))
