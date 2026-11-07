# HYP-26 — forced liquidation flow -> subsequent return — verdict

Date: 2026-11-07 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-26-liquidation-flow-cascade.md (pre-registered, FIXED — no tuning)
Driver: scripts/gauntlet/backtest_hyp26_liquidation_flow.py
Trials: data/gauntlet/trials.jsonl (HYP-26, 4 entries, fresh param_hashes)

VERDICT: THE CASCADE (H1 continuation) IS FALSIFIED; the exhaustion/reversal arm
(H2) is the winning direction — and even it does NOT survive cost at a daily
tradeable horizon. The raw rank-IC is NEGATIVE (reversal) but economically
negligible (|IC| ~ 0.02). The single net-positive cell (H2 reversal, 5d) clears
realistic cost only marginally (+45 bps/reb, Sharpe 0.10) and FAILS the
fail-closed G0 hurdle (-21 bps/reb) and the 4x gross-capture standard. Forced
liquidation flow is real-but-fast: testable on real data for the first time, but
NOT harvestable daily.

---

## 0. What was tested

First measurement of a genuinely NEW structural data class: tick-level forced
liquidation fills (8.06M fills, 2.85M events, 2025-05-25 -> 2026-10-31). A
long-liquidation is CLOSED by sells (downward pressure); a short-liquidation by
buys (upward). Signal = daily per-market net flow = (forced-buy notional
- forced-sell notional), cross-sectionally ranked so large books don't dominate.

Two PRE-REGISTERED arms (direction READ, not assumed):
  * H1 continuation (cascade): net-flow rank predicts SAME-sign forward return.
  * H2 reversal   (exhaustion): net-flow rank predicts OPPOSITE-sign.

Universe: native HL perps (dex == ''), liquidity floor = trailing 7d mean daily
last open_interest_usd >= $250k (repo MIN_DAILY_NOTIONAL_USD), measured at
signal time t (no look-ahead). ~165 liquid coins/day.

Fill: next-open entry (open[t+1]), exit open[t+1+hold]. Signal consumes only
day-t fills/OI, entry is after midnight -> strictly no look-ahead (fills run to
~23:30Z; a close-to-close return would leak the 23:00-23:30 fill window).

Horizon: 1d and 5d, NON-OVERLAPPING (rebalance every `hold` days). 1d = 523
rebalances; 5d = 104 rebalances.

Cost: realistic fee_source crypto round-trip (4.5 bps/leg taker x2 + 2.5 bps
adverse slip + 0.5 bps funding = 12 bps/position), charged ONCE per rebalance to
BOTH legs of the ±1x spread = 24 bps/rebalance. A fail-closed 4x hurdle
(45 bps/leg x2 = 90 bps/rebalance) reported separately as the G0 cross-check.
No leverage beyond ±1x. LIVE off.

IMPORTANT boundary: liquidation data only exists from 2025-05-25, so the
measurable window is 2025-05-25 -> 2026-10-31 (~525 days, ~1.4 years). Before
that, net flow is STRUCTURALLY zero (no data), not "measured zero", so pre-fill
OI history is excluded — a data-availability boundary, not a tuning choice. This
is a short, single-regime sample and a further reason not to promote.

---

## 1. The raw predictive relationship (honest, cost-free)

Cross-sectional Spearman rank-IC of net flow vs forward return (and Pearson IC
on raw dollars, to catch size/geometric artifacts):

| horizon | n_days | n_coins/day | Spearman IC (t)   | Pearson IC (t)  |
|--------:|-------:|------------:|------------------:|----------------:|
| 1d      | 523    | 165         | -0.0157 (t -3.16) | -0.0006 (t -0.18) |
| 5d      | 519    | 165         | -0.0201 (t -4.09) | -0.0012 (t -0.41) |

Sign: NEGATIVE = REVERSAL (H2). High net flow (forced buying, short squeezes)
predicts LOWER subsequent return; low net flow (forced selling, long cascades)
predicts HIGHER return. This is the exhaustion/"long-squeeze bottom" thesis, NOT
cascade continuation. The direction is statistically reliable (t ~ -3 to -4,
large N), BUT the magnitude is economically negligible (|IC| ~ 0.02). ~57% of
days have negative IC.

The Pearson IC on raw notional is ~0 — the signal exists only in the RANK
(monotone, robust to BTC/ETH tail), confirming the pre-registered choice to rank.

Where does the signal live? A decomposition of the cross-section:
  * nonzero-flow-only IC (magnitude among coins that actually liquidated):
    -0.0248 (1d, t -3.48) / -0.0266 (5d, t -4.05).
  * binary "any liquidation today vs none" IC (event presence):
    -0.0130 (1d, t -2.67) / -0.0043 (5d, t -0.91).

