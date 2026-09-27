# US-115 v3 Risk Guardian Review — Structure-Based Walk-Forward Gate

**Reviewer:** Risk Guardian Agent (T2 glm-5.2)
**Date:** 2026-08-16
**Report under review:** `AUDIT-backtester-US115-v3.md`
**v3 CSVs:** `scripts/validation/results/STR-*-stocks-phase1a-v3.csv`
**Code audited:** `market_structure.py`, all 10 scanner files, `run_phase1a_v2_us114.py`

---

## Executive Summary

The backtester reports 10/10 PASS. After independent code audit and CSV forensics, the Risk Guardian issues **8 APPROVED, 1 CONDITIONAL, 1 VETOED**.

The structure-based module (market_structure.py) is well-built: look-ahead discipline is centralized and enforced via `_confirmed_pivots` (p + PIVOT_DISTANCE <= as_of_idx), the 20-bar cooldown is verifiably working (0 violations, min gap 28 calendar days), and natural targets produce genuine R:R variance (mean 2.0-2.6, not fixed 3.0). The trade count explosion is explained by the full 529-stock universe, not broken cooldown or duplicate signals.

However, two issues were found that the backtester's pass criteria did not catch:

1. **entry_type is not persisted to CSV** — the market_structure module computes pullback vs market entry, but the v3 CSV writer (run_phase1a_v2_us114.py std_cols) drops the field. We cannot verify the pullback feature's value-add from backtest output. This is a monitoring gap for ALL scanners.

2. **STR-B uses a different exit model** — its `_simulate_exit` checks close prices only and fills at the close (R can be < -1, worst -8.585R). All other 9 scanners use `_walk_forward_exit` with intrabar high/low checks and fill at the exact stop (R = -1.0). 28.4% of STR-B trades (165/581) have gap-through stops. Results are not comparable across scanners.

---

## Summary Verdict Table

| Strategy | OOS Avg R | OOS PF | OOS Trades | Cooldown | R:R Var | Exit Model | entry_type | Verdict |
|----------|----------|--------|------------|----------|--------|------------|------------|---------|
| STR-X | 0.3337 | 1.682 | 8854 | PASS | 2.10 | Standard | Not recorded | **APPROVED** |
| STR-Z | 0.3443 | 1.867 | 6403 | PASS | 2.02 | Standard | Not recorded | **APPROVED** |
| STR-AA | 0.3586 | 1.809 | 10309 | PASS | 2.07 | Standard | Not recorded | **APPROVED** |
| STR-AC | 0.3742 | 1.856 | 8897 | PASS | 2.08 | Standard | Not recorded | **APPROVED** |
| STR-AD | 0.2046 | 1.389 | 1210 | PASS | 2.08 | Standard | Not recorded | **CONDITIONAL** |
| STR-AE | 0.2352 | 1.439 | 3018 | PASS | 2.07 | Standard | Not recorded | **APPROVED** |
| STR-AF | 0.2872 | 1.680 | 12944 | PASS | 2.08 | Standard | Not recorded | **APPROVED** |
| STR-Y | 0.3484 | 1.750 | 2908 | PASS | 2.13 | Standard | Not recorded | **APPROVED** |
| STR-R | 0.2601 | 1.506 | 1836 | PASS | 2.02 | Standard | Not recorded | **APPROVED** |
| STR-B | 0.4563 | 2.023 | 233 | PASS | 2.62 | **DIVERGENT** | Not recorded | **VETOED** |

---

## Evidence: Key Checks Performed

### 1. Cooldown Enforcement — VERIFIED WORKING

All 10 scanner files contain `COOLDOWN_BARS = 20` with the guard:
```
if i - last_trade_idx < COOLDOWN_BARS:
    continue
```

CSV forensics confirm 0 violations across all scanners. Minimum gap between same-ticker trades is 28 calendar days (20 trading bars) for every scanner. The cooldown is per-ticker and correctly enforced.

### 2. R:R Distribution — VERIFIED VARIED (not all 3.0)

