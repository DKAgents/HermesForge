---
id: STR-20260726-bollinger-squeeze-breakout-entry
type: strategy
status: killed
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: transitional
core_idea: volatility-breakout
confidence: low
publish_enabled: false
publish_channel: stocks
evidence_links:
  - STR-F-bollinger-squeeze-breakout-phase1a
last_reviewed: 2026-07-26
created: 2026-07-26
updated: 2026-07-26
tags: [strategy, hypothesis, bollinger-bands, volatility-squeeze, breakout, swing, killed]
topic: strategies
has_quotes: false
source: HermesForge Strategies
---
# Bollinger Band Squeeze Breakout Entry

## Thesis

Volatility contracts and expands in cycles. When Bollinger Band width (the normalized distance between the +2σ and -2σ bands relative to the 20-period SMA) compresses to its lowest reading of the trailing 60 bars, the market is coiling in a low-volatility "squeeze" that historically precedes an expansion move. The thesis is that a decisive close beyond the prior day's band boundary, confirmed by above-average volume (>=1.2x the 20-bar average), signals the resolution of that squeeze in the breakout direction and offers a tradeable entry with the compressed band width itself serving as a naturally tight risk unit. This is a bidirectional strategy: long on upside breaks above yesterday's upper band, short on downside breaks below yesterday's lower band, with a projected 2:1 reward-to-risk target measured off the band-width-derived stop.

## Entry Criteria

- [ ] **Squeeze detection:** Yesterday's Bollinger Band width — (upper_band − lower_band) / middle_band, using 20-period SMA and population (ddof=0) standard deviation ×2 — must equal the minimum band width of the trailing 60-bar window (today not included in the squeeze check, only yesterday).
- [ ] **Breakout confirmation (long):** Today's close breaks above yesterday's upper Bollinger Band value.
- [ ] **Breakout confirmation (short):** Today's close breaks below yesterday's lower Bollinger Band value.
- [ ] **Volume filter:** Today's volume must be ≥ 1.2× the 20-bar average volume (confirms genuine breakout participation vs. noise).
- [ ] **R:R filter:** Skip any signal where projected reward-to-risk < 2.0, or where stop price equals entry price (zero-risk/degenerate bar).

## Exit Criteria

- [ ] **Stop loss (long):** Today's (breakout bar's) lower Bollinger Band value.
- [ ] **Stop loss (short):** Today's (breakout bar's) upper Bollinger Band value.
- [ ] **Take profit:** 2× the stop distance projected from entry in the trade direction (2:1 R:R target using the band-width risk unit).
- [ ] **Time stop:** Exit at market (close) if neither target nor stop is hit within 10 trading bars — squeezes can take longer to resolve than plain breakouts, hence the extended window vs. Strategy C's 8-bar stop.

## Risk Rules Applied

- [ ] PS-001: Max 1% capital risk per position (stop distance × shares ≤ 1% capital) — to be applied if/when operationalized
- [ ] RG032/analogous: Minimum 2:1 R:R enforced at signal generation (MIN_RR = 2.0 in scanner)
- [ ] RG037: Protective stop is mandatory and derived directly from band geometry, not discretionary
- [ ] PT-001: N/A — strategy killed at Phase 1A, does not advance to paper trading

## Supporting Evidence

- Bollinger Band squeeze-to-breakout is a well-documented technical pattern (volatility contraction preceding expansion) in classical TA literature; volume confirmation mirrors the same filter used successfully in Strategy C (breakout + volume).
- Bidirectional signal generation (long/short symmetry) mirrors the working pattern used in Strategy B (MACD divergence), which follows HermesForge's established bidirectional scanner architecture.

## Counter-Evidence

