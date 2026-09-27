---
status: backtest_failed
source: rotation
edge_type: sector_momentum_continuation
composite_score: 67.6
confidence: medium
regime_fit: ['risk_on']
created: 20260814
topic: research
has_quotes: false
tags: []
---
# Edge Candidate: Technology (XLK) leading with momentum continuing

## Source
rotation scanner

## Signal

20d RS: +4.20%, 1d RS: +0.65%

## Hypothesis
Strong sector with continued RS improvement. Momentum persistence suggests more upside. Buy top stocks in sector on pullbacks to 10MA.

## Entry Rules
Buy top 3 stocks in XLK sector on pullback to 10MA with volume contraction. Stop below 20MA.

## Exit Rules
Exit when sector RS turns negative on 5d, or target 3R.

## Score Breakdown
- Composite: 67.6
- Signal Strength: 12.6
- Confidence: medium (15 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 10

## Regime Fit
['risk_on']

## Recommended Pipeline Action
SPECULATIVE — quick Phase 1A backtest to check for edge.

## Pipeline Processing Log (2026-08-16, HermesForge Autonomous Pipeline)

**Scanner coded:** `scripts/validation/scanners/scanner_sector_momentum_pullback.py`
- Generalized beyond XLK: each day identifies the leading sector (sector ETF with
  best 20-day relative strength vs SPY, RS>0) sustained for >=5 consecutive days,
  then buys that sector's stocks on a 10-MA pullback with volume contraction
  (vol < 0.9 × 20d avg), trend agreement (close>50MA>200MA), stop below 20MA, target 3R.
- Static GICS sector map for ~170 well-known S&P constituents; tickers outside the
  map are skipped (no external sector reference available).

**Phase 1A backtest** (`run_phase1a.py --scanner ... --json`):
- total_signals: 2689 | signals_per_year: 409.1 | mean_r: **+0.007** | median_r: -0.484
- win_rate: 44.5% | sub_positive: 1/3 | p_value: **0.8396** | t_stat: 0.20
- ADR-004 classification: ❌ KILL (avg_r < 0.2); friction flag: true

**Verdict: BACKTEST_FAILED.** mean_r is positive but statistically indistinguishable
from zero (p=0.84, t=0.20). The sector-momentum-continuation pullback shows no
detectable edge frictionless — the persistence of leading-sector RS does not
reliably predict 10-MA-pullback continuation in this universe. Edge almost
certainly does not survive transaction costs. Not advanced to walk-forward.

**Survivorship caveat:** universe is current S&P constituents (ADR-004); sector
map reflects current memberships. Historical members later removed are not
represented, which could flatter or (here) simply not rescue the result.

