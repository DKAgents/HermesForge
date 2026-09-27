---
type: discovery-report
created: 2026-07-26
updated: 2026-07-26
status: active
tags: [discovery, graph-aware, w32, high-volatility]
---

# Second Graph-Aware Discovery Cycle — W32 (High-Volatility Regime)

## Graph Query Results

### Regime Coverage (updated post-W31)

| Regime | Strategies Tried | Live? | Gap? |
|--------|-----------------|-------|------|
| Trending | 6 (STR-A, B, D, G, H, I) | ✅ STR-B + STR-I live | Covered |
| Ranging | 3 (STR-D, J, E) | ❌ STR-J WATCH but not live | Under-covered |
| Transitional | 2 (STR-F killed, STR-K killed) | ❌ None | **GAP** |
| **High-volatility** | **0** | ❌ None | **★ TARGET GAP** |
| Low-volatility | 1 (STR-L WATCH) | ❌ Not live | Filled by W31 |

### Core Idea Coverage (updated post-W31)

| Idea | Tried | Status | Notes |
|------|-------|--------|-------|
| Momentum | STR-I | ✅ LIVE (stocks) | Trend-following, PASS |
| Reversal | STR-B, D, E, J | ✅ STR-B LIVE, STR-J WATCH | Multiple approaches |
| Pullback | STR-A, H | ❌ Both untested/killed | Never validated |
| Breakout | STR-C | ❌ Untested | Not backtested |
| Volatility-breakout | STR-F (killed), STR-L (WATCH) | STR-L WATCH | W31 rescue |
| Relative-strength | STR-G | ❌ KILLED | RS-crossover too noisy |
| Gap | STR-K | ❌ KILLED | Breadth filter too restrictive |
| Breadth | STR-K | ❌ KILLED | Zero signals |
| **Capitulation/reversal-day** | **None** | **❌ NOT TRIED** | 17 Murphy notes available |

### Knowledge Assets for High-Volatility Gap

| Topic | Murphy Notes | Key Concepts |
|-------|-------------|-------------|
| Selling climax | 2 (N006, N162) | Capitulation bottom, exhaustion of selling, high-volume reversal |
| Key reversal day | 2 (N146, N003) | New high/low then reverse close, more significant on high volume |
| Outside day | 2 (N004, R033) | Wide range + heavy volume = significance multiplier |
| Reversal significance | 3 (R031, R033, N155) | Volume + range width = reversal day importance |
| Tops vs bottoms | 1 (C084) | Tops shorter, more volatile; bottoms take longer |
| Weekly reversal | 2 (N007, N057) | Weekly reversals more significant than daily |

### Failure Mode Patterns (updated post-W31)

| Pattern | Strategies Affected | Lesson |
|---------|--------------------|----|
| No regime filter → false signals | STR-E | Mean-reversion fails without regime gating |
| Too many filters → no signals | STR-H, STR-K | Max 2-3 filters for mechanical scanners |
| Squeeze too permissive | STR-F | Need stricter contraction definition |
| RS triggered by noise | STR-G | Need slower/longer confirmation |
| Timeframe mismatch | STR-I crypto | Can't transfer across timeframes |
| Volume filter preserves edge | STR-L | Removing volume filter destroys edge |

## Opportunity Identification

Two opportunities target the high-volatility regime, the largest remaining graph gap. Both use reversal-day patterns grounded in Murphy's framework, but differ in their setup mechanics:

### Opportunity 1: STR-M — Selling Climax Reversal

- **Fills gap:** High-volatility regime (zero strategies tried)
- **Leverages:** N006 selling climax, N162 selling climax, R033 reversal day significance, N155 reversal days
- **Learns from:** STR-E failure (add regime filter — only trade in high-vol) + STR-H failure (keep filters simple: 3 filters max) + STR-L success (volume filter preserves edge)
- **Concept:** Multi-day sharp decline (3+ days) on heavy volume → price makes new low but closes above prior close (reversal day) → enter long with stop at reversal day low
- **Why high-volatility:** Selling climaxes occur during elevated volatility. ATR/Close > 2x its 50-day average identifies the regime. Murphy explicitly states selling climaxes signal "a significant low has been seen."
- **Differentiation from STR-E:** STR-E was RSI mean-reversion without regime gating. STR-M gates on volatility regime + requires multi-day decline + uses reversal-day close (not oscillator).

### Opportunity 2: STR-N — Wide-Range Outside Reversal

- **Fills gap:** High-volatility regime (zero strategies tried)
- **Leverages:** N004 outside day, R033 reversal day significance factors, N146 key reversal day, R031 reversal day significance
- **Learns from:** STR-H failure (keep filters simple) + STR-F failure (don't use band-width as stop) + STR-L success (volume filter matters)
- **Concept:** After a 3+ day decline, price forms an outside day (engulfs prior bar's range) and closes above prior close (key reversal) → enter long with stop at outside day low
- **Why high-volatility:** Outside days with wide ranges are more significant in high-vol regimes (R033: "the wider the range, the more significant"). ATR/Close > 1.5x its 50-day average.
- **Differentiation from STR-M:** STR-M requires extreme capitulation (multi-day decline + extreme volume). STR-N focuses on the structural reversal pattern (outside day + key reversal) which can occur without full capitulation.

## Related

- [[STRATEGIES-MOC]]
- [[REGIME-high-volatility]]
- [[REGIME-transitional]]
- [[FAIL-STR-E-rsi-mean-reversion]]
- [[FAIL-STR-H-first-pullback]]
- [[FAIL-STR-F-bollinger-squeeze]]
- [[Discoveries-2026-W31-graph-aware]]
- [[GRAPH-INVENTORY-AND-ONTOLOGY]]