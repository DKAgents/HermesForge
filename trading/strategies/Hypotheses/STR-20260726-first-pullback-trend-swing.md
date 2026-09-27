---
id: STR-20260726-first-pullback-trend-swing
type: strategy
status: hypothesis
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: pullback
confidence: medium
publish_enabled: false
publish_channel: stocks
evidence_links:
  - RG032-3-to-1-reward-to-risk-ratio
last_reviewed: 2026-07-26
created: 2026-07-26
updated: 2026-07-26
"tags: [strategy, hypothesis, pullback, trend, swing, long-short, regime-filter]"
topic: strategies
has_quotes: false
source: HermesForge Strategies
tags: []
scanner_module: scanner_h_first_pullback

strategy_id: STR-H-first-pullback
---
# High-RR First-Pullback Trend Swing (Long/Short) v1.4

## Origin

Strategy submitted by the user as a strategy-evaluation request (PDF: `High-RR_First-Pullback_Trend_Swing_LongShort.pdf`), then iterated through four review rounds with Hermes (v1.0 → v1.1 → v1.2 → v1.3 → v1.4) addressing gaps identified at each pass: mechanical "first pullback" definition, concrete confirmation-candle rule, tightened short-regime trigger, removal of a soft "or rising" clause, and — in this v1.4 — a swing-segmented leg redefinition to address a signal-scarcity concern.

## Thesis

Only trade the *first* pullback within a trend leg on liquid US equities and ADRs, with a hard minimum Risk:Reward of 1:3. Both long and short are permitted, but each is regime-dependent (risk-on longs only, risk-off shorts only). The core wager: trend-continuation entries taken immediately after the *first* pullback of a leg carry a better risk-adjusted edge than chasing extended trends or re-entering on later, weaker pullbacks in the same leg.

**Relationship to existing work:** This is a close cousin of [[STR-20260719-ma-pullback-fibonacci-entry]]. Both are trend-pullback strategies sharing the same architectural skeleton (trend filter → pullback → momentum confirmation → hard RR gate). **They should be treated as correlated hypotheses** — the portfolio risk/heat system must prevent both from holding the same ticker simultaneously, or at minimum apply a combined heat limit across the pair. This is a system-level requirement, not something either strategy file can self-enforce.

**Holding period:** 3–20 trading days
**Universe:** US-listed stocks and ADRs
**Hard liquidity filter:** 20-day average dollar volume ≥ $5,000,000

## Regime Filter

- **Risk-on** (longs only): SPY close > 50-SMA **and** SPY close > 200-SMA, **and** VIX < 25 (hard gate)
- **Risk-off** (shorts only): SPY close < 50-SMA **and** SPY close < 200-SMA. VIX is **never** an independent short trigger — if VIX > 25 while the SPY condition is met, reduce position size by 50% (size-reduction flag only, not a trigger)
- **Neutral:** No new trades

*(Data suggestion: yfinance/Yahoo-style SPY/VIX OHLCV)*

## Trend-Leg & First-Pullback Definition (v1.4 — swing-segmented)

