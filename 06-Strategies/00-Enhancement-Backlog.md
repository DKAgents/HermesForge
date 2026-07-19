---
type: enhancement-backlog
updated: 2026-07-20
tags: [strategy, backlog, enhancements, research]
---

# Strategy Enhancement Backlog

Running log of ideas, future tests, and potential improvements surfaced during strategy development and review. Captured here so nothing is lost between sessions.

**Process:** Any time a strategy is built or revised, new items are added to this file. Strategy-specific research questions also live in the Open Questions section of each strategy note — this file captures cross-strategy ideas and framework-level enhancements.

---

## How to Use This File

- **Status values:** `idea` → `queued` → `in-progress` → `done` / `rejected`
- Items promoted to formal user stories get a US-XXX reference and status `queued`
- Items resolved by paper trading data get status `done` with a note on the outcome
- Items ruled out by evidence get status `rejected` with a reason

---

## Strategy A — MA Pullback with Fibonacci Entry
*STR-20260719-ma-pullback-fibonacci-entry.md*

| # | Enhancement | Status | Notes |
|---|------------|--------|-------|
| A-001 | **50-day vs. 20-day MA as anchor** — which MA produces better entries? Tag each paper trade with which MA the price bounced from. Compare hit rate and avg R after 20 trades. | `idea` | Open Question on strategy note |
| A-002 | **38% vs. 50% Fibonacci entry zone** — which zone produces higher R-multiple? Tag paper trades with entry zone. Compare after 20 trades. | `idea` | Open Question on strategy note |
| A-003 | **Weekly gate practicality** — does requiring all 3 weekly gates leave too few trades per month? Count setups passing all 3 gates vs. each individually over 30 days. | `idea` | Open Question on strategy note |
| A-004 | **Entry trigger quality** — RSI recovery vs. dual-oscillator vs. reversal candle — which produces best outcomes? Tag every paper trade with trigger type. Compare after 20 trades. | `idea` | Open Question on strategy note |
| A-005 | **Declining pullback volume** — should volume declining on down bars (and expanding on up bars) be a required condition? Compare outcomes with/without volume condition. | `idea` | Open Question on strategy note |

---

## Strategy B — MACD Histogram Divergence with Weekly Trend Assessment
*STR-YYYYMMDD-macd-histogram-divergence.md (not yet built)*

| # | Enhancement | Status | Notes |
|---|------------|--------|-------|
| B-001 | **ADX maturity gate** — does adding ADX ≥ 25 + declining as a secondary filter improve signal quality beyond the 15-bar MACD gate alone? | `idea` | Moved from v1 to Open Questions — ADX is noisy and lagging |
| B-002 | **15-bar threshold calibration** — is 15 the right maturity threshold, or does 10 or 20 produce better signal-to-noise? | `idea` | Open Question on strategy note |
| B-003 | **Stage 1 as partial entry** — take a smaller position on histogram narrowing alone, add full size on MACD line divergence. Does this improve average entry price without increasing loss rate? | `idea` | Interesting but adds complexity — v2 candidate |
| B-004 | **Time stop calibration** — is 8 bars the right exit window? Test 5 vs. 8 vs. 12 bars across paper trades. | `idea` | Open Question on strategy note |
| B-005 | **Bidirectional symmetry** — do bullish divergence setups in downtrends perform comparably to bearish setups in uptrends? One direction may be structurally stronger. | `idea` | Open Question on strategy note |
| B-006 | **Three-tier quality sizing** — v1 uses two levels (0.5% and 1.0%). A third tier for highest-conviction setups (MACD + RSI diverging + Stochastics overbought) could be added in v2. | `idea` | Deliberately simplified for v1 testability |
| B-007 | **Continuous weekly scaling matrix** — v1 uses a 3-level weekly modifier. A continuous scaling function (e.g. based on % of gates passing) could be more precise. | `idea` | Complexity vs. testability tradeoff — v2 |
| B-008 | **Divergence invalidation automation** — if price makes a new extreme with a higher MACD reading after Stage 1, the setup is void. Could be surfaced by a screener alert. | `idea` | Important edge case — worth scripting eventually |

---

## Cross-Strategy / Framework Enhancements

| # | Enhancement | Status | Notes |
|---|------------|--------|-------|
| F-001 | **Weekly filter design principle** — hard gate for trend-following strategies (Strategy A), soft sizing modifier for reversal strategies (Strategy B). Formalize as an ADR so future strategies inherit this decision without re-debating it. | `idea` | High value — prevents same design discussion recurring |
| F-002 | **Strategy quality tier framework** — a reusable component defining how oscillator corroboration scales position size. Currently defined per-strategy; could be a shared reference in ADR or Template. | `idea` | Would keep sizing logic consistent across strategies |
| F-003 | **Paper trading tracker** — a structured Obsidian note or CSV template to log paper trades against each strategy. Required to answer the Open Questions in A and B. | `idea` | Prerequisite for all Open Questions — high priority |
| F-004 | **Strategy review cadence** — a defined schedule for reviewing Hypotheses strategies after N paper trades and deciding Active / Deprecated / Revised. | `idea` | Could be a cron job or manual checklist |
| F-005 | **Cross-strategy conflict detection** — if Strategy A says "buy the pullback" and Strategy B says "fade the strength" on the same ticker simultaneously, which takes precedence? Needs a rule. | `idea` | Will become real once both strategies are paper trading |
| F-006 | **Backtest integration** — once paper trading validates a strategy, formalize a backtest process (vectorbt or manual) before moving to Active. | `idea` | US candidate — depends on paper trading infrastructure |

---

## Resolved / Rejected

| # | Item | Resolution | Date |
|---|------|-----------|------|
| R-001 | ADX as hard maturity gate for Strategy B | Rejected for v1 — too noisy and lagging. Moved to Open Questions (B-001). | 2026-07-20 |
| R-002 | Three-tier quality sizing for Strategy B | Simplified to two levels for v1 testability. Preserved as B-006 for v2. | 2026-07-20 |
| R-003 | Continuous weekly scaling matrix for Strategy B | Simplified to 3-level modifier for v1. Preserved as B-007 for v2. | 2026-07-20 |
