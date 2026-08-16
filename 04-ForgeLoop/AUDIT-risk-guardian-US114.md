# RISK GUARDIAN AUDIT — US-114
## 19 Strategy Scanner Risk Review

**Auditor:** Risk Guardian, HermesForge Swarm
**Date:** 2026-08-16
**Scope:** 19 scanner files (STR-S through STR-R) reviewed across 4 risk dimensions
**Authority:** Veto power per US-114. Vetoed scanners must NOT be trusted in paper trading until fixed.

---

## EXECUTIVE SUMMARY

| Metric | Count |
|--------|-------|
| Total scanners reviewed | 19 |
| VETOED | 4 |
| CONDITIONAL | 15 |
| APPROVED | 0 |

**No scanner receives full APPROVED status.** All 19 scanners share two universal deficiencies:
1. **In-sample-only backtests** — no walk-forward / OOS split (US-109 lesson: stop optimization looked great in-sample, failed OOS with p=0.928)
2. **Zero survivorship bias disclosure** — the 18-stock backtest universe (SPY, QQQ, AAPL, NVDA, TSLA, AMZN, MSFT, GOOGL, META, AMD, NFLX, JPM, BAC, XOM, CVX, PFE, UNH, COST) is a hand-picked set of mega-cap survivors. This is the worst possible case for survivorship bias. All performance metrics are biased upward.

**4 scanners VETOED for critical issues:**
- STR-S: 51 trades, PF=1.12, 1/51 target hits — insufficient sample + no edge
- STR-W: 83% duplicate signals (13,876 of 16,644) — corrupted metrics
- STR-R: Code bug — 43 "sleep" exits with R=0.0 instead of actual R — corrupted data
- STR-AH: 84% time exits driving 70.3% WR — survivorship bias amplified, no real edge

---

## SUMMARY TABLE

| Scanner | Verdict | Trades | Key Risk | Recommendation |
|---------|---------|--------|----------|----------------|
| STR-S Elliott Wave | VETO | 51 | <100 trades, PF=1.12, 1/51 target hits | Expand universe + OOS before paper |
| STR-T Head&Shoulders | CONDITIONAL | 294 | In-sample only, survivorship bias | OOS + bias disclosure |
| STR-U Double Top/Bottom | CONDITIONAL | 86 | <100 trades, marginal sample | Expand universe for more trades |
| STR-V Triangles | CONDITIONAL | 776 | Pattern detection sensitivity | OOS + PIVOT_DISTANCE sensitivity |
| STR-W Flags/Pennants | VETO | 16,644 (83% dupes) | Massive duplicate signals | Fix duplicate generation, re-run |
| STR-X Parabolic SAR | CONDITIONAL | 1,607 | In-sample only, whipsaw risk | OOS + bias disclosure |
| STR-Y ADX/DMI | CONDITIONAL | 241 | In-sample only | OOS + ADX threshold sensitivity |
| STR-Z Stochastic | CONDITIONAL | 976 | In-sample only, 44.7% WR | OOS + bias disclosure |
| STR-AA Williams %R | CONDITIONAL | 2,167 | In-sample only, 43.3% WR | OOS + bias disclosure |
| STR-AB OBV Divergence | CONDITIONAL | 230 | Tight swing window (2 bars) | OOS + SWING_WINDOW sensitivity |
| STR-AC CCI | CONDITIONAL | 1,466 | In-sample only, 44.1% WR | OOS + bias disclosure |
| STR-AD Keltner | CONDITIONAL | 1,326 | In-sample only | OOS + bias disclosure |
| STR-AE 4-Week Rule | CONDITIONAL | 2,178 | 79% time exits, trend-drift dependent | OOS + bias disclosure |
| STR-AF Candlestick | CONDITIONAL | 7,195 | Arbitrary thresholds, 2R target | OOS + threshold sensitivity |
| STR-AG Wedge | CONDITIONAL | 1,271 | In-sample only, variable R | OOS + bias disclosure |
| STR-AH Island Reversal | VETO | 118 | 84% time exits, bias-amplified WR | Bias-free universe + OOS required |
| STR-AI Seasonal | CONDITIONAL | 264 | Seasonal instability | OOS + multi-market validation |
| STR-AJ Intermarket | CONDITIONAL | 501 | Correlated signals, concentration risk | OOS + correlation control |
| STR-R Alligator | VETO | 510 | Code bug: 43 sleep exits R=0 | Fix sleep exit R calc, re-run |

