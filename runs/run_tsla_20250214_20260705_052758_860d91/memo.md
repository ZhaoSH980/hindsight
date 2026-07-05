# Research memo

## Background
TSLA shares have fallen sharply from ~$463 in mid-December 2024 to ~$356 as of February 14, 2025, a decline of roughly 23% over two months. The most recent SEC filings—the Q4/FY2024 8-K (January 29) and the 10-K (January 30)—reveal a mixed picture: 2024 revenue was essentially flat YoY at $97.7B, GAAP net income fell 53% to $7.1B, and automotive revenue declined 6% for the full year. However, Q4 set records for vehicle deliveries and energy storage deployments, COGS per vehicle hit an all-time low, and management guided to a return to vehicle volume growth in 2025 alongside new affordable models and at least 50% growth in energy storage.

## Bull case
Tesla's Q4 2024 operational results show genuine momentum: record vehicle deliveries of 495,570 (up 2% YoY), all-time-low COGS per vehicle below $35,000, energy storage deployments of 11.0 GWh (up 244% YoY), and $36.6B in cash and investments. Management explicitly expects vehicle business growth to resume in 2025 with new affordable models launching in H1 2025, energy storage deployments growing at least 50%, and continued AI/autonomy progress including FSD V13 and Cybercab development. The stock's 23% decline over two months may have overshot fundamentals, potentially setting up for a mean-reversion bounce.

## Bear case
The financial deterioration is severe and accelerating: full-year GAAP net income collapsed 53% to $7.1B, operating income fell 20% to $7.1B with operating margin compressing to 7.2% (down 194 bp), automotive revenue declined 6% for the year and 8% in Q4, and free cash flow dropped 18% to $3.6B. Capex surged 27% to $11.3B, squeezing free cash flow even as operating cash flow grew. The new affordable models will achieve 'less cost reduction than previously expected,' and the broader macroeconomic environment remains uncertain. The stock's persistent downtrend through February suggests the market is pricing in continued margin pressure and execution risk.

## Conclusion
TSLA faces a tension between deteriorating near-term financials and promising medium-term catalysts (new affordable models, energy storage growth, AI/autonomy progress). The stock has already fallen 23% in two months, which may partially discount the bad news, but the persistent downtrend into mid-February with no clear stabilization signal suggests further downside risk remains. I expect continued volatility with a downward bias over the next 20-40 trading days, as the market digests weak 2024 results and awaits evidence that 2025 growth guidance is materializing.

## Claims
- `c1` [direction, 20d, conf 0.55] TSLA closes at least 5% below the as-of price of $355.84 on the 20th trading day after as-of -> **hit** (horizon-end return -33.11% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.4] TSLA's 20-trading-day return lands between -15% and -5% -> **miss** (horizon-end return -33.11% vs [-15.0, -5.0])
- `c3` [volatility, 30d, conf 0.6] TSLA's realized daily log-return volatility over the next 30 trading days is above the 70th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.05316 vs p70 0.04365 (above))
- `c4` [direction, 40d, conf 0.5] TSLA closes at least 8% below the as-of price of $355.84 on the 40th trading day after as-of -> **hit** (horizon-end return -29.08% vs down 8.0%)
