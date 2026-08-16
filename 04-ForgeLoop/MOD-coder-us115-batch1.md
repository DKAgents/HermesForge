# US-115 Phase 2 — Coder Batch 1: market_structure Module Integration

**Coder:** Coder agent (T2, glm-5.2)
**Date:** 2026-08-16
**Status:** COMPLETE — 4 scanners modified, verified, committed
**Design doc:** `~/HermesForge/04-ForgeLoop/DESIGN-architect-US115-market-structure.md` (§3 Scanner Integration Plan)
**Module:** `~/HermesForge/scripts/validation/scanners/market_structure.py` (21 tests pass, unchanged this batch)

---

## 1. Scope

Batch 1 of 3. Modified 4 SWITCH scanners to derive entry/stop/target from the
shared `market_structure.compute_structure_trade` orchestrator instead of
fixed-ATR stops and a fixed 3R target:

| Scanner | File | v1.x logic | v2.0 |
|---------|------|-----------|------|
| STR-X | scanner_x_parabolic_sar.py | entry=close[i], stop=SAR value, target=3R | structure-based |
| STR-Z | scanner_z_stochastic.py | entry=close[i], stop=1.5 ATR, target=3R | structure-based |
| STR-AA | scanner_aa_williams_r.py | entry=close[i], stop=1.5 ATR, target=3R | structure-based |
| STR-AC | scanner_ac_cci.py | entry=close[i], stop=1.5 ATR, target=3R | structure-based |

---

## 2. STR-W Classification Finding (requested inspection)

**scanner_w_flags_pennants.py (STR-W) → KEEP (do not modify).**

STR-W derives its target from **pattern geometry (mast/pole height)**, not a
fixed R multiple:
```python
# long:  target = entry + mast_h   (mast_h = close[mast_end] - close[mast_start])
# short: target = entry - mast_h
```
`mast_h` is the measured height of the impulsive move projected from the
consolidation breakout — pattern-derived, matching the KEEP rationale in the
design doc §3.1 (T/U/V/AG derive target from pattern geometry/neckline/wedge
height). Additionally, STR-W already computes target-exit R dynamically
(`r_multiple: None` in `_walk_forward_exit`, recomputed from prices in
`run_backtest`) — the exact pattern this batch applies to the SWITCH scanners.

Conclusion: STR-W stays in KEEP. Its stop (currently `lower - 1 ATR`) could be
routed through `compute_structure_stop` under a future US, but its pattern
target must be preserved. Batches 2/3 should NOT include STR-W.

---

## 3. Changes Applied (per design doc §3.2, all 8 required)

For each of the 4 scanners:

1. **Import** — added `from market_structure import compute_structure_trade`
   with a `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`
   sibling-import guard (per §3.2 note #5) so imports work regardless of CWD.
2. **Entry/stop/target block** — replaced the fixed `entry=close[i]` /
   `stop=ATR_MULT*atr` / `target=risk*TARGET_RR` block (both long and short)
   with a single `compute_structure_trade(df, signal_idx=i, direction=...,
   max_wait_bars=5, min_rr=1.5, max_atr=2.0, atr=atr, entry_fallback="signal")`
   call. `atr=atr` reuses each scanner's already-computed Wilder ATR series.
   `trade is None → continue` (skip signals with no valid structure target).
3. **entry_idx propagated** — new `entry_idx` and `entry_date` fields in every
   signal dict. `entry_date = df.index[trade["entry_idx"]]` (actual fill bar;
   may be > signal bar for pullback fills).
4. **run_backtest() exit-walk start** — now uses `sig.get("entry_idx")` to
   start the exit walk; falls back to `df.index.get_loc(sig["date"])` for
   legacy v1.x signals (no entry_idx). Slice/array index guards retained.
5. **Dynamic target R** — `_walk_forward_exit` no longer hardcodes
   `r_multiple: TARGET_RR` on target hits. R is computed from actual prices:
   `risk = entry-stop` (signed by direction); `gain = target-entry` (or
   `entry-target` short); `r_mult = round(gain/risk, 3)`. Stop exits remain
   -1.0R; time exits already used the dynamic formula (unchanged).
6. **Version bump** — `STRATEGY_VERSION = "2.0"`; docstrings updated to
   describe structure-based entry/stop/target and note the v1.x behaviour.
7. **20-bar per-ticker cooldown** — added `COOLDOWN_BARS = 20` and a
   `cooldown_until` guard inside each direction's signal block. After a
   signal is accepted (compute_structure_trade returns non-None) at bar i,
   `cooldown_until = i + COOLDOWN_BARS`; subsequent signals on that ticker
   are skipped while `i < cooldown_until`. Prevents the overlap risk
   magnified by pullback entries (design §5.4).
8. **Constants removed** — `TARGET_RR` and `STOP_ATR_MULT` deleted (no longer
   referenced). Indicator/signal constants (K_PERIOD, WR_PERIOD, CCI_PERIOD,
   AF_*, OVERSOLD/OVERBOUGHT, signal_type strings) and indicator computation
   functions are unchanged — the trigger logic is untouched.

Signal dicts now also carry `risk`, `rr`, and `entry_type` ("pullback"|"market")
from the orchestrator; scanner-specific diagnostic fields (psar, pct_k/pct_d,
williams_r, cci) are preserved.

---

## 4. Verification

### 4.1 Import check
```
cd ~/HermesForge/scripts/validation/scanners && python3 -c \
  'import scanner_x_parabolic_sar; import scanner_z_stochastic; \
   import scanner_aa_williams_r; import scanner_ac_cci; print("All 4 import OK")'
→ All 4 import OK
```

### 4.2 SPY backtest (tail-200/500/600, long_only=True)

| Scanner | signals | first entry_type | first rr | ver | backtest trades | avg R | target exits | target-R variance |
|---------|---------|------------------|----------|-----|-----------------|-------|--------------|-------------------|
| STR-X   | 5 (200) | pullback         | 2.698    | 2.0 | 36              | 0.474 | 12           | 0.364             |
| STR-Z   | 3 (500) | pullback         | 1.601    | 2.0 | 24              | 0.362 | 6            | 0.172             |
| STR-AA  | 10 (500)| market           | 1.526    | 2.0 | 40              | 0.165 | 12           | 0.161             |
| STR-AC  | 8 (500) | market           | 1.526    | 2.0 | 34              | 0.256 | 12           | 0.428             |

- All signals carry `entry_idx`, `entry_date`, `entry_type`, `risk`, `rr`,
  `strategy_version="2.0"` (I1/I3 pass).
- Target-exit R-multiples show **variance** (0.16–0.43), not a constant 3.0 —
  confirms the hardcoded-R bug is fixed (I2 pass: no target exit equals the
  old TARGET_RR; distribution has variance).
- Pullback entries observed (STR-X, STR-Z first signals: entry_date =
  signal_date + 1) — the wait-window limit fill is exercised.

### 4.3 Module test suite (regression)
```
cd ~/HermesForge/scripts/validation/scanners && python3 test_market_structure.py
→ Ran 21 tests in 0.987s  OK
```
Module untouched this batch; all 21 tests (T1–T15, L1–L3, P1–P3) still pass.

### 4.4 Leftover-constant check
`grep TARGET_RR|STOP_ATR_MULT` across the 4 modified scanners returns zero
code references (one docstring mention in STR-X describing the change).

---

## 5. Commit

```
git add -A && git commit -m 'US-115: Modify STR-X, Z, AA, AC to use market_structure module'
→ [main c94756b] 8 files changed, 628 insertions(+), 321 deletions(-)
```

### IMPORTANT — commit contents note for the user/architect

The `git add -A` (as specified in the task) also swept in 4 scanners that had
**pre-existing uncommitted modifications in the working tree from a prior
session**: scanner_ad_keltner.py (STR-AD), scanner_ae_4week_rule.py (STR-AE),
scanner_af_candlestick.py (STR-AF), scanner_r_alligator.py (STR-R). These are
the batch-2 SWITCH scanners and were already fully converted to v2.0
(compute_structure_trade import, version 2.0, COOLDOWN_BARS=20, dynamic R,
no TARGET_RR/STOP_ATR_MULT). I verified they import and produce valid v2.0
signals with entry_idx on SPY:

| Scanner | signals | v2.0 + entry_idx |
|---------|---------|------------------|
| STR-AD  | 2       | True             |
| STR-AE  | 5       | True             |
| STR-AF  | 16      | True             |
| STR-R   | 3       | True             |

They are on-spec and not broken, so the commit is clean. However the commit
message names only "STR-X, Z, AA, AC" while the commit actually contains 8
scanners (batch 1 + the pre-existing batch-2 conversions). This satisfies the
"no uncommitted changes left in the working tree" hard rule, but the message
is slightly narrower than the contents. Options for the user:
  (a) Leave as-is (batch-2 work is committed and verified; message is a minor
      inaccuracy).
  (b) Amend the commit message to: "US-115: Modify STR-X, Z, AA, AC, AD, AE,
      AF, R to use market_structure module" for accurate auditability.
I did not amend because the task specified the exact message; flagging for the
user's decision. Batch 2/3 work for AD/AE/AF/R is now committed and should not
be redone.

---

## 6. Notes for the Risk-Guardian / Architect

- **Trade-count reduction expected** (design §5.5): v2.0 filters trades with
  no valid structure target (min_rr=1.5) and replaces signal-close entries
  with pullback entries. Expect 20–50% fewer trades vs v1.x. The
  risk-guardian should compare v1.x vs v2.x on win-rate, avg R, profit
  factor, AND trade count — a sharp drop with flat avg R is a yellow flag.
- **Dynamic R distribution**: target-exit R now ranges (e.g. STR-X 0.36
  variance), so v1.x summary assumptions that target == 3R no longer hold.
  `_print_summary` aggregates `r_multiple` generically — no change needed.
- **Hold-time semantics**: bars-in-trade counted from `entry_idx + 1` (the
  pullback fill), not the signal bar. Total trade duration may lengthen by
  up to max_wait_bars. Realistic (you're not "in" during the wait).
- **Cooldown = 20 bars from the signal bar** of the last accepted signal.
  Simpler than the design's "until exit resolved" variant; sufficient to
  suppress overlap given MAX_HOLD_BARS <= 20.
- **STR-W stays KEEP** (pattern-derived mast-height target + already-dynamic
  R). Batches 2/3 must not include STR-W. Its stop could be routed through
  compute_structure_stop in a future US.

---

## 7. Remaining Work

- **Batch 2/3**: AD, AE, AF, R are ALREADY converted and committed (see §5).
  Remaining un-converted SWITCH scanners to verify/complete: STR-Y (ADX/DMI)
  and STR-B (MACD divergence) — confirm their state in the next batch.
- **KEEP scanners (T, U, V, AG, W)**: untouched, as required.
- **Acceptance gate** (design §7.5): 7.4 integration tests I1–I3 pass for the
  4 batch-1 scanners (smoke, no-hardcoded-R, entry_idx consistency). I4
  (v1.x vs v2.x CSV delta) and risk-guardian sign-off pending swarm review.
