# US-06 — Power Calibration (M-4) + MDE Reporting (M-5) — Findings

Date: 2026-11-09 (UTC)
Owner: coder (HermesForge swarm)
Files:
- scripts/gauntlet/power_calibration.py  (M-4 harness)
- scripts/gauntlet/mde.py                (M-5 MDE helper)
- scripts/gauntlet/cpcv_harness.py        (M-5 wiring: run_cpcv now returns MDE)
- scripts/gauntlet/tests/test_mde.py       (9 tests)

Addresses the critical review's core critique — "statistical power was never
measured," so nulls may reflect under-powered tests rather than no edge.

---

## 1. What was built

M-4 — a reusable power-calibration harness that injects synthetic edges of KNOWN
strength into REAL Hyperliquid 6h price data, charges realistic taker round-trip
cost (fee_source), runs each through the EXISTING gate evaluators (G0 cost
screen, G1 power, G3 fill-realism, G4 CPCV, G5 DSR/PBO, G6 regime), and records
pass rates across a Monte Carlo of edge realizations. Re-run annually or after
any gate change: `python3 scripts/gauntlet/power_calibration.py`.

M-5 — an MDE helper (`mde.py`) plus wiring so `cpcv_harness.run_cpcv` (the G5
chokepoint) now emits `mde_sharpe_dsr` / `mde_sharpe_single` / `n_observations`
/ `n_trials`. The helper exposes `format_null_verdict()` so future nulls are
reported as "not detected above MDE X," never "no edge."

## 2. MDE worked example (M-5)

At n=300 non-overlapping trades and n_trials=168 (current trials-ledger N):

| quantity | value |
|---|---|
| MDE Sharpe, single hypothesis (no search) | 0.162 |
| MDE Sharpe, DSR-deflated (G5 gate)       | 0.635 |
| MDE IC, breadth=1                          | 0.162 |
| MDE IC, breadth=30 (cross-sectional)       | 0.029 |

The search deflation (168 prior trials) raises the detectable Sharpe by ~4×
(0.16 → 0.64). Any future null below Sharpe 0.64 must be reported as "not
detected above MDE Sharpe = 0.64 at n=300 / 168 trials," not "no edge."

## 3. Power-calibration pass-rate table (200 seeds/edge)

Real data: BTC 6h closes (1668 bars). 300 non-overlapping trades/run. Round-trip
cost 12.0 bps = 0.120 R at a 1% stop; sigma_R = 1.0.

G0 (real data, deterministic pre-condition): median |move| 48.7 bps vs needed
54.0 bps → FAIL. Even BTC's 6h median move does not clear G0's 4× all-in-cost
hurdle (13.5 bps all-in × 4 = 54 bps) — consistent with the prior finding that
"cost, not signal, is the binding constraint."

```
injected edge          net R/trade    ALL     G1     G3     G4    DSR    PBO     G6
----------------------------------------------------------------------------------------
Sharpe 0.0 (null ctrl)      -0.120   0.00   0.00   0.00   0.00   0.00   0.00   0.00
Sharpe 0.5                  +0.380   0.00   1.00   1.00   0.99   0.00   0.01   0.98
Sharpe 1.0                  +0.880   0.01   1.00   1.00   1.00   1.00   0.01   1.00
Sharpe 1.5                  +1.380   0.01   1.00   1.00   1.00   1.00   0.01   1.00
IC 0.01                     -0.112   0.00   0.00   0.00   0.00   0.00   0.01   0.00
IC 0.02                     -0.104   0.00   0.00   0.00   0.00   0.00   0.01   0.00
IC 0.04                     -0.088   0.00   0.00   0.00   0.00   0.00   0.01   0.00
```

Mean DSR / PBO per edge (200 seeds): Sharpe-0.0 DSR=0.15 PBO=0.50 · Sharpe-0.5
DSR=0.80 PBO=0.50 · Sharpe-1.0 DSR=1.00 PBO=0.50 · Sharpe-1.5 DSR=1.00 PBO=0.50
· IC edges DSR≈0.16 PBO≈0.51.

## 4. Findings — the miscalibration check the task asked for

**Trigger condition met: a Sharpe-1.0 edge is effectively never detected
(ALL pass rate ≈ 0.5%).** The thresholds are miscalibrated for this account
size. Root cause is specific and actionable:

1. **G5 PBO sub-gate is a rank-scatter artifact for SINGLE strategies.** PBO is
   pinned near 0.50 for EVERY edge, including the null control AND Sharpe-1.5
   (which is DSR=1.0 and 10th-pct-PF>1.0). `cpcv_harness.compute_pbo` compares
   adjacent CPCV-fold Sharpes of ONE strategy; a stationary edge scatters fold
   Sharpes randomly, so ~half the adjacent pairs "regress," giving PBO≈0.5. The
   ≤0.30 threshold is therefore unreachable for single-strategy evaluation, and
   every candidate fails G5 on PBO regardless of true edge strength. This is a
   gate-IMPLEMENTATION defect, not a threshold choice — and it matches the
   observed real-world record (every HYP report shows PBO 0.39–0.52, all FAIL).

2. **G5 DSR discriminates correctly but strictly:** it detects Sharpe-1.0/1.5
   (100%) and rejects Sharpe-0.5 (0%). DSR ≥ 0.95 deflated by N=168 pushes the
   detection floor to ~Sharpe 0.64, so a still-strong +0.38R/trade edge sits
   below the MDE. DSR's computed MDE (0.635) is internally consistent with this
   observed boundary, validating both the harness and the helper.

3. **IC edges are uneconomic, not merely under-powered:** at breadth=1 the
   gross edge of IC 0.04 is ~0.032 R/trade before the 0.12R cost drag — already
   net-negative. IC 0.01–0.04 cannot clear cost at $10K single-signal, so G1/G3
   reject them by construction (correctly). Detection would require
   cross-sectional breadth: MDE IC = 0.029 at breadth=30.

4. **False-positive control is clean:** the null control passes 0% (>5% would
   flag overly-loose thresholds). No over-looseness evident.

## 5. Recommendations (documented here; NOT implemented — per US-06 scope)

1. **Repair or retire the single-strategy PBO approximation before trusting any
   G5 PBO verdict.** Apply PBO only when ranking AMONG multiple configurations
   (its intended use, per the compute_pbo docstring), or replace the
   adjacent-fold-Sharpe comparison with a proper IS-vs-OOS configuration-rank
   distribution. Until then, treat PBO≤0.30 as uninformative for single
   strategies and do NOT use it as a kill signal.
2. **Reconsider the DSR≥0.95 threshold.** At n=300 / 168 trials it rejects a
   +0.38R/trade edge. If a Sharpe-0.5 edge is economically material at $10K,
   either lower the DSR threshold or (better) cap the effective search N used
   for deflation to the number of genuinely independent strategy families, not
   all 168 ledger rows.
3. **Re-examine G0 at the 6h horizon.** BTC's median 6h move (48.7 bps) fails
   the 4× hurdle (54 bps); a 4× multiplier may be too strict for 6h, or the
   funding-overhead constant (2.0 bps vs fee_source's 0.5 bps) inflates the
   all-in cost. Investigate before changing.

## 6. Re-run cadence

`python3 scripts/gauntlet/power_calibration.py` (full, 200 seeds) annually or
after ANY change to a gate threshold / cost model / trials count. `--quick`
(30 seeds) for smoke tests; `--json` for machine-readable output.
