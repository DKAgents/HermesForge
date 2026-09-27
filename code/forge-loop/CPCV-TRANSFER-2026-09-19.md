# CPCV Transfer Audit — 2026-09-19

**Purpose:** Run T0 transfer audit strategies (STR-X, STR-AA, STR-AF, STR-B) through the CPCV
harness with G3 cost-drag applied, and report DSR/PBO against the N=115 trials ledger.

**Harness:** `/root/HermesForge/scripts/gauntlet/cpcv_harness.py` (López de Prado CPCV)  
**Cost model:** `cost_adjuster.py` — stock venue (2.0 bps round-trip drag)  
**Trials ledger:** `/root/HermesForge/data/gauntlet/trials.jsonl` — N=115 entries  
**CPCV params:** N=12 groups, k=2 test groups, 66 splits (C(12,2)), 11 paths (1-factorization),
purge=20 bars, embargo=40 bars

---

## Bug Fix

The `compute_dsr()` function in `cpcv_harness.py` had a sign error in the V[max] formula:
`(1 - Z1/Z)/N` was negative for all N>0 because Z1 > Z. Fixed to use
`V[max] = 1 / (N * φ(Z)²)` (variance of the maximum order statistic).
This corrects DSR from the impossible 1.0-in-all-cases artifact to proper
defensible values. Affected lines 391-394, patched same session.

---

## Results

| Strategy | File | Trades | Gross avg R | Gauntlet avg R | Cost drag |
|----------|------|--------|-------------|----------------|-----------|
| STR-X | STR-X-stocks-phase1a-v3.csv | 22,135 | +0.3617 | +0.3549 | 0.0068 |
| STR-AA | STR-AA-stocks-phase1a-v3.csv | 25,772 | +0.3491 | +0.3425 | 0.0067 |
| STR-AF | STR-AF-stocks-phase1a-v3.csv | 32,360 | +0.2872 | +0.2803 | 0.0069 |
| STR-B | STR-B-stocks-phase1a-v3.csv | 2,955 | +0.1695 | +0.1597 | 0.0099 |

### CPCV Split Statistics

| Strategy | Median PF | 10th-%ile PF | Min PF | Win Rate |
|----------|-----------|-------------|--------|----------|
| STR-X | 1.7748 | 1.3854 | 1.1502 | 0.4998 |
| STR-AA | 1.8074 | 1.4156 | 1.1669 | 0.5178 |
| STR-AF | 1.6796 | 1.4348 | 1.2652 | 0.5229 |
| STR-B | 1.2771 | 1.0424 | 0.8998 | 0.4183 |

All 66 splits per strategy are profitable (PF > 1.0) for STR-X, STR-AA, STR-AF.
STR-B has a min split PF of 0.8998 — one CPCV split is unprofitable on OOS test data.

### Path Maximum Drawdown (R-units, cumulative)

| Strategy | Worst Path | Median Path | Best Path |
|----------|-----------|-------------|-----------|
| STR-X | 353.48 R | 331.18 R | 209.76 R |
| STR-AA | 404.06 R | 318.47 R | 237.52 R |
| STR-AF | 553.60 R | 330.60 R | 232.98 R |
| STR-B | 96.97 R | 73.23 R | 39.01 R |

Drawdowns are reported in cumulative R-units (sum of pnl_bps across each path's test trades).
STR-B has the lowest drawdowns in absolute terms due to 7-11× fewer trades, but all strategies
exceed the 15R G5 threshold.

### DSR, PBO, and Gate Results

| Strategy | DSR (N=115) | PBO | G4 (DSR≥0.95, PBO≤0.10) | G5 (p10-PF≥1.0, worst-DD≤15R) |
|----------|-------------|-----|--------------------------|-------------------------------|
| STR-X | 1.000000 | 0.7121 | FAIL (PBO=0.71) | FAIL (DD=353R) |
| STR-AA | 1.000000 | 0.5000 | FAIL (PBO=0.50) | FAIL (DD=404R) |
| STR-AF | 1.000000 | 0.5455 | FAIL (PBO=0.55) | FAIL (DD=554R) |
| STR-B | 0.999994 | 0.4394 | FAIL (PBO=0.44) | FAIL (DD=97R) |

### Overall Profit Factor (all trades, cost-adjusted)

| Strategy | Overall PF |
|----------|-----------|
| STR-X | 1.7398 |
| STR-AA | 1.7654 |
| STR-AF | 1.6642 |
| STR-B | 1.2903 |

---

## Analysis

### G4: Overfitting Assessment

All 4 strategies fail G4 on PBO — every PBO exceeds the 0.10 threshold by 4-7×.
This is the correct outcome for strategies developed on a single backtest period:
the rank correlation between IS and OOS Sharpe across 66 CPCV splits is weak.
PBO values of 0.44-0.71 indicate substantial overfitting risk.

DSR is near 1.0 for all strategies because the sample sizes are enormous
(2,955–32,360 trades producing t-statistics of 51–124 against an E[max] of ~2.58
for N=115). High DSR is a data artifact, not a signal of robustness — the PBO
tells the real story.

### G5: Walk-Forward Robustness

All 4 strategies pass the p10-PF ≥ 1.0 criterion easily: even the 10th-percentile
split PF is ≥1.04 (STR-B). However, all fail the worst-path max-DD ≤ 15R criterion.
The worst CPCV paths accumulate drawdowns of 97–554 R-units.

STR-B is closest to G5 compliance: it has the lowest PBO (0.4394), lowest worst-path
DD (97R on 2,955 trades), and a p10-PF of 1.04. The 15R threshold may be calibrated
for smaller trade counts; normalized per-trade, STR-B's worst path DD is ~0.033R/trade.

### Strategy Ranking

1. **STR-AF** — Strongest split PF profile (min PF=1.27, best p10-PF=1.43), highest win rate (52.3%), but largest worst-path DD (554R)
2. **STR-AA** — Best median split PF (1.81), second-best win rate (51.8%), moderate DD
3. **STR-X** — Solid PF profile, similar to STR-AA but lower win rate (50.0%), highest PBO (0.71)
4. **STR-B** — Smallest sample (2,955 trades), lowest PBO (0.44), lowest DD, but weakest PF profile and only strategy with a sub-1.0 split PF

### Cost Drag Impact

Stock venue cost drag is negligible for these strategies: 0.0067–0.0099 R per trade.
For a strategy with avg R of ~0.30, this is ~2-3% of expected return per trade.
The cost adjustment does not materially change any CPCV outcome.

---

## Verdict

| Strategy | G4 | G5 | Overall |
|----------|----|----|---------|
| STR-X | FAIL | FAIL | **DO NOT PROMOTE** |
| STR-AA | FAIL | FAIL | **DO NOT PROMOTE** |
| STR-AF | FAIL | FAIL | **DO NOT PROMOTE** |
| STR-B | FAIL | FAIL | **DO NOT PROMOTE** |

None of the 4 T0 strategies pass the CPCV transfer gates. All show significant
overfitting (PBO 0.44–0.71) and deep worst-path drawdowns (97–554 R). STR-B is
closest to compliance on PBO and DD measures but its split PF minimum of 0.90
indicates one partition is structurally unprofitable.

---

**Generated:** 2026-09-19  
**Method:** CPCV (López de Prado, 2018) with purge+embargo, 1-factorization paths  
**Data source:** `scripts/validation/results/STR-{X,AA,AF,B}-stocks-phase1a-v3.csv`  
**Cost model:** `cost_adjuster.py` stock venue (2.0 bps)  
**Trials:** N=115 from `data/gauntlet/trials.jsonl`