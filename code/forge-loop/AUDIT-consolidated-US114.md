# US-114 Consolidated Audit — Three-Agent Swarm Verdict

**Date:** 2026-08-16
**Agents:** Architect (T2), Risk Guardian (T2 hard floor), Backtester (T3)
**Scope:** 19 strategy scanners built without swarm oversight

---

## Consolidated Verdict

| Strategy | Architect | Risk Guardian | Backtester | **FINAL** | Block Reason |
|----------|-----------|---------------|------------|-----------|--------------|
| STR-X (PSAR) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-Z (Stochastic) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-AA (Williams %R) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-AC (CCI) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-AD (Keltner) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-AE (4-Week) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-AF (Candlestick) | PASS | CONDITIONAL | PASS | **✅ TRUSTED** | — |
| STR-AJ (Intermarket) | NEEDS-FIX | CONDITIONAL | PASS | **✅ TRUSTED*** | *Needs interface fix + concentration control |
| STR-V (Triangles) | FAIL | CONDITIONAL | PASS* | **❌ BLOCKED** | Look-ahead bias (find_peaks) — WF contaminated |
| STR-W (Flags) | NEEDS-FIX | VETO | PASS* | **❌ BLOCKED** | Look-ahead + 83% duplicate signals |
| STR-AB (OBV) | NEEDS-FIX | CONDITIONAL | PASS* | **❌ BLOCKED** | Look-ahead bias (1-bar) — WF contaminated |
| STR-AG (Wedge) | NEEDS-FIX | CONDITIONAL | PASS* | **❌ BLOCKED** | Look-ahead bias (find_peaks) — WF contaminated |
| STR-S (Elliott) | FAIL | VETO | FAIL | **❌ BLOCKED** | Look-ahead + veto + OOS negative |
| STR-T (H&S) | FAIL | CONDITIONAL | FAIL | **❌ BLOCKED** | Look-ahead + OOS degradation |
| STR-U (Double Top) | FAIL | CONDITIONAL | FAIL | **❌ BLOCKED** | Look-ahead + OOS not significant |
| STR-Y (ADX/DMI) | PASS | CONDITIONAL | FAIL | **❌ BLOCKED** | OOS not significant (p=0.066) |
| STR-AI (Seasonal) | PASS | CONDITIONAL | FAIL | **❌ BLOCKED** | OOS not significant (p=0.163) |
| STR-AH (Island) | PASS | VETO | FAIL | **❌ BLOCKED** | Vetoed — survivorship bias artifact |
| STR-R (Alligator) | NEEDS-FIX | VETO | FAIL | **❌ BLOCKED** | Vetoed — code bug corrupts R data |

**Totals:** 8 TRUSTED | 11 BLOCKED

---

## What the Swarm Caught

### 1. Look-Ahead Bias (Architect) — 7 scanners
`scipy.signal.find_peaks(distance=N)` requires N future bars to confirm a pivot. Scanners S, T, U, V, W, AB, AG enter 1-2 bars after unconfirmed pivots. This makes their backtests systematically optimistic. **4 of these 7 passed the walk-forward gate — but only because the look-ahead bias inflated both IS and OOS.** Their walk-forward PASS is contaminated and invalid.

**Fix:** Start entry search at `pivot_idx + PIVOT_DISTANCE` instead of `pivot_idx + 1`. Adopt STR-AE's `.shift(1)` pattern.

### 2. Data Corruption (Risk Guardian) — 2 scanners
- **STR-W:** 83% duplicate signals (13,876 of 16,644). Sliding window generates the same trade multiple times, inflating sum R by 8.7x.
- **STR-R:** 43 "sleep" exits hardcode `r_multiple=0` instead of actual R, corrupting 8.4% of trade data.

### 3. Survivorship Bias Artifact (Risk Guardian) — 1 scanner
- **STR-AH:** 84% of trades exit via time stop with 79.8% WR. The "edge" is just beta exposure to mega-cap survivors in a bull market, not a pattern-specific edge. PF 3.52 would collapse on a bias-free universe.

