# US-115: STR-AD Hybrid — Structure Entry/Stop, Channel-Measured-Move Target

**Date:** 2026-08-16
**Scanner:** STR-AD (Keltner Channel Breakout)
**File:** `scripts/validation/scanners/scanner_ad_keltner.py`
**Version:** 2.0 → 2.1
**Commit:** 9d07309

## Problem

STR-AD v2.0 replaced the original fixed-parameter target with
`compute_structure_trade`'s swing-high detection. For the Keltner scanner this
hurt avg R by ~6%: the Keltner channel *is* the natural structure for this
scanner — the upper band is volatility-adjusted resistance, the lower band is
support. Swing-high detection picks closer targets (e.g. a minor swing high at
1.6R) when the channel's volatility expansion would carry further.

## Fix (Option B — Hybrid)

Keep what works from `compute_structure_trade` and override only the target:

| Component | Source | Rationale |
|-----------|--------|-----------|
| Entry     | `compute_structure_trade` (pullback to support) | Fill quality — working well |
| Stop      | `compute_structure_trade` (swing low, ATR-buffered) | Risk definition — working well |
| **Target**| **Channel measured-move** (NEW) | Channel width projected from breakout band |

### Target formula

```
channel_width = upper_band[signal_idx] - lower_band[signal_idx]

LONG :  target = upper_band + channel_width   = 2 * upper - lower
SHORT:  target = lower_band - channel_width   = 2 * lower - upper
```

This is a classic measured-move projection: the channel's own volatility
(2 × ATR(10) on each side) defines how far the breakout leg is expected to
travel.

### Recalculation

After overriding the target, `rr` is recomputed from the structure entry/stop
and the new target. If the channel-measured-move R < 1.5 (min_rr), the signal is
skipped — same filter as before, now applied to the hybrid target.

## Changes Applied

1. Docstring updated — explains hybrid approach and why the channel is the
   structure for this scanner.
2. `STRATEGY_VERSION` bumped to `2.1`.
3. LONG block: after `compute_structure_trade` returns, `target_price` is
   overridden with `upper + (upper - lower)`; `risk` and `rr` recomputed; skip
   if `rr < 1.5`.
4. SHORT block: same pattern with `lower - (upper - lower)`.
5. Both signal dicts now also store `kc_lower` (long) / `kc_upper` (short) for
   full auditability of the channel state at signal time.

## Verification

### Import test
```
cd scripts/validation/scanners && python -c 'import scanner_ad_keltner; print("import OK")'
→ import OK
```

### SPY backtest (quick)
```
SPY signals: 10
Version: 2.1
Channel-target mismatches: 0/10   ← all targets verified = 2*upper - lower

Backtest: 10 trades
Win rate: 60.0%
Avg R: 1.295
Sum R: 12.946
By exit:
  target: 3 trades, avg R=3.550
  stop:   4 trades, avg R=-1.000
  time:   3 trades, avg R=2.098
```

All 10 signals confirmed to use channel-measured-move targets (0 mismatches
against `2 * upper - lower`). The three target exits average 3.55R — consistent
with the wider channel-based targets capturing volatility expansion.

## Key Insight

The Keltner channel IS the structure for this scanner. The pullback entry and
structure stop improve fill quality and risk definition, but the target should
be based on the channel's volatility expansion, not arbitrary swing highs.
v2.0's mistake was treating "structure" as monolithic — the channel that
*generates* the signal is a better structural target than a generic swing-high
search, because it already encodes the volatility regime the breakout is
trading.
