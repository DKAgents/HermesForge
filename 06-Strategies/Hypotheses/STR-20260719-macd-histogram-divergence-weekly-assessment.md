---
id: STR-20260719-macd-histogram-divergence-weekly-assessment
type: strategy
status: hypothesis
created: 2026-07-19
last_reviewed: 2026-07-19
version: "1.0"
author: HermesForge
name: MACD Histogram Divergence with Weekly Trend Assessment
core_idea: reversal
market_regime: trending
trade_style: swing
asset_class: stocks
timeframe: daily
direction: bidirectional
confidence: low
tags: [strategy, hypothesis, macd, divergence, reversal, oscillator, swing]
evidence_links:
  - N062-macd-divergence-analysis
  - C154-macd-histogram-momentum-warning-signals
  - N067-macd-histogram-as-early-warning-signal
  - R140-oscillator-weight-relative-to-trend-maturity
  - RG017-overboughtoversold-readings-in-strong-trends
  - N165-relative-strength-index-rsi-overboughtoversold-levels
  - C149-rsi-vs-stochastics-volatility-comparison
  - R142-weekly-signals-as-trend-filters-for-macd-and-stochastics
  - INS-2026-07-19-triple-weekly-confirmation-system-for-daily-trade-entries
  - RG032-3-to-1-reward-to-risk-ratio
  - RG031-protective-stop-placement-as-an-art
  - RG035-combining-technical-factors-with-money-management-for-stop-p
  - R305-oscillators-and-trend-importance
  - E034-mechanical-trend-following-systems-work-only-in-certain-envi
---

# MACD Histogram Divergence with Weekly Trend Assessment

## Thesis

This strategy acts on **momentum divergence between price and MACD** — not on overbought or oversold readings alone.

Murphy explicitly warns (`RG017`) that overbought conditions in a strong trend are unreliable signals: the oscillator can stay elevated for many bars while price continues higher. This strategy avoids that trap entirely by requiring a structural divergence: price makes a new swing extreme while MACD momentum simultaneously moves in the opposite direction. That separation between price and momentum — not the overbought reading itself — is the signal.

The philosophical rationale comes directly from the vault: `R140` states that oscillators should be given *less* weight in the early stages of a trend, and *greater* weight as the trend matures. This strategy is designed to act on that principle — divergence signals are only evaluated after a trend has been running long enough for momentum exhaustion to be meaningful.

**Why the weekly filter is a soft sizing modifier, not a hard gate:** A reversal strategy by definition fires while the opposing trend is still intact. If the weekly trend were a binary pass/fail gate (as it is in trend-following Strategy A), it would eliminate nearly every valid divergence setup — because the weekly chart is still upward when daily exhaustion appears. Instead, weekly trend strength governs *how much* risk to take: the stronger the opposing weekly current, the smaller the position. This is a deliberate design choice, not an oversight.

**Direction:** This strategy is bidirectional. Bearish divergence setups apply in uptrends; bullish divergence setups apply in downtrends. All rules below are stated for both directions.

---

## Entry Criteria

Work through these gates in order. Any failure = no trade.

### Gate 1 — Trend Maturity (mandatory binary gate)

Confirms the trend has been running long enough for momentum divergence to be meaningful.

**Bearish setup:** The daily MACD line (not the histogram) has been **continuously above zero** for at least **15 consecutive bars**.

**Bullish setup:** The daily MACD line has been **continuously below zero** for at least **15 consecutive bars**.

If this condition is not met, do not evaluate the divergence signal. A divergence that fires too early in a trend — before the MACD has spent meaningful time above/below zero — is unreliable.

*Evidence: `N062` — MACD lines above/below zero indicate trend direction and duration of the underlying move.*

> ADX-based maturity definitions (ADX ≥ 25 and declining) are documented in Open Questions as a v2 enhancement candidate.

---

### Gate 2 — Core Divergence Signal (two stages, both required)

**Stage 1 — Histogram Momentum Shift (early warning):**
- Price makes a new swing extreme (higher high for bearish; lower low for bullish) relative to the prior comparable swing.
- The MACD histogram bar at that new extreme is **smaller in absolute value** than the histogram bar at the prior comparable swing extreme (histogram is narrowing toward zero).
- Minimum **2 consecutive bars** of histogram narrowing required — a single narrowing bar is noise.
- Stage 1 fires first. It is the early warning, not the trade signal.

*Evidence: `C154` — histogram narrowing toward zero warns of momentum loss before price confirms. `N067` — histogram turns precede actual crossover signals, providing earlier warnings.*

**Stage 2 — MACD Line Divergence (confirmation):**
- Price has made a **new swing high** (bearish) or **new swing low** (bullish) vs. the prior comparable swing.
- The **MACD line itself** has made a **lower high** (bearish) or **higher low** (bullish) vs. its reading at the prior price swing extreme.
- This is the confirmation. Stage 1 alone is not a tradeable signal.

*Evidence: `N062` — bearish divergence exists when MACD lines are well above the zero line and start to weaken while prices continue higher; bullish divergence is the mirror.*

**Divergence invalidation rule:** If, after Stage 1 fires, price makes a new extreme AND the MACD line makes a new extreme in the same direction (equal or higher high for bearish), the divergence is resolved upward and the setup is void. Do not enter. Start over.

---

### Gate 3 — Entry Trigger (one required)

The divergence identifies the setup. A trigger initiates the position. Do not enter on divergence alone.

Choose one of the following:

1. **MACD crossover:** MACD line crosses below its signal line (bearish) or above (bullish) — the classic post-divergence crossover. Most common trigger.
2. **Price action break:** Price closes below the prior bar's low (bearish) or above the prior bar's high (bullish) after forming the divergence swing extreme — selling/buying pressure confirmed by price.
3. **Reversal candle:** A bearish reversal candle (shooting star, bearish engulfing, evening star) or bullish reversal candle (hammer, bullish engulfing, morning star) closes at or near the divergence swing extreme on above-average volume.

---

## Position Sizing

### Step 1 — Confirmation Level (sets base risk)

| Level | Condition | Base Risk |
|-------|-----------|-----------|
| **Level 2 — Full size** | Stage 1 + Stage 2 + RSI ≥ 70 (bearish) or ≤ 30 (bullish) OR Stochastics > 80 (bearish) or < 20 (bullish) | 1.0% of capital |
| **Level 1 — Reduced size** | Stage 1 + Stage 2 only, no oscillator corroboration | 0.5% of capital |

*Evidence: `N165` — RSI above 70 / below 30 are overbought/oversold levels; divergence from price at these extremes is a key signal. `C149` — RSI and Stochastics reach extremes at different frequencies; simultaneous extremes produce the best signals. `INS-dual-oscillator-gate` — requiring both oscillators to confirm simultaneously raises the bar beyond what either alone provides.*

### Step 2 — Weekly Trend Scaling (applied to Level base risk)

Assess weekly trend strength using the three-gate framework (`INS-triple-weekly`): (1) weekly price channel direction, (2) weekly MACD/Stochastics alignment, (3) price vs. 40-week MA.

| Weekly Gates Passing | Weekly Scaling Factor | Rationale |
|---------------------|----------------------|-----------|
| All 3 passing | × 0.5 | Trading directly against a fully intact weekly trend — highest risk |
| 1 of 3 failing | × 0.75 | Weekly trend showing early deterioration |
| 2 or 3 failing | × 1.0 | Weekly trend is itself weakening — supports reversal thesis |

*Evidence: `R142` — MACD and Stochastics daily signals require weekly-chart trend confirmation. `INS-triple-weekly` — three-layer weekly confirmation framework.*

### Step 3 — Full Sizing Matrix

| | All 3 weekly gates | 1 gate failing | 2–3 gates failing |
|---|---|---|---|
| **Level 2 (1.0% base)** | 0.50% risk | 0.75% risk | 1.00% risk |
| **Level 1 (0.5% base)** | 0.25% risk | 0.375% risk | 0.50% risk |

### Step 4 — Position Size Formula

```
shares = (capital × final_risk%) / |stop_price − entry_price|
```

**Worked example:** $100,000 account. Level 2 setup (1.0% base), 1 weekly gate failing (× 0.75) → final risk = 0.75%.
Stock at $150, stop at $153.00 (entry above swing high + 0.5 ATR buffer where ATR = $3.00 → stop = $153.00 + $1.50 = $154.50 → round to $153 for this example). Distance = $3.00.
`shares = ($100,000 × 0.0075) / $3.00 = $750 / $3.00 = 250 shares`

---

## Stop Placement

**Bearish:** Stop placed **0.5 × ATR(14) above** the swing high at which MACD divergence formed.

**Bullish:** Stop placed **0.5 × ATR(14) below** the swing low at which MACD divergence formed.

The 0.5 ATR buffer avoids noise-based stops (a tick above/below the high/low) without dramatically widening risk.

**Minimum R:R gate:** Calculate before entering. If `(entry to primary target) / (stop to entry) < 3.0` → skip the trade. R:R must be at least 3:1 before entry.

*Evidence: `RG032` — minimum 3:1 reward-to-risk ratio. `RG031` — stop placement must combine technical chart factors with money management. `RG035` — protective stops must satisfy both technical and money management criteria.*

> Do not place stops at obvious round numbers (e.g. $100.00, $150.00). If the calculated stop lands on a round number, move it 0.5–1% beyond to reduce the risk of stop hunts.

---

## Exit Criteria

### Planned Exit (target reached)
- **Primary target:** The most recent significant support level (bearish) or resistance level (bullish) on the daily chart — a prior swing low, prior breakout level, or major MA (50-day or 200-day) sitting below/above entry. Structural, not percentage-based.
- **Partial exit:** Close 50% of position at primary target.
- **Remainder:** Move stop to break-even. Trail stop below each successive lower swing high (bearish) or above each successive higher swing low (bullish) on the daily chart.

### Time Stop (no movement)
If price has **not moved toward the target within 8 bars** of entry, exit the full position. A divergence trade that stalls gives the trend time to reassert.

### Divergence Invalidation Exit
If, after entry, price makes a new swing extreme AND the MACD line makes a new extreme in the same direction, the divergence thesis is invalidated. Exit immediately regardless of P&L.

## Risk Rules Applied

- Maximum risk per trade: 1.0% of capital (Level 2 full size)
- Minimum R:R ratio: 3:1 before entry — hard gate per `RG032`
- Stop placement: 0.5 × ATR(14) beyond the divergence swing extreme — per `RG031`, `RG035`
- Weekly scaling: reduces size to 0.5× when opposing weekly trend is fully intact
- Position size formula: `shares = (capital × final_risk%) / |stop − entry|`
- Never risk more than 1.0% of capital on a single divergence trade regardless of Level or weekly factor
- Do not enter within 5 trading days of known earnings date (gap risk — no technical stop prevents gaps)
- Daily loss limit: do not open new positions if portfolio is already down 2% on the day

## Supporting Evidence

[[N062-macd-divergence-analysis]] — Core: MACD line divergence from price; lines above/below zero confirm trend duration for the maturity gate

[[C154-macd-histogram-momentum-warning-signals]] — Core: MACD histogram momentum shift is the Stage 1 early warning signal

[[N067-macd-histogram-as-early-warning-signal]] — Core: histogram turns precede crossover signals — justifies the two-stage sequential structure

[[R140-oscillator-weight-relative-to-trend-maturity]] — Philosophical anchor: oscillators gain weight as trend matures; rationale for the 15-bar maturity gate

[[RG017-overboughtoversold-readings-in-strong-trends]] — Counter-tension: overbought in strong trends is unreliable — this strategy's structural rebuttal

[[N165-relative-strength-index-rsi-overboughtoversold-levels]] — RSI ≥ 70 / ≤ 30 thresholds for Level 2 oscillator confirmation

[[C149-rsi-vs-stochastics-volatility-comparison]] — RSI and Stochastics simultaneous extremes produce best signals — justifies two-level sizing

[[R142-weekly-signals-as-trend-filters-for-macd-and-stochastics]] — Weekly trend filter rationale for MACD and Stochastics daily signals

[[INS-2026-07-19-triple-weekly-confirmation-system-for-daily-trade-entries]] — Three-gate weekly framework (channel + MACD/Stoch + 40-week MA)

[[INS-2026-07-19-dual-oscillator-confirmation-gate-for-candle-reversal-entrie]] — Dual-oscillator gate raises conviction bar beyond single oscillator alone

[[RG032-3-to-1-reward-to-risk-ratio]] — Minimum 3:1 R:R requirement — applied as hard gate before entry

[[RG031-protective-stop-placement-as-an-art]] — Stop placement must combine technical and money management criteria

[[RG035-combining-technical-factors-with-money-management-for-stop-p]] — Protective stops must satisfy both technical and money management requirements

[[R305-oscillators-and-trend-importance]] — Oscillators must be used in conjunction with prevailing trend — supports weekly assessment

[[E034-mechanical-trend-following-systems-work-only-in-certain-envi]] — Trend-following systems only work in certain environments — counter-evidence for failure mode 1

---

## Counter-Evidence and Failure Modes

### Failure Mode 1: Strong trend absorbs the divergence
The trend reasserts before the reversal materializes. Divergence can persist for many bars — even 10–20 — in a powerful move. The oscillator eventually "catches up" to price rather than price falling to the oscillator. This is the most common way this signal fails in practice.

*Citations: `RG017` (overbought unreliable in strong trend), `E034` (trend-following wins in trending environments; reversal is lower probability).*

**Mitigations in this strategy:** The 15-bar maturity gate filters setups that fire too early. The 3:1 R:R gate prevents entries where the reward does not justify the risk of trend reassertion. The 8-bar time stop limits the capital locked in a stalled trade.

### Failure Mode 2: Divergence resolves upward — oscillator catches up to price
After Stage 1 fires (histogram narrowing), price makes a new high and the MACD line makes a new high as well — the divergence is resolved in the direction of the trend, not against it. The setup is void.

*Citation: `N062` — divergence resolution conditions.*

**Rule in this strategy:** Explicitly documented as the Divergence Invalidation Rule in Gate 2. Any new price extreme accompanied by a new MACD extreme in the same direction cancels the setup entirely.

### Failure Mode 3: Gap through stop on fundamental catalyst
Earnings, macro data, or a news event causes a gap open beyond the stop level. No technical stop placement prevents this. The trade is entered at the gap open price, not the stop price — resulting in a larger-than-planned loss.

*No vault citation — this is a universal execution risk.*

**Mitigation in this strategy:** The weekly scaling factor (Rule 6 in construction) naturally reduces position size when trading against a fully intact weekly trend (× 0.5). Avoid initiating divergence trades within 5 trading days of known earnings dates. Position sizing (never more than 1.0% base risk) limits the damage of any single gap event.

---

## Open Questions

These are the research agenda for paper trading. Each question has a measurable answer after 20+ paper trades.

| # | Question | How to Answer |
|---|----------|---------------|
| OQ-1 | **ADX maturity gate** — does adding ADX(14) ≥ 25 AND declining as a secondary filter improve signal quality beyond the 15-bar MACD gate alone? | Run paper trades with and without ADX condition. Compare hit rate and average R-multiple after 20 trades per group. |
| OQ-2 | **15-bar threshold calibration** — is 15 bars the right maturity threshold? Would 10 or 20 bars produce better signal-to-noise? | Tag each paper trade with the MACD-above-zero bar count at entry. After 30 trades, compare outcomes by bar count bucket (≤10, 11–15, 16–20, >20). |
| OQ-3 | **Stage 1 as partial entry** — take 25% position on Stage 1 (histogram narrowing), add remaining 75% on Stage 2 (line divergence). Does this improve average entry price without materially increasing loss rate? | Paper trade a parallel set using staged entries vs. Stage 2 only. Compare average entry price and outcome distribution. |
| OQ-4 | **Time stop calibration** — is 8 bars the right exit window? Would 5 or 12 bars produce better outcomes? | Tag each paper trade with the number of bars held. Compare win rate and average R for trades exited at bars 1–5, 6–8, 9–12, and 13+. |
| OQ-5 | **Bidirectional symmetry** — do bullish divergence setups in downtrends perform comparably to bearish divergence setups in uptrends? | Track direction on every paper trade. After 20+ per direction, compare hit rate, average R, and average hold time. |

---

## Backtest / Paper Trade Log

*No trades recorded yet. See `09-Journal/` for trade entries when paper trading begins.*

---

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-07-19 | 1.0 | Initial hypothesis created. Two-stage MACD divergence signal, 15-bar maturity gate, two-level sizing, bidirectional rules, weekly soft sizing modifier. |

---
*Strategy created: 2026-07-19 | Schema: ADR-003 v1.0 | Validated: pending*
