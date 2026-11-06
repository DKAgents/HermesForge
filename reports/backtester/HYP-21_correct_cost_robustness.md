# HYP-21 re-run @ CORRECT cost model + G4/G5 robustness — verdict

Date: 2026-11-06 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-21-multifactor-cross-sectional.md (pre-registered, FIXED)
Driver: scripts/gauntlet/revalidate_hyp21_correct_cost.py
Trials: data/gauntlet/trials.jsonl (HYP-21 x2 fresh param_hash: C-positioning 35c8660a…, C-all 4e8b8f84…; chain verified OK; N=132)

VERDICT (honest): at the CORRECT cost, the cross-sectional OI-level edge CLEARS the
fee hurdle at 5d hold (net positive) but does NOT survive robustness. It collapses
under G4 (CPCV 10th-pct PF) and G5 (DSR / PBO). The kill rule FIRES on robustness,
not on cost. No promotion. LIVE off.

---

## 0. What was wrong before, and what changed

The prior HYP-20/21 runs charged COST_HURDLE_BPS_LEG=45 (90 bps round-trip) as the
DECISION cost. That was a PROMPT ERROR — it priced the spread at a ~4–6× tail cost
(US-228 §44), not the real fee. The correct model (this run):

  * TAKER_FEE_BPS = 4.5 /leg            (execution_sim.py)
  * fee_source round-trip = 12 bps      (4.5*2 taker + 2.5 slip + 0.5 funding)
  * G3 fill model: maker fill_prob=0.35, adverse_selection_bps=1.5
      maker-blended per-leg = 0.35*(1.5+1.5) + 0.65*4.5 = 3.975 bps/side
      per-position round-trip = 2*3.975 + 2.5 + 0.5 = 10.95 bps

The spread is LONG top-decile + SHORT bottom-decile = 2 positions, so "both legs"
cost = 2 × per-position round-trip:

  | tier                 | both-legs bps | basis                                  |
  |----------------------|---------------|----------------------------------------|
  | G3 maker-blend       | 21.90         | fill_prob 0.35 + adverse 1.5 (sensitivity; passive fill NOT demonstrated) |
  | fee_source taker     | 24.00         | REALISTIC / DECISION (matches US-228 liquid ~20–28) |
  | conservative         | 32.00         | mid-cap all-taker (taker + 6 slip + 1 funding = 16/leg × 2) |

DECISION uses 24 bps. The 90 bps hurdle is retired as a data-grounded tail, not the
central cost.

---

## 1. C-positioning net @ correct cost (the numbers asked for)

| composite     | hold | gross/reb | net@maker(21.9) | net@fee_source(24) | net@conservative(32) | n_rebal |
|---------------|------|-----------|-----------------|--------------------|----------------------|---------|
| C-positioning | 1d   | +18.53    | -3.37           | -5.47              | -13.47               | 890     |
| C-positioning | 5d   | +72.27    | +50.37          | +48.27             | +40.27               | 886     |
| C-all (ctrl)  | 1d   | +12.04    | -9.86           | -11.96             | -19.96               | 890     |
| C-all (ctrl)  | 5d   | +34.30    | +12.40          | +10.30             | +2.30                | 886     |

C-positioning (no price) beats C-all at every hold — the added OI-level dimension
is the real driver (same structure as the prior run). At the CORRECT cost it is net
POSITIVE at 5d (and even at the 32 bps conservative tier, +40 bps). It is net
NEGATIVE at 1d. So after the cost correction, the signal that "should clear" is the
5d position.

---

## 2. G4 / G5 robustness (the decisive test)

Ran on the NET series at the decision cost (24 bps), using a NON-OVERLAPPING sample.
(Overlapping daily-rebalanced 5d returns — the prior report's n=886 — are
autocorrelated and inflate Sharpe/DSR; the honest OOS sample rebalances every 5 days:
n=178.)

| config | n_obs | splitPF med | splitPF P10 | G4 10th-pct PF>=1.0? | DSR | PBO | DSR>=0.95 / PBO<=0.30? |
|-----------------|-------|---------|--------|-----|-------|-------|-----|
| C-positioning 1d| 890   | 0.919   | 0.712  | FAIL (0.71) | 0.214 | 0.576 | FAIL |
| C-positioning 5d| 178   | 1.255   | 0.662  | FAIL (0.66) | 0.334 | 0.394 | FAIL |
| C-all 5d (ctrl) | 178   | 1.035   | 0.574  | FAIL (0.57) | 0.252 | 0.424 | FAIL |

Kill thresholds (HYP-21 frontmatter): G4 10th-pct PF >= 1.0 · G5 DSR >= 0.95 ·
PBO <= 0.30.

Best case (C-positioning 5d): 10th-pct split PF = 0.66 (< 1.0), DSR = 0.334
(< 0.95), PBO = 0.394 (> 0.30). ALL THREE fail. The 1d config is worse on every
axis and is net-negative on cost.

The non-overlapping 5d sample is the real picture: mean net ≈ +32 bps (phase-0
alignment; the overlapping headline +48 bps overstates it), std ≈ 503 bps,
Sharpe ≈ +0.064, win rate 48.9%. That is a coin-flip with a thin positive drift —
t-stat ≈ 0.85, nowhere near significance once the 130-trial multiple-testing
correction is applied.

---

## 3. Honest verdict

Does the cross-sectional OI-level edge survive robustness at the CORRECT cost? NO.

1. The COST correction was real and necessary — but it is not what kills the
   strategy. At the correct fee (24 bps both-legs, or even the 32 bps conservative
   tier), C-positioning is genuinely net-positive at 5d (+48 / +40 bps). The prior
   "fails at 90 bps" was an artifact of a wrong (≈4–6× too high) cost assumption.

2. The strategy dies in the NEXT layer, robustness. The gross +72 bps @5d is
   swamped by ~500 bps/rebalance of volatility: per-5d-rebalance Sharpe ≈ 0.064,
   win rate ~49%. After the proper non-overlapping resample (178 independent 5d
   rebalances) and the ledger multiple-testing deflation (N=132), the result is
   DSR 0.33 (need ≥ 0.95), PBO 0.39 (need ≤ 0.30), and a 10th-percentile
   cross-validation PF of 0.66 (need ≥ 1.0).

3. The overlap artifact is worth flagging explicitly: the prior headline "net +48
   bps @5d" was computed on DAILY-rebalanced overlapping 5d forward returns
   (n=886). Overlap does not bias the mean but it inflates the effective sample
   ~5× and therefore any t-stat/Sharpe/annualization treating the 886 records as
   independent trials. The honest non-overlapping 5d rebalance is n=178 with a
   mean of ~+32 bps and no statistical significance.

Kill rule FIRES on G4/G5. The cross-sectional OI-level positioning direction — the
one genuinely new, price-independent dimension the composite found — is real in
direction but too weak relative to its own noise to claim as a non-overfit edge at
the available sample (1260d × 235 coins). This closes multi-factor cross-sectional
positioning for now: the signal exists, but it does not clear the robustness bar.

No promotion. No paper-forward. LIVE off. This is a genuine in-sample + robustness
verdict, not a data-gate punt (OI full coverage; funding dropped for the already
documented tie-degeneracy; one cost model, one decision cost; no look-ahead).