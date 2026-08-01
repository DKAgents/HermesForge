---
type: elevation-plan
created: 2026-07-30
updated: 2026-07-30
status: proposed
tags: [meta, ontology, graph-engineering, elevation-plan]
related: [[GRAPH-INVENTORY-AND-ONTOLOGY]]
---

# Second-Brain Elevation Plan

## Overview

Concrete, low-risk changes to transform the HermesForge vault from a documentation store into a living knowledge graph. Every change here is additive — nothing touches the live trading path (STR-B, STR-I, scanners, daily_publish.py, or cron jobs).

## Phase A: Foundation (This Session)

### A1. Create MOCs (Maps of Content)

Create 5 MOC files as navigation hubs. Each is a typed node with Dataview queries + curated wiki-links.

| MOC | Path | Covers | Dataview Query |
|-----|------|--------|----------------|
| **Strategies MOC** | `06-Strategies/STRATEGIES-MOC.md` | All strategies, grouped by status, regime, and asset class | `TABLE status, market_regime, asset_class, confidence FROM "06-Strategies/Hypotheses" WHERE type = "strategy" SORT status, market_regime` |
| **Risk MOC** | `07-Risk/RISK-MOC.md` | Risk rules, incidents, guardian decisions, position sizing | `TABLE type, status FROM "07-Risk" SORT file.name` |
| **Knowledge MOC** | `08-Knowledge/KNOWLEDGE-MOC.md` | Insights, Murphy book topics, skills, derived knowledge | Grouped by `concept_type` and `connection_type` |
| **Decisions MOC** | `03-ADRs/DECISIONS-MOC.md` | All ADRs, sorted by date, with affected strategies | `TABLE status, date, affects FROM "03-ADRs" WHERE type = "adr" OR type = "decision" SORT date DESC` |
| **Agents MOC** | `01-Agents/AGENTS-MOC.md` | All agent profiles, their roles, tools, and work products | `TABLE role, tools, status FROM "01-Agents/Profiles" SORT file.name` |

### A2. Create Regime Nodes

Create dedicated regime notes that strategies can link to. These are the missing bridge between `market_regime: trending` in strategy YAML and a queryable knowledge node.

```
06-Strategies/Regimes/
  REGIME-trending.md
  REGIME-ranging.md
  REGIME-transitional.md
  REGIME-high-volatility.md
  REGIME-low-volatility.md
```

Each regime node has:
```yaml
---
type: regime
regime_type: trending
description: "Sustained directional price movement with higher highs/lower lows"
indicators: [ADX > 25, price above/below 200 SMA, MACD histogram expanding]
applicable_strategies: [STR-I, STR-B, STR-A, STR-H]
tags: [regime, trending]
---
```

### A3. Create Backtest Result Nodes (Retroactive)

Extract Phase 1A/1B/2 results from the 10 strategy hypothesis files into separate, structured nodes. This makes results queryable and comparable without reading prose.

```
06-Strategies/Backtests/
  STR-I-phase1a.md          (Phase 1A: bidirectional, long-only, short-only)
  STR-I-phase1b2-stocks.md  (Phase 1B/2: portfolio backtest, stocks)
  STR-I-phase1b2-crypto.md  (Phase 1B/2: portfolio backtest, crypto)
  STR-B-phase1a.md
  STR-B-phase1b.md
  STR-J-phase1a.md
  STR-J-phase1b2-stocks.md
  ... (one per strategy per phase)
```

Each backtest result node has:
```yaml
---
type: backtest-result
strategy_id: STR-20260728-adaptive-trend
strategy_name: AdaptiveTrend
phase: 1B/2
asset_class: stocks
direction: long-only
sharpe: 0.815
annual_return: 5.8
max_drawdown: -10.2
win_rate: 44.5
trade_count: 238
avg_hold_days: null
period_start: 2019-04-01
period_end: 2025-12-31
equity_final: 144542
verdict: PASS
verdict_reason: "Sharpe > 0.5, acceptable MDD"
data_limitations: "Daily bars, survivorship bias (current S&P constituents), no intraday"
produced_by: [[Backtester]]
tags: [backtest, phase1b2, STR-I, stocks]
---
```

### A4. Create Failure Mode Nodes

For the 4 killed strategies (STR-E, F, G, H) + crypto STR-I, extract the failure reason into a structured node.

```
06-Strategies/Failure-Modes/
  FAIL-STR-E-rsi-mean-reversion.md
  FAIL-STR-F-bollinger-squeeze.md
  FAIL-STR-G-relative-strength.md
  FAIL-STR-H-first-pullback.md
  FAIL-STR-I-crypto-daily-bars.md
```

Each failure mode node has:
```yaml
---
type: failure-mode
strategy_id: STR-20260726-rsi-mean-reversion
strategy_name: RSI Mean-Reversion
phase: 1A
verdict: KILL
reason: "Negative R after transaction costs (-0.056R)"
metrics:
  r_expectancy: -0.056
  signals: 47
  win_rate: 38
  sub_periods_positive: 0/3
lesson: "RSI mean-reversion on daily bars without regime filter produces too many false signals in trending markets. Needs higher timeframe confirmation or volatility filter."
data_limitations: "Daily bars, survivorship bias"
tags: [failure-mode, killed, rsi, mean-reversion]
---
```

### A5. Add Inline Properties to Strategy Files

Add Dataview inline properties to each strategy hypothesis file body. This makes relationships queryable from Dataview without changing YAML.