---

## UNIVERSAL FINDINGS (apply to all 19 scanners)

### Dimension 2: Survivorship Bias Disclosure — FAIL (all 19)

The yfinance stock universe (529 stocks) is NOT survivorship-bias-free. The 18-stock backtest universe is a subset of mega-cap survivors — companies that have survived and thrived over the backtest period. Delisted or bankrupt companies are absent. This biases all results upward.

**Required action for all scanners:** Add a `SURVIVORSHIP_BIAS_DISCLAIMER` constant to each scanner file and print it in the Phase 1A summary output. Example:

```python
SURVIVORSHIP_BIAS_DISCLAIMER = (
    "WARNING: Backtest results are subject to survivorship bias. "
    "The stock universe contains only currently-listed companies. "
    "Delisted/bankrupt companies are excluded, biasing returns upward. "
    "Performance metrics should not be trusted without OOS validation "
    "on a survivorship-bias-free universe."
)
```

### Dimension 4: Statistical Validity — In-Sample Only (all 19)

No scanner implements walk-forward / train-test split / OOS validation. All metrics are in-sample. The US-109 lesson (stop optimization looked great in-sample, failed OOS with p=0.928) directly applies. In-sample performance is necessary but NOT sufficient to trust any strategy.

**Required action for all scanners:** Implement a minimum 60/40 in-sample/OOS split with separate metrics reported for each period. Ideally use walk-forward analysis with multiple folds.

### Dimension 3: Risk Rule Compliance — Mostly PASS

**Position sizing:** None of the scanners implement position sizing (they produce signals, not execute trades). The 1% flat risk rule must be enforced downstream by the orchestrator/risk-guardian layer. This is acceptable IF documented.

**Stops:** All 19 scanners set a stop_price on every signal and include a `risk <= 0` guard that prevents signals where the stop is on the wrong side of entry. PASS.

**Leverage:** None used. PASS.
**Naked options:** None. PASS.
**Averaging down:** No scanner adds to existing positions. PASS.

**Exceptions:**
- STR-W: Duplicate signals could cause over-allocation if the orchestrator does not deduplicate. RISK.
- STR-R: Sleep exit bug means 43 trades have incorrect R-multiple (0.0 instead of actual). DATA CORRUPTION.

---

## DETAILED PER-SCANNER ANALYSIS

### STR-S Elliott Wave — VETO

**File:** scanner_s_elliott_wave.py
**Trades:** 51 | WR: 51.0% | Avg R: 0.053 | Sum R: +2.70 | PF: 1.12 | Target hits: 1/51

**Dimension 1 — Overfitting Risk: MEDIUM**
Parameters: FIB_MIN=0.382, FIB_MAX=0.618 (standard Fibonacci), PIVOT_DISTANCE=3, STOP_ATR_MULT=1.0, TARGET_RR=3.0, MAX_HOLD_BARS=25. The Fibonacci range is standard, not curve-fit. However, the 5-wave impulse + ABC correction pattern is complex with many degrees of freedom in how pivots are identified via scipy.find_peaks. The `distance=3` parameter controls pivot detection sensitivity — small changes would alter which waves qualify.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop on every trade, 1 ATR, 3R target)
**Dimension 4 — Statistical Validity: FAIL**
- 51 trades is below the 100-trade threshold for statistical significance
- PF=1.12 is barely above breakeven — this is within normal noise range
- Only 1 target hit out of 51 trades (2%) — the 3R target is essentially never reached
- 29/51 trades exit via time stop (57%) — the strategy mostly holds to expiration and hopes for a small gain
- In-sample only, no OOS validation

**Verdict: VETO**
The combination of insufficient trades (<100), barely-breakeven performance (PF=1.12), and near-zero target hit rate (1/51) means this scanner has no demonstrated edge. The complex pattern detection adds overfitting risk on top. Must not be trusted in paper trading until: (1) universe expanded to generate 100+ trades, (2) OOS validation performed, (3) survivorship bias disclosed.

---

### STR-T Head and Shoulders — CONDITIONAL

**File:** scanner_t_head_shoulders.py
**Trades:** 294 | WR: 63.6% | Avg R: 0.248 | Sum R: +72.94 | PF: 1.99 | Target hits: 115/294

**Dimension 1 — Overfitting Risk: LOW-MEDIUM**
Parameters: SHOULDER_TOLERANCE=0.03 (3%), PIVOT_DISTANCE=5, STOP_ATR_MULT=1.0, MAX_HOLD_BARS=25. Target is pattern-height-based (not fixed 3R), which adapts to the pattern and reduces curve-fitting. The 3% shoulder tolerance and pivot distance=5 are reasonable. The 1R floor on target (line 128-129) is a sensible guard.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop on every trade, 1 ATR beyond head)
**Dimension 4 — Statistical Validity: MARGINAL**
- 294 trades is above 100 — sufficient for preliminary assessment
- PF=1.99 and 63.6% WR look reasonable
- 115 target hits (39%) and 56 stops (19%) — reasonable distribution
- BUT: in-sample only, no OOS validation

**Verdict: CONDITIONAL**
Can proceed to OOS validation. Not trusted for paper trading until OOS split confirms the edge and survivorship bias is disclosed.

---

### STR-U Double Top/Bottom — CONDITIONAL

**File:** scanner_u_double_top_bottom.py
**Trades:** 86 | WR: 62.8% | Avg R: 0.165 | Sum R: +14.17 | PF: 1.70 | Target hits: 25/86

**Dimension 1 — Overfitting Risk: LOW**
Parameters: PEAK_TOLERANCE=0.03, MIN_BARS_BETWEEN=10, PIVOT_DISTANCE=4, STOP_ATR_MULT=1.0, MAX_HOLD_BARS=25. Target is pattern-height-based. Standard parameters, minimal curve-fitting risk.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS**
**Dimension 4 — Statistical Validity: MARGINAL**
- 86 trades is below the 100-trade threshold
- PF=1.70 is decent but with only 86 trades, confidence intervals are wide
- Only 14 stops (16%) and 25 targets (29%) — 47 time exits (55%)
- In-sample only

**Verdict: CONDITIONAL**
Below the 100-trade significance threshold. Can proceed to expanded-universe testing to generate more trades, then OOS validation. Not trusted for paper trading yet.

---

### STR-V Triangles — CONDITIONAL

**File:** scanner_v_triangles.py
**Trades:** 776 | WR: 56.3% | Avg R: 0.240 | Sum R: +186.54 | PF: 1.68 | Target hits: 233/776

**Dimension 1 — Overfitting Risk: MEDIUM**
Parameters: MIN_WINDOW=20, VOLUME_MULT=1.5, PIVOT_DISTANCE=3, FLAT_TOL=0.001. The flat line classification uses `flat_band/10` as slope tolerance — this is a magic number without justification. The volume multiplier of 1.5x is common but unvalidated. The triangle classification logic (symmetrical/ascending/descending) has multiple branches with arbitrary thresholds.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop at opposite side of triangle)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 776 trades is well above 100
- PF=1.68, 56.3% WR, balanced exit distribution (234 stops, 233 targets, 309 time)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Sufficient trades for preliminary assessment. Needs OOS validation and sensitivity analysis on PIVOT_DISTANCE and FLAT_TOL parameters. Survivorship bias disclosure required.

---

### STR-W Flags and Pennants — VETO

**File:** scanner_w_flags_pennants.py
**Trades:** 16,644 raw / 2,768 unique (83% duplicates) | WR: 54.8% raw / 53.7% dedup | Avg R: 0.154 raw / 0.106 dedup

**Dimension 1 — Overfitting Risk: HIGH**
Parameters: MAST_MIN_BARS=5, MAST_MIN_GAIN=0.05, CONSOL_MIN=5, CONSOL_MAX=15, PARALLEL_TOL=0.25, PIVOT_DISTANCE=2. The parallel tolerance (0.25) and pennant convergence threshold (0.6 ratio) are magic numbers. The scanner slides through every possible mast_start and for each tries every consolidation end — this generates massive overlapping signals.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS (with risk)**
Stop on every signal. BUT: duplicate signals mean the same trade entry could be signaled multiple times. If the orchestrator does not deduplicate, this leads to position over-allocation — a direct risk rule violation (exceeding 1% risk per idea).

**Dimension 4 — Statistical Validity: FAIL — DATA CORRUPTION**
The scanner generates 16,644 signals but 13,876 (83%) are exact duplicates (same symbol, date, signal_type). The raw performance metrics are meaningless — they count the same trade multiple times:
- Raw: 54.8% WR, 0.154 avg R, +2,564.79 sum R
- Deduped: 53.7% WR, 0.106 avg R, +294.39 sum R

The inflation is 8.7x on sum R. Any downstream analysis using the raw CSV will be massively biased.

**Verdict: VETO**
Critical data corruption. The scanner's sliding window approach generates duplicate signals that inflate all metrics by ~8x. The raw Phase 1A CSV is unusable. Must fix the signal generation to produce one signal per (symbol, date, signal_type) combination, then re-run the backtest. Additionally, the high parameter count (6+ free parameters with magic numbers) creates overfitting risk.

---

### STR-X Parabolic SAR — CONDITIONAL

**File:** scanner_x_parabolic_sar.py
**Trades:** 1,607 | WR: 50.5% | Avg R: 0.275 | Sum R: +441.26 | PF: 1.64

**Dimension 1 — Overfitting Risk: LOW**
Parameters: AF_START=0.02, AF_INCREMENT=0.02, AF_MAX=0.2. These are Welles Wilder's original defaults — the canonical Parabolic SAR parameters. Not curve-fit. TARGET_RR=3.0, MAX_HOLD_BARS=20.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS**
Stop = current SAR value (acts as trailing stop). The fallback to ATR-based stop when SAR is above entry (line 156) is a sensible guard.

**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 1,607 trades, well above 100
- PF=1.64, 50.5% WR — the near-50% win rate is expected for a mechanical SAR system (edge comes from R-multiple asymmetry, not win rate)
- 636 stops (40%), 134 targets (8%), 837 time exits (52%) — high time-stop rate is typical of SAR systems in choppy markets
- BUT: in-sample only

**Verdict: CONDITIONAL**
Standard mechanical system with Wilder's parameters. Sufficient trades. Needs OOS validation — SAR systems are known to perform differently in trending vs choppy regimes, and the in-sample period (2018-2025) includes both.

---

### STR-Y ADX/DMI — CONDITIONAL

**File:** scanner_y_adx_dmi.py
**Trades:** 241 | WR: 44.4% | Avg R: 0.184 | Sum R: +44.41 | PF: 1.35

**Dimension 1 — Overfitting Risk: LOW**
Parameters: ADX_PERIOD=14, ADX_THRESHOLD=25.0, STOP_ATR_MULT=2.0, TARGET_RR=3.0, MAX_HOLD_BARS=20. Standard Wilder parameters. ADX > 25 threshold is the textbook trending filter.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (2 ATR stop, 3R target)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 241 trades, above 100
- PF=1.35, 44.4% WR — below 50% win rate but positive expectancy via 3R targets
- 122 stops (51%), 21 targets (9%), 98 time exits (41%)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Standard parameters, sufficient trades. The 2 ATR stop is wider than most other scanners — this reduces stop-out frequency but increases per-trade risk. Needs OOS validation and sensitivity analysis on the ADX_THRESHOLD (25 vs 20 vs 30).

---

### STR-Z Stochastic — CONDITIONAL

**File:** scanner_z_stochastic.py
**Trades:** 976 | WR: 44.7% | Avg R: 0.222 | Sum R: +216.55 | PF: 1.43

**Dimension 1 — Overfitting Risk: LOW**
Parameters: K_PERIOD=14, K_SMOOTH=3, D_PERIOD=3, STOP_ATR_MULT=1.5, TARGET_RR=3.0, MAX_HOLD_BARS=15. Standard Lane stochastic parameters.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS**
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 976 trades, well above 100
- PF=1.43, 44.7% WR — below 50% but positive via 3R asymmetry
- 492 stops (50%), 111 targets (11%), 373 time exits (38%)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Standard oscillator strategy. Sufficient trades. Needs OOS — oscillator strategies are known to underperform in strong trends (which the 2018-2025 period had).

---

### STR-AA Williams %R — CONDITIONAL

**File:** scanner_aa_williams_r.py
**Trades:** 2,167 | WR: 43.3% | Avg R: 0.205 | Sum R: +443.33 | PF: 1.39

