---
id: STR-20260726-relative-strength-sector-rotation-entry
type: strategy
status: killed
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: relative-strength-breakout
confidence: low
publish_enabled: false
publish_channel: stocks
evidence_links:
  - RG032-3-to-1-reward-to-risk-ratio
  - RG037-use-protective-stops-to-limit-losses
last_reviewed: 2026-07-26
created: 2026-07-26
updated: 2026-07-26
tags: [strategy, hypothesis, relative-strength, sector-rotation, breakout, swing, killed]
topic: strategies
has_quotes: false
source: HermesForge Strategies
scanner_module: scanner_g_relative_strength

strategy_id: STR-G-relative-strength
---
# Relative-Strength / Sector-Rotation Breakout Entry

## Thesis

Stocks that begin outperforming the broader market (SPY) on a multi-week
basis, while simultaneously trading in their own absolute uptrend, tend to
continue outperforming — the "sector rotation" / relative-strength
principle popularized by IBD-style and O'Neil-style trend-following
practitioners. The strategy computes a relative-strength (RS) line as
`ticker_close / spy_close`, and looks for the RS line to break out above
its own 20-period moving average while its 20-bar rate-of-change is
positive (confirming the outperformance is a multi-week trend, not a
1-day blip). The signal is combined with an absolute trend filter
(ticker close above its own 50-period SMA) so that only tickers that are
*also* in a technical uptrend on their own chart are traded — combining
absolute and relative trend per conventional relative-strength/rotation
theory. A swing-low stop (10-bar low) anchors the risk, with a 2.5:1
reward:risk target.

## Entry Criteria

- [ ] **RS breakout:** RS line (`ticker_close / spy_close`) crosses above
  its own 20-period SMA today (RS was below RS_SMA20 yesterday, at/above
  it today).
- [ ] **RS momentum confirmation:** 20-bar RS rate-of-change
  (`RS[i]/RS[i-20] - 1`) > 0 — the RS line itself has been rising over
  the past month, confirming genuine multi-week outperformance vs. SPY.
- [ ] **Absolute trend filter:** Ticker's own close is above its own
  50-period SMA (only take RS breakouts in names that are also trending
  up on their own chart).
- [ ] **Data sufficiency:** Requires >= 50 bars of ticker history (SMA50
  warmup) and >= 40 bars of dates aligned with SPY (20 for RS_SMA20 +
  20 for RS_ROC lookback). Signals on SPY itself are skipped (RS vs. self
  is meaningless).
- [ ] **Entry price:** Close of the signal bar.

## Exit Criteria

- [ ] **Stop loss:** Low of the most recent 10 bars (swing-low stop),
  placed at the time of entry.
- [ ] **Take profit / target:** Entry + 2.5 × (entry − stop) — fixed
  2.5:1 reward:risk projection target.
- [ ] **Time stop:** Forward-scan exit simulation runs for a maximum of
  10 bars; if neither stop nor target is hit, exit at the close of bar 10.
- [ ] **Filter:** Signals where stop >= entry (zero/negative risk) are
  discarded pre-entry.

## Risk Rules Applied

- [ ] PS-001: Max 1% capital risk per position (stop distance × shares ≤ 1% capital) — not yet operationalized, Phase 1A backtest-only.
- [ ] RG032: Target R:R fixed at 2.5:1 by construction (below the standard 3:1 threshold, used here as the strategy-specific parameter under test).
- [ ] RG037: Use protective stops to limit losses — swing-low stop is mandatory, computed before entry.
- [ ] PT-001: Not applicable — strategy killed at Phase 1A, will not advance to paper trading.

## Graph Properties

