---
id: STR-20260719-breakout-volume-trend
type: strategy
status: hypothesis
asset_class: stocks
trade_style: swing
timeframe: daily
confidence: medium
evidence_links:
  - EN008-volume-confirmation-at-pattern-completion
  - R052-filters-for-confirming-breakouts
  - N028-bull-trap-false-upside-breakout
  - N013-volume-as-a-filter-for-false-breakouts
  - RG032-3-to-1-reward-to-risk-ratio
  - INS-2026-07-19-volume-confirmation-as-binary-entry-gate-reducing-position-r
  - INS-2026-07-19-multi-filter-breakout-system-with-volume-triggered-stop-plac
last_reviewed: 2026-07-19
created: 2026-07-19
updated: 2026-07-19
tags: [strategy, hypothesis, breakout, volume, swing]
---

# Trend-Following Breakout with Volume Confirmation

## Thesis

Price breakouts from consolidation patterns (flags, rectangles, triangles, cup-and-handle) above resistance levels, confirmed by above-average volume, in the direction of the primary weekly trend, offer a statistically favorable entry point with a well-defined stop and measurable target. The edge comes from combining a structural breakout (pattern completion) with a volume gate (false breakout filter) and a weekly trend filter — all three must agree. Without volume confirmation, the breakout is treated as unconfirmed and no position is taken. This approach is grounded in Murphy's core principle that volume must confirm price action at every significant juncture.

## Entry Criteria

- [ ] **Trend filter (weekly):** Price is above the 20-week MA AND the weekly chart shows a series of higher highs and higher lows (uptrend confirmed). No entry against the weekly trend.
- [ ] **Pattern / Setup:** Price forms a recognizable continuation pattern (flag, pennant, rectangle, symmetrical triangle) after a prior impulsive advance. The consolidation period is ≥5 bars on the daily chart.
- [ ] **Breakout bar:** Price closes above the upper boundary of the consolidation pattern on the daily chart. A single intraday pierce does not count — requires a closing breakout (R052 close-beyond filter).
- [ ] **Volume confirmation:** The breakout bar's volume is ≥ 1.5× the 20-day average volume (EN008, N013). If volume is below this threshold, the entry is deferred; entry is permitted on the *next* day's open only if price holds above the breakout level and volume was above average on the breakout close.
- [ ] **No overbought divergence:** Daily RSI is below 75 at time of entry. If RSI is diverging bearishly (price at new high, RSI lower than prior swing high), skip this setup.

## Exit Criteria

- [ ] **Stop loss:** Placed below the low of the breakout bar OR below the lower boundary of the consolidation pattern, whichever is closer to entry price, but always ≥ 1 ATR(14) below entry. Round down to nearest support level.
- [ ] **Take profit / target:** Measured move = height of the consolidation pattern added to the breakout point. Minimum 3:1 reward-to-risk ratio required before entering (RG032). Partial exit (50%) at 2:1, remainder held to full target.
- [ ] **Time stop:** If price has not made meaningful progress (< 1 ATR) within 10 trading days of entry, exit regardless of P&L.
- [ ] **Bull trap exit:** If a breakout bar followed by a heavy-volume reversal bar below the breakout level occurs, exit immediately — this is the bull trap signature (N028, INS multi-filter).
- [ ] **Trailing stop:** Once target 1 hit and 50% position exited, trail remainder below each successive swing low on the daily chart.

## Risk Rules Applied

- [ ] PS-001: Max 1% capital risk per position (stop distance × shares ≤ 1% capital)
- [ ] PS-004: Position size calculated before entry using (1% capital) ÷ (entry − stop)
- [ ] LL-001: Daily loss limit 2% — stop trading for the day if hit
- [ ] LL-003: Single trade max loss = 1% (links to PS-001)
- [ ] PT-001: Paper mode minimum 30 days before live consideration
- [ ] RG032: 3:1 minimum reward-to-risk — do not enter if measured move < 3× stop distance

## Supporting Evidence

- [[EN008-volume-confirmation-at-pattern-completion]] — Pattern completion requires noticeable volume increase (Murphy pp. 121–140)
- [[R052-filters-for-confirming-breakouts]] — Close-beyond filter, two-day rule, percentage rule for confirming valid breakouts
- [[N028-bull-trap-false-upside-breakout]] — Light-volume breakout followed by heavy-volume reversal = bull trap signature
- [[N013-volume-as-a-filter-for-false-breakouts]] — Volume as directional qualifier; negative chart combination defined
- [[RG032-3-to-1-reward-to-risk-ratio]] — Minimum 3:1 R:R required before any trade entry
- [[INS-2026-07-19-volume-confirmation-as-binary-entry-gate-reducing-position-r]] — Discovery insight: volume as binary gate, mandatory exit on heavy-volume reversal
- [[INS-2026-07-19-multi-filter-breakout-system-with-volume-triggered-stop-plac]] — Discovery insight: layered structural + volume filter, bull trap high as short stop reference

## Counter-Evidence

- [[E022-moving-averages-work-best-in-trending-markets]] — Breakout strategies underperform in ranging/choppy markets; the weekly trend filter partially mitigates but does not eliminate this
- [[E034-mechanical-trend-following-systems-work-only-in-certain-envi]] — Mechanical trend-following only profitable ~30% of the time; requires large winners to offset losers — sizing discipline is critical
- [[RG014-whipsaw-risk-with-short-term-moving-averages]] — False signals generate whipsaws; the two-day close filter (R052) reduces but doesn't eliminate

## Backtest / Paper Trade Log

- Paper trade log: _not started — requires PT-001 (30 days minimum)_
- Backtest results: _not started — see US-014 for backtesting library selection_

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-19 | Strategy created | US-052 Living Strategy Layer; seeded from Murphy ingestion + US-051 discoveries |
