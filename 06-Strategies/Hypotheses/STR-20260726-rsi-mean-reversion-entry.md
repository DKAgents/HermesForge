---
id: STR-20260726-rsi-mean-reversion-entry
type: strategy
status: killed
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: ranging
core_idea: reversal
confidence: low
publish_enabled: false
publish_channel: stocks
evidence_links:
  - RG032-3-to-1-reward-to-risk-ratio
  - RG037-use-protective-stops-to-limit-losses
last_reviewed: 2026-07-26
created: 2026-07-26
updated: 2026-07-26
tags: [strategy, hypothesis, rsi, mean-reversion, killed, phase1a]
topic: strategies
has_quotes: false
source: HermesForge Strategies
scanner_module: scanner_h_rsi

strategy_id: STR-H-rsi-mean-reversion
---
# RSI Mean-Reversion at Extremes

## Thesis

RSI(14) readings above 70 or below 30 identify statistical price extremes. Rather than fading the extreme itself (which risks catching a falling knife or fighting a strong trend), this strategy waits for RSI to *cross back through* the 30/70 threshold — RSI crossing up through 30 confirms an oversold bounce is already underway (long), and RSI crossing down through 70 confirms overbought momentum is fading (short). The entry trigger is deliberately lagged relative to the raw extreme to filter out continued momentum moves. Stops are anchored to the signal bar's high/low plus a small ATR buffer for noise, and targets project either 2R or the distance to the 20-period SMA (whichever is farther), assuming price reverts toward its short-term mean.

## Entry Criteria

- [ ] **RSI(14) computed with Wilder's smoothing** on daily close.
- [ ] **LONG signal:** RSI(14) crosses up through 30 (previous bar RSI < 30, current bar RSI >= 30).
- [ ] **SHORT signal:** RSI(14) crosses down through 70 (previous bar RSI > 70, current bar RSI <= 70).
- [ ] **Entry price:** close of the signal bar.
- [ ] **R:R filter:** skip trade if reward/risk < 2.0.
- [ ] **Zero-range filter:** skip if stop == entry.

## Exit Criteria

- [ ] **Stop loss (long):** low of signal bar − 0.25 × ATR(14).
- [ ] **Stop loss (short):** high of signal bar + 0.25 × ATR(14).
- [ ] **Target:** risk = |entry − stop|; reward = max(2 × risk, |SMA20 − entry|); target = entry ± reward (sign per direction).
- [ ] **Time stop:** exit after 8 trading bars if neither target nor stop is hit, at the close of the 8th bar.
- [ ] **Exit priority in simulation:** target/stop checked each forward bar on daily close (long: target when close ≥ target, stop when close ≤ stop; short: mirrored).

## Risk Rules Applied

- [ ] PS-001: Max 1% capital risk per position (stop distance × shares ≤ 1% capital)
- [ ] RG032: Minimum 2:1 R:R enforced at signal generation (relaxed from standard 3:1 for this mean-reversion test, per spec)
- [ ] RG037: Protective stop is mandatory on every signal (ATR-buffered beyond signal bar extreme)
- [ ] PT-001: Paper mode minimum 30 days before live consideration — **N/A, strategy killed in Phase 1A, will not advance to paper trading**

## Graph Properties

produced_by:: [[Backtester]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
regime_node:: [[REGIME-trending]]
killed_by:: [[FAIL-STR-E-rsi-mean-reversion]]
tested_in:: [[STR-E-phase1a]]

## Supporting Evidence

- [[RG032-3-to-1-reward-to-risk-ratio]] — General principle that adequate R:R must be enforced before entry (this strategy used a relaxed 2:1 floor per spec, contributing to the weak realised edge)
- [[RG037-use-protective-stops-to-limit-losses]] — Protective stop is mandatory; applied here as signal-bar extreme + ATR buffer

## Counter-Evidence

- Phase 1A backtest shows **negative average R (-0.056)** and a **40.6% win rate** — the crossover-confirmation entry did not produce a statistical edge across the 216-ticker universe (2019-2026).
- **0 of 3 sub-periods positive** — the strategy lost money in every evaluated sub-period bucket, indicating the negative edge is not confined to one regime (e.g., 2022 bear market) but is structural to the entry logic itself.
- Short signals (7,861 of 12,042, ~65%) dominated over longs (4,181) — RSI(14) crossing down through 70 triggers far more often than crossing up through 30 in this multi-year, broadly bullish sample, meaning the strategy is systematically biased toward fighting the dominant uptrend on the short side.
- Only 1,640 of 12,042 signals (13.6%) hit target; 5,612 (46.6%) hit stop; 4,790 (39.8%) timed out — the stop is hit far more often than the target, consistent with mean-reversion entries fading moves that continue rather than reverting within the 8-bar window.
- The reward projection (max of 2R or distance-to-SMA20) frequently produces very large targets relative to a tight ATR-buffered stop, making the "target" outcome rare in practice and the realised R distribution left-skewed.

## Backtest / Paper Trade Log

- **Backtest run:** Phase 1A, `run_phase1a.py --strategy e`, 216-ticker universe, cached daily OHLCV 2019-04-01 to 2026-07 (per-ticker warmup varies).
- **Total signals:** 12,042 (4,181 long / 7,861 short)
- **Signals/year:** 1,666.7 (aggregate across full 216-ticker universe)
- **Average R-multiple:** -0.056
- **Median R-multiple:** -0.609
- **Win rate:** 40.6%
- **Sub-periods positive:** 0 / 3
- **Friction flag:** ⚠️ YES (avg R -0.056, well below the 0.5 friction threshold — costs would only make this worse)
- **Exit reason breakdown:** stop 46.6% (5,612), time 39.8% (4,790), target 13.6% (1,640)
- **ADR-004 classification: ❌ KILL** — avg R (-0.056) is far below the kill threshold of 0.2 (and negative outright); signal frequency is not the limiting factor here (1,666.7 sig/yr is well above both kill and pass thresholds), the entry/exit logic itself does not produce a positive edge.
- Paper trade log: **not started — strategy killed in Phase 1A, does not advance to Phase 1B or paper trading.**

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy created and Phase 1A backtested | New strategy build request — RSI(14) mean-reversion-at-extremes entry test |
| 2026-07-26 | Killed per ADR-004 (avg R -0.056, 0/3 sub-periods positive) | Phase 1A backtest results — negative edge across full universe and all sub-periods |
| 2026-07-26 | Phase 1B sensitivity sweep run (tuning attempt) — remains KILL, no production changes made | See "Phase 1B Sensitivity Note" section below |

## Phase 1B Sensitivity Note (2026-07-26)

**Purpose:** Determine whether reasonable parameter tuning (long-only entry,
wider stop buffer, longer holding window, and either a looser R:R filter or a
deeper oversold threshold) could rescue the RSI mean-reversion edge above the
ADR-004 KILL floor (avg R >= 0.2, signals/yr >= 12). This is a standalone
sensitivity test — **the original scanner (`scanner_e_rsi_mean_reversion.py`)
and its Phase 1A registration in `run_phase1a.py` were left untouched**;
results below come from a new script,
`scripts/validation/phase1b_sensitivity_sweep_e.py`, which reuses the
baseline RSI/ATR/SMA indicator math but varies entry/exit parameters and
re-runs the backtest over the same cached 216-ticker universe
(`~/.hermes/market_data/*.parquet`). Sub-period classification for this sweep
uses the **correct date-based bucketing** (`period1_bull` 2019-04-01 to
2021-12-31, `period2_bear` 2022-01-01 to 2023-12-31, `period3_current`
2024-01-01+) rather than the baseline scanner's quarter-label
`subperiod` column, which does not match ADR-004's 3-period test.

### Variants tested (cumulative unless noted)

| Variant | Description | Long-only | ATR stop mult | Max hold (bars) | Min R:R | RSI oversold |
|---|---|---|---|---|---|---|
| V1 | Drop short signal entirely | Yes | 0.25 (baseline) | 8 (baseline) | 2.0 (baseline) | 30 (baseline) |
| V2 | V1 + wider stop buffer | Yes | 0.75 | 8 | 2.0 | 30 |
| V3 | V1+V2 + longer hold | Yes | 0.75 | 14 | 2.0 | 30 |
| V4 | V1+V2+V3 + looser R:R filter | Yes | 0.75 | 14 | 1.5 | 30 |
| V4b | V1+V2+V3 + deeper oversold trigger (tried in place of V4 since V4 had zero effect — see note) | Yes | 0.75 | 14 | 2.0 | 25 |

### Results table

| Variant | Sig/Yr | Avg R | Median R | Win Rate | Sub-Periods+ (date-based) | Friction Flag | ADR-004 Classification |
|---|---|---|---|---|---|---|---|
| V1_long_only | 578.9 | 0.102 | -0.223 | 46.2% | 2/3 | ⚠️ YES | ❌ KILL |
| V2_wider_stop | 578.9 | 0.034 | 0.008 | 50.3% | 2/3 | ⚠️ YES | ❌ KILL |
| V3_longer_hold | 578.9 | 0.110 | -0.007 | 49.8% | 3/3 | ⚠️ YES | ❌ KILL |
| V4_looser_rr | 578.9 | 0.110 | -0.007 | 49.8% | 3/3 | ⚠️ YES | ❌ KILL |
| V4b_deeper_oversold | 214.8 | 0.055 | -0.088 | 48.5% | 2/3 | ⚠️ YES | ❌ KILL |

*(Baseline for reference: 1,666.7 sig/yr, avg R -0.056, 0/3 sub-periods positive, ❌ KILL — bidirectional, ATR mult 0.25, max_bars 8, R:R 2.0, RSI 30/70, using the CSV's quarter-label subperiod column rather than the corrected date-based buckets used here.)*

### Findings

- **Dropping the short side (V1) removes the -0.14 avg R short-side drag and roughly doubles avg R** from the baseline's -0.056 to +0.102 — confirming the diagnostic that shorts were fighting the dominant uptrend. This alone is directionally correct but still falls well short of the 0.2 KILL floor, and the long-only signal count (578.9/yr) is far below the 25/yr PASS bar too (though comfortably above the 12/yr KILL floor).
- **Widening the stop buffer (V2, 0.25x -> 0.75x ATR) improved win rate (46.2% -> 50.3%) and made median R roughly breakeven (+0.008)**, but avg R actually *dropped* to 0.034 — a wider stop reduces stop-out frequency but also shrinks R-per-trade-unit (since risk is now larger for the same dollar move), so realized average R-multiple didn't improve even though the raw win/loss profile did.
- **Extending the hold window (V3, 8 -> 14 bars) recovered avg R back to 0.110** (best of the four core variants) and pushed sub-period positivity to 3/3 (the first variant to clear that hurdle) — more bars gives more chances to reach the SMA20/2R target before timing out. Still, 0.110 avg R is roughly half the 0.2 KILL floor.
- **Loosening the R:R filter (V4, 2.0 -> 1.5) had zero measurable effect** — identical signal count and R stats to V3. Inspecting the entry logic: reward is always `max(2*risk, |SMA20 - entry|)`, so the *realized* R:R at signal generation is bounded below by 2.0 regardless of the filter threshold; loosening the filter from 2.0 to 1.5 therefore never actually admits any additional signals that the 2.0 floor would have rejected. This filter is structurally redundant given the reward formula and is not a useful lever for this entry logic.
- Given V4's no-op, tried the documented alternative instead: **deeper oversold trigger (V4b, RSI cross-up through 25 instead of 30)**, reasoning that a more extreme oversold reading before confirmation should produce higher-quality, less-frequent bounces. Result: signal count collapsed from 578.9/yr to 214.8/yr (still far above the 12/yr floor) but avg R *fell* to 0.055 and sub-period positivity dropped back to 2/3 — the more extreme entries did not translate into a better realized edge; if anything the deeper-oversold names tended to keep falling rather than bounce cleanly within the hold window.
- **No variant reached the ADR-004 WATCH threshold, let alone PASS.** The best result (V3_longer_hold, avg R 0.110) is still ~45% short of the 0.2 KILL floor. The structural problem is not signal frequency (all variants clear the 12/yr floor by a wide margin) but the entry/exit edge itself: RSI-crossover confirmation entries with SMA20/2R targets do not produce a statistically positive edge on this universe even after removing the short-side drag, widening stops, extending the hold, and adjusting sensitivity/filter thresholds.

### Conclusion

**Status unchanged: KILL.** Phase 1B tuning (long-only, wider stops 0.25x->0.75x ATR, longer hold 8->14 bars, and two alternative fourth levers — a no-op R:R loosening and a deeper-oversold RSI trigger) failed to rescue this strategy above the ADR-004 KILL floor. The best variant (long-only + wider stop + longer hold, avg R 0.110) still falls under half the required 0.2 avg R. No new production scanner or hypothesis doc was created per the Phase 1B decision rule (no variant reached WATCH). This strategy remains dropped; further tuning of this specific entry/exit skeleton is not recommended — a materially different entry trigger or exit logic (not just parameter perturbation) would be required to revisit RSI mean-reversion as a strategy family.

**Sweep script:** `scripts/validation/phase1b_sensitivity_sweep_e.py` (new file, standalone; does not modify `scanner_e_rsi_mean_reversion.py` or `run_phase1a.py`).