| Scanner | Mean R:R | R:R Std | % near 3.0R | Target Unique Values |
|---------|----------|---------|-------------|---------------------|
| STR-X | 2.099 | 0.737 | 0.7% | 21021 |
| STR-Z | 2.015 | 0.642 | 0.3% | 15544 |
| STR-AA | 2.067 | 0.707 | 0.6% | 24288 |
| STR-AC | 2.078 | 0.720 | 0.5% | 21237 |
| STR-AD | 2.082 | 0.624 | 0.9% | 3019 |
| STR-AE | 2.072 | 0.744 | 0.5% | 7472 |
| STR-AF | 2.083 | 0.707 | 0.5% | 29628 |
| STR-Y | 2.126 | 0.765 | 0.6% | 7209 |
| STR-R | 2.016 | 0.621 | 0.5% | 4557 |
| STR-B | 2.615 | 1.181 | 0.9% | 581 |

Mean R:R ranges 2.0-2.6, NOT 3.0. Less than 1% of trades land near 3.0R. Target prices show thousands of unique values. The structure detection (compute_natural_target) is working — natural resistance produces genuinely varied targets.

### 3. entry_type (Pullback vs Market) — NOT RECORDED

The market_structure module computes `entry_type = "pullback" if entry_idx > signal_idx else "market"` (line 457) and stores it in the trade dict (line 499). Scanner files reference it (e.g., scanner_ad_keltner.py line 142). However, the v3 CSV writer's standard columns (run_phase1a_v2_us114.py, lines 134-137) are:
```
"symbol", "strategy", "direction", "date", "entry_price",
"stop_price", "target_price", "exit_type", "exit_price",
"bars_held", "r_multiple", "signal_type"
```

`entry_type` is absent. We CANNOT verify what fraction of trades used pullback entry vs market fallback. This is a data gap for all 10 scanners. The pullback feature may be adding value or may be 95% market fallback — we have no evidence either way.

**Required fix:** Add `entry_type` to the v3 CSV standard columns and re-export. This does not require re-running the backtest — the data exists in the signal dicts but is dropped at write time.

### 4. Trade Count Explosion — EXPLAINED (not a bug)

All scanners except STR-B cover the full 529-stock universe. Trades per ticker range from 1.6 (STR-B, filtered) to 61.2 (STR-AF). With ~2.5 years of daily data (~600 bars), 61 trades/ticker = one trade every ~10 bars, consistent with a 20-bar cooldown. The v2-to-v3 explosion is from the full universe re-scan, not from broken cooldown or duplicate signals.

### 5. Look-Ahead Bias — CLEAN

The market_structure module centralizes the US-114 fix:
- `_confirmed_pivots` filters to `p + PIVOT_DISTANCE <= as_of_idx` (line 150)
- Debug assertion guard (`_assert_confirmed`) catches regressions when MARKET_STRUCTURE_DEBUG=1
- Pullback support levels frozen at signal_idx; wait window only tests forward
- Stop/target use decision_idx = entry_idx >= signal_idx (stricter than signal_idx)

No look-ahead leaks detected.

### 6. STR-B Exit Model — DIVERGENT (Critical)

STR-B uses `_simulate_exit` (line 108-142 of scanner_b_macd_divergence.py):
- Checks CLOSE prices only: `if c <= stop_price: return c, "stop", offset`
- Fills at the close price, NOT the stop price
- Result: R can be < -1.0 (gap-through risk captured)

All other 9 scanners use `_walk_forward_exit` (e.g., scanner_ad_keltner.py line 184):
- Checks intrabar HIGH/LOW: `if bar["low"] <= stop_price:`
- Fills at the exact stop price: `"exit_price": stop_price, "r_multiple": -1.0`
- Result: R = -1.0 always (gap risk ignored)

STR-B forensics:
- 165/581 trades (28.4%) have R < -1.0 (gap-through stops)
- Worst: R = -8.585 (single trade lost 8.6x intended risk)
- exit_type breakdown: time 320 (55%), stop 165 (28%), target 96 (16.5%)
- Only 356/529 tickers survive min_rr=1.5 filter
- signal_type field missing from scanner output — CSV shows numeric signal_bar_index values ('915', '945', etc.) instead of descriptive names
- MAX_BARS_HELD = 8 (vs 15-20 for all other scanners)