**Dimension 1 — Overfitting Risk: LOW**
Parameters: WR_PERIOD=14, OVERSOLD=-80, OVERBOUGHT=-20, STOP_ATR_MULT=1.5, TARGET_RR=3.0, MAX_HOLD_BARS=15. Standard Williams parameters.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS**
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 2,167 trades, well above 100
- PF=1.39, 43.3% WR — below 50%, relying on 3R asymmetry
- 1,110 stops (51%), 252 targets (12%), 805 time exits (37%)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Standard parameters, sufficient trades. The 43.3% win rate is concerning — it means more than half the trades stop out. The edge is entirely dependent on the 3R target being hit often enough to compensate. OOS validation is critical.

---

### STR-AB OBV Divergence — CONDITIONAL

**File:** scanner_ab_obv_divergence.py
**Trades:** 230 | WR: 53.0% | Avg R: 0.251 | Sum R: +57.72 | PF: 1.72

**Dimension 1 — Overfitting Risk: MEDIUM**
Parameters: SWING_WINDOW=2, MIN_BETWEEN_PIVOTS=5, STOP_ATR_MULT=1.5, TARGET_RR=3.0, MAX_HOLD_BARS=20. The SWING_WINDOW=2 is very tight — only 2 bars on each side to confirm a pivot. This makes pivot detection highly sensitive to noise. Small changes to this parameter would significantly alter which pivots qualify and thus which divergences are detected.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (1.5 ATR stop below divergence low)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 230 trades, above 100
- PF=1.72, 53.0% WR
- 66 stops (29%), 9 targets (4%), 155 time exits (67%) — very high time-exit rate, very low target-hit rate
- BUT: in-sample only

**Verdict: CONDITIONAL**
The 4% target hit rate (9/230) is very low — the 3R target is almost never reached. The edge comes primarily from time exits being positive. This is sensitive to the overall market drift (survivorship bias). Needs OOS validation and sensitivity analysis on SWING_WINDOW (test 2 vs 3 vs 5).

---

### STR-AC CCI — CONDITIONAL

**File:** scanner_ac_cci.py
**Trades:** 1,466 | WR: 44.1% | Avg R: 0.229 | Sum R: +335.71 | PF: 1.44

**Dimension 1 — Overfitting Risk: LOW**
Parameters: CCI_PERIOD=20, OVERSOLD=-100, OVERBOUGHT=100, STOP_ATR_MULT=1.5, TARGET_RR=3.0, MAX_HOLD_BARS=15. Standard Lambert CCI parameters. The 0.015 constant in the CCI formula is the original Lambert constant.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS**
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 1,466 trades, well above 100
- PF=1.44, 44.1% WR
- 730 stops (50%), 168 targets (11%), 568 time exits (39%)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Standard CCI strategy. Sufficient trades. Needs OOS validation.

---

### STR-AD Keltner Channel — CONDITIONAL

**File:** scanner_ad_keltner.py
**Trades:** 1,326 | WR: 52.6% | Avg R: 0.306 | Sum R: +405.70 | PF: 1.73

**Dimension 1 — Overfitting Risk: LOW**
Parameters: EMA_PERIOD=20, ATR_PERIOD=10, ATR_MULT=2.0, TARGET_RR=3.0, MAX_HOLD_BARS=20. Standard Keltner parameters. Stop at the middle band (EMA) is structurally sound.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop at EMA, 3R target)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 1,326 trades, well above 100
- PF=1.73, 52.6% WR — above 50% with positive avg R
- 517 stops (39%), 100 targets (8%), 709 time exits (53%)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Standard parameters, sufficient trades. Needs OOS validation.

---

### STR-AE Donchian 4-Week Rule — CONDITIONAL

**File:** scanner_ae_4week_rule.py
**Trades:** 2,178 | WR: 57.5% | Avg R: 0.194 | Sum R: +421.60 | PF: 1.72

**Dimension 1 — Overfitting Risk: LOWEST**
Parameters: CHANNEL_PERIOD=20, TARGET_RR=3.0, MAX_HOLD_BARS=30. Only 3 parameters — the simplest mechanical system in the batch. This is the classic Donchian rule with minimal curve-fitting risk. The 30-bar time stop is longer than most, giving trends room to develop.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop at opposite channel boundary)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 2,178 trades, well above 100
- PF=1.72, 57.5% WR
- 415 stops (19%), 41 targets (2%), 1,722 time exits (79%) — extremely high time-exit rate
- BUT: in-sample only

