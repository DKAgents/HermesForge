# US-116: Register All LIVE Strategies in Regime Strategy Selector

**Date:** 2026-08-16
**Task:** US-116 follow-up — add missing LIVE strategies to STRATEGY_REGISTRY
**File:** `scripts/research/regime_strategy_selector.py`

## Problem

The `STRATEGY_REGISTRY` dict in `regime_strategy_selector.py` only contained 12 old strategies (STR-A through STR-H, STR-L, STR-P, STR-VIXC). The 17 new LIVE strategies from US-114/US-115 (STR-Q, STR-R, STR-T through STR-AJ) were missing, so the regime selector could not generate directives for them.

## Changes

### Added 17 new LIVE strategy entries

Each entry includes: name, asset type, status, regime_best, regime_avoid, base_risk, and type.

| Strategy | Name | regime_best | regime_avoid | type |
|----------|------|-------------|--------------|------|
| STR-Q | Liquidity Sweep Reversal | [all] | [] | reversal |
| STR-R | Williams Alligator Trend | [risk_on, neutral] | [risk_off] | trend_following |
| STR-T | Head & Shoulders Reversal | [neutral, caution] | [risk_on] | reversal |
| STR-U | Double Top/Bottom | [neutral, caution] | [risk_on] | reversal |
| STR-V | Triangle Breakout | [risk_on, neutral] | [risk_off] | breakout |
| STR-W | Flags & Pennants | [risk_on, neutral] | [risk_off] | breakout |
| STR-X | Parabolic SAR | [risk_on, neutral] | [risk_off] | trend_following |
| STR-Y | ADX/DMI Directional | [risk_on, neutral] | [risk_off] | trend_following |
| STR-Z | Stochastic Oscillator | [neutral, diversified] | [risk_on] | mean_reversion |
| STR-AA | Williams %R | [neutral, diversified] | [risk_on] | mean_reversion |
| STR-AB | OBV Divergence | [neutral, caution] | [risk_on] | divergence |
| STR-AC | CCI Oscillator | [neutral, diversified] | [risk_on] | mean_reversion |
| STR-AD | Keltner Channel | [risk_on, neutral] | [risk_off] | breakout |
| STR-AE | 4-Week Rule (Donchian) | [risk_on, neutral] | [risk_off] | breakout |
| STR-AF | Candlestick Reversal | [neutral, diversified, caution] | [] | reversal |
| STR-AG | Wedge Breakout | [neutral, caution] | [risk_on] | reversal |
| STR-AJ | Intermarket Rotation | [risk_on, neutral] | [risk_off] | macro |

### Updated existing entry

- **STR-H**: status changed from `WATCH` to `KILLED` to match `strategy_status.py` (STR-H was killed in US-114).

### Verified existing entries

- **STR-B**: regime_best includes `diversified` — confirmed correct.
- **STR-I**: status `LIVE`, regime_best `[risk_on, neutral]` — confirmed correct.

### Import verification

- `get_regime_state()` calls `from regime_filter import get_regime` — works correctly. Regime filter returns `overall: diversified`, `VIX: 14.2`, `F&G: 34.0`.

## Test Results

```
Registry: 29 total (19 LIVE, 3 WATCH, 7 KILLED)
Directives: 29 strategies
Active (non-skip): 22
Skipped: 7 (all KILLED)
Posture: normal
```

Current regime (diversified) correctly boosts oscillator/divergence strategies:
- STR-B, STR-Z, STR-AA, STR-AC, STR-AF: boosted (risk=1.8) — diversified correlation boost applies
- STR-Q, STR-T, STR-U, STR-AB, STR-AG: run at risk=1.2 — reversal/divergence types get diversified boost

## Type Assignments

Type field drives the directive logic (VIX adjustments, correlation adjustments, breadth adjustments):
- `trend_following`: STR-R, STR-X, STR-Y (reduce at VIX>30)
- `breakout`: STR-V, STR-W, STR-AD, STR-AE (VRP + breadth adjustments)
- `reversal`: STR-Q, STR-T, STR-U, STR-AF, STR-AG (diversified correlation boost)
- `mean_reversion`: STR-Z, STR-AA, STR-AC (VIX>30 boost, oversold breadth boost)
- `divergence`: STR-AB (diversified correlation boost)
- `macro`: STR-AJ (no special type-based adjustments, regime-based only)

## Commit

`3c65e5b` — US-116: Register all 19 LIVE strategies in regime_strategy_selector