### 4. OOS Not Significant (Backtester) — 4 clean-code scanners
- **STR-Y:** p=0.066 (tantalizingly close)
- **STR-AI:** p=0.163 (seasonal instability)
- **STR-T, STR-U:** OOS degradation beyond thresholds

---

## The 8 Trusted Scanners

These passed all three gates: no look-ahead bias (architect), not vetoed (risk guardian), OOS profitable + significant (backtester).

| Strategy | OOS Trades | OOS Avg R | OOS PF | OOS p-value | OOS 95% CI |
|----------|-----------|-----------|--------|-------------|-----------|
| STR-V → ❌ | — | — | — | — | (look-ahead, contaminated) |
| STR-X (PSAR) | 643 | +0.265 | 1.625 | 0.0000 | [0.162, 0.367] |
| STR-Z (Stochastic) | 391 | +0.353 | 1.713 | 0.0000 | [0.199, 0.506] |
| STR-AA (Williams %R) | 867 | +0.247 | 1.476 | 0.0000 | [0.147, 0.346] |
| STR-AB → ❌ | — | — | — | — | (look-ahead, contaminated) |
| STR-AC (CCI) | 587 | +0.278 | 1.556 | 0.0000 | [0.158, 0.398] |
| STR-AD (Keltner) | 531 | +0.301 | 1.694 | 0.0000 | [0.187, 0.415] |
| STR-AE (4-Week) | 872 | +0.178 | 1.678 | 0.0000 | [0.119, 0.237] |
| STR-AF (Candlestick) | 2878 | +0.162 | 1.287 | 0.0000 | [0.112, 0.213] |
| STR-AG → ❌ | — | — | — | — | (look-ahead, contaminated) |
| STR-AJ (Intermarket) | 201 | +0.480 | 2.262 | 0.0000 | [0.288, 0.672] |

**Remaining conditions for all 8:**
1. Add survivorship bias disclosure constant to each scanner file
2. STR-AJ: fix interface (4th param) + add concentration risk control (limit positions per intermarket trigger)

---

## Remediation Plan

### Phase 1: Fix Look-Ahead Bias (7 scanners) → Re-backtest → Re-validate
Route through **coder** (T2) to fix, then **backtester** (T3) to re-run:
1. STR-S, STR-T, STR-U: Change entry search start to `pivot_idx + PIVOT_DISTANCE`
2. STR-V, STR-AG: Exclude unconfirmed pivots from trendline fit
3. STR-W: Fix duplicate signal generation + look-ahead
4. STR-AB: Start entry search at `p2_idx + SWING_WINDOW + 1`

### Phase 2: Fix Code Bugs (2 scanners)
5. STR-R: Fix `r_multiple=0` sleep exit bug, O(n²) recomputation, fragile date field
6. STR-W: Deduplicate signals (one per symbol/date/signal_type)

### Phase 3: Universal Fixes (all 19)
7. Rename `ticker` → `symbol` in all scan() return dicts
8. Add `SURVIVORSHIP_BIAS_DISCLAIMER` constant to all scanners
9. STR-AJ: Fix interface + add concentration risk control

### Phase 4: Re-validate Fixed Scanners
10. Re-run Phase 1A backtests on fixed scanners
11. Re-run walk-forward validation (backtester)
12. Final risk guardian review on re-validated scanners

---

## Key Lessons

1. **The swarm works.** Three independent agents caught issues a single agent missed: look-ahead bias (architect), data corruption (risk guardian), OOS failure (backtester). The 7 look-ahead scanners that "passed" walk-forward would have contaminated paper trading without the architect's code audit.

2. **find_peaks is dangerous.** `scipy.signal.find_peaks(distance=N)` is a look-ahead function by design — it needs N future bars to confirm a pivot. Any scanner using it for entry signals must delay entry by PIVOT_DISTANCE bars.

3. **In-sample backtests are necessary but not sufficient.** The backtester caught 7 overfit strategies. The architect then showed 4 of the 12 that "passed" had contaminated data from look-ahead bias.

4. **Walk-forward alone isn't enough.** The backtester passed STR-V, STR-W, STR-AB, STR-AG — all had look-ahead bias that inflated OOS results. Code audit must precede statistical validation.