**Verdict: CONDITIONAL**
Lowest overfitting risk of all 19 scanners (3 parameters). However, the 79% time-exit rate and 2% target-hit rate means the strategy almost never hits its 3R target — the edge comes from holding to expiration and capturing drift. This makes it highly dependent on the overall market uptrend (survivorship bias amplified). OOS validation is essential.

---

### STR-AF Candlestick — CONDITIONAL

**File:** scanner_af_candlestick.py
**Trades:** 7,195 | WR: 42.2% | Avg R: 0.164 | Sum R: +1,178.07 | PF: 1.29

**Dimension 1 — Overfitting Risk: MEDIUM**
Parameters: Multiple pattern detection thresholds — `body < rng * 0.35` (small body), `lw >= 2 * body` (hammer), `b1_body < b1_rng * 0.4` (small gap candle). These ratios (0.35, 0.40, 2x) are somewhat standard but the specific thresholds are arbitrary. TARGET_RR=2.0 (not 3R like most others), MAX_HOLD_BARS=10 (shortest holding period). The 2R target and 10-bar limit means this is a quick-reversal strategy — different risk profile than the 3R scanners.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (1 ATR stop, 2R target)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 7,195 trades, well above 100
- PF=1.29, 42.2% WR — lowest win rate, relying on 2R asymmetry
- 3,961 stops (55%), 2,269 targets (32%), 965 time exits (13%)
- BUT: in-sample only

**Verdict: CONDITIONAL**
Sufficient trades, but the arbitrary pattern thresholds need sensitivity analysis. The 2R target (vs 3R for most others) means smaller wins — more sensitive to stop-out rate. OOS validation required.

---

### STR-AG Wedge — CONDITIONAL

**File:** scanner_ag_wedge.py
**Trades:** 1,271 | WR: 57.2% | Avg R: 0.279 | Sum R: +354.21 | PF: 1.81 | Max win: 9.38R

**Dimension 1 — Overfitting Risk: LOW-MEDIUM**
Parameters: MIN_WINDOW=20, PIVOT_DISTANCE=3, SLOPE_TOL=1e-9. Few parameters. Target is wedge-height-based (not fixed R). The slope tolerance is essentially zero (1e-9), meaning any positive slope qualifies — this is not curve-fit.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop at wedge extreme)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 1,271 trades, well above 100
- PF=1.81, 57.2% WR — strong in-sample performance
- 383 stops (30%), 298 targets (23%), 590 time exits (46%) — reasonable distribution
- Max win of 9.38R indicates variable R targets (pattern-height-based) — some outsized wins
- BUT: in-sample only

**Verdict: CONDITIONAL**
Good in-sample metrics with balanced exit distribution. The variable R target (pattern-height-based) means some trades have very large R-multiples, which is structurally sound. Needs OOS validation.

---

### STR-AH Island Reversal — VETO

**File:** scanner_ah_island_reversal.py
**Trades:** 118 | WR: 70.3% | Avg R: 0.464 | Sum R: +54.74 | PF: 3.52 | Target hits: 4/118

**Dimension 1 — Overfitting Risk: LOW**
Parameters: MIN_ISLAND_BARS=1, MAX_ISLAND_BARS=5, TARGET_RR=3.0, MAX_HOLD_BARS=15. Few parameters, none curve-fit.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (stop at island extreme)
**Dimension 4 — Statistical Validity: FAIL — SURVIVORSHIP BIAS AMPLIFIED**
- 118 trades, barely above 100
- PF=3.52 and 70.3% WR are suspiciously high
- Exit distribution: 15 stops (13%), 4 targets (3%), 99 time exits (84%)
- The 70.3% win rate is almost entirely driven by time exits (79.8% WR on time exits)
- This means the "edge" is: enter after an island reversal, hold 15 bars, and exit at close. On mega-cap survivors in a bull market, this will be positive ~80% of the time — but this is just beta exposure, not a pattern-specific edge.
- Only 4 target hits (3%) means the 3R target is essentially never reached
- The strategy is effectively a "hold and hope" strategy disguised as a pattern recognizer

