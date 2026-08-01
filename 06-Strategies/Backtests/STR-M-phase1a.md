---
type: backtest-result
strategy_id: STR-20260726-selling-climax-reversal
strategy_name: STR-M Selling Climax Reversal
phase: 1A
verdict: KILL
date: 2026-07-26
metrics:
  total_signals: 6
  signals_per_year: 1.1
  avg_r: -1.000
  win_rate: 0.0
  sub_periods_positive: 0
  exit_breakdown:
    stop: 6
data_limitations: "Daily bars, survivorship bias, 529-ticker universe"
tags: [backtest-result, phase1a, killed, selling-climax, reversal]
---

# Backtest Result: STR-M Phase 1A

## Summary

| Metric | Value |
|--------|-------|
| Total signals | 6 |
| Signals/year | 1.1 |
| Average R | -1.000 |
| Win rate | 0.0% |
| Sub-periods positive | 0/3 |
| Classification | ❌ KILL |

## Phase 1B Perturbation Results

| Variant | Sigs | Avg R | Win% | SP+ | Notes |
|---------|------|-------|------|-----|-------|
| Baseline (reversal-day low stop) | 6 | -1.000 | 0.0% | 0/3 | 100% stopped out |
| V2: ATR stop 1.5x | 6 | -1.000 | 0.0% | 0/3 | ATR stop didn't help |
| V3: ATR stop 2x + 2:1 RR | 6 | -1.000 | 0.0% | 0/3 | Still 100% stopped |
| V4: Vol 1.5x + ATR 2x + 2:1 | 24 | -0.429 | 33.3% | 0/3 | More signals, still negative |
| V5: 2-day decline + ATR 2x + 2:1 | 6 | -1.000 | 0.0% | 0/3 | Same as baseline |
| V6: Vol 1.5x + 2-day + ATR 2x + 2:1 | 33 | -0.212 | 42.4% | 2/3 | Best variant, still negative |

## Failure Analysis

The selling climax reversal concept does not work as a mechanical scanner:
1. **Reversal day low is too tight as a stop** — 100% of signals hit the stop in baseline
2. **ATR-based stop doesn't fix it** — widening the stop to 1.5x or 2x ATR still results in -1.000 avg R (all stopped)
3. **Loosening all filters** (V6) generates more signals (33) but still net negative
4. **Zero target hits** across all variants — the 3:1 and 2:1 targets are never reached

The fundamental problem: buying a reversal after a multi-day decline in high-volatility conditions produces continued downside rather than a bounce. The selling climax pattern may work in specific index-level contexts (N162 describes market-wide capitulation) but not as a per-stock scanner.

## Related

- [[STR-20260726-selling-climax-reversal|STR-M Strategy]]
- [[REGIME-high-volatility]]
- [[Discoveries-2026-W32-high-vol]]
- [[ADR-004-Phase1-Validation-Framework]]