Example addition to STR-I body:
```markdown
## Graph Properties

produced_by:: [[Backtester]]
validated_by:: [[ADR-004]]
governed_by:: [[RISK_RULES]], [[ADR-001]]
regime_node:: [[REGIME-trending]]
correlates_with:: [[STR-20260726-eufearia-cci-reversal|STR-J]]
tested_in:: [[STR-I-phase1a]], [[STR-I-phase1b2-stocks]], [[STR-I-phase1b2-crypto]]
```

## Phase B: Link Strengthening (Next 1-2 Sessions)

### B1. Bidirectional Link Audit

For every strategy file, ensure:
- Links to its backtest result nodes
- Links to its failure mode (if killed)
- Links to its regime node
- Links to relevant ADRs (ADR-004 for all, ADR-001 for model routing)
- Links to risk rules that govern it
- Links to insights that inform it
- Links to related/correlated strategies

For every ADR, ensure:
- Links to strategies it affects
- Links to agents who participated in the decision

For every agent profile, ensure:
- Links to processes it participates in
- Links to notable work products (backtests, research notes)

### B2. Insight Backlinking

The 67 insight files have `sources` pointing to Murphy book notes. Add `informs_strategy` field to each insight that is referenced by a strategy's `evidence_links`. This completes the chain: Strategy → Insight → Book Note.

### B3. Murphy Book Cross-Linking (Batch)

Use a Python script to batch-add wiki-links to Murphy book atomic notes. For each note:
- Find notes with matching `topic` and create links
- Find notes referenced in `sources` by insights and create backlinks
- Link notes with complementary `concept_type` (e.g., indicator → rule → pattern)

This is the highest-volume task (1,257 files) but the lowest risk — it only adds links, doesn't change content.

## Phase C: Dashboard Expansion (After Phase B)

### C1. Strategy Comparison Dashboard

New Dataview dashboard that joins strategies with their backtest results and failure modes:

```
06-Strategies/STRATEGY-COMPARISON.md
```

Queries:
- All strategies with their best backtest Sharpe, MDD, and verdict
- Strategies grouped by regime, showing which regime is under-explored
- Killed strategies grouped by failure mode reason
- Strategy correlation matrix (which strategies are uncorrelated diversifiers)

### C2. Research Gap Dashboard

```
06-Strategies/RESEARCH-GAP-DASHBOARD.md
```

Queries:
- Regimes with no live strategy
- Asset classes with no strategy
- Core ideas (breakout, pullback, reversal, momentum) with only 1 strategy
- Time since last new hypothesis
- Insights with no `informs_strategy` (orphaned knowledge)

### C3. Paper Trading Dashboard

```
06-Strategies/PAPER-TRADING-DASHBOARD.md
```

Queries:
- Active paper positions (from trade log)
- Win/loss by strategy
- Near-miss history (from state file, if exported to notes)
- Days since last signal

## Phase D: Discovery Loop Integration (After Phase C)

### D1. Graph Query Protocol

Before any new hypothesis creation, the Researcher agent must:
1. Query the graph for existing strategies in the same regime + asset class + core idea
2. Query failure modes to see what's been tried and killed
3. Query insights for relevant knowledge
4. Document the query results in the new hypothesis file's `prior_art` section

### D2. Weekly Graph Health Check

A weekly cron job (or manual review) that:
- Counts total nodes and edges
- Identifies orphan nodes (no links)
- Identifies under-explored regimes
- Flags insights without strategy backlinks
- Reports graph growth metrics

## Implementation Order & Risk Assessment

| Step | Risk | Touches Live Path? | Can Be Done Now? |
|------|------|---------------------|-------------------|
| A1: Create MOCs | None — new files only | No | ✅ Yes |
| A2: Create regime nodes | None — new files only | No | ✅ Yes |
| A3: Extract backtest results | Low — reads strategy files, creates new files | No | ✅ Yes |
| A4: Create failure modes | None — new files only | No | ✅ Yes |
| A5: Add inline properties | Low — appends to strategy file bodies | No (doesn't change YAML or publish flags) | ✅ Yes |
| B1: Bidirectional link audit | None — adds wiki-links | No | ✅ Yes |
| B2: Insight backlinking | None — adds YAML fields to insights | No | ✅ Yes |
| B3: Murphy book cross-linking | Low — batch adds links to 1,257 files | No | ✅ Yes |
| C1-C3: Dashboards | None — new files only | No | ✅ Yes |
| D1: Graph query protocol | None — process change | No | ✅ Yes |
| D2: Weekly graph health | None — new cron job | No | ✅ Yes |

**Nothing in this plan touches STR-B, STR-I, the scanner registry, daily_publish.py, or any cron job that feeds the live publish pipeline.** All changes are additive: new files, new links, new YAML fields on existing non-live files.

## Success Metrics (4-6 Weeks)

| Metric | Current | Target |
|--------|---------|--------|
| Files with wiki-links | 21% (306) | 50%+ (737+) |
| HermesForge-native links (strategy↔ADR, strategy↔regime, etc.) | ~0 | 200+ |
| Dataview inline properties | 0 | 50+ across strategy/ADR/agent files |
| MOCs | 0 | 5 |
| Regime nodes | 0 | 5 |
| Backtest result nodes | 0 (embedded) | 15+ |
| Failure mode nodes | 0 (embedded) | 5+ |
| Dashboards | 4 | 7 |
| Graph query before hypothesis | Not done | Always done |