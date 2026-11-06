# HYP-21 (multi-factor cross-sectional positioning composite) — verdict

Date: 2026-11-06 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-21-multifactor-cross-sectional.md (pre-registered, factors + composites FIXED, no tuning)
Driver: scripts/gauntlet/revalidate_hyp21_multifactor_composite.py
Trials: data/gauntlet/trials.jsonl (HYP-21 x2: C-positioning 6c40e3f8…, C-all 4da7510f…; chain verified OK)

VERDICT: the composite of independent positioning dimensions materially
strengthens the gross edge (there IS a real additional dimension), but it still
does NOT clear the pre-registered 45bps both-legs (90bps round-trip) hurdle at
any holding. Kill rule FIRES.

---

## 0. Data & factors (read first)

- OI: /root/.hermes/market_data/hl_oi_hf/*.parquet, native perps (dex == ''),
  235 coins, 1261 daily bars (2023-05-20 -> 2026-10-31). Daily resample:
  OI = last hourly OI, close = last mark, open = first mark.
- Funding (factor 3): DROPPED. The HL funding store is still degenerate —
  57.4% of all (coin,day) funding cells sit at the modal/default rate 0.00001250/hr
  (HL's 0.01%/8h baseline). Cross-sectional funding rank is therefore tie-dominated
  (same finding as HYP-20 §3). Per pre-registration, the composite is reported
  WITHOUT funding and this is noted honestly.

Pre-registered factors (each cross-sectionally z-scored DAILY):
1. OI-change = trailing 7d OI log change.
2. OI-level = OI vs its own trailing 90d mean (time-series z, prior-90d
   baseline excluding the current day), then cross-sectionally z-scored.
3. Funding — dropped (tie degeneracy).
4. Price-momentum = trailing 7d price log change (CONTROL).

Composites (equal-weight z-sum): C-positioning = z(OI-change)+z(OI-level);
C-all = C-positioning + z(price-momentum).

Cost model (single owner = fee_source + pre-registered hurdle, charged once):
- Hurdle: 45bps fail-closed taker PER LEG x2 = 90bps round-trip.
- Realistic cross-check: fee_source round-trip 12bps/leg x2 = 24bps round-trip.

Fill: next-open both sides (signal at close[t] -> enter open[t+1]; exit
open[t+1+hold]). No look-ahead. ±1x long/short, no leverage. LIVE off.
Reconcile total R == by-trade R verified True in every config.

---

## 1. Per-factor attribution (the decisive table)

Gross spread / rebalance, long top-decile minus short bottom-decile:

| factor | hold | gross/reb | net@90bps | net@24bps | n |
|---|---|---|---|---|---|
| OI-change (7d) | 1d | +11.54 | -78.46 | -12.46 | 1237 |
| OI-change (7d) | 5d | +2.47 | -87.53 | -21.53 | 1233 |
| OI-level (90d) | 1d | +9.50 | -80.50 | -14.50 | 890 |
| OI-level (90d) | 5d | +40.58 | -49.42 | +16.58 | 886 |
| price-mom (7d) | 1d | +11.56 | -78.44 | -12.44 | 1240 |
| price-mom (7d) | 5d | -0.38 | -90.38 | -24.38 | 1236 |

Key structure:
- OI-change is the STRONG but FAST signal HYP-20 already found: +11.5 bps @1d,
  decays to +2.5 bps @5d.
- OI-level is a NEW, SLOW, PERSISTENT signal: it does not decay at 5d — it
  ACCUMULATES (+9.5 @1d -> +40.6 @5d). The 90d-window z-score is a slow-moving
  cross-sectional rank, so decile membership is stable and the positioning
  effect compounds over the holding window.
- Price-momentum (control) is +11.6 @1d but reverses to -0.4 @5d — it adds
  nothing durable and its 5d gross is essentially zero.

---

## 2. Composites (both pre-committed, reported separately)

| composite | hold | gross/reb | net@90bps | net@24bps | sharpe | n | recon |
|---|---|---|---|---|---|---|---|
| C-positioning | 1d | +18.53 | -71.47 | -5.47 | -0.283 | 890 | True |
| C-positioning | 5d | +72.27 | -17.73 | +48.27 | -0.032 | 886 | True |
| C-all | 1d | +12.04 | -77.96 | -11.96 | -0.261 | 890 | True |
| C-all | 5d | +34.30 | -55.70 | +10.30 | -0.090 | 886 | True |

C-positioning (OI-change + OI-level), no price: gross nearly doubles the single
OI factor at 1d (+18.5 vs +11.5), and at 5d hold gross is +72.3 bps/reb (vs +2.5
for OI-change alone). It clears the REALISTIC 24bps cost at 5d hold (+48.3 net)
but NOT the 90bps hurdle (-17.7 net).

C-all (adds price momentum): WORSE at both holds. Adding the control factor
dilutes the positioning composite (1d gross drops +18.5 -> +12.0; 5d gross drops
+72.3 -> +34.3). Price momentum is near-orthogonal (+0.10 corr with OI-level,
+0.13 with OI-change) but carries an independent ~zero-5d-mean, so mixing it in
only adds noise.

---

## 3. Per-factor contribution — where does the composite edge come from?

Answer is unambiguous: the composite edge comes from the NEW positioning
dimension (OI-level), NOT from re-introducing price momentum.

1. OI-level is the marginal contributor that moves C-positioning from the weak
   +2.5 bps @5d (OI-change alone) to +72.3 bps @5d. It is a slow, persistent,
   positive-gross signal that the fast OI-change factor lacked.
2. Price momentum, which xsmom already failed, is a CONTROL here — and it
   DEGRADES the composite (C-all < C-positioning at every hold). The composite
   is not a disguised bet on price momentum; if anything, price momentum is the
   component we should NOT add.
3. Cross-sectional correlation OI-change vs OI-level = +0.55 (they overlap
   partially — both are "positioning" views), OI-level vs price-mom = +0.10.
   OI-level is ~orthogonal to price and is the genuinely new dimension.

---

## 4. Honest verdict

Does a multi-factor cross-sectional composite clear cost where the single OI
factor (+11-13 bps) could not? — NOT AT THE PRE-REGISTERED HURDLE.

1. The composite DOES find a materially stronger gross edge: the added OI-level
   dimension is real, persistent, price-independent, and lifts gross from
   ~+11.5 bps (1d single factor) to +18.5 bps (1d) and +72.3 bps (5d) for
   C-positioning.
2. It clears the REALISTIC 24bps both-legs cost at 5d hold (+48.3 bps/reb net)
   — the first time any cross-sectional positioning config is net-positive at a
   realistic cost.
3. It does NOT clear the pre-registered 45bps both-legs (90bps round-trip)
   conservative hurdle: best case is C-positioning @5d at -17.7 bps/reb net.
   Every config is net-negative at 90bps.

Kill rule FIRES (first clause): "neither composite produces a top-minus-bottom
spread positive net of 45bps both-legs fail-closed taker." Since the net @
90bps is negative for BOTH composites at BOTH holds, the G4/G5 (CPCV/PBO/DSR)
escalation is not reached under the pre-registered rule — it only escalates when
net R > 0 at the hurdle.

The binding constraint remains turnover cost, not signal. OI-level is a genuine
new, persistent positioning dimension (this closes the "is there anything else
in cross-sectional positioning" question: yes, there is a slow crowding factor),
but even a composite of it does not clear the conservative 90bps round-trip
hurdle on a daily-rebalanced spread.

No promotion. No paper-forward. LIVE off. Report is a genuine in-sample verdict,
not a data-gate punt (OI 1260d x 235 coins full coverage; funding dropped for
documented tie-degeneracy, not for a missing store).