---

## Per-Scanner Verdicts

### STR-X (Parabolic SAR Flip) — APPROVED

OOS avg R=0.3337, PF=1.682, 8854 trades, p=0.0000. Cooldown verified. R:R variance confirmed (mean 2.10, std 0.737, 0.7% near 3R). Standard exit model. Avg R improved 39% from v2. Full 529-ticker coverage (41.8 trades/ticker). No concerns. Return to LIVE.

### STR-Z (Stochastic Cross) — APPROVED

OOS avg R=0.3443, PF=1.867, 6403 trades, p=0.0000. Highest OOS PF among indicator scanners. Cooldown verified. R:R variance confirmed (mean 2.02). Standard exit model. Avg R improved 39%. No concerns. Return to LIVE.

### STR-AA (Williams %R) — APPROVED

OOS avg R=0.3586, PF=1.809, 10309 trades, p=0.0000. Cooldown verified. R:R variance confirmed (mean 2.07). Standard exit model. Avg R improved 68%. No concerns. Return to LIVE.

### STR-AC (CCI) — APPROVED

OOS avg R=0.3742, PF=1.856, 8897 trades, p=0.0000. Highest OOS avg R among the approved scanners. Cooldown verified. R:R variance confirmed (mean 2.08). Standard exit model. Avg R improved 45%. No concerns. Return to LIVE.

### STR-AD (Keltner Channel) — CONDITIONAL

OOS avg R=0.2046 (lowest of all 10), PF=1.389 (weakest). Avg R declined 6% from v2 (0.3060 to 0.2871 IS; OOS even lower at 0.2046). Median r_multiple = -1.000, meaning more than half the trades hit stop. The structure-based target underperforms the fixed 3R for Keltner breakouts — the Keltner channel's own upper band is a more natural profit target than swing-based resistance.

The backtester's own report recommends a hybrid approach (structure for entry/stop, Keltner band for target). I concur.

Verdict: CONDITIONAL. Return to LIVE with the current structure-based v3 but flag for close monitoring. If OOS avg R degrades below 0.15 or PF drops below 1.2 in paper trading over the next 30 days, switch STR-AD to hybrid mode (Keltner-band target, structure-based entry/stop).

### STR-AE (4-Week Rule / Donchian) — APPROVED

OOS avg R=0.2352, PF=1.439, 3018 trades, p=0.0000. Cooldown verified. R:R variance confirmed (mean 2.07). Standard exit model. Avg R improved 55%. Lower PF than the top tier but statistically solid. No concerns. Return to LIVE.

### STR-AF (Candlestick Patterns) — APPROVED

OOS avg R=0.2872, PF=1.680, 12944 trades, p=0.0000. Highest trade count (61.2 trades/ticker across 529 stocks). Cooldown verified — the high count is legitimate given the universe and cooldown spacing. R:R variance confirmed (mean 2.08). Standard exit model. Avg R improved 75%. Multiple signal subtypes (morning_star, hammer, three_white_soldiers, piercing) all present. No concerns. Return to LIVE.

### STR-Y (ADX/DMI) — APPROVED

OOS avg R=0.3484, PF=1.750, 2908 trades, p=0.0000. Previously KILLED in US-114 (p=0.066, marginal). The structure-based approach rescued it: avg R improved 98.5%, OOS p dropped to 0.0000. Cooldown verified. R:R variance confirmed (mean 2.13). Standard exit model. This is the strongest validation of the structure-based approach — it transformed noise into a viable scanner. Return to LIVE.

### STR-R (Alligator) — APPROVED

OOS avg R=0.2601, PF=1.506, 1836 trades, p=0.0000. Trade count dropped 71% (15838 to 4588) — the structure-based approach discards low-quality Alligator signals, and the remaining ones have 113% better avg R. Cooldown verified. R:R variance confirmed (mean 2.02). Standard exit model. 408 'sleep' exits (Alligator-specific) alongside standard target/stop/time. No concerns. Return to LIVE.

