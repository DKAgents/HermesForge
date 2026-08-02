---
id: STR-20260730-breadth-gated-gap-reversal
type: strategy
status: killed
created: 2026-07-30
updated: 2026-07-30
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: transitional
core_idea: gap-reversal
direction: long-only
confidence: medium
publish_enabled: false
publish_channel: stocks
source: HermesForge Discovery Cycle W31
source_authors: Dan Keseloff + Hermes
source_title: "Breadth-Gated Gap Reversal — First Graph-Aware Hypothesis"
source_published: 2026-07-30
evidence_links:
  - N009-breakaway-gap
  - N011-exhaustion-gap
  - EN069-price-gaps-as-support-and-resistance-for-timing
  - N118-advance-decline-ad-line-construction
  - N186-mcclellan-oscillator
  - N159-mcclellan-oscillator
  - N123-new-highs-vs-new-lows-indicator
  - R257-mcclellan-oscillator-overboughtoversold-levels
  - R262-ad-line-breadth-confirmation-rule
  - C024-market-breadth-indicators
  - R034-myth-gaps-are-always-filled
tags: [strategy, hypothesis, gap, breadth, reversal, transitional, swing, long-only]
topic: strategies
has_quotes: false
---
# STR-K: Breadth-Gated Gap Reversal

## Graph Properties

prior_art_query:: [[Discoveries-2026-W31-graph-aware]]
regime_node:: [[REGIME-transitional]]
improves_upon:: null
correlates_with:: [[STR-20260726-eufearia-cci-reversal|STR-J (also mean-reversion)]]
learns_from:: [[FAIL-STR-E-rsi-mean-reversion]] (add regime filter), [[FAIL-STR-H-first-pullback]] (keep filters simple)
tested_in:: [[STR-K-phase1a]]
produced_by:: [[Researcher]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
governed_by:: [[RISK_RULES]]

## Core Hypothesis

Gap-down openings in stocks that occur during oversold breadth conditions (per the McClellan Oscillator and Advance-Decline Line) tend to reverse and fill the gap when the breadth indicators begin recovering. This is a mean-reversion strategy specifically targeting the **transitional regime** where gap exhaustion signals are most reliable.

**Why transitional regime:** Gaps frequently occur at regime transitions (bull-to-bear, bear-to-bull). Breadth indicators detect whether the transition is exhaustion (likely to reverse) or continuation (likely to persist). This fills the largest regime gap in the HermesForge portfolio — no strategy currently targets transitional markets.

**Why gap-reversal vs gap-continuation:** The Murphy knowledge base has 15 notes on gap types. [[R034-myth-gaps-are-always-filled]] warns against assuming gaps always fill, but [[N011-exhaustion-gap]] and [[EX007-exhaustion-gap-bearish-confirmation-signal]] show that exhaustion gaps in oversold conditions do tend to fill. The breadth filter distinguishes exhaustion gaps (trade them) from breakaway gaps (don't trade them).

## Entry Criteria

### 1. Gap Detection
- Stock gaps down at open (open < previous close by at least 1.5 ATR)
- This identifies a meaningful gap, not normal overnight drift

### 2. Breadth Regime Gate (2 filters only — lesson from STR-H)
- **McClellan Oscillator < -50** (oversold market breadth)
- **AD Line trending up over last 3 days** (breadth starting to recover)
- This is the regime filter that STR-E lacked — only enter when breadth confirms exhaustion

### 3. Entry Trigger
- Price crosses above the gap midpoint (50% gap fill) on the same day or next day
- This confirms the gap is being bought, not just a brief bounce

## Exit Criteria

- **Stop:** Gap low (bottom of the gap). If price breaks below the gap low, the exhaustion thesis is invalid.
- **Target:** Previous close (full gap fill). The gap fill is the primary target.
- **Time stop:** 5 bars. Gap fills that haven't completed within a week are unlikely to complete.

## Risk Management

- Risk per trade: 1% of equity (per [[RISK_RULES]] PT-001)
- Max portfolio heat: 15%
- Long-only: Gap-down reversals are a long strategy. No short equivalent (gap-up shorting in overbought markets is riskier and untested)

## Why This Should Work Where Others Failed

| Failed Strategy | Failure Reason | How STR-K Avoids It |
|-----------------|---------------|---------------------|
| [[STR-20260726-rsi-mean-reversion-entry\|STR-E]] | No regime filter, fades trends | Breadth gate ensures market is oversold, not trending |
| [[STR-20260726-first-pullback-trend-swing\|STR-H]] | Too many filters (5+), 3 signals in 7 years | Only 2 filters: McClellan + AD Line |
| [[STR-20260726-bollinger-squeeze-breakout-entry\|STR-F]] | Squeeze too permissive, 2% target hit rate | Gap fill is a concrete price target (previous close), not a ratio |

## Data Requirements

- **Stocks:** Daily OHLCV from yfinance (529-ticker universe, already cached)
- **Breadth:** McClellan Oscillator and AD Line computed from the universe itself (advance-decline statistics derivable from the 529 tickers)
- **No external breadth data needed** — compute from existing universe

## Limitations (to be stated in every validation)

1. Daily bars only — no intraday gap data
2. Survivorship bias — universe is current S&P constituents, not historical
3. Breadth computed from 529 stocks, not full NYSE/NASDAQ (~6000 stocks)
4. Gap identification at open requires open price, which yfinance provides

## Phase 1A Plan

Standalone scanner: `scanner_k_breadth_gap.py` (not added to live registry)

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-30 | Strategy created | First graph-aware discovery cycle — fills transitional regime gap + gap core idea gap |

## Related

- [[REGIME-transitional]]
- [[REGIME-ranging]]
- [[Discoveries-2026-W31-graph-aware]]
- [[STRATEGIES-MOC]]
- [[FAIL-STR-E-rsi-mean-reversion]]
- [[FAIL-STR-H-first-pullback]]
- [[ADR-004-Phase1-Validation-Framework]]
