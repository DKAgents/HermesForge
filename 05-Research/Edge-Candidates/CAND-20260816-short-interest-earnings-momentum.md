---
status: staged
source: web
edge_type: short_interest_earnings_momentum
composite_score: 57.0
confidence: medium
regime_fit: ['risk_on', 'neutral']
created: 20260816
topic: research
has_quotes: false
tags: [short-interest, earnings, momentum, external]
---
# Edge Candidate: Short Interest Post-Earnings Momentum Amplification

## Source
Web research — Paper Trading Journal (Aug 10, 2026), GuruFocus Most Shorted Stocks, ShortSqueeze.com

## Signal
- High short interest stocks (>10% of float) show amplified post-earnings momentum
- PLTR example: 3.55% short float → strong post-earnings move in Aug 2026
- When short interest > 15% of float, post-earnings moves average 2-3x normal daily range
- Short squeeze dynamic: bears forced to cover on positive earnings, amplifying upside
- Current market has elevated short interest in several names due to Iran conflict uncertainty

## Hypothesis
Stocks with high short interest (>10% float) that report positive earnings surprises experience:
1. Short covering rallies that amplify normal post-earnings momentum
2. The effect is strongest when the beat is on revenue (not just EPS), as it invalidates the bear thesis
3. The effect compounds when the stock is already in a downtrend (bears are confident, squeeze is violent)
4. Pre-earnings IV is elevated, so post-earnings IV crush + short covering = double tailwind

This is testable by screening for high short interest stocks before earnings dates and measuring post-earnings returns.

## Entry Rules
- Screen for stocks with short interest > 10% of float and earnings within 5 trading days
- Enter long on the close of earnings day if: (a) stock beat EPS AND revenue estimates, (b) stock is up > 3% post-earnings, (c) guidance raised or maintained
- Position size: 0.5% risk (below 1% max due to event risk)
- Stop: below the pre-earnings close

## Exit Rules
- Exit after 5 trading days (momentum decays quickly post-earnings)
- Or exit at 2R profit target
- Or exit if stock gaps below pre-earnings close on any day

## Score Breakdown
- Composite: 57.0
- Signal Strength: 10.0 (short interest > 10% is a strong filter)
- Confidence: medium (15 pts) — short squeeze dynamics are well-documented
- Data Quality: 15 (short interest from FINRA, earnings from yfinance/earnings calendar)
- Actionable: 15
- Precedent: 7 (some_evidence — documented in academic literature and practitioner accounts)

## Regime Fit
['risk_on', 'neutral'] — works best when market sentiment supports risk-taking

## Testability
✅ Fully testable: Short interest data from FINRA (free, via fmp/finviz), earnings calendar from yfinance, price data from yfinance. Can backtest on 529 stock universe.

## Overlap with Engine
Engine scans for short interest squeeze candidates generally, but does NOT specifically focus on the post-earnings momentum amplification angle. This is a more specific, event-driven variant.

## Recommended Pipeline Action
PROMISING — proceed to backtest: screen high short interest stocks before earnings, measure 1-5 day post-earnings returns after positive surprises. The event-driven specificity makes this more actionable than generic short squeeze scanning.