produced_by:: [[Backtester]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
regime_node:: [[REGIME-trending]]
killed_by:: [[FAIL-STR-G-relative-strength]]
tested_in:: [[STR-G-phase1a]]

## Supporting Evidence

- [[RG032-3-to-1-reward-to-risk-ratio]] — General R:R discipline principle informing the 2.5:1 target design, even though realized R fell far short in backtest.
- [[RG037-use-protective-stops-to-limit-losses]] — Swing-low stop placement follows standard protective-stop practice.
- Conventional relative-strength / sector-rotation theory (IBD/O'Neil-style): stocks outperforming their benchmark while also trending up absolutely tend to continue outperforming. This is the core thesis under test; the Phase 1A backtest did **not** support it in its current parameterization.

## Counter-Evidence

- **Phase 1A backtest result (this run):** Average R-multiple of only
  0.105 across 8,830 signals (2019-06-11 → 2026-07-17), well below the
  0.2 kill threshold (ADR-004). The RS-crossover + RS-ROC + SMA50 filter
  combination generates an extremely high signal rate (~1,244/year across
  the 216-ticker universe) but with very low average edge per trade —
  consistent with a noisy, frequently-whipsawing crossover signal rather
  than a genuine, tradable inflection point.
- 60.3% of exits (`6,277 / 8,830`) hit the 10-bar time stop rather than
  target or stop, and only 5.6% (`491 / 8,830`) reached the 2.5:1 target,
  indicating the fixed 2.5:1 target is rarely achieved within the holding
  window — the edge, such as it is, comes from small median drift rather
  than clean directional continuation.
- Sub-period positivity check (bull/bear/current thirds) showed 0 of 3
  periods positive under the standard `SUBPERIODS` bucketing used by
  `run_phase1a.py` (note: this scanner emits quarter-based `subperiod`
  labels like `2024-Q1`, which do not match the `period1_bull` /
  `period2_bear` / `period3_current` labels the summarizer checks for —
  the same convention gap affects other quarter-labelling scanners in
  this repo, so the 0/3 figure should be read as "not measurable under
  the current bucketing" rather than a strict "always negative" finding;
  regardless, the average-R kill threshold was already breached
  independently).
- The extremely high signal count (an order of magnitude above the
  25 sig/yr pass threshold) combined with a razor-thin average edge
  suggests the RS-crossover condition alone is too easily triggered by
  short-term noise in the RS ratio; a stricter/slower breakout
  definition (e.g., longer SMA, RS at N-bar high, or a minimum RS_ROC
  magnitude threshold) would likely be needed to filter for higher-
  conviction rotations before this idea could be considered again.

## Backtest / Paper Trade Log

- **Backtest results (Phase 1A, run 2026-07-26):**
  - Universe: 216 cached tickers, SPY used as benchmark (excluded from own scan).
  - Total signals: **8,830**
  - Date range: 2019-06-11 → 2026-07-17 (~7.1 years)
  - Signals/year: **1,243.8**
  - Average R-multiple: **0.105**
  - Median R-multiple: **0.046**
  - Win rate (R > 0): **52.2%**
  - Exit breakdown: time 6,277 (71.1%) / stop 2,062 (23.4%) / target 491 (5.6%)
  - Sub-periods positive: **0 / 3** (using `run_phase1a.py`'s default `period1_bull`/`period2_bear`/`period3_current` buckets — not directly comparable to this scanner's quarter-label `subperiod` field; average-R kill criterion already independently triggered)
  - Friction flag: **⚠️ FLAGGED** (avg R 0.105 < 0.5 friction threshold — would not survive commission/slippage in Phase 1B even if it had passed Phase 1A)
  - **Classification per ADR-004: ❌ KILL** (signals/year 1,243.8 ≥ 12, but avg R 0.105 < 0.2 kill threshold — kill triggers on the avg-R leg alone)
  - Results CSV: `scripts/validation/results/STR-G-relative-strength-rotation-phase1a.csv`
- Paper trade log: _not applicable — strategy killed at Phase 1A, does not advance to paper trading._

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy created and Phase 1A backtested; killed due to avg R (0.105) below the 0.2 ADR-004 kill threshold despite high signal frequency (1,243.8/yr) | New strategy build — STR-G Relative-Strength / Sector-Rotation Breakout |
| 2026-07-26 | Phase 1B parameter sensitivity sweep run (see note below); status remains **killed** — no variant crossed the ADR-004 kill floor | Phase 1B rescue attempt on the closest-to-floor of the 3 killed strategies |

## Phase 1B Sensitivity Note (2026-07-26)

Because STR-G was the closest of the three newly-killed strategies to the
ADR-004 kill floor (avg R 0.105 vs. the 0.2 threshold) and was already
positive in all three date-bucketed sub-periods (`period1_bull` +0.095,
`period2_bear` +0.048, `period3_current` +0.148, using the correct
date-range bucketing rather than the scanner's quarter-label field), a
Phase 1B-style parameter sensitivity sweep was run to test whether tuning
the target, stop, and holding window could push it above the kill floor.
The sweep used a standalone script
(`scripts/validation/scanners/_phase1b_g_sweep.py`) that clones the exact
RS-crossover / RS-ROC / SMA50 entry logic from `scanner_g_relative_strength.py`
but parametrizes the target multiple, stop-lookback, max-hold, and adds two
optional stricter momentum/quality filters. It was run against the same
217-ticker cached parquet universe used by `run_phase1a.py`, with the
identical date-based `SUBPERIODS` bucketing prescribed by ADR-004.

**Rationale for variants:** The Phase 1A diagnostic showed only 5.6% of
trades hit the 2.5:1 target, 71.1% timed out at 10 bars (with a decent
+0.34 avg R there), and 23.4% hit the stop (-1.46 avg R). This suggested
(a) the target is set too far away to be reached often, (b) a wider stop
might reduce premature stop-outs from short-term noise, and (c) a longer
holding window might let more trades reach the more favorable price action
seen at the time-stop exit. A fourth variant tested whether restricting
entries to higher-conviction RS momentum (either a minimum ROC magnitude,
or requiring RS to be near the top of its own 60-bar range) could raise
average edge per trade even at the cost of frequency.

**Result: no variant cleared the KILL floor (avg R < 0.2 in every case).**
Full sensitivity table (same 217-ticker universe, ~7-year span, date-based
sub-period bucketing):

| Variant | Params (rr / stop / hold / roc_min / range-filter) | Sig/Yr | Avg R | Median R | Win Rate | Sub-Pos | Friction | ADR-004 |
|---|---|---|---|---|---|---|---|---|
| Baseline (repro) | 2.5 / 10 / 10 / — / — | 1250.5 | 0.101 | 0.054 | 52.6% | 3/3 | ⚠️ | KILL |
| V1: closer target | 1.5 / 10 / 10 / — / — | 1250.5 | 0.099 | 0.075 | 53.4% | 3/3 | ⚠️ | KILL |
| V2: V1 + wider stop (15-bar) | 1.5 / 15 / 10 / — / — | 1252.8 | 0.062 | 0.074 | 54.1% | 3/3 | ⚠️ | KILL |
| V3: V1+V2 + longer hold (15 bars) | 1.5 / 15 / 15 / — / — | 1252.8 | 0.087 | 0.096 | 53.9% | 3/3 | ⚠️ | KILL |
| V4a: V1+V2+V3 + RS_ROC > 0.02 | 1.5 / 15 / 15 / 0.02 / — | 686.5 | 0.071 | 0.080 | 53.3% | 3/3 | ⚠️ | KILL |
| V4b: V1+V2+V3 + RS in top 20% of 60-bar range | 1.5 / 15 / 15 / — / 0.8 | 482.7 | 0.121 | 0.136 | 55.6% | 3/3 | ⚠️ | KILL |
| X1 (exploratory): V1 only + range-filter(0.8), stop/hold left at baseline | 1.5 / 10 / 10 / — / 0.8 | 481.3 | 0.090 | 0.083 | 53.6% | 3/3 | ⚠️ | KILL |
| X2 (exploratory): baseline stop/hold + tighter range-filter(0.9) | 1.5 / 10 / 10 / — / 0.9 | 216.7 | 0.107 | 0.120 | 55.8% | 3/3 | ⚠️ | KILL |
| X3 (exploratory): rr=1.5 + range-filter(0.9) + RS_ROC>0.02 | 1.5 / 10 / 10 / 0.02 / 0.9 | 147.8 | 0.088 | 0.087 | 54.4% | 3/3 | ⚠️ | KILL |

All variants remained positive in all 3 date-based sub-periods (a mild
positive signal for robustness of direction), but none reached avg R
≥ 0.2. Notable observations:

- **Closer target (V1) barely moved the needle** (0.105 → 0.099): most
  trades still resolve at the time-stop rather than the target regardless
  of where the target is set, so shrinking the R:R multiple mostly
  redistributes which "winners" count as target-hits vs. time-stop, without
  meaningfully raising average edge.
- **Widening the stop (V2) made things worse** (0.099 → 0.062): a 15-bar
  swing low sits further below entry than a 10-bar low, increasing the risk
  denominator per trade and shrinking realized R-multiples on both winners
  and losers alike, while not materially reducing the raw stop-hit rate.
  This is the opposite of the hoped-for effect.
- **Longer hold (V3) partially offset V2's damage** (0.062 → 0.087) by
  letting more borderline trades resolve favorably, but not enough to
  recover even to baseline, let alone clear 0.2.
- **Quality filters (V4a, V4b) raised average R per trade the most**
  (up to 0.121 with the RS-top-of-range filter) but at a steep frequency
  cost (down to 482.7 sig/yr, still far above the 12/yr floor) — directly
  confirming the earlier diagnostic's hypothesis that a stricter momentum
  filter selects higher-quality setups. However, even the best-performing
  single change (V4b) only reached ~60% of the way to the 0.2 threshold.
- Exploratory runs (X1–X3) that isolated the range-filter from the
  stop/hold widening (which had proven net-negative) confirm the range
  filter alone, even tightened to the top 10% of the 60-bar range (X2:
  avg R 0.107, sig/yr 216.7), still falls short of 0.2.
- **period2_bear consistently showed the weakest edge** across all
  variants (avg R roughly +0.01 to +0.06 vs. +0.06 to +0.17 in the other
  two periods) — the RS-rotation signal has the least edge specifically
  during broad market drawdowns, even though it never turns net negative
  there.

**Conclusion:** Reasonable, targeted parameter tuning along all three axes
suggested in the diagnostic (target distance, stop width, holding period)
plus two additional momentum-quality filters were tested individually and
in combination (9 total configurations). None crossed the ADR-004 kill
floor of avg R ≥ 0.2. The core issue is structural, not parametric: the
RS-SMA20 crossover condition alone fires far too often (>1,200 signals/yr)
on short-term noise in the RS ratio rather than genuine multi-week
rotations, and no combination of exit-side tuning (target/stop/hold) can
compensate for a large volume of low-conviction entries. The
highest-average-R configurations found (V4b, X2) required restricting to
a genuine RS-momentum-quality subset of entries, which is a more
fundamental change to the entry logic than "Phase 1B parameter
sensitivity" — a true fix would require a different entry filter design
(e.g., minimum multi-week RS persistence, sector-relative ranking, or a
slower/less noisy crossover definition), which is out of scope for this
sweep. **Status remains `killed`; no production variant was created.**

Standalone sweep script (not registered in `run_phase1a.py`, does not
affect the killed baseline scanner): `scripts/validation/scanners/_phase1b_g_sweep.py`

