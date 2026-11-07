# HYP-25 — short-side continuation, gated on shortability — verdict

Date: 2026-11-07 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-25-short-side-continuation.md (pre-registered, FIXED — no tuning)
Driver: scripts/gauntlet/revalidate_hyp25_short_continuation.py
Trials: data/gauntlet/trials.jsonl (HYP-25, param_hash f90fb4… full / b1de81… liquid)

VERDICT: THE SHORT-THE-LOSERS EDGE SURVIVES THE SHORTABILITY FLOOR + REALISTIC
FILLS + FUNDING. It is NOT a geometry-of-dying-coins artifact. The +0.20R
control-beating edge is essentially UNCHANGED when restricted to liquid,
actually-shortable names — it even improves slightly.

---

## 0. What was tested

Cross-sectional 7d price momentum, SHORT ONlY the bottom-decile (losers).
Stop = 2x ATR14 (=1R); target = 3R (fixed); HOURLY first-touch resolution.
Cost = 4.5 bps/leg taker (2 legs, charged ONCE as round-trip) + 2.5 bps adverse
entry slip + hourly funding (shorts PAY when funding<0, receive when >0).
235 native HL perps, 2023-05-20 -> 2026-10-31.

Shortability floor: trailing 7d MEAN of daily last open_interest_usd at signal
time t (no look-ahead). A coin is "shortable" only above the floor. Primary
floor = $250k (matches the repo's MIN_DAILY_NOTIONAL_USD liquidity convention);
$100k/$500k/$1m reported as transparent sensitivity brackets.

A zero-drift synthetic control (per-coin hourly log-returns demeaned, re-anchored
at each trade's REAL entry — identical entries/ATR/fees/funding, only forward
drift removed) runs ALONGSIDE. alpha = real - control, discounting log-normal
geometric tilt.

## 1. The core comparison (the crux)

| universe              | n_real | REAL net R | CTRL net R | alpha (real-ctrl) |
|-----------------------|-------:|-----------:|-----------:|------------------:|
| FULL bottom-decile    | 16,199 | +0.1087    | -0.0923    | **+0.2010**       |
| LIQUID (OI >= $250k)  | 13,447 | +0.1278    | -0.0812    | **+0.2090**       |

The answer is unambiguous: the edge does NOT live on the illiquid/dying tail.
Restricting to shortable names does not erode the control-beating edge — alpha
is +0.2010R (full) vs +0.2090R (liquid), and the REAL net R actually RISES
(+0.1087 -> +0.1278R) once the un-shortable tail is removed.

The full run reproduces HYP-24's leg decomposition exactly (SHORT +0.109R net,
+0.201R alpha vs the control's -0.092R geometric tilt), confirming the driver.

## 2. Sensitivity brackets (trailing OI floor)

| floor      | n_real | REAL net R | CTRL net R | alpha   |
|-----------:|-------:|-----------:|-----------:|--------:|
| $100k      | 14,721 | +0.1205    | -0.0871    | +0.2076  |
| $250k (P)  | 13,447 | +0.1278    | -0.0812    | +0.2090  |
| $500k      | 11,403 | +0.1327    | -0.0707    | +0.2035  |
| $1m        |  9,160 | +0.1352    | -0.0439    | +0.1791  |

Alpha is stable (+0.18 to +0.21R) across a 10x floor range. The REAL net R is
monotone-rising with the floor (more liquid -> better net). The edge is not an
artifact of the OI tail.

## 3. G3 fill-realism (post-floor liquid short leg)

n = 13,447. optimistic +0.1430R / realistic +0.1358R / pessimistic PF 1.315 /
edge-decay 0.950. PASSED — the edge survives a full extra adverse exit leg
(worst-print stop stand-in). Realistic keeps 95% of the optimistic edge.

## 4. Funding

Shorts PAY funding when funding<0, and the liquid leg's mean funding is
-0.0080R (full: -0.0012R) — funding is a NET COST for shorting losers, because
these names more often print negative funding (spot-shorted crowded losers), and
it is ALREADY netted into every number above. The edge is positive DESPITE
paying funding. (2023 funding was net-positive for shorts +0.134R; by 2026 it
has flipped to -0.030R, a real deteriorating cost to shorting losers.)

## 5. Sub-period robustness (LIQUID short leg, REAL net R by year)

| year | n     | mean net R |
|------|------:|-----------:|
| 2023 |   120 | +0.1245    |
| 2024 | 3,301 | +0.1049    |
| 2025 | 5,554 | +0.1874    |
| 2026 | 4,472 | +0.0710    |

Positive every year, no sign flips. BUT it peaks in 2025 and decays to +0.071R
by 2026 — the same decaying trend HYP-24 flagged on the short leg. The edge
survives the shortability gates here, but is NOT obviously stationary; a live
forward paper must treat 2026's +0.07R (not 2025's +0.19R) as the honest
forward prior.

## 6. Verdict

Pre-registered falsification: "if +0.20R vanishes when restricted to
liquid/shortable names, close short-continuation as un-harvestable." It does NOT
vanish — it survives the $250k floor, a 10x floor-range sweep, full funding
(shorts paying), and a pessimistic-fill G3 add-on.

=> SHORT-THE-LOSERS IS A REAL, TRADEABLE-ON-LIQUID-NAMES EDGE, not a
geometry-of-dying-coins artifact.

Caveats that bound promotion (G4/G5 territory, NOT re-tested here):
  1. Declining magnitude (2025 +0.19R -> 2026 +0.07R); not stationary.
  2. Funding has rotated from a tailwind to a headwind for shorts (-0.03R in 2026).
  3. Edge is one-sided short-only: no long leg to diversify drawdowns, and
     shorting losers has unbounded adverse tail (squeeze/delist/relist risk)
     which a 2xATR stop only partially bounds.
  4. No leverage beyond -1x; live off (unchanged).

This HYP-25 pass confirms the short leg is harvestable-in-principle on liquid
names; it does NOT clear the decaying-magnitude / robustness gates. Promotion
would require a walk-forward / CPCV robustness pass (future G4/G5), with 2026's
+0.07R as the forward prior, and a live-paper forward.