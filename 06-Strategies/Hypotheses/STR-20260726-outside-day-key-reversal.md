---
id: STR-20260726-outside-day-key-reversal
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
source_title: "Outside Day Key Reversal — High-Volatility Regime Strategy"
source_published: 2026-07-26
evidence_links:
  - N004-outside-day-as-reversal-confirmation
  - N146-key-reversal-day
  - N003-reversal-day-definition
  - R033-reversal-day-significance-factors
  - R031-reversal-day-significance-factors
  - N155-reversal-days
  - N013-volume-as-a-filter-for-false-breakouts
  - RG032-3-to-1-reward-to-risk-ratio
  - C084-differences-between-tops-and-bottoms
tags: [strategy, hypothesis, reversal, outside-day, key-reversal, high-volatility, swing, long-only]
topic: strategies
has_quotes: false
---
# STR-N: Outside Day Key Reversal

## Graph Properties

prior_art_query:: [[Discoveries-2026-W32-high-vol]]
regime_node:: [[REGIME-high-volatility]]
learns_from:: [[FAIL-STR-H-first-pullback]] (keep filters simple), [[FAIL-STR-F-bollinger-squeeze]] (don't use band-width as stop), [[STR-L-phase1b]] (volume filter matters)
correlates_with:: [[STR-20260726-selling-climax-reversal|STR-M Selling Climax]] (both reversal-based, different trigger mechanics)
produced_by:: [[Researcher]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
governed_by:: [[RISK_RULES]]

## Core Hypothesis

After a short-term decline (2+ consecutive down days) during a period of elevated volatility (ATR/Close > 1.5x its 50-day average), a bar that forms an outside day (engulfs the prior bar's range) and closes above the prior bar's close (key reversal day) signals a high-probability reversal. The outside day pattern combined with the key reversal close and heavy volume creates a three-layered reversal confirmation that Murphy identifies as carrying maximum significance (N004, R033).

**Why high-volatility regime:** Outside days and key reversals are more significant when they occur with wider ranges (R033: "the wider the range, the more significant"). High-volatility regimes produce wider ranges by definition. ATR/Close > 1.5x its 50-day average identifies this regime.

**Why this differs from STR-M:** STR-M requires a 3+ day decline and 2x volume (extreme capitulation). STR-N uses a 2+ day decline threshold and focuses on the outside day structural pattern. STR-N catches reversals that may not reach full capitulation but still show strong reversal dynamics. Lower vol threshold (1.5x vs 2.0x) captures a broader set of high-vol environments.

**Why this differs from STR-E (killed):** STR-E used RSI oversold readings without structural confirmation. STR-N requires a structural outside-day reversal pattern with volume confirmation — the pattern itself is the signal, not an oscillator reading.

## Entry Criteria

### 1. Regime Filter (Elevated Volatility)
- ATR(14) / Close > 1.5 × (50-day average of ATR(14)/Close)
- 1 filter only (lesson from STR-H: keep filters simple)

### 2. Setup (Short-Term Decline)
- Close lower than prior day's close for >= 2 consecutive days
- Ensures a decline exists to reverse

### 3. Outside Day + Key Reversal (3 conditions, 1 structural pattern)
- **Outside day:** Today's high > prior day's high AND today's low < prior day's low (engulfs prior range, per N004)
- **Key reversal:** Today makes a new low for the decline then closes above prior day's close (per N146, N003)
- **Volume:** Today's volume >= 1.5× the 20-day average (confirms genuine participation per N013)

### 4. Trend Filter
- Price above 200-day SMA (long-only, structural bull context)

## Exit Criteria

- **Stop loss:** Outside day's low. If price breaks below the reversal bar's low, the reversal failed.
- **Take profit:** 3:1 R:R fixed target (per RG032). Partial exit 50% at 2:1.
- **Time stop:** 12 bars. If no meaningful progress within ~2.5 weeks, exit.
- **Trailing stop:** After 2:1 reached, trail remainder below each successive higher swing low.

## Risk Management

- Risk per trade: 1% of equity (per [[RISK_RULES]] PT-001)
- Max portfolio heat: 15%
- Long-only: Outside day reversals after declines are bottom-finding patterns

## Why This Should Work

| Factor | Rationale | Murphy Reference |
|--------|-----------|-----------------|
| Elevated vol regime | Wide ranges make reversals more significant | R033, R031 |
| Outside day | Engulfing range confirms reversal force | N004 |
| Key reversal close | Close above prior close = reversal signal | N003, N146 |
| Volume confirmation | Heavy volume = genuine participation | N013, R033 |
| 2-day decline | Shorter setup than STR-M, broader signal pool | N155 |
| 3:1 R:R | Asymmetric payoff after reversal | RG032 |

## Differentiation from STR-M

| Factor | STR-M (Selling Climax) | STR-N (Outside Day) |
|--------|----------------------|---------------------|
| Decline requirement | 3+ consecutive down days | 2+ consecutive down days |
| Vol threshold | ATR/Close > 2.0x avg | ATR/Close > 1.5x avg |
| Volume threshold | 2.0x average | 1.5x average |
| Structural pattern | Reversal day close | Outside day + key reversal |
| Signal type | Capitulation exhaustion | Reversal pattern structure |
| Expected frequency | Lower (stricter) | Higher (looser) |

## Data Requirements

- **Stocks:** Daily OHLCV from yfinance (529-ticker universe, already cached)
- **Indicators:** ATR(14), SMA(200), volume — all computable from OHLCV
- **No external data needed**

## Limitations

1. Daily bars only — no intraday outside day confirmation
2. Survivorship bias — universe is current S&P constituents
3. Outside day requirement may still be relatively rare
4. 1.5x vol threshold is less selective than STR-M's 2.0x
5. 12-bar time stop may be too short for slow reversals

tested_in:: [[STR-N-phase1a]]
killed_by:: [[FAIL-STR-N-outside-day]]

## Phase 1A Plan

Standalone scanner: `scanner_n_outside_day.py` (not added to live registry)

## Phase 1A Result (2026-07-26)

| Metric | Value |
|--------|-------|
| Total signals | 28 |
| Signals/year | 4.2 |
| Average R | -0.037 |
| Win rate | 46.4% |
| Sub-periods positive | 1/3 (period3_current: +0.332) |
| **Classification** | **❌ KILL** |

Phase 1B best variant (V5: 3-day decline + 2:1 + 20-bar): +0.125 avg R, 60% win rate, still below 0.2 threshold. Period3_current shows strong edge (+0.574) but overall avg R is insufficient. See [[STR-N-phase1a]] for full details.

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy created | Second graph-aware discovery cycle — fills high-volatility regime gap |
| 2026-07-26 | Strategy killed at Phase 1A | -0.037 avg R overall. Regime-dependent edge in period3_current not enough. |

## Related

- [[REGIME-high-volatility]]
- [[Discoveries-2026-W32-high-vol]]
- [[STRATEGIES-MOC]]
- [[ADR-004-Phase1-Validation-Framework]]