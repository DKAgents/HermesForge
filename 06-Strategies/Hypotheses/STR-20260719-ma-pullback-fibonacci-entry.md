---
id: STR-20260719-ma-pullback-fibonacci-entry
type: strategy
status: hypothesis
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: pullback
confidence: medium
evidence_links:
  - C050-secondary-trend-retracement-range
  - N085-fibonacci-percentage-retracements-38-50-62
  - C347-percentage-retracements
  - RG006-two-thirds-retracement-as-critical-reversal-level
  - EN041-oscillator-entry-strategy-in-trending-markets
  - R142-weekly-signals-as-trend-filters-for-macd-and-stochastics
  - C064-previous-peaks-as-future-support-in-uptrend
  - R213-fibonacci-tools-as-secondary-inputs
  - RG032-3-to-1-reward-to-risk-ratio
  - EN004-trendline-as-a-buying-area-in-an-uptrend
  - C149-rsi-vs-stochastics-volatility-comparison
  - N165-relative-strength-index-rsi-overboughtoversold-levels
  - INS-2026-07-19-triple-weekly-confirmation-system-for-daily-trade-entries
last_reviewed: 2026-07-19
created: 2026-07-19
updated: 2026-07-19
tags: [strategy, hypothesis, pullback, fibonacci, moving-average, swing, trending]
---

# Moving Average Pullback with Fibonacci Precision Entry

## Thesis

