# IMPL: US-116 — Real regime_filter Module

**Coder:** HermesForge Coder Agent
**Date:** 2026-08-16
**Ticket:** US-116
**Commit:** 17951c6

---

## Summary

Replaced the 74-line hardcoded JSON stub in `scripts/data/regime_filter.py` with a real regime detection module that reads from cached parquet data and exposes `get_regime()` + `tag_signal()`.

## What Was Implemented

### get_regime(as_of=None, force_refresh=False) -> dict

Computes regime from 7 weighted components:

| Component    | Weight | Data Source                    |
|-------------|--------|--------------------------------|
| VIX         | 20%    | VIXINDEX.parquet               |
| Breadth     | 20%    | 100-stock random sample        |
| SPY Trend   | 20%    | SPY.parquet                    |
| DXY         | 15%    | DXY.parquet                    |
| Fear&Greed  | 10%    | fear_greed.parquet             |
| Correlation | 10%    | SPY vs BTC (6h/BTC.parquet)    |
| Yields      | 5%     | TNX.parquet                    |

- 4 hard override rules: crisis (VIX>30 or VIX>25+spike), VIX spike caution, unified (corr>0.8), diversified (corr<0.2 + low internal corr)
- Look-ahead-free: `as_of` truncates all data to that date
- Never raises — total failure (VIX+SPY both missing) returns neutral with confidence=0
- Confidence adjusted by completeness ratio and minimum freshness penalty
- Returns full dict satisfying all 3 callers (regime_strategy_selector, capture_signals, compute_confluence)

### tag_signal(signal, regime=None) -> dict

- MUTATES signal dict in place AND returns it
- Adds: regime, regime_confidence, regime_compatible, regime_action, regime_risk_multiplier, regime_tagged_at
- Imports STRATEGY_REGISTRY locally (avoids circular imports)
- Actions: boost (1.5x), run (1.0x), reduce (0.7x), suppress (0.0x)
- Unknown/confidence=0 regime -> tags as "unknown", action=run (no blocking)

### Additional Components

- Volatility Risk Premium: VIX - SPY 20d realized vol
- Term structure: VIX vs VIX3M (contango/backwardation/flat)
- Breadth divergence detection (bearish/bullish)
- Stock internal correlation: avg pairwise of 20 sampled stocks
- Legacy placeholders: put_call, tvl, stablecoin, rotation, funding, economic_events

## Performance

- Measured: ~374ms per call (well under 1s budget)
- Column projection (`columns=["close"]`) on all parquet reads
- 100-stock random sample for breadth (fixed seed=42 for reproducibility)
- 5-minute TTL breadth cache for repeated calls within a session
- 20-stock sample for internal correlation

## Data Source Notes

- VIXINDEX, DXY, TNX, SPY, fear_greed all present and fresh (last bar 2026-08-14/16)
- VIX3M present but stale (2026-07-17) — term structure still computed, freshness penalized
- BTC 6h data stale (2026-07-29) but within 30-day window — correlation computed
- DXY file is `DXY.parquet` (not DX-Y.NYB.parquet) — module checks both
- TNX file is `TNX.parquet` (not ^TNX.parquet) — module checks both
- fear_greed.parquet has no DatetimeIndex (has 'date' column) — handled with conversion
- All parquet columns are lowercase as expected

## numpy Import Guard

Module works in both Hermes venv and default venv:
```python
try:
    import numpy as np
    import pandas as pd
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Pure-Python fallbacks for correlation/SMA
```

## Bug Found and Fixed During Implementation

`_check_freshness()` used `_last_date()` which projected only the `close` column. fear_greed.parquet has no `close` column (it has `date`, `value`, `classification`), causing it to always return "unavailable" freshness (0.3 penalty). Fixed by making `_last_date()` fall back to reading all columns when the `close` projection returns None.

## Test Results

90/90 tests pass in `scripts/data/test_regime_filter.py`:

- [1] get_regime() structure: 29 tests (all required fields present)
- [2] tag_signal() mutation: 14 tests (in-place mutation, all keys, valid values)
- [2b] tag_signal() with regime=None: 2 tests
- [2c] tag_signal() unknown strategy: 2 tests (no blocking)
- [2d] tag_signal() confidence=0: 3 tests (unknown tags, no blocking)
- [3] Graceful degradation: 5 tests (empty dir, total failure, never raises)
- [4] Look-ahead-free: 6 tests (as_of truncation, VIX differs across dates)
- [5] Real data integration: 11 tests (VIX/SPY/breadth/components available)
- [6] Performance: 3 tests (<1s, <0.7s headroom, cache works)
- [7] Component functions: 9 tests
- [8] Strategy selector integration: 5 tests (end-to-end chain works)

## Verification Commands

1. `python3 test_regime_filter.py` -> 90 passed, 0 failed
2. `get_regime()` -> Regime: diversified | Confidence: 0.56
3. `get_strategy_directives()` -> 12 strategies

## Current Regime Output (2026-08-16)

```
Overall: diversified | Confidence: 0.56 | Freshness: stale
Stock: risk_on | Crypto: neutral
VIX: 14.25 (low) 5d: -4.4%
DXY: 99.67 (falling)
F&G: 34 (Fear)
Breadth: 72.0% > 50MA (n=100)
SPY: uptrend (>50ma=True, >200ma=True)
Corr: diversified (SPY-BTC=0.0623, internal=0.0657)
10Y: 4.696% (caution)
VRP: 0.6 (RV20d=13.7)
```

The diversified override triggered because SPY-BTC correlation (0.0623) < 0.2 and stock internal correlation (0.0657) < 0.3 — indicating a stock-picking environment.

## Files Changed

- `scripts/data/regime_filter.py` — full rewrite (1040 lines)
- `scripts/data/test_regime_filter.py` — new test file (90 tests)

## Callers Verified Working

- `scripts/research/regime_strategy_selector.py` (get_regime_state + get_strategy_directives)
- `scripts/paper_trading/capture_signals.py` (get_regime + tag_signal)
- `scripts/research/compute_confluence.py` (get_regime)
- `scripts/research/regime_transition_detector.py` (get_regime)