**Verdict: VETO**
The 70.3% win rate is an artifact of survivorship bias and the overall bull market in mega-cap stocks, not a genuine island-reversal edge. With 84% of trades exiting via time stop and only 3% hitting target, the pattern detection adds no value over simply buying and holding. The PF of 3.52 is almost certainly noise — it would collapse on a survivorship-bias-free universe or in a bear market. Must not be trusted until tested on a bias-free universe with OOS validation.

---

### STR-AI Seasonal — CONDITIONAL

**File:** scanner_ai_seasonal.py
**Trades:** 264 | WR: 49.6% | Avg R: 0.393 | Sum R: +103.79 | PF: 1.88

**Dimension 1 — Overfitting Risk: MEDIUM**
Parameters: POS_THRESHOLD=0.60, NEG_THRESHOLD=0.60, STOP_ATR_MULT=2.0, TARGET_RR=3.0, MAX_HOLD_BARS=20, ATR_PERIOD=14. The 60% threshold is a magic number. The expanding window approach (no lookahead) is well-implemented and reduces overfitting. However, seasonal patterns are notoriously unstable — they work in some decades and fail in others. The strategy enters on the first trading day of qualifying months, which is a very specific timing assumption.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS** (2 ATR stop, 3R target)
**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 264 trades, above 100
- PF=1.88, 49.6% WR, avg R=0.393 — strong in-sample
- 110 stops (42%), 30 targets (11%), 124 time exits (47%)
- BUT: in-sample only. Seasonal strategies are the MOST likely to fail OOS because the historical patterns they rely on may not persist.

**Verdict: CONDITIONAL**
The expanding window implementation is good (no lookahead bias). But seasonal strategies have the highest regime-failure risk of any strategy type. OOS validation is absolutely critical — the "edge" may be a statistical artifact of the specific 2018-2025 period. Multi-market validation (test on non-US markets) would strengthen confidence.

---

### STR-AJ Intermarket — CONDITIONAL

**File:** scanner_aj_intermarket.py
**Trades:** 501 | WR: 54.9% | Avg R: 0.463 | Sum R: +232.12 | PF: 2.16

**Dimension 1 — Overfitting Risk: LOW-MEDIUM**
Parameters: SLOPE_WINDOW=20, SMA_PERIOD=50, STOP_ATR_MULT=2.0, TARGET_RR=3.0, MAX_HOLD_BARS=20. Standard parameters. The intermarket logic (DXY + TNX slopes for risk-on/off) is conceptually sound and based on established macro relationships.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS (with STRUCTURAL RISK)**
- 2 ATR stop, 3R target on every trade. PASS.
- BUT: The intermarket signal is market-wide — when DXY/TNX trigger risk-on, EVERY stock in the universe gets a long signal simultaneously. This creates perfect cross-sectional correlation. If 18 stocks all signal long on the same day, and the orchestrator allows 8 positions (US-111 limit), the portfolio is concentrated in a single macro bet. This is a hidden concentration risk that the per-trade risk rules don't address.

**Dimension 4 — Statistical Validity: SUFFICIENT (in-sample)**
- 501 trades, above 100
- PF=2.16, 54.9% WR, avg R=0.463 — strong in-sample
- 184 stops (37%), 53 targets (11%), 264 time exits (53%)
- BUT: in-sample only. The intermarket relationship (DXY/TNX driving equities) may have changed over the backtest period.

**Verdict: CONDITIONAL**
Strong in-sample metrics with sound macro logic. However, the correlated-signal problem is a structural risk that must be addressed at the portfolio level. The orchestrator must limit intermarket-driven entries to avoid over-concentration in a single macro bet. OOS validation required.

---

### STR-R Alligator — VETO

**File:** scanner_r_alligator.py
**Trades:** 510 | WR: 35.7% | Avg R: 0.242 | Sum R: +123.42 | PF: 1.44 | Sleep exits: 43 (all R=0.0)

**Dimension 1 — Overfitting Risk: MEDIUM**
Parameters: SMMA(13/8/5) with shifts (8/5/3) — Bill Williams' original parameters, not curve-fit. STOP_ATR_MULT=1.5, TARGET_RR=3.0, MAX_HOLD_BARS=20. The "sleeping" threshold (line_spread < 0.5 * ATR) is a magic number without justification.