So the reversal is carried primarily by flow MAGNITUDE (not merely "had an
event"), and the event-only effect decays to ~zero by 5d while the magnitude
effect persists. A genuine — but tiny — monotone reversal relationship.

---

## 2. Traded net multi-R per arm per horizon

| arm               | horizon | n_rebal | gross bps/reb | net@24bps bps/reb | multi-R (net) | net@90bps hurdle | Sharpe | win |
|-------------------|--------:|--------:|--------------:|------------------:|--------------:|-----------------:|-------:|----:|
| H1 continuation   | 1d      | 523     | -14.69        | -38.69            | -2.023        | -104.69          | -0.162 | 0.440 |
| H2 reversal       | 1d      | 523     | +14.69        | -9.31             | -0.487        | -75.31           | -0.039 | 0.474 |
| H1 continuation   | 5d      | 104     | -69.29        | -93.29            | -0.970        | -159.29          | -0.214 | 0.404 |
| H2 reversal       | 5d      | 104     | +69.29        | +45.29            | +0.471        | -20.71           | +0.104 | 0.558 |

Leg decomposition (the two decile means, direction-agnostic):
  * 1d: high-flow decile -21.34 bps/day, low-flow decile -6.66 bps/day.
  * 5d: high-flow decile -130.56 bps,  low-flow decile -61.27 bps.

Both deciles are NEGATIVE on average over 2025-05 -> 2026-10 (a bear/sideways
alt regime); the dollar-neutral spread cancels the common drift. H1 (buy high-
flow, short low-flow) loses because high-flow coins fall faster than low-flow —
the continuation thesis is wrong in the sign that matters.

Only ONE cell is net-positive: H2 reversal at 5d, +45 bps/rebalance net at
realistic cost (+0.47 multi-R over 104 rebalances / ~1.4 years). But:
  * Sharpe 0.104 — negligible.
  * net@fail-closed 90bps hurdle = -20.7 bps/rebalance (NEGATIVE).
  * gross (69.3 bps) is below 4x realistic all-in (4 x 24 = 96 bps) — fails the
    G0 4x gross-capture standard.
  * Driver is a rank-IC of -0.02 — razor-thin, would not survive realistic
    adverse selection, capacity, or day-scaled funding modeling.

---

## 3. Honest verdict

The cascade is REAL-BUT-FAST and UNHARVESTABLE at a daily tradeable horizon:

  1. Direction: reversal/exhaustion (H2) dominates — continuation (H1) is
     falsified outright (its gross is negative in the continuation direction).
  2. Magnitude: the underlying rank-IC is ~-0.02 (t ~ -3.5), economically
     negligible. The "statistical significance" is an artifact of N (~520 days),
     not of tradeable edge.
  3. Cost survival: NO arm clears cost robustly. H2-5d is the best cell and it
     nets +45 bps/reb only at the realistic (not fail-closed) cost, with Sharpe
     0.10; it fails BOTH the 90 bps fail-closed hurdle and the G0 4x
     gross-capture standard (69 bps gross < 96 bps = 4x realistic all-in).

Would the winning arm clear the G0 cost hurdle? NO. H2-reversal-5d gross
(69.3 bps/reb) is ~2.9x the realistic all-in cost (24 bps), short of the 4x
threshold; against the conservative 90 bps hurdle it is deeply negative.

=> The forced-flow class is TESTED-AND-NULL at a tradeable horizon. The first
honest measurement on real liquidation data confirms the prior stated in the
hypothesis: the cascade/exhaustion structure is real but completes intraday-to-
multi-day and is already largely priced by the time a daily-rebalanced strategy
can act. No promotion; no G4/G5 robustness pass is warranted. The data class is
retained (it is clean and usable), but the daily-horizon signal does not clear
the bar.

Pre-registered falsification (hypothesis §Falsification): "If neither arm clears
net-of-cost, the forced-flow class is tested-and-null at tradeable horizon."
Neither arm clears net-of-cost at a robust standard -> the hypothesis is FALSIFIED
as a tradeable source, exactly as its own prior anticipated.

Caveats that bound even the null reading:
  1. Sample is ~1.4 years, one regime (bear/sideways alts), 104 non-overlapping
     5d rebalances only — thin for a structural claim in EITHER direction.
  2. Funding is a flat 0.5 bps/round-trip overhead; a day-scaled funding pass
     would only make the marginal H2-5d cell worse.
  3. The reversal signal is monotone-rank (Pearson on raw dollars ~0), so any
     capacity/execution assumption that degrades the rank distribution erases it.
  4. Intraday cascade (sub-daily) was NOT tested — the hypothesis's "real-but-
     fast" thesis says the harvestable part lives < 1d, which is outside this
     pre-registered daily operationalization and would need tick-level execution
     (a different, harder test).