- **Phase 1A backtest result is decisively negative on frictionless returns.** Average R multiple across 1,466 signals over the 216-ticker universe (2019–2026) was **-0.048**, well below the ADR-004 kill threshold of 0.2, despite very high signal frequency (209.7 signals/year).
- Win rate was 48.2% — close to a coin flip, indicating the 2:1 R:R target is rarely being hit; most breakouts appear to fail or drift sideways/against the signal direction before the 10-bar time stop triggers.
- The squeeze condition (lowest band-width in trailing 60 bars) is extremely common in practice — nearly any low-volatility day can register as a local minimum, which likely explains the very high signal count but also dilutes signal quality since it doesn't require an unusually *deep* or *prolonged* compression.
- Using the band width itself as the risk unit (stop = same-bar opposite band) means the stop is often quite wide relative to the breakout's actual follow-through, producing an unfavorable realized-R distribution even before considering that most exits were time-stops rather than clean target/stop hits.
- No sub-period (of the harness's hardcoded regime labels) registered as net-positive, though note the harness's `SUBPERIODS` labels (`period1_bull`/`period2_bear`/`period3_current`) do not match this strategy's quarter-based `subperiod` labels (`YYYY-QN`), so the "0/3" sub-period-positive count is a harness labeling artifact rather than a true quarter-by-quarter breakdown; regardless, the overall negative average R already fails the kill threshold independent of that count.

## Backtest / Paper Trade Log

**Phase 1A Backtest (2026-07-26)** — run via `python3 scripts/validation/run_phase1a.py --strategy f` against the cached 216-ticker universe (2019-04-01 through 2026-07-17 data window):

| Metric | Value |
|---|---|
| Total signals | 1,466 |
| Signals / year | 209.7 |
| Average R multiple | -0.048 |
| Median R multiple | -0.034 |
| Win rate | 48.2% |
| Sub-periods positive (harness labels) | 0/3 |
| Friction flag | ⚠️ Yes (avg R < 0.5) |
| **Classification (ADR-004)** | **❌ KILL** |

ADR-004 kill rule: signals/year < 12 OR avg R < 0.2. This strategy clears the frequency bar easily (209.7/yr) but fails decisively on edge — avg R of -0.048 is well below the 0.2 kill threshold, and the strategy would lose money even before transaction costs/slippage are applied (friction flag also triggered independently). No further Phase 1B testing is warranted.

- Paper trade log: _not started — strategy killed at Phase 1A, will not advance to paper trading_.

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy created and backtested; killed at Phase 1A | New strategy build (STR-F); Phase 1A backtest returned avg R -0.048 (< 0.2 kill threshold) despite adequate signal frequency (209.7/yr); classified KILL per ADR-004 |
| 2026-07-26 | Phase 1B parameter sensitivity sweep run; strategy remains KILL, no rescue found | See "Phase 1B Sensitivity Note" section below |

## Phase 1B Sensitivity Note (2026-07-26)

Following the Phase 1A KILL, a diagnostic breakdown of the 1,466 baseline
signals found: target-hit rate only 2.0% (the 2:1 R:R target essentially
never resolves), 80% of trades exit at the 10-bar time stop with a barely
positive avg R there (+0.16), stop-hit rate 18% at avg -1.24R, and the short
side was a clear drag (long avg R +0.04 vs. short avg R -0.13). This
motivated a Phase 1B tuning sweep to see whether cutting the losing short
leg, lowering the target ambition, and giving trades more room to work could
lift the strategy out of KILL territory.

**Method:** A standalone script,
`scripts/validation/phase1b_bollinger_sweep.py`, was built that reuses the
Bollinger Band math and exit-simulation logic from
`scanners/scanner_f_bollinger_squeeze.py` (unmodified — that file and
`run_phase1a.py`'s `'f'` registration were left exactly as-is) but
parameterizes `long_only`, `rr_target`, `max_hold`, `volume_mult`, and
`squeeze_window`. Each variant was run against the identical cached
216-ticker universe (`~/.hermes/market_data/*.parquet`, loaded via
`fetch_data.load_all()`), and classified using the **correct date-based
sub-period buckets** (`period1_bull` 2019‑04‑01→2021‑12‑31,
`period2_bear` 2022‑01‑01→2023‑12‑31, `period3_current` 2024‑01‑01→),
not the CSV's quarter-label `subperiod` column (a known harness bug —
see Counter-Evidence above). A sub-period counts positive only if it has
≥3 trades and avg R > 0.

Variants tested (cumulative):

| Variant | long_only | RR target | max_hold | volume_mult | squeeze_window |
|---|---|---|---|---|---|
| V1 | ✅ | 2.0 | 10 | 1.2× | 60 |
| V2 | ✅ | **1.2** | 10 | 1.2× | 60 |
| V3 | ✅ | 1.2 | **20** | 1.2× | 60 |
| V4 | ✅ | 1.2 | 20 | **1.0×** | 60 |

V4's tweak (relaxing the volume filter from 1.2× to 1.0× avg volume) was
chosen over the "deeper squeeze" alternative (90-bar vs. 60-bar squeeze-low
window) because the diagnostic pointed to a *volume of signals / exit-timing*
problem rather than a squeeze-quality problem — the 60-bar squeeze detector
was already firing on genuine local volatility minima; the volume filter
looked like the more likely source of false starts being screened in/out
inconsistently, so relaxing it was tested as a way to gather more signal
volume to see if underlying average R held up or degraded with lower-quality
entries admitted.

**Results:**

| Variant | Sig/Yr | Avg R | Median R | Win Rate | Sub-Periods+ | Friction | Classification |
|---|---|---|---|---|---|---|---|
| Baseline (bidirectional, RR 2.0, hold 10) | 209.7 | -0.048 | n/a | 48.2% | 0/3* | ⚠️ Yes | ❌ KILL |
| V1: long-only | 100.5 | 0.037 | 0.068 | 52.5% | 2/3 | ⚠️ Yes | ❌ KILL |
| V2: + RR target 1.2 | 56.6 | 0.010 | 0.035 | 52.0% | 2/3 | ⚠️ Yes | ❌ KILL |
| V3: + max_hold 20 | 56.6 | 0.060 | 0.131 | 55.1% | 2/3 | ⚠️ Yes | ❌ KILL |
| V4: + volume_mult 1.0 | 94.0 | 0.124 | 0.196 | 57.2% | 2/3 | ⚠️ Yes | ❌ KILL |

\* Baseline sub-period count re-derived under the correct date-based
buckets in this sweep script also comes out at 0/3 positive (consistent
with the original doc's note that the harness's quarter-label column was
buggy — the underlying conclusion doesn't change either way).

**Findings:**

- Dropping the short leg (V1) alone roughly *doubles* avg R (from -0.048 to
  +0.037) and lifts win rate from 48.2% to 52.5%, confirming the diagnosis
  that shorts were a straightforward drag — but it only gets the strategy
  from deeply negative to barely positive, nowhere near the 0.2 KILL floor.
- Lowering the R:R target to 1.2 (V2) actually *hurts* avg R (0.037 → 0.010)
  despite presumably raising the target-hit rate, because it also roughly
  halves signal count (100.5 → 56.6/yr) via the RR filter interacting with
  the same stop-distance geometry, and the smaller target size shrinks the
  reward per win faster than the extra win-rate compensates.
- Extending the hold window to 20 bars (V3) helps meaningfully (avg R
  0.010 → 0.060, median R 0.035 → 0.131) — giving trades more room clearly
  matters, consistent with the original diagnostic showing time-stop exits
  were only barely positive under the 10-bar cutoff — but it's still an
  order of magnitude below the 0.2 kill threshold.
- Relaxing the volume filter to 1.0× (V4) is the single best lever tested:
  avg R rises to 0.124 (median 0.196, win rate 57.2%) with signal frequency
  back up to 94/yr. This is the closest any variant gets to daylight, but it
  still falls short of the 0.2 frictionless KILL floor — and would be
  guaranteed to fail once realistic commission/slippage is applied given the
  friction flag is already triggered before costs.
- **No variant, individually or cumulatively, clears the ADR-004 KILL
  threshold (avg R ≥ 0.2).** The best result (V4, avg R 0.124) is roughly
  62% of the way to the kill floor but not there. Sub-period consistency
  (2/3 positive) was achieved by every long-only variant, so the remaining
  problem is edge magnitude, not regime fragility.
- **Conclusion:** long-only filtering, a closer 1.2:1 target, a longer
  20-bar hold, and a looser volume filter all point in the *right*
  direction individually and stack constructively, but combined they only
  get the strategy from deeply negative (-0.048) to modestly positive
  (+0.124) — still below the frictionless KILL floor of 0.2, let alone the
  WATCH/PASS bar. The core problem diagnosed at Phase 1A — a stop-distance
  (band-width) risk unit that is too wide relative to typical post-breakout
  follow-through, producing a poor realized-R distribution regardless of
  target ambition or hold length — is not resolved by these parameter
  tweaks. **Status remains KILL; no Phase 1B rescue found.** No STR-F2
  production scanner, run_phase1a.py registration, or new hypothesis doc
  was created as a result of this sweep, per the decision rule that no
  variant reached WATCH or better.
- Script used: `scripts/validation/phase1b_bollinger_sweep.py` (standalone;
  does not modify `scanner_f_bollinger_squeeze.py` or the existing `'f'`
  registration in `run_phase1a.py`).