**Dimension 2 — Survivorship Bias: FAIL** (no disclosure)
**Dimension 3 — Risk Rules: PASS (with CODE BUG)**
Stop on every signal. BUT: the `_walk_forward_exit` function has a critical bug in the sleep-exit logic (lines 248-259):
- When the Alligator "goes back to sleep" during the holding period, the exit returns `r_multiple: 0` instead of computing the actual R at the exit price
- This is incorrect — the actual R could be positive or negative
- 43 out of 510 trades (8.4%) have corrupted R-multiples
- Additionally, the sleep-exit detection recomputes `compute_alligator(df.iloc[:i+1])` for every bar during the holding period — this is O(n^2) and extremely slow, but more importantly, it recomputes the indicator on a truncated dataset which may produce different results than the full-series computation

**Dimension 4 — Statistical Validity: CORRUPTED**
- 510 trades, above 100
- PF=1.44, 35.7% WR — but 43 trades have R=0.0 instead of their actual R
- The sum R (+123.42), avg R (0.242), and PF (1.44) are all inaccurate
- If the 43 sleep exits had negative R (likely, since the Alligator tangling suggests trend failure), the actual performance would be worse
- In-sample only

**Verdict: VETO**
Code bug corrupts 8.4% of trade results. The sleep-exit R-multiple must be computed as `(exit_price - entry_price) / risk` (for longs) or `(entry_price - exit_price) / risk` (for shorts), not set to 0. The backtest must be re-run after fixing this bug. Additionally, the O(n^2) recomputation of the Alligator indicator inside the exit loop is a performance issue that should be fixed (precompute once on the full series, then check the sleeping flag by index).

---

## CROSS-CUTTING RECOMMENDATIONS

### 1. Implement OOS Validation (ALL scanners)
Every scanner must implement a walk-forward or train-test split. Minimum: 60% in-sample / 40% OOS, with separate metrics reported. The US-109 lesson is clear — in-sample optimization can produce p=0.928 OOS (pure noise).

### 2. Add Survivorship Bias Disclosure (ALL scanners)
Add the `SURVIVORSHIP_BIAS_DISCLAIMER` constant and print it in Phase 1A output. Additionally, consider expanding the backtest universe beyond 18 mega-caps to include mid-caps and small-caps, which would provide more trades and reduce (but not eliminate) survivorship bias.

### 3. Fix Critical Bugs (STR-W, STR-R)
- STR-W: Add deduplication in signal generation — one signal per (symbol, date, signal_type). Re-run backtest.
- STR-R: Fix sleep-exit R-multiple calculation. Precompute Alligator on full series. Re-run backtest.

### 4. Position Sizing Documentation (ALL scanners)
Add a comment or constant documenting that position sizing (1% flat risk) is enforced downstream by the orchestrator/risk-guardian layer, not at the scanner level.

### 5. Correlation Risk (STR-AJ specifically)
The intermarket scanner generates correlated signals across all stocks. The orchestrator must implement a max-positions-per-trigger limit to prevent portfolio concentration in a single macro bet.

### 6. Parameter Sensitivity Testing (MEDIUM-risk scanners)
For scanners with magic numbers (STR-V, STR-W, STR-AB, STR-AF, STR-R, STR-AI), run parameter sweeps to verify the edge is not an artifact of specific parameter values. If small parameter changes destroy the edge, the strategy is overfit.

---

## VERDICT DISTRIBUTION

```
VETOED (4):       STR-S, STR-W, STR-AH, STR-R
CONDITIONAL (15): STR-T, STR-U, STR-V, STR-X, STR-Y, STR-Z, STR-AA,
                  STR-AB, STR-AC, STR-AD, STR-AE, STR-AF, STR-AG,
                  STR-AI, STR-AJ
APPROVED (0):     None
```

**No scanner is approved for paper trading.** All 19 require OOS validation and survivorship bias disclosure before being trusted. The 4 VETOED scanners have critical issues (insufficient trades, data corruption, code bugs, or bias-amplified metrics) that must be fixed before any further validation.

---

*Audit complete. Risk Guardian, HermesForge Swarm.*
*US-114 — 2026-08-16*