**v1.1–v1.3 approach (superseded):** anchored the trend-leg origin strictly to the most recent 50/200-SMA cross date, and only recognized one "first pullback" per cross. This was fully mechanical but structurally rare — a 50/200 cross happens infrequently, and once used, the strategy went dark on that name until the next cross. Combined with removing the "or rising" grace clause in v1.3, this created a real signal-scarcity risk (see Open Questions #1) — likely insufficient trade volume to reach the 30–50 paper trades needed to validate PT-001 in a reasonable window.

**v1.4 fix — redefine "leg" as swing-segmented, not cross-anchored:**

- The 50/200-SMA cross relationship is **retained as the regime gate only** — price/SMA structure must still confirm a genuine uptrend (50-SMA > 200-SMA, price > 50-SMA) for longs, or the mirror for shorts. This is unchanged and still required (checklist item #2 below).
- **A new trend "leg" begins at any point where price makes an impulsive move of ≥ 1.5 × ATR(14) in the trend direction, measured from either (a) the most recent qualifying pullback low/high, or (b) the 50/200-SMA cross date if no qualifying pullback has yet occurred in the current cross-regime.**
- **First-pullback rule (applies per leg, not per cross):**
  1. From the leg's origin (as defined above), price must first make a new extreme of at least 1.5 × ATR(14) in the trend direction (new swing high for longs, new swing low for shorts).
  2. The **first** subsequent close that retraces ≥ 1.0 × ATR(14) from that extreme, while price remains on the correct side of the 50-SMA (above for longs, below for shorts), is the first pullback of that leg.
  3. Any later retracement of ≥ 1.0 × ATR(14) within the *same* leg is a second (or later) pullback and is disqualified.
  4. Once a qualifying pullback has resolved (price resumes the trend and makes a fresh ≥ 1.5 × ATR extreme beyond the prior pullback low/high), a **new leg begins** and its first pullback becomes eligible again.

**Net effect:** a single durable, sustained trend can now produce multiple valid "first pullback of a leg" setups over its lifetime (leg 1's pullback → leg 2's pullback → leg 3's pullback...), which directly targets the signal-scarcity problem — while every quality/discipline rule (impulsive-move requirement, only-the-first-retracement-counts, all disqualifiers, RR ≥ 3.0, ADX, RSI, volume contraction, confirmation candle) is preserved exactly as in v1.3. This is a frequency fix, not a quality relaxation.

## Pullback Zone

Price must be **inside or have just touched the 9-EMA / 20-EMA zone**. (The earlier "or recent swing structure" clause was removed in v1.2 for determinism — not reinstated.)

## Confirmation Candle

**Long** (either):
- Daily close > prior day's high, **or**
- Daily candle closes in the top 30% of its range **and** closes above the 9-EMA

**Short** (mirror):
- Daily close < prior day's low, **or**
- Daily candle closes in the bottom 30% of its range **and** closes below the 9-EMA

4-hour confirmation of the same condition is preferred but not required.

## Entry Criteria

**Long — all required:**
- [ ] **Risk-on regime** (SPY > 50-SMA and > 200-SMA, VIX < 25)
- [ ] **Uptrend structure:** Price > 50-SMA **and** 50-SMA > 200-SMA (no "or rising" grace clause — v1.3 change, retained)
- [ ] **Qualifies as the first pullback of the current leg** (swing-segmented definition above)
- [ ] Price inside or just touched the 9/20-EMA zone
- [ ] RSI(14) between 40–60
- [ ] ADX(14) ≥ 22
- [ ] Pullback volume < 20-day average volume (contraction)
- [ ] Confirmation candle (definition above)
- [ ] Calculated RR ≥ 3.0
- [ ] ATR% of price ≤ 6%
- [ ] No earnings within ±5 calendar days
- [ ] 20-day average dollar volume ≥ $5,000,000

**Short** — mirrored rules under the risk-off regime (uptrend structure mirror: Price < 50-SMA **and** 50-SMA < 200-SMA).

## Exit Criteria

- [ ] **Stop loss:** structure-based — below (long) / above (short) the pullback extreme ± 0.2 × ATR(14)
- [ ] **Hard RR gate:** primary target must be ≥ 3 × risk distance; never take a trade with calculated RR < 3.0
- [ ] **Partial exit:** scale out 50% of the position at 3R
- [ ] **Trailing stop (remainder):** trail with 1.5 × ATR(14) or the 9-EMA, whichever is tighter
- [ ] **Time stop:** exit remaining shares after 15 trading days if 3R has not been hit
- [ ] **Volatility filter:** skip entry entirely if ATR% of price > 6%

## Risk Rules Applied

- [ ] **PS-001:** Maximum single position risk = 1% of total capital (hard limit; this strategy defaults to a tighter 0.75%, see below)
- [ ] **Default risk per trade:** 0.75% of equity (parameterizable, below the PS-001 ceiling)
- [ ] **PS-002:** Max concurrent positions = 6; Max portfolio heat = 4.5% (6 × 0.75% = 4.5%, consistent)
- [ ] **VIX size-reduction modifier:** if VIX > 25 while a valid short setup is otherwise qualified, reduce position size by 50%
- [ ] **RG032:** 3:1 minimum reward-to-risk enforced pre-entry; skip if RR < 3.0
- [ ] **PT-001:** Minimum 30 days paper trading before live consideration
- [ ] **Correlation control (see Open Questions #2):** central risk/heat system must treat this strategy and STR-20260719-ma-pullback-fibonacci-entry as correlated — prevent simultaneous same-ticker holdings or apply a combined heat limit across the pair

## Hard Disqualifiers

- Liquidity below $5M ADV
- Earnings within ±5 calendar days
- Gap > 2 ATR against the trade at the open
- ADX < 22
- Neutral regime
- Not the first pullback of the current leg
- Calculated RR < 3.0

## Data Sources

- **Primary:** yfinance (Yahoo)
- **Fallback:** Stooq (no rate limits — useful when Yahoo endpoints throttle)
- **Earnings calendar:** Finnhub free tier or Yahoo earnings calendar (for the ±5-day exclusion filter)

## Supporting Evidence

- [[RG032-3-to-1-reward-to-risk-ratio]] — Minimum 3:1 R:R required before any entry; directly applied as the pre-entry RR gate here.
- [[STR-20260719-ma-pullback-fibonacci-entry]] — Sibling trend-pullback strategy; shares core architecture (trend filter → pullback → momentum confirmation → RR gate). Flagged as correlated; portfolio system must manage combined exposure.

## Counter-Evidence

### Failure Mode 1 — Signal scarcity (see Open Questions #1)
The 50/200-SMA regime gate combined with a strict "first pullback only" rule per leg is inherently restrictive. The v1.4 swing-segmented leg redefinition is designed to mitigate this by allowing multiple legs (and thus multiple valid setups) within a single durable trend, but actual signal frequency is unverified until the scanner is built and run against real data. If frequency is still insufficient to reach 30–50 paper trades in a reasonable window, next levers (in order of preference) are: (a) widen the universe beyond a curated watchlist to the full $5M+ ADV liquid universe, (b) consider ADX ≥ 20 as a secondary/looser tier — treated as a last resort since it is a real quality tradeoff, unlike the leg redefinition.

### Failure Mode 2 — Whipsaw risk on short entries (mitigated in v1.2)
Earlier drafts allowed VIX > 25 alone to trigger risk-off shorts, which risked authorizing shorts purely on volatility spikes that often accompany sharp recoveries rather than genuine downtrends. Resolved by requiring SPY below *both* 50-SMA and 200-SMA for the risk-off regime, with VIX demoted to a size-reduction modifier only.

### Failure Mode 3 — Cannot fully verify "first pullback of a leg" logic without backtesting
The swing-segmented leg definition is more complex than the original cross-anchored version and has not yet been implemented in a scanner or backtested. There is a risk that the leg-boundary logic (what counts as "resolved" before a new leg can begin) produces edge cases not anticipated here. This must be validated against real price data before paper trading begins.

## Backtest / Paper Trade Log

- Paper trade log: *not started — requires PT-001 (30-day minimum)*
- Backtest results: **Phase 1A scanner complete (2026-07-26)** — see results below
- Target sample size before evaluation: ≥ 30–50 completed trades (per user's stated evaluation threshold for this strategy), covering at least one full market cycle where possible

## Graph Properties

produced_by:: [[Backtester]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
regime_node:: [[REGIME-trending]]
killed_by:: [[FAIL-STR-H-first-pullback]]
tested_in:: [[STR-H-phase1a]]

## Phase 1A Scanner Results (2026-07-26)

Scanner implemented at `scripts/validation/scanners/scanner_h_first_pullback_trend_swing.py`, registered in `run_phase1a.py` as strategy `h`, run against the full 216-ticker cached universe (2019-04-01 onward valid signal period).

**Result: ❌ KILL (per ADR-004 criteria)**

| Metric | Value | Threshold |
|---|---|---|
| Signals/year | 0.9 | Kill if <12/yr |
| Avg R multiple | -1.975 | Kill if <0.2 |
| Win rate | 0.0% | — |
| Sub-periods positive | 0/3 | Pass needs ≥2/3 |
| Total signals (full history) | 3 | — |

All 3 signals across the entire universe/history stopped out (AIG -3.75R, GOOGL -1.11R, PRU -1.07R). This is a decisive, evidence-based kill — not a marginal watch-band result. The v1.4 leg-redefinition fix (intended to address the v1.3 signal-scarcity concern) did **not** resolve it: 0.9 sig/yr across 216 tickers is far below even the pre-fix v1.3 concern level, and the confirmation-candle + EMA-zone + volume-contraction + ADX + RSI filter stack compounds so severely that almost no bar in the dataset satisfies all gates simultaneously. Single-ticker smoke test (AAPL, full history) independently confirmed 0 signals passed all filters despite 23 raw pullback-leg bars being found — the leg logic itself works, but the downstream discretionary-style filter stack (especially the confirmation candle) is the bottleneck.

**Recommendation:** Do not proceed to paper trading in current form. Either (a) formally kill this strategy per ADR-004, or (b) run one more revision pass loosening the confirmation-candle/EMA-zone/volume filters specifically (not just the leg definition) before re-testing — user's call. Full signal-level detail: `scripts/validation/results/STR-20260726-first-pullback-trend-swing-phase1a.csv`.

## Open Questions

*These must be resolved by paper trading and backtesting before this strategy advances from `hypothesis` to `tested`.*

1. **Signal scarcity — RESOLVED, confirmed severe.** Phase 1A scan (2026-07-26) found only 3 signals across 216 tickers over ~7 years (0.9 sig/yr), far below the 12 sig/yr kill threshold. The v1.4 leg-redefinition fix did not meaningfully help — the bottleneck is the confirmation-candle/EMA-zone/volume-contraction filter stack, not the leg-origin logic. Secondary levers (universe widening, ADX loosening) will not close a gap this large on their own.
2. **Portfolio-level correlation enforcement** — This strategy and [[STR-20260719-ma-pullback-fibonacci-entry]] are correlated (same core architecture, likely overlapping candidate names). The central risk/heat system, not either strategy file, must prevent simultaneous same-ticker holdings between the two or apply a combined heat limit. Moot pending a decision on this strategy's kill/rework status.
3. **Leg-boundary edge cases — implemented and smoke-tested.** The v1.4 swing-segmented leg logic was implemented in the Phase 1A scanner and verified against AAPL full history (23 qualifying pullback-leg bars found, logic behaves as specified). Not the source of the scarcity problem.
4. **Performance expectations — invalidated by data.** All 3 realized signals were losers (win rate 0%, avg R -1.975). The 35–45%/48–55% planning ranges were pre-data estimates and should not be relied on further; current empirical evidence points to negative expectancy in this rule configuration.

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy submitted by user (PDF), v1.0 initial evaluation by Hermes | User strategy-evaluation request |
| 2026-07-26 | v1.1 — mechanical "first pullback" definition, concrete confirmation candle, tightened short regime, correlation flag added | Hermes critique of v1.0 |
| 2026-07-26 | v1.2 — removed "or recent swing structure" clause for determinism; logged open questions on signal scarcity and portfolio correlation | Hermes critique of v1.1 |
| 2026-07-26 | v1.3 — removed soft "or rising" clause from checklist item #2 (redundant given hard SMA-cross-anchored origin) | Hermes nitpick from v1.2 review |
| 2026-07-26 | v1.4 — redefined trend "leg" as swing-segmented (impulsive move from most recent qualifying pullback, not solely the 50/200 cross date) to address signal-scarcity risk identified when reviewing v1.3 | Hermes critique flagging v1.3's tightened rules would likely produce insufficient trade volume for PT-001 evaluation; user approved folding the fix directly into the frozen spec |
| 2026-07-26 | Created as formal hypothesis file, `status: hypothesis`, `publish_enabled: false` | User request to formalize after 4 review rounds |
| 2026-07-26 | Phase 1A scanner built (`scanner_h_first_pullback_trend_swing.py`), registered in `run_phase1a.py`, run against full 216-ticker universe. Result: **KILL** — 0.9 sig/yr, avg R -1.975, 0% win rate, 0/3 sub-periods positive. v1.4 fix did not resolve signal scarcity; confirmation-candle/EMA-zone/volume filter stack identified as the actual bottleneck. | User instruction "Proceed" after v1.4 fold-in confirmation |

## Related
- [[R081-volume-should-confirm-price-trend-direction]] — See R081-volume-should-confirm-price-trend-direction for volume confirmation of valid pullbacks

- [[EN068-4060-retracement-zones-for-timing-entries]] — Constrain valid pullbacks to 40-60% retracement zone per Murphy
