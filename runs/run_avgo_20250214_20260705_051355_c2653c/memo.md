# Research memo

## Background
Broadcom closed at $230.11 on 2025-02-14, down 6.53% over the prior ~42 trading days, with a sharp single-day drop from $241.62 to $199.58 on 2025-01-27 followed by a partial recovery. The company reported record FY2024 revenue of $51.6 billion (up 44% YoY) driven by AI revenue of $12.2 billion (up 220% YoY) and the successful integration of VMware, with Q1 FY2025 revenue guidance of approximately $14.6 billion (up 22% YoY). The balance sheet carries significant debt from the VMware acquisition ($66.3B long-term debt) but also strong free cash flow generation ($19.4B in FY2024).

## Bull case
Broadcom's AI revenue grew 220% YoY to $12.2 billion in FY2024, and the company guided Q1 FY2025 revenue to $14.6 billion (up 22% YoY) with Adjusted EBITDA margins of ~66%, signaling continued strong growth momentum. The stock has already experienced a significant pullback from its December highs near $246 to $230, and with record free cash flow of $19.4 billion and a 14th consecutive annual dividend increase, the fundamental backdrop supports a recovery. The January 13, 2025 credit agreement refinancing also suggests proactive balance sheet management.

## Bear case
AVGO's balance sheet shows $66.3 billion in long-term debt and $97.97 billion in total liabilities following the VMware acquisition, with retained earnings at zero as of November 3, 2024. The stock experienced a violent 17.4% single-day decline on January 27, 2025 (from $241.62 to $199.58), and the 10-K explicitly warns of risks including VMware integration challenges, semiconductor cyclicality, dependence on a limited number of customers, and trade restrictions. The stock's 6.53% decline over the measurement window suggests the market remains cautious despite strong headline numbers.

## Conclusion
AVGO presents a mixed picture: exceptional AI-driven revenue growth and strong free cash flow generation are offset by a heavily leveraged balance sheet and recent price volatility including a sharp January selloff. The Q1 FY2025 guidance of $14.6B revenue with 66% EBITDA margins provides a credible fundamental floor, but the debt overhang and integration risks from VMware create meaningful uncertainty. Over a 40-trading-day horizon, I expect modest upside driven by AI momentum and the post-selloff recovery pattern, but with elevated volatility reflecting ongoing integration and macro risks.

## Claims
- `c1` [direction, 20d, conf 0.55] AVGO closes at least 3% above the as-of price of $230.11 on the 20th trading day after 2025-02-14 -> **miss** (horizon-end return -16.54% vs up 3.0%)
- `c2` [magnitude, 20d, conf 0.4] AVGO's 20-trading-day return lands between +3% and +12% -> **miss** (horizon-end return -16.54% vs [3.0, 12.0])
- `c3` [volatility, 40d, conf 0.6] AVGO's realized daily log-return volatility over the 40-trading-day horizon is above the 70th percentile of same-length rolling windows from the prior ~252 trading days -> **hit** (realized vol 0.04889 vs p70 0.03925 (above))
- `c4` [direction, 40d, conf 0.5] AVGO closes at least 5% above the as-of price of $230.11 on the 40th trading day after 2025-02-14 -> **miss** (horizon-end return -23.23% vs up 5.0%)
