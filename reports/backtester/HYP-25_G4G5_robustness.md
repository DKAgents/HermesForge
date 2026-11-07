# HYP-25 — G4/G5 robustness pass (CPCV + DSR + PBO) — verdict

Date: 2026-11-07 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-25-short-side-continuation.md
Leg under test: LIQUID-floor short leg ONLY (the HYP-25 spec) — bottom-decile 7d
  momentum losers, restricted to names above the $250k trailing-OI floor.
Driver: scripts/gauntlet/g4g5_hyp25_robustness.py
Prior verdict: reports/backtester/HYP-25_short_side_continuation.md (G3 PASSED)
Trials ledger N (for DSR): 141 (data/gauntlet/trials.jsonl)
Fresh param_hash (robustness harness): 18ff7107269ee827…

VERDICT: THE ROBUSTNESS PASS FAILS. "Short-the-losers" does NOT survive
CPCV / DSR / PBO as a real persistent edge. The control-beating +0.20R was a
pre-2026 bull/carry-regime artifact; 2026's honest forward prior is ~+0.06R,
and the OOS folds are unstable enough (10th-%ile fold PF ≈ 0.72, PBO 0.52,
DSR 0.84) that promotion is NOT warranted. Do NOT promote.

---

## 0. Method (honesty rules applied)

Harness: scripts/gauntlet/cpcv_harness.py (López de Prado CPCV). Two unit traps
were corrected for this run:

  1. INTEGER DAY NUMBERS. cpcv_harness purge/embargo subtracts the holding/
     embargo window from entry_time/exit_time in whatever unit those fields
     carry. Feeding ms/epoch or datetime would mix units and silently nullify
     the purge. entry_time/exit_time are fed as INTEGER day indices, with
     holding_horizon=20 days (max hold = TIMESTOP_BARS = 20d) and embargo=40
     days (the same 20/40 split as the prior stock transfer audit, restated in
     this strategy's daily-bar unit).

  2. NON-OVERLAPPING SAMPLES. The raw driver emits 13,447 "trades" that are
     heavily serially-overlapping — a coin stuck in the bottom decile is
     re-shorted day after day while the prior short is still open. Overlapping
     returns under-state per-trade σ and inflate Sharpe/PF. Trades are thinned
     per-coin to non-overlapping holding windows (greedy chronological keep,
     entry_idx > last kept exit_idx for that coin), preserving cross-sectional
     breadth (which IS the strategy's edge). CPCV + DSR/PBO are computed on the
     3,252-trade non-overlapping sample; the raw overlapping run is reported
     once for transparency only.

DSR is computed with n_observations = distinct non-overlapping trades (3,252),
NOT the harness's 11×-stacked 66-fold concatenation, and n_trials = N = 141
read from the trials ledger. LIVE off; leverage ≤ -1x; cost charged once
(4.5 bps/leg taker + 2.5 bps entry slip + hourly funding) exactly as netted
into net_r by the HYP-25 driver. No look-ahead.

## 1. G4 CPCV — split profit factor (N=12, k=2, 66 splits, 11 paths)

| sample               | trades | 10th-%ile PF | median PF | min PF | gate (10-%ile ≥ 1.0) |
|----------------------|-------:|-------------:|----------:|-------:|----------------------|
| overlapping (transp) | 13,447 |       0.8821 |    1.2983 | 0.7896 | FAIL |
| non-overlapping      |  3,252 |       0.7185 |    1.3382 | 0.4722 | **FAIL** |

10th-%ile fold PF = 0.7185 < 1.0. Approximately one-in-ten OOS folds is
unprofitable, and the worst fold is PF 0.47 — deep red. The median (1.34) sits
just above the 1.30 threshold, but the left tail (the binding G4 criterion) is
decisively below 1.0. The edge does not reproduce out-of-sample.

## 2. G5 DSR + PBO

- DSR (N=141 trials, n=3,252 non-overlapping trades): 0.841317  → FAIL (< 0.95).
- PBO (rank-based over the 66 fold Sharpes): 0.5152  → FAIL (> 0.30).

Per-trade Sharpe on the non-overlapping sample is 0.1208 (mean +0.1424R,
σ 1.1791R, skew +0.616, ex-kurt −0.610). Once the multiple-testing selection
premium (N=141) is deflated out, the remaining evidence does not clear 0.95,
and PBO well over 0.30 says the observed rank ordering across folds is more
consistent with overfitting/regime drift than a stable edge.

## 3. The decay, made explicit (honest 2026 forward prior)

Non-overlapping liquid short leg, mean net R by year:

| year | n     | mean net R |
|------|------:|-----------:|
| 2023 |    41 | +0.0458    |
| 2024 |   883 | +0.1618    |
| 2025 | 1,207 | +0.2119    |
| 2026 | 1,121 | +0.0558    |

ALL = +0.1424R (a pre-2026-inflated sample mean). The honest 2026 forward
prior is +0.0558R ≈ +0.06R, a near-quarter of the 2025 peak.

OOS-fold concentration (sum of net R across all 66 splits' test trades):

| year | n      | mean | share of positive edge |
|------|-------:|-----:|------------------------|
| 2024 |  9,713 | +0.162 | dominant |
| 2025 | 13,277 | +0.212 | dominant |
| 2026 | 12,331 | +0.056 | marginal |

The OOS folds overwhelmingly concentrate their positive edge in 2024–2025. The
2026 folds run near-flat, which is exactly why the fold-PF left tail collapses
below 1.0 once a fold is forced to carry 2026 (or a 2026-heavy) regime: the
edge IS a decaying one, and its pre-2025 positive contribution is a bull/
carry-regime artefact, not a stationary structural alpha.

## 4. Honest go/no-go

| gate | criterion                       | observed          | result |
|------|---------------------------------|-------------------|--------|
| G4   | 10th-%ile split PF ≥ 1.0        | 0.7185            | FAIL |
| G5   | DSR > 0.95                      | 0.8413            | FAIL |
| G5   | PBO < 0.30                      | 0.5152            | FAIL |

Gates not independently re-scored here (out of the requested scope, and
moot given the above): G4 worst-path max-DD and the block-bootstrap p<0.05 leg
would only add the short tail's unbounded squeeze/delist risk to a verdict that
already fails on PF/DSR/PBO.

## 5. Conclusion

HYP-25's short-the-losers asymmetry was REAL as a control-beating geometry
(+0.20R over the zero-drift control) and it did survive the shortability floor
+ G3 fills + funding. That was the right, necessary finding. But the promised
G4/G5 robustness pass now adjudicates the NEXT question — is it a persistent,
promotable edge? — and the answer is NO:

  - 10th-%ile OOS fold PF 0.72 (worst 0.47): the edge does not reproduce
    out-of-sample;
  - DSR 0.84 (below 0.95) and PBO 0.52 (above 0.30): the apparent edge does not
    survive multiple-testing deflation or rank-stability checks;
  - the 2026 forward prior is ~+0.06R (not the +0.20R sample mean), and the OOS
    folds concentrate the positive in 2024–2025 — a decaying, regime-dependent
    effect, with funding having rotated from tailwind to headwind.

Recommendation: leave HYP-25 in Hypotheses (do NOT promote). If revisited, it
must be as a regime-conditional re-entry (funding>0 / momentum-crowding state
in a decaying-basket context) with 2026's +0.06R as the pre-registered forward
prior and a live-paper forward before any promotion is considered. The raw
short-the-losers continuation as a standalone edge is CLOSED as not robust.

Persisted: /root/.hermes/cache/scratch/hyp25_g4g5_result.json
