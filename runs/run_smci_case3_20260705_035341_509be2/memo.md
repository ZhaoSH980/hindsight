# Research memo

## Background
SMCI filed its delayed FY2024 10-K on February 25, 2025, regaining Nasdaq compliance with no restatements and a clean BDO audit opinion on financial statements, though BDO issued an adverse opinion on internal controls. The stock has rallied roughly 90% from its early-February low of $26.85 to $51.11 on February 26, driven by relief on delisting risk and CEO Charles Liang's $40 billion FY26 revenue target. However, gross margins have compressed to ~11.8-11.9%, FY25 guidance was cut to $23.5-$25.0 billion, and DOJ/SEC inquiries remain open.

## Bull case
With the existential delisting risk removed, no restatements, and BDO's unqualified opinion on the financial statements, institutional buyers who were sidelined for two quarters can return. The AI capex backdrop is the strongest in the company's history with hyperscalers guiding ~$320 billion in 2025 capex, Blackwell rack-scale systems are in full production, and management's $40 billion FY26 revenue target implies ~65% growth. Loop Capital raised its price target to $70 on the compliance news.

## Bear case
The stock has already doubled from its February 3 low, pricing in much of the good news. Gross margin has compressed to 11.8-11.9% from the mid-teens, FY25 guidance was cut by ~$4 billion at the midpoint, and the $40 billion FY26 figure is a target, not guidance. BDO issued an adverse opinion on internal controls, DOJ and SEC subpoenas remain active, $700 million in new convertible notes create dilution risk near a $61.06 conversion price, and the stock has already faded from its $60.25 intraday peak on February 19 to $45.54 on February 25 before bouncing.

## Conclusion
The compliance overhang is genuinely cleared and the AI demand backdrop is robust, but the stock's 90% rally from the lows has already discounted much of the relief. With margins compressed, FY25 guidance cut, open DOJ/SEC inquiries, an adverse internal controls opinion, and dilution risk from convertibles, the risk-reward at $51.11 is balanced to slightly negative over a 20-40 trading day horizon. Further upside likely requires evidence of margin stabilization or Blackwell ramp execution that has not yet been demonstrated.

## Claims
- `c1` [direction, 20d, conf 0.45] SMCI closes at least 5% below the as-of price ($51.11) on the 20th trading day after as-of -> **hit** (horizon-end return -27.53% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.3] SMCI's 20-trading-day return lands between -15% and -5% -> **miss** (horizon-end return -27.53% vs [-15.0, -5.0])
- `c3` [magnitude, 40d, conf 0.4] SMCI's 40-trading-day return lands between -20% and +5% -> **miss** (horizon-end return -29.94% vs [-20.0, 5.0])
- `c4` [volatility, 40d, conf 0.55] SMCI's realized daily log-return volatility over 40 trading days is above the 70th percentile of same-length rolling windows from the prior 252 trading days -> **miss** (realized vol 0.06939 vs p70 0.08666 (above))