In a confirmed primary uptrend, price advances impulsively then corrects in secondary movements. Murphy establishes that corrections typically retrace one-third to two-thirds of the prior advance, with 38%, 50%, and 62% Fibonacci levels acting as the most common reversal zones. The edge in this strategy comes from **combining structural support with Fibonacci precision**: the rising 50-day moving average and prior resistance-turned-support levels define *where* support should exist; Fibonacci retracement levels narrow *which specific price zone within that support* offers the highest-probability entry. Fibonacci tools are secondary inputs (Murphy's explicit guidance, `R213`) — they refine the MA/trendline support zone, they do not replace it.

The entry is confirmed only when an oscillator-based trigger fires *while price is inside the combined support zone* — buying oversold in an uptrend (`EN041`). A mandatory three-gate weekly filter (`INS-triple-weekly`) ensures the primary trend is fully confirmed before any daily setup is considered. The stop is defined by Murphy's two-thirds rule (`RG006`): a daily close below the 62% Fibonacci level signals the correction is likely becoming a reversal, not a continuation, and the trade is exited without exception.

## Entry Criteria

### Gate 1 — Weekly Trend Confirmation (mandatory binary gate — all three must pass)

*Based on `INS-triple-weekly-confirmation-system-for-daily-trade-entries` (sources: `R142`, `C130`, `N044`). No daily setup is evaluated until this gate passes.*

- [ ] **Weekly channel direction:** Price is trading above the most recent 4-week high (weekly channel breakout in place) — confirms uptrend per the weekly rule (`C130`)
- [ ] **Weekly MACD/Stochastics alignment:** Weekly MACD histogram is positive (above zero), OR weekly Stochastics %K is above %D — confirms trend direction at weekly timeframe (`R142`)
- [ ] **40-week MA filter:** Price is above the 40-week (≈ 200-day) moving average — confirms primary uptrend (`N044`)

*If any of these three fails: no entry. Do not look at the daily chart for this name until the weekly gate passes.*

---

### Gate 2 — Daily Setup Conditions (evaluated only after Gate 1 passes)

- [ ] **Prior impulsive advance identified:** Price has advanced at least 8% from a clear swing low within the prior 40 trading days, without retracing more than 38% during that advance. This establishes the "leg" from which the Fibonacci retracement is measured. *(Note: the 8% / 40-day parameters are provisional — see Open Questions #1)*
- [ ] **Correction underway:** Price has pulled back from the swing high by at least 1 ATR(14) on the daily chart — confirming a real correction is in progress, not just a 1-bar pause
- [ ] **Fibonacci zone active:** Price is within the 38%–62% Fibonacci retracement zone of the prior impulsive advance (measured from the swing low to the swing high). Calculate this zone precisely before evaluating any other daily conditions
- [ ] **Rising 50-day MA coincides:** The 50-day simple moving average is rising (today's value > value 10 bars ago) AND price is within 3% of the 50-day MA. This is the primary structural anchor (`EN004`). If the Fibonacci zone and the 50-day MA are more than 3% apart, the setup is lower quality — treat as a skip or reduce position size by 50%
- [ ] **Prior resistance-turned-support confluence (preferred, not required):** A prior chart peak or breakout level (`C064`) falls within the Fibonacci zone. When this three-way confluence exists (Fibonacci + 50MA + prior resistance), treat as highest-quality setup. When only two of three agree, treat as standard quality. When only one agrees, skip

---

### Gate 3 — Daily Entry Trigger (at least one must fire while price is in the Fibonacci/MA zone)

*Price reaching the zone is a condition, not a signal. The trigger is what initiates the position.*

- [ ] **RSI recovery trigger:** Daily 14-period RSI crosses back above 40, rising from below 40. This signals oversold recovery in an uptrend (`EN041`, `N165`). RSI must have been below 40 on at least one of the three prior bars — prevents chasing a RSI already well above 40
- [ ] **Dual oscillator trigger (higher quality):** Daily Stochastics %K crosses above %D while both are below 30, AND daily RSI is below 50. Per Murphy, best signals occur when both oscillators are simultaneously in oversold territory (`C149`). This trigger is rarer but higher quality — use full position size when it fires
- [ ] **Price action trigger:** A bullish reversal candle (hammer, bullish engulfing, or morning star) closes above the prior bar's high while price remains within the Fibonacci zone. Volume on the trigger bar must be at or above the 10-day average volume — confirming participation at the support level

*If a trigger fires but price has already moved more than 1.5% above the 50-day MA or above the 38% Fibonacci level: skip. The entry has been missed. Do not chase.*

## Exit Criteria

### Stop Loss — Hard Rule (no exceptions)

- **Primary stop:** A daily closing price below the 62% Fibonacci retracement level invalidates the thesis. Per Murphy's explicit rule (`RG006`): *"If prices move beyond the two-thirds point, the odds then favor a trend reversal rather than just a retracement."* Exit on the close, not intraday — a single intraday pierce is not sufficient. Intraday violations are monitored but position is held until a closing violation is confirmed
- **Maximum stop distance:** If the distance from entry to the 62% level exceeds 7% of entry price, the setup does not meet the 3:1 R:R requirement at typical targets — skip the trade rather than widening risk. See Position Sizing below
- **Gap-through stop:** If price opens more than 1% below the 62% level on a gap, exit at market open — do not wait for the close

### Take Profit / Target

- **Primary target:** The prior swing high (the high from which the pullback began). This is the most structurally defensible target — previous resistance revisited
- **Secondary target (extended runs):** If price breaks above the prior swing high with above-average volume, trail the stop to below the breakout bar's low and hold for the measured-move extension (height of prior advance added to the breakout point)
- **Partial exit rule:** Close 50% of the position when price reaches a prior resistance level or 1.5× R (whichever comes first) — locks in profit and reduces risk on the remainder to zero or near-zero

### Time Stop

- If price is still within the entry Fibonacci zone (has not moved meaningfully toward target) after 12 trading days, exit the position regardless of P&L. A stalling correction suggests the impulsive energy has dissipated (`E034`)

### Trailing Stop (after partial exit)

- Once 50% is closed, trail the stop on the remainder to below each successive higher swing low on the daily chart. Exit if a swing low is violated on a closing basis

## Risk Rules Applied

- [ ] **PS-001:** Maximum single position risk = 1% of total capital. Hard limit
- [ ] **PS-004:** Position size calculated before entry, never estimated: `size = (1% of capital) ÷ (entry price − 62% Fibonacci level)`. This formula ties risk precisely to the structural stop from Murphy's two-thirds rule
- [ ] **PS-002:** Check total portfolio risk before entry. If existing positions already consume 4% of the 5% portfolio risk budget, skip this trade
- [ ] **LL-001:** Daily loss limit 2%. If hit, stop trading for the day — do not take this setup after a losing day that has approached the limit
- [ ] **LL-003:** Single trade max loss = 1% of capital (enforced by PS-001 and the position sizing formula)
- [ ] **PT-001:** Minimum 30 days paper trading before live consideration
- [ ] **RG032:** 3:1 minimum reward-to-risk. Before entry: confirm `(prior swing high − entry) ÷ (entry − 62% Fibonacci level) ≥ 3.0`. If less than 3.0 at any quality level, skip

## Supporting Evidence

- [[C050-secondary-trend-retracement-range]] — Dow: secondary corrections retrace one-third to two-thirds of prior move; 50% most common. Establishes the theoretical basis for *why* Fibonacci zones are where corrections end
- [[N085-fibonacci-percentage-retracements-38-50-62]] — Murphy (pp. 336–338): 38%, 50%, 62% as specific retracement zones; strong trends stop at 38%, weaker trends at 62%. Defines the entry zone boundaries
- [[C347-percentage-retracements]] — Murphy (pp. 85–87): one-third and two-thirds levels as the structural anchors, 50% as most-watched. Corroborates the Fibonacci zones from classical Dow perspective
- [[RG006-two-thirds-retracement-as-critical-reversal-level]] — Murphy (p. 86): explicit rule that a close beyond two-thirds signals trend reversal, not correction. This note is the direct source of the stop rule
- [[EN041-oscillator-entry-strategy-in-trending-markets]] — Murphy (p. 251): buy when oversold in an uptrend. The philosophical anchor for the oscillator trigger requirement
- [[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]] — Murphy (p. 256): weekly signals must filter daily signals; MACD and Stochastics specifically. Source for Gate 1 weekly filter requirement
- [[C064-previous-peaks-as-future-support-in-uptrend]] — Murphy (pp. 82–84): prior resistance becomes support on corrections in uptrend. Source for the third confluence element in the setup quality tier
- [[R213-fibonacci-tools-as-secondary-inputs]] — Murphy (p. 380): Fibonacci tools are secondary inputs that complement primary tools (trendlines, MAs). Explicitly demotes Fibonacci to secondary role — this note justifies the MA-first architecture
- [[RG032-3-to-1-reward-to-risk-ratio]] — Minimum 3:1 R:R required before any entry. Applied as pre-entry gate using (swing high − entry) / (entry − 62% level)
- [[EN004-trendline-as-a-buying-area-in-an-uptrend]] — Murphy (p. 68): trendline provides support boundary used as buying area in uptrend. The 50-day MA plays this structural role for this strategy when price is correcting
- [[C149-rsi-vs-stochastics-volatility-comparison]] — Murphy (p. 249): best signals when both RSI and Stochastics are simultaneously oversold. Source for the dual oscillator trigger (highest-quality trigger variant)
- [[N165-relative-strength-index-rsi-overboughtoversold-levels]] — Murphy (pp. 130, 131–135): RSI below 30 = oversold; 9 or 14-period standard. Defines RSI recovery trigger threshold
- [[INS-2026-07-19-triple-weekly-confirmation-system-for-daily-trade-entries]] — Discovery Engine insight (actionability 4/5): three independent weekly gates (channel, MACD/Stochastics, 40-week MA) must all confirm before daily entry. Source for Gate 1 architecture

## Counter-Evidence

### Failure Mode 1 — Strategy requires a trending market; fails in choppy conditions

This is a trend-following variant and inherits the core weakness: mechanical trend-following systems only work in certain environments. Murphy is explicit that these systems only work approximately 30% of the time — the rest being choppy, non-trending conditions (`E034`). Moving averages specifically perform poorly in ranging markets (`E022`). The weekly gate reduces but does not eliminate this risk — a trend can be confirmed on the weekly chart but choppy on the daily, producing repeated stop-outs at the Fibonacci zone.

*Mitigation: if a prior pullback to the same zone produced a stop-out, treat the next setup in the same name with reduced size (50%) until a full leg completes without the 62% level being closed through.*

### Failure Mode 2 — Cannot distinguish correction from new trend at the time of entry

This is Murphy's own stated hardest problem: distinguishing a secondary correction within a trend from the first leg of a new trend in the opposite direction (`E004`). At the moment of entry, the evidence is ambiguous — a correction to the 50% Fibonacci level looks identical to the start of a reversal. The 62% stop rule (`RG006`) is the circuit breaker, but it fires after a loss, not before.

*Pre-entry warning signs of a reversal rather than a correction (exit before stop if two or more are present):*
- *Volume is expanding on the down bars, not the up bars, during the pullback*
- *The 50-day MA itself has begun declining (not just price falling away from a rising MA)*
- *A prior swing low has been violated on a closing basis during the pullback (broken uptrend structure per Dow)*
- *Weekly MACD histogram has crossed below zero (Gate 1 filter #2 has now failed)*

### Failure Mode 3 — Fibonacci levels are self-fulfilling and subject to crowding

Murphy warns that Fibonacci tools should be secondary inputs precisely because they are widely used and can become overcrowded (`R213`). When too many traders place buy orders at the 38% or 50% level, the level becomes a liquidity event rather than a genuine support zone — it is hit, triggering a brief bounce, and then fails as stop-hunt selling pushes through it. The 50-day MA coincidence requirement partially mitigates this: when the MA and Fibonacci agree, the support has both algorithmic (MA) and technical (Fibonacci) constituency. When only Fibonacci is at the level with no MA or prior structure nearby, treat as lowest-quality.

*Active check: before entering, verify the 50-day MA is within 3% of the Fibonacci entry zone. If it is not, skip or reduce size by 50%.*

## Backtest / Paper Trade Log

- Paper trade log: *not started — requires PT-001 (30-day minimum)*
- Backtest results: *not started — see US-014 for library selection*
- Target sample size before evaluation: ≥ 20 completed trades covering at least one full market cycle (trending + pullback period)

## Open Questions

*These must be resolved by paper trading and backtesting before this strategy advances from `hypothesis` to `tested`.*

1. **MA period:** Is the 50-day MA the correct primary anchor for swing trades, or does the 20-day MA produce better entries? The 50-day is standard for intermediate trends; the 20-day may give earlier, tighter entries at the cost of more false signals. Measure: hit rate and average R at each MA period across ≥ 20 trades

2. **Fibonacci entry zone:** Does the 38% Fibonacci entry outperform the 50% entry in backtests? The 38% level offers more room to target but fires less often. The 50% level is more accessible but leaves less room before the 62% stop. Measure: average R-multiple at 38% vs 50% entry across the same setups

3. **Weekly gate practicality:** Does requiring all three weekly gate conditions simultaneously reduce the entry frequency to the point of being impractical (fewer than 1–2 trades per month)? If so, which single gate has the highest filtering power and should be kept as the mandatory condition? Measure: count setups that pass all three gates vs. each gate individually across a representative stock universe

4. **Trigger quality:** Which entry trigger (RSI recovery vs. dual oscillator vs. price action) produces the highest average R-multiple? The dual oscillator trigger is theoretically superior but rarer — does the wait for it actually improve outcomes vs. taking the RSI-only trigger? Measure: tag each completed paper trade with which trigger fired and compare outcomes

5. **Volume requirement on pullback:** Murphy's volume principles (`R003`) suggest volume should decline during a correction and expand on resumption. Should declining pullback volume be added as a required entry condition? Currently it is not in the entry criteria. Measure: compare outcomes for setups where pullback volume was declining vs. expanding

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-19 | Strategy created | US-052 schema; revised instructions from pre-build critical review |