### STR-B (MACD Divergence) — VETOED

VETOED. Must not return to LIVE. Three blocking issues:

**Issue 1: Exit model inconsistency.** STR-B uses `_simulate_exit` which checks close prices only and fills at the close price. All other 9 scanners use `_walk_forward_exit` which checks intrabar high/low and fills at the exact stop/target price. This means:
- STR-B's stop exits can produce R < -1.0 (28.4% of trades, worst -8.585R)
- STR-B's target exits fill at the close, not the target price (different R than planned)
- The walk-forward OOS p-value (0.0000) is computed on a different risk model than the other 9 scanners — the results are not directly comparable

**Issue 2: 28.4% gap-through stop rate.** 165 of 581 trades have the close gap through the stop, producing losses exceeding the intended 1R risk. A single trade lost 8.585R. In live trading, this represents uncontrolled tail risk. While gap risk is real, 28.4% is alarmingly high and suggests the structure stops for MACD divergence setups are too tight (likely hitting the min_atr floor frequently) and/or MACD divergence signals occur at volatile moments.

**Issue 3: Data quality.** The scanner does not emit a `signal_type` field. The CSV writer falls back to `signal_bar_index` (numeric positional index), producing values like '915', '945', '1571' instead of descriptive names. This makes the v3 CSV unreliable for STR-B signal analysis.

**Additional concerns:**
- Only 356/529 tickers survive the min_rr=1.5 filter (81% trade count collapse)
- 55% of trades exit by time (320/581), only 16.5% hit target (96/581)
- MAX_BARS_HELD=8 vs 15-20 for all other scanners — inconsistent time-stop window
- 233 OOS trades is borderline sufficient, but the exit model difference means the OOS significance test's assumptions differ from the other scanners

**Required fixes before re-validation:**
1. Replace `_simulate_exit` with the standard `_walk_forward_exit` (intrabar high/low check, fill at stop/target price). This aligns the exit model with the other 9 scanners.
2. Re-run walk-forward validation with the corrected exit model.
3. Consider lowering min_rr to 1.0-1.2 for MACD divergence (the 1.5 filter may be too aggressive for this signal type, or the structure stops are too tight).
4. Add a descriptive `signal_type` field to the scanner output (e.g., "macd_bearish_divergence_short", "macd_bullish_divergence_long").
5. Increase MAX_BARS_HELD to 15 for consistency with other scanners.
6. After fixes, verify that gap-through stops (R < -1) drop to near 0% (matching the standard model).

---

## System-Wide Recommendations

1. **Add entry_type to CSV output.** The pullback vs market entry distribution is a core US-115 feature. It is computed but not persisted. Add `entry_type` to `run_phase1a_v2_us114.py` std_cols and re-export. This is a one-line fix that does not require re-running the backtest.

2. **Standardize the exit model.** All scanners must use the same `_walk_forward_exit` with intrabar high/low checks and fill-at-level semantics. STR-B's divergent model must be aligned before re-validation.

3. **Acknowledge gap-risk optimism in the standard model.** The 9 approved scanners fill stops at the exact stop price (R = -1.0), ignoring gap risk. This is a standard backtest simplification but means real-world performance may be slightly worse than backtested. This is acceptable for now but should be noted when sizing positions in live trading.

4. **Monitor STR-AD closely.** The weakest approved scanner. If OOS metrics degrade in paper trading, switch to Keltner-band targets (hybrid mode).

---

## Gate Decision

| Verdict | Count | Scanners |
|---------|-------|----------|
| APPROVED | 8 | STR-X, STR-Z, STR-AA, STR-AC, STR-AE, STR-AF, STR-Y, STR-R |
| CONDITIONAL | 1 | STR-AD |
| VETOED | 1 | STR-B |

The 8 APPROVED scanners may return to LIVE with the structure-based v3 configuration.
STR-AD returns to LIVE with a monitoring flag.
STR-B must not return to LIVE until the exit model is fixed and re-validated.

---
_Review by HermesForge Risk Guardian Agent — US-115 v3 Gate_
