# Research memo

## Background
Supermicro filed its delayed FY2024 10-K on February 25, 2025, regaining Nasdaq compliance with no restatements and a clean BDO audit opinion on the financial statements. The stock has rallied roughly 90% from its early-February low of $26.85, closing at $51.11 on February 26. The bull case centers on the removal of delisting risk reopening the stock to institutional buyers, a $40 billion FY26 revenue target, Blackwell rack-scale systems in full production, and $320 billion in hyperscaler capex. The bear case highlights gross margins compressed to ~12%, an adverse internal controls opinion from BDO, open DOJ/SEC inquiries, potential convertible-note dilution, and JPMorgan's Street-low $23 target.

## Bull case
With the existential delisting risk resolved, no restatements, and BDO's unqualified opinion on the financials, the stock is now re-opened to index funds and risk-averse institutions who were sidelined for two quarters. The demand backdrop is the strongest in the company's history: hyperscalers have guided ~$320 billion in 2025 capex, Blackwell rack-scale systems are in full production with a DLC cooling moat, and the $40 billion FY26 target implies ~65% growth. Loop Capital raised its price target to $70 on the compliance news.

## Bear case
Gross margins of 11.8-11.9% are far below the mid-teens of a year ago, and the AI-server business is structurally lower-margin and contested by Dell, HPE, and ODM-direct suppliers. BDO issued an adverse opinion on internal controls, the DOJ and SEC inquiries remain open, the CFO search is unresolved, and $700 million in new convertible notes plus amended existing convertibles create dilution risk. JPMorgan remains Underweight with a $23 target, noting no significant order movement validating the acceleration story. FY25 guidance was cut by ~$4 billion at the midpoint.

## Conclusion
The removal of delisting risk is a genuine catalyst, but the stock has already rallied ~90% from its lows and now trades at twice JPMorgan's bear-case target. With margins near 12%, open regulatory probes, and an adverse internal-controls opinion, the risk-reward over a 40-trading-day horizon is balanced to cautious. The stock is likely to remain volatile as the market digests whether the compliance relief is sufficient to sustain the re-rating or whether fundamentals and governance concerns reassert themselves.

## Claims
- `c1` [direction, 20d, conf 0.55] SMCI closes at least 5% below the as-of price of $51.11 on the 20th trading day after as-of -> **hit** (horizon-end return -27.53% vs down 5.0%)
- `c2` [magnitude, 20d, conf 0.4] SMCI's 20-trading-day return falls between -15% and -5% -> **miss** (horizon-end return -27.53% vs [-15.0, -5.0])
- `c3` [volatility, 40d, conf 0.68] SMCI's realized daily log-return volatility over the 40-trading-day horizon ranks above the 70th percentile of the prior 252-day rolling windows -> **miss** (realized vol 0.06939 vs p70 0.08666 (above))
- `c4` [direction, 40d, conf 0.35] SMCI closes at least 10% above the as-of price of $51.11 on the 40th trading day after as-of -> **miss** (horizon-end return -29.94% vs up 10.0%)
