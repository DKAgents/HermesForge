---
id: STR-20260730-atr-contraction-breakout
type: strategy
status: watch
created: 2026-07-30
updated: 2026-07-30
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: low-volatility
core_idea: volatility-breakout
direction: long-only
confidence: medium
publish_enabled: false
publish_channel: stocks
source: HermesForge Discovery Cycle W31
source_authors: Dan Keseloff + Hermes
source_title: "ATR Contraction Breakout — First Graph-Aware Hypothesis"
source_published: 2026-07-30
evidence_links:
  - N140-average-true-range-atr-definition
  - N195-standard-deviation-and-bollinger-bands
  - N041-bollinger-bands-construction
  - C124-bollinger-band-width-as-volatility-measure
  - N099-adx-line-measuring-directional-movement
  - N101-adx-line-trending-vs-trading-market-identification
  - R215-adx-level-thresholds-40-and-20
  - R216-using-adx-to-select-markets-for-trend-following
  - N044-long-term-moving-averages-on-weekly-charts
  - R082-breakouts-must-be-accompanied-by-heavy-volume
tags: [strategy, hypothesis, volatility, atr, breakout, low-volatility, swing, long-only]
---

# STR-L: ATR Contraction Breakout

## Graph Properties

prior_art_query:: [[Discoveries-2026-W31-graph-aware]]
regime_node:: [[REGIME-low-volatility]]
improves_upon:: [[STR-20260726-bollinger-squeeze-breakout-entry|STR-F (killed)]]
correlates_with:: [[STR-20260728-adaptive-trend|STR-I (trend-following, uncorrelated)]]
learns_from:: [[FAIL-STR-F-bollinger-squeeze]] (stricter contraction), [[FAIL-STR-G-relative-strength]] (add confirmation), [[FAIL-STR-H-first-pullback]] (keep filters simple)
tested_in:: [[STR-L-phase1a]], [[STR-L-phase1b]]
produced_by:: [[Researcher]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
governed_by:: [[RISK_RULES]]

## Core Hypothesis

When ATR contracts to a multi-month low (prolonged low-volatility period) and ADX confirms a non-trending environment (ADX < 18), the subsequent breakout above the recent range tends to produce a sustained directional move. This strategy enters at the contraction-to-expansion inflection point.

**Why low-volatility regime:** The low-volatility regime has ZERO strategies tried. Low-volatility periods precede explosive moves. This fills the second-largest regime gap in the portfolio.

**Why ATR contraction vs Bollinger squeeze (STR-F):** STR-F was killed because the Bollinger band-width squeeze condition was too permissive (60-bar low is common). ATR contraction is more robust because:
1. ATR captures true range (including gaps), not just close-to-close volatility
2. Requiring ATR at a 120-bar low (6 months) is much stricter than 60-bar
3. ADX < 18 adds a second confirmation that the low volatility is genuine (not just a brief pause in a trend)

**Improvement over STR-F (killed):**

| STR-F (Killed) | STR-L (This) | Why Better |
|----------------|-------------|------------|
| Bollinger band-width 60-bar low | ATR 120-bar low | Stricter, captures true range |
| No regime confirmation | ADX < 18 gate | Confirms genuine low-vol regime |
| Bidirectional (shorts dragged) | Long-only | Shorts structurally negative in equities |
| 2:1 R:R target rarely hit (2%) | Trailing stop after breakout | Lets winners run, no fixed target |
| 10-bar time stop | 20-bar time stop | More room for breakout to develop |

## Entry Criteria

### 1. Volatility Contraction
- ATR(14) is at its lowest level in the trailing 120 bars (6 months)
- This identifies a prolonged low-volatility period, not a brief dip

### 2. Regime Confirmation (1 filter — lesson from STR-H)
- ADX(14) < 18 (confirmed non-trending, low-volatility regime)
- This ensures we're entering at a genuine low-vol inflection, not a pause in an existing trend

### 3. Breakout Trigger
- Price closes above the highest high of the trailing 20 bars (range breakout)
- Volume on breakout day > 1.5x average 20-day volume (per [[R082-breakouts-must-be-accompanied-by-heavy-volume]])

### 4. Trend Filter
- Price above 200-day SMA (long-only, don't short in low-vol)

## Exit Criteria

- **Stop:** Breakout day low. If price breaks below the breakout candle, the breakout failed.
- **Target:** None (trailing stop only). The volatility expansion can produce large moves — don't cap them.
- **Trailing stop:** ATR(14) × 2.0 below the highest close since entry. Tightens as volatility expands.
- **Time stop:** 20 bars. If no meaningful move within 4 weeks, exit.

## Risk Management

- Risk per trade: 1% of equity (per [[RISK_RULES]] PT-001)
- Max portfolio heat: 15%
- Long-only: Breakout shorting in low-vol is riskier (catching falling knives)

## Why This Should Work Where STR-F Failed

| STR-F Issue | STR-L Fix |
|-------------|-----------|
| Squeeze too common (60-bar low) | 120-bar low is much rarer, identifies prolonged contraction |
| No regime confirmation | ADX < 18 gate confirms non-trending environment |
| 2:1 target hit only 2% of time | No fixed target — trailing stop lets winners run |
| 80% exit at time stop with tiny R | 20-bar time stop + trailing stop captures expansion |
| Bidirectional (shorts dragged) | Long-only |

## Data Requirements

- **Stocks:** Daily OHLCV from yfinance (529-ticker universe, already cached)
- **Indicators:** ATR(14), ADX(14), SMA(200), volume — all computable from OHLCV
- **No external data needed**

## Limitations (to be stated in every validation)

1. Daily bars only — no intraday breakout confirmation
2. Survivorship bias — universe is current S&P constituents, not historical
3. ATR 120-bar low may be rare in volatile markets (fewer signals)
4. Volume requirement may filter out valid breakouts in low-volume stocks

## Phase 1A Plan

Standalone scanner: `scanner_l_atr_contraction.py` (not added to live registry)


## Phase 1B Perturbation Results (2026-07-30)

| Variant | ATR Lookback | ADX | Vol | Sigs/100tk | Avg R | Win% |
|---------|-------------|-----|-----|-----------|-------|------|
| V1: Baseline | 120 | <18 | Yes | 1.3 | +0.582 | 57.1% |
| V2: ATR 60 | 60 | <18 | Yes | 2.8 | +0.168 | 40.0% |
| V4: Looser ADX, no vol | 60 | <25 | No | 110 | -0.203 | 17.3% |
| V8: ADX <20 | 60 | <20 | Yes | 2.0 | -1.000 | 0.0% |

**Decision: WATCH** — Baseline config is optimal. Volume filter preserves edge, ADX<18 is the frequency bottleneck. Per updated ADR-004, low frequency is not a kill reason. Strategy contributes occasional high-conviction setups to portfolio.

See [[STR-L-phase1b]] for full details.

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-30 | Strategy created | First graph-aware discovery cycle — fills low-volatility regime gap + improves upon killed STR-F |

## Related

- [[REGIME-low-volatility]]
- [[REGIME-transitional]]
- [[Discoveries-2026-W31-graph-aware]]
- [[STRATEGIES-MOC]]
- [[FAIL-STR-F-bollinger-squeeze]]
- [[FAIL-STR-G-relative-strength]]
- [[FAIL-STR-H-first-pullback]]
- [[ADR-004-Phase1-Validation-Framework]]
