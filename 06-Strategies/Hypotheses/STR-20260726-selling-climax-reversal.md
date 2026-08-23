---
id: STR-20260726-selling-climax-reversal
type: strategy
status: killed
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: high-volatility
core_idea: reversal
direction: long-only
confidence: medium
publish_enabled: false
publish_channel: stocks
source: HermesForge Discovery Cycle W32
source_authors: Dan Keseloff + Hermes
source_title: "Selling Climax Reversal — High-Volatility Regime Strategy"
source_published: 2026-07-26
evidence_links:
  - N006-selling-climax-bottom-reversal-day
  - N162-selling-climax
  - N003-reversal-day-definition
  - N155-reversal-days
  - R033-reversal-day-significance-factors
  - R031-reversal-day-significance-factors
  - N013-volume-as-a-filter-for-false-breakouts
  - C084-differences-between-tops-and-bottoms
  - RG032-3-to-1-reward-to-risk-ratio
tags: [strategy, hypothesis, reversal, selling-climax, high-volatility, swing, long-only]
topic: strategies
has_quotes: false
scanner_module: scanner_m_selling_climax

strategy_id: STR-M-selling-climax
---
# STR-M: Selling Climax Reversal

## Graph Properties

prior_art_query:: [[Discoveries-2026-W32-high-vol]]
regime_node:: [[REGIME-high-volatility]]
learns_from:: [[FAIL-STR-E-rsi-mean-reversion]] (add regime filter), [[FAIL-STR-H-first-pullback]] (keep filters simple), [[STR-L-phase1b]] (volume filter preserves edge)
correlates_with:: [[STR-20260726-eufearia-cci-reversal|STR-J EUFEARIA CCI]] (both reversal-based, different regime)
produced_by:: [[Researcher]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
governed_by:: [[RISK_RULES]]

## Core Hypothesis

When a stock experiences a multi-day sharp decline (3+ consecutive down days) during a period of elevated volatility (ATR/Close > 2x its 50-day average), and the decline culminates in a reversal day where price makes a new low but closes above the prior day's close on heavy volume (>= 2x average), the selling pressure is likely exhausted. This is the selling climax pattern described by Murphy (N006, N162). The subsequent absence of selling pressure creates a vacuum that prices rally to fill.

**Why high-volatility regime:** The high-volatility regime has ZERO strategies tried. Selling climaxes by definition occur during elevated volatility. ATR/Close > 2x its 50-day average identifies the regime without requiring VIX data.

**Why this differs from STR-E (killed):** STR-E was RSI mean-reversion without regime gating — it bought oversold stocks regardless of volatility context. STR-M gates on elevated volatility (the regime where capitulation actually occurs), requires a multi-day decline (not just an oscillator reading), and uses the reversal-day close as the trigger (structural, not oscillator-based).

**Why this differs from STR-J (WATCH):** STR-J uses CCI extremes for mean-reversion in low-volatility regimes. STR-M uses selling-climax dynamics in high-volatility regimes. They target opposite volatility environments.

## Entry Criteria

### 1. Regime Filter (High-Volatility)
- ATR(14) / Close > 2.0 × (50-day average of ATR(14)/Close)
- This identifies elevated volatility without needing VIX data
- Only 1 regime filter (lesson from STR-H: keep filters simple)

### 2. Setup (Multi-Day Decline)
- Close lower than prior day's close for >= 3 consecutive days
- This ensures there is an actual decline to reverse, not just noise

### 3. Reversal Day Trigger
- Price makes a new low for the decline (lower than any of the prior 3 days' lows)
- Close is above the prior day's close (reversal day per N003)
- Volume >= 2.0× the 20-day average volume (heavy volume confirms capitulation per R033)
- Long-only: price must be above 200-day SMA (structural bull context)

## Exit Criteria

- **Stop loss:** Reversal day's low. If price breaks below the capitulation low, the reversal failed.
- **Take profit:** 3:1 R:R fixed target (per RG032). Partial exit 50% at 2:1, remainder at 3:1.
- **Time stop:** 15 bars. If no meaningful progress within 3 weeks, exit.
- **Trailing stop:** After 2:1 reached, trail remainder below each successive higher swing low.

## Risk Management

- Risk per trade: 1% of equity (per [[RISK_RULES]] PT-001)
- Max portfolio heat: 15%
- Long-only: Selling climaxes in equities are bottom-finding patterns

## Why This Should Work

| Factor | Rationale | Murphy Reference |
|--------|-----------|-----------------|
| High-vol regime gate | Selling climaxes occur during elevated vol | N006, N162 |
| Multi-day decline | Ensures genuine decline to reverse | N155 |
| Reversal day close | Structural reversal signal | N003, N146 |
| Heavy volume | Confirms capitulation/exhaustion | R033, N013 |
| Wide range | Wider range = more significant reversal | R033, R031 |
| 3:1 R:R | Asymmetric payoff after capitulation | RG032 |

## Data Requirements

- **Stocks:** Daily OHLCV from yfinance (529-ticker universe, already cached)
- **Indicators:** ATR(14), SMA(200), volume — all computable from OHLCV
- **No external data needed** (no VIX required — ATR/Close ratio as vol proxy)

## Limitations

1. Daily bars only — no intraday reversal confirmation
2. Survivorship bias — universe is current S&P constituents
3. ATR/Close ratio as vol proxy may not perfectly replicate VIX regime
4. 3-day decline requirement may miss V-shaped reversals
5. 2x volume requirement may be too strict for low-volume stocks

tested_in:: [[STR-M-phase1a]]
killed_by:: [[FAIL-STR-M-selling-climax]]

## Phase 1A Plan

Standalone scanner: `scanner_m_selling_climax.py` (not added to live registry)

## Phase 1A Result (2026-07-26)

| Metric | Value |
|--------|-------|
| Total signals | 6 |
| Signals/year | 1.1 |
| Average R | -1.000 |
| Win rate | 0.0% |
| Sub-periods positive | 0/3 |
| **Classification** | **❌ KILL** |

All 6 signals were stopped out. Phase 1B perturbations (ATR-based stop, lower target, looser filters) could not rescue. Best variant V6 (all filters loosened) achieved -0.212 avg R. See [[STR-M-phase1a]] for full details.

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy created | Second graph-aware discovery cycle — fills high-volatility regime gap |
| 2026-07-26 | Strategy killed at Phase 1A | -1.000 avg R, 0% win rate. No Phase 1B rescue found. |

## Related

- [[REGIME-high-volatility]]
- [[Discoveries-2026-W32-high-vol]]
- [[STRATEGIES-MOC]]
- [[FAIL-STR-E-rsi-mean-reversion]]
- [[ADR-004-Phase1-Validation-Framework]]

## Evidence Base (auto-generated from evidence_links)

- [[N006-selling-climax-bottom-reversal-day]]
- [[N162-selling-climax]]
- [[N003-reversal-day-definition]]
- [[N155-reversal-days]]
- [[R033-reversal-day-significance-factors]]
- [[R031-reversal-day-significance-factors]]
- [[N013-volume-as-a-filter-for-false-breakouts]]
- [[C084-differences-between-tops-and-bottoms]]
- [[RG032-3-to-1-reward-to-risk-ratio]]

