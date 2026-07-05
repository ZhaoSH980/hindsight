# Research memo

## Background
META closed at $638.63 on 2026-02-13, down ~13% from its post-earnings peak of $737 on 2026-01-29. The company reported strong Q4 2025 results with revenue of $59.89B (+24% YoY) and full-year revenue of $201B (+22% YoY), but Q4 operating margin compressed to 41% from 48% as costs surged 40% YoY. Management guided 2026 capex of $115-135B, a dramatic increase from $72B in 2025, driven by AI infrastructure investments.

## Bull case
META's core advertising business remains exceptionally strong, with Q4 ad impressions growing 18% YoY and average price per ad up 6%, driving 24% revenue growth. The company generated $115.8B in operating cash flow in 2025 and holds $81.59B in cash and marketable securities, providing substantial resources to fund its AI ambitions. Q1 2026 revenue guidance of $53.5-56.5B implies continued strong double-digit growth, and the stock has already pulled back sharply from its January peak, potentially pricing in much of the cost concern.

## Bear case
The cost trajectory is alarming: Q4 costs and expenses surged 40% YoY, compressing operating margin from 48% to 41%, and management guided 2026 total expenses to $162-169B (up 38-44% from 2025's $117.7B). Capex is set to roughly double to $115-135B, with Reality Labs continuing to lose ~$19B annually. Full-year 2025 net income actually declined 3% YoY to $60.5B due to a elevated tax rate, and the massive infrastructure ramp creates significant free cash flow pressure that could persist for multiple years before AI investments pay off.

## Conclusion
META presents a tension between a robust core advertising franchise and an unprecedented ramp in AI/infrastructure spending that pressures margins and free cash flow. The stock's sharp pullback from its January peak partially reflects these concerns, but the magnitude and duration of the capex cycle creates genuine uncertainty about near-term earnings power. Over a 40-trading-day horizon, the risk-reward appears balanced with a slight bearish tilt given the cost trajectory and recent price action showing sustained selling pressure.

## Claims
- `c1` [direction, 20d, conf 0.38] META closes at least 5% below the as-of price of $638.63 on the 20th trading day after 2026-02-13 -> **miss** (horizon-end return -1.84% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.3] META's 20-trading-day return lands between -5% and -15% -> **miss** (horizon-end return -1.84% vs [-15.0, -5.0])
- `c3` [volatility, 40d, conf 0.42] META's realized daily log-return volatility over the 40-trading-day window after 2026-02-13 falls below the 60th percentile of same-length rolling windows from the prior ~252 trading days -> **miss** (realized vol 0.02608 vs p60 0.02299 (below))
- `c4` [direction, 40d, conf 0.4] META closes at least 3% above the as-of price of $638.63 on the 40th trading day after 2026-02-13 -> **hit** (horizon-end return +3.64% vs up 3.0%)
