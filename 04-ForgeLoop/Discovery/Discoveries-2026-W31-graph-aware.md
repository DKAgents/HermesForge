---
type: discovery-report
created: 2026-07-30
updated: 2026-07-30
status: active
tags: [discovery, graph-aware, w31]
---

# First Graph-Aware Discovery Cycle — W31

## Graph Query Results

### Regime Coverage

| Regime | Strategies Tried | Live? | Gap? |
|--------|-----------------|-------|------|
| Trending | 6 (STR-A, B, D, G, H, I) | ✅ STR-B + STR-I live | Covered |
| Ranging | 3 (STR-D, J, E) | ❌ STR-J WATCH but not live | Under-covered |
| Transitional | 1 (STR-F, killed) | ❌ None | **GAP** |
| High-volatility | 0 | ❌ None | **GAP** |
| Low-volatility | 0 | ❌ None | **GAP** |

### Core Idea Coverage

| Idea | Tried | Status | Notes |
|------|-------|--------|-------|
| Momentum | STR-I | ✅ LIVE (stocks) | Trend-following, PASS |
| Reversal | STR-B, D, E, J | ✅ STR-B LIVE, STR-J WATCH | Multiple approaches |
| Pullback | STR-A, H | ❌ Both untested/killed | Never validated |
| Breakout | STR-C | ❌ Untested | Not backtested |
| Volatility-breakout | STR-F | ❌ KILLED | Squeeze too permissive |
| Relative-strength | STR-G | ❌ KILLED | RS-crossover too noisy |
| **Gap** | **None** | **❌ NOT TRIED** | 15 Murphy notes available |
| **Breadth** | **None** | **❌ NOT TRIED** | 35 Murphy notes available |

### Failure Mode Patterns

| Pattern | Strategies Affected | Lesson |
|---------|--------------------|----|
| No regime filter → false signals | STR-E | Mean-reversion fails without regime gating |
| Too many filters → no signals | STR-H | Max 2-3 filters for mechanical scanners |
| Squeeze too permissive | STR-F | Need stricter contraction definition |
| RS triggered by noise | STR-G | Need slower/longer confirmation |
| Timeframe mismatch | STR-I crypto | Can't transfer across timeframes |

### Knowledge Assets Available for Gap Areas

| Topic | Murphy Notes | Key Concepts |
|-------|-------------|-------------|
| Gap trading | 15 | Breakaway, runaway, exhaustion gaps; gap-as-support/resistance |
| Breadth indicators | 35 | McClellan oscillator, Arms/TRIN, AD line, new highs/lows |
| Volatility | 17 | Bollinger, Keltner, ATR, band-width |
| ADX/trend strength | 9 | ADX thresholds (20/40), DMI, trend vs trading market |

## Opportunity Identification

Two opportunities address the biggest graph gaps while leveraging existing knowledge and learning from failure modes:

### Opportunity 1: Breadth-Gated Gap Reversal

- **Fills gaps:** Transitional regime + gap core idea (both empty)
- **Leverages:** 15 gap notes + 35 breadth notes (largest untried knowledge bases)
- **Learns from:** STR-E failure (add regime filter via breadth) + STR-H failure (keep filters simple)
- **Concept:** Gap down on bad news → check breadth (AD line, McClellan) for oversold conditions → enter long when price fills the gap and breadth confirms reversal
- **Why transitional:** Gaps often occur at regime transitions. Breadth indicators detect when the transition is exhaustion vs continuation.

### Opportunity 2: ATR Contraction Breakout

- **Fills gaps:** Low-volatility regime + improves upon killed STR-F
- **Leverages:** 17 volatility notes + 9 ADX notes
- **Learns from:** STR-F failure (squeeze too permissive) + STR-G failure (RS too noisy)
- **Concept:** ATR contracts to multi-year low (prolonged, not just 60-bar low) → ADX < 18 (confirmed low trend) → enter on breakout above recent range with volume confirmation
- **Why low-volatility:** Low-vol periods precede explosive moves. The strategy enters at the contraction-to-expansion inflection point.
- **Improvement over STR-F:** ATR contraction is more robust than Bollinger band-width; requires prolonged contraction (not just a 60-bar low); adds ADX gate to confirm genuine low-vol regime.

## Related
- [[STRATEGIES-MOC]]
- [[REGIME-transitional]]
- [[REGIME-low-volatility]]
- [[FAIL-STR-E-rsi-mean-reversion]]
- [[FAIL-STR-F-bollinger-squeeze]]
- [[FAIL-STR-H-first-pullback]]
- [[GRAPH-INVENTORY-AND-ONTOLOGY]]
