---
type: graph-inventory
created: 2026-07-30
updated: 2026-07-30
status: active
tags: [meta, ontology, graph-engineering, knowledge-graph]
topic: meta
confidence: high
has_quotes: false
source: unknown
---
# Graph Inventory & Ontology — HermesForge Knowledge Graph

## 1. Current Vault Inventory

### 1.1 Scale & Composition

| Metric | Count |
|--------|-------|
| Total markdown files | 1,475 |
| Files with YAML frontmatter | 1,463 (99%) |
| Files with wiki-links | 306 (21%) |
| Files with zero wiki-links | 1,170 (79%) |
| Unique wiki-link targets | 1,593 |
| Total link instances | 1,973 |
| Dataview queries (across 11 files) | ~60 |
| Inline properties (`key:: value`) | 0 |

### 1.2 Directory Structure & File Counts

| Directory | Files | Primary Type | YAML Quality |
|-----------|-------|-------------|--------------|
| `00-Meta/` | 3 | meta, dashboard | Basic (type, created, updated, tags) |
| `01-Agents/Profiles/` | 8 | agent profiles | Basic (agent, hermes_profile, role, tools) |
| `02-Backlog/Epics/` | 13 | epic | Moderate (type, epic, status, priority) |
| `02-Backlog/Stories/` | 42 | user-story | Moderate (type, story, status, priority, epic) |
| `03-ADRs/` | 6 | adr, decision | Moderate (type, status, date, deciders) |
| `04-ForgeLoop/` | 4 | system design, discovery | Basic |
| `04-ForgeLoop/Maintenance/` | 15 | maintenance-log | Auto-generated YAML |
| `05-Research/Market-Intelligence/` | 10 | market-briefing | Auto-generated YAML |
| `06-Strategies/Hypotheses/` | 10 | strategy | **Strong** (id, status, asset_class, trade_style, timeframe, market_regime, core_idea, confidence, publish_enabled, evidence_links) |
| `06-Strategies/Pending-Updates/` | 1 | update | Basic |
| `07-Risk/` | 8 | risk rules, incident log | Basic to moderate |
| `08-Knowledge/Insights/` | 67 | insight | **Strong** (type, date, actionability, connection_type, domains, sources, seed_id) |
| `08-Knowledge/Trading-Systems/...` | 1,257 | atomic-note | **Rich but uniform** (auto-generated from book ingestion) |
| `08-Knowledge/Skills/` | 4 | skill reference | Minimal |
| `09-Journal/` | 4 | journal, lesson | Moderate (type, date, source, outcome, related_strategy) |
| `10-Operations/` | 6 | operations docs | Basic |
| `Templates/` | 8 | templates | Minimal |

### 1.3 YAML Type Distribution

| `type:` value | Count | Notes |
|----------------|-------|-------|
| `atomic-note` | 1,257 | Murphy book ingestion — uniform schema, no wiki-links |
| `insight` | 67 | Auto-generated connection discoveries |
| `story` | 31 | Backlog stories |
| `maintenance-log` | 15 | Vault maintenance runs |
| `epic` | 13 | Backlog epics |
| `user-story` | 12 | Older story format |
| `strategy` | 11 | Strategy hypotheses |
| `market-briefing` | 10 | Daily market intelligence |
| `decision` | 4 | ADRs (also 3 typed as `adr`) |
| `lesson` | 3 | Journal lessons |
| `adr` | 3 | ADRs |
| `index` | 2 | Strategy index, agent index |
| `journal` | 2 | Journal entries |
| `meta` | 2 | System context |
| `dashboard` | 2 | Dashboards |
| `discovery-report` | 2 | Forge Loop discoveries |
| Other (1 each) | 5 | backlog-index, risk-escalation, guardian-decisions, incident-log, graph-inventory |

### 1.4 Installed Obsidian Plugins

| Plugin | Status | Usage |
|--------|--------|-------|
| **Dataview** | ✅ Installed | ~60 queries across 11 files (DASHBOARD, Strategy Index, Lesson Index, Murphy Dashboard) |
| **Templater** | ✅ Installed | Templates exist in `Templates/` but not heavily used |
| **obsidian-git** | ✅ Installed | Auto-commits vault to git |
| **obsidian-tasks-plugin** | ✅ Installed | Light usage |
| **smart-connections** | ✅ Installed | AI-powered connections (generates `.smart-env/` directory) |

**Not installed:** ExcaliBrain, Juggl, Synapses, Dataview (have it), Calendar, Timelines

### 1.5 Existing Dataview Dashboards

Three functional dashboards already exist:

1. **`00-Meta/DASHBOARD.md`** — Backlog overview (in-progress, ready, backlog, done stories), ADRs, agents, journal
2. **`06-Strategies/00-Strategy-Index.md`** — Strategy table (core_idea, market_regime, trade_style, asset_class, confidence), grouped by status
3. **`09-Journal/00-Lesson-Index.md`** — Lessons by outcome (confirms, contradicts, refines, new-finding), confirmation count
4. **`08-Knowledge/Trading-Systems/00-Murphy-Dashboard.md`** — Murphy book: notes by concept_type, by topic, high-confidence rules, entry/exit criteria

## 2. Graph Connectivity Analysis

### 2.1 Link Distribution

| Category | Files with Links | Files without Links | Link Rate |
|----------|-----------------|---------------------|-----------|
| Murphy book (atomic-notes) | ~250 | ~1,007 | 20% |
| Insights | ~40 | ~27 | 60% |
| Strategies | ~8 | ~2 | 80% |
| ADRs | ~1 | ~5 | 17% |
| Agent profiles | ~4 | ~4 | 50% |
| Backlog (epics + stories) | ~5 | ~47 | 10% |
| Risk | ~1 | ~7 | 13% |
| Market briefings | ~0 | ~10 | 0% |
| Journal | ~2 | ~2 | 50% |
| Meta/Ops | ~3 | ~6 | 33% |

### 2.2 Top 10 Most Linked Targets

All top linked targets are Murphy book atomic notes — no HermesForge-native nodes (strategies, ADRs, insights, agents) appear in the top 25. This means the knowledge graph is currently dominated by book-to-book links, not by operational links between HermesForge's own artifacts.

### 2.3 Critical Connectivity Gaps

**Gap 1: Strategies don't link to each other.** STR-J (mean-reversion) and STR-I (trend-following) are described as "uncorrelated diversifiers" but neither file links to the other. No strategy references prior strategies it improves upon or replaces.

**Gap 2: Strategies don't link to ADRs.** ADR-004 defines the Phase 1 validation framework that all strategies pass through, but no strategy hypothesis file links to it. ADR-001 (model routing) and ADR-003 (strategy schema) are similarly orphaned.

**Gap 3: ADRs don't link to affected strategies or agents.** ADRs are isolated decision records with no edges to the strategies, agents, or processes they govern.

**Gap 4: Insights don't backlink to strategies.** Insights have `sources` (Murphy book notes) but don't link to the strategies that use them. Strategy files have `evidence_links` pointing to Murphy notes, but the chain strategy → insight → book note is incomplete (insights don't sit in the middle).

**Gap 5: Risk rules don't link to strategies.** `07-Risk/RISK_RULES.md` defines position sizing, max risk per trade, etc., but doesn't link to the strategies it governs. Strategies don't link back to risk rules.

**Gap 6: No regime nodes.** Strategies have a `market_regime` field (trending, ranging, transitional) but there are no dedicated regime nodes that define what these mean, what indicators identify them, or which strategies work in each.

**Gap 7: No backtest result nodes.** Phase 1A/1B/2 results are embedded in strategy hypothesis files as prose. There are no separate `BacktestResult` nodes with structured metrics that can be queried, compared, or linked.

**Gap 8: No near-miss / failure mode nodes.** Near-miss data lives in scripts and JSON state files, not in the graph. Failed strategies (STR-E, F, G, H) are marked `status: killed` but don't have structured failure mode nodes explaining why they failed.

**Gap 9: Agent profiles don't link to their work.** The Backtester profile doesn't link to backtest results. The Researcher doesn't link to market briefings. The Orchestrator doesn't link to Forge Loop runs.

**Gap 10: Market briefings are isolated.** 10 daily market briefing files have no links to strategies, regimes, or decisions they informed. They're write-only artifacts.

**Gap 11: Murphy book notes (1,257 files) are largely disconnected.** 80% have no wiki-links. This is a massive knowledge base that's not navigable as a graph — it's a flat list.

**Gap 12: No MOCs (Maps of Content).** There are no intermediate navigation nodes between the folder structure and individual files. No "Swing Trading MOC", "Risk Management MOC", "Oscillator MOC", etc.

## 3. Proposed Ontology

### 3.1 Node Types

| Type | Description | Required YAML Fields | Current Status |
|------|-------------|---------------------|----------------|
| `strategy` | A trading strategy hypothesis | `id`, `status`, `asset_class`, `trade_style`, `timeframe`, `market_regime`, `core_idea`, `confidence`, `publish_enabled` | ✅ Exists, good schema |
| `regime` | A market regime (trending, ranging, high-vol, low-vol, macro) | `id`, `regime_type`, `description`, `indicators` | ❌ Does not exist |
| `backtest-result` | Structured results from a Phase 1A/1B/2 backtest | `id`, `strategy_id`, `phase`, `asset_class`, `sharpe`, `annual_return`, `max_drawdown`, `win_rate`, `trade_count`, `period_start`, `period_end`, `verdict` | ❌ Embedded in strategy files |
| `paper-result` | Paper trading capture outcome | `id`, `strategy_id`, `ticker`, `direction`, `entry_date`, `exit_date`, `pnl_r`, `status` | ❌ In JSON logs, not in graph |
| `near-miss` | A setup that almost qualified but fell short | `id`, `strategy_id`, `ticker`, `date`, `entry_price`, `stop_price`, `target_price`, `achieved_rr`, `required_rr`, `rr_gap`, `outcome` | ❌ In JSON state, not in graph |
| `failure-mode` | How/why a strategy was killed | `id`, `strategy_id`, `phase`, `reason`, `metrics`, `lesson` | ❌ Embedded in strategy status |
| `insight` | A discovered connection or pattern | `type`, `date`, `actionability`, `connection_type`, `domains`, `sources`, `seed_id` | ✅ Exists, good schema |
| `atomic-note` | A book knowledge atom | (existing Murphy schema) | ✅ Exists, 1,257 files |
| `adr` | Architecture Decision Record | `type`, `status`, `date`, `deciders` | ✅ Exists, needs richer linking |
| `agent-profile` | An agent's role and responsibilities | `agent`, `hermes_profile`, `role`, `tools` | ✅ Exists, needs linking |
| `moc` | Map of Content — navigation hub for a topic | `type: moc`, `topic`, `covers` | ❌ Does not exist |
| `dashboard` | Dataview-powered dashboard | `type: dashboard` | ✅ Exists, needs expansion |
| `process` | A defined workflow (Forge Loop, Discovery Cycle, etc.) | `type: process`, `steps`, `participants` | ❌ Partially in Forge Loop docs |

### 3.2 Edge Types (Expressed as Wiki-Links + Inline Properties)

Edges will be expressed through:
1. **Wiki-links** (`[[target]]`) in the body text — for narrative connections
2. **YAML list fields** — for structured, queryable connections (e.g., `evidence_links`, `tested_in`, `killed_by`)
3. **Dataview inline properties** (`key:: value`) — for queryable metadata within note bodies

| Edge Type | Direction | Expression | Example |
|-----------|-----------|------------|---------|
| `derived_from` | Strategy → Source | YAML: `source`, `source_authors` | STR-I derived_from arxiv_2602.11708 |
| `evidence_links` | Strategy → Knowledge | YAML: `evidence_links: [...]` | STR-B evidence_links N062-macd-divergence |
| `tested_in` | Strategy → BacktestResult | Wiki-link in body: `[[STR-I-phase1b2]]` | STR-I tested_in Phase1B/2 results |
| `killed_by` | Strategy → FailureMode | YAML: `killed_by: ...` + wiki-link | STR-E killed_by "negative R after costs" |
| `improves_upon` | Strategy → Strategy | Wiki-link: `[[STR-20260728-adaptive-trend\|improves upon STR-I]]` | New strategy improves upon STR-I |
| `correlates_with` | Strategy → Strategy | Inline: `correlates_with:: [[STR-J]]` | STR-I correlates_with STR-J (negatively) |
| `regime_dependent_on` | Strategy → Regime | YAML: `market_regime: trending` + wiki-link to regime node | STR-I regime_dependent_on [[regime-trending]] |
| `near_miss_of` | NearMiss → Strategy | YAML: `strategy_id` | CBRE near_miss_of STR-D |
| `governed_by` | Strategy → RiskRule | Wiki-link: `[[RISK_RULES#PT-001]]` | All strategies governed_by PT-001 |
| `validated_by` | Strategy → ADR | Wiki-link: `[[ADR-004]]` | All strategies validated_by ADR-004 |
| `produced_by` | Result → Agent | Inline: `produced_by:: [[Backtester]]` | Phase1B/2 results produced_by Backtester |
| `informs` | Briefing → Strategy/Decision | Wiki-link in briefing body | Market briefing informs STR-I signal |
| `participates_in` | Agent → Process | Wiki-link: `[[FORGE_LOOP]]` | Backtester participates_in Forge Loop |
| `connection_type` | Insight → Knowledge | YAML: `connection_type: adds_condition` | Insight adds_condition to Murphy notes |
| `superseded_by` | Old Strategy → New Strategy | Wiki-link + YAML status | STR-A superseded_by STR-I |

### 3.3 Required YAML Additions by Node Type

**Strategy files — add:**
```yaml
tested_in: [STR-I-phase1a, STR-I-phase1b2]    # list of backtest result note links
killed_by: null                                # failure mode link if killed
improves_upon: null                            # predecessor strategy link
correlates_with: []                            # diversification partners
regime_node: "[[regime-trending]]"             # explicit regime link
governed_by: [[RISK_RULES]], [[ADR-004]]       # governance links
validated_by: [[ADR-004]]                      # validation framework
```

**ADR files — add:**
```yaml
affects: [STR-I, STR-B]                        # strategies/processes affected
supersedes: null                               # prior ADR if applicable
participants: [Architect, Risk-Guardian]       # who decided
```

**Agent profiles — add:**
```yaml
produced: []                                   # links to work products
participates_in: [[FORGE_LOOP]]                # process links
```

**Insight files — add:**
```yaml
informs_strategy: []                           # which strategies use this insight
derived_from: []                               # which notes seeded this insight
```

**New node types — create:**
- `regime` nodes with `regime_type`, `description`, `indicators`, `applicable_strategies`
- `backtest-result` nodes with structured metrics
- `near-miss` nodes (or aggregate weekly/monthly)
- `failure-mode` nodes for killed strategies
- `moc` nodes for topic navigation

## 4. Plugin Recommendations

### 4.1 Already Installed — Leverage More

| Plugin | Current Usage | Recommendation |
|--------|---------------|----------------|
| **Dataview** | ~60 queries in 4 dashboards | Add: Strategy Comparison Dashboard, Regime Dashboard, Failure Mode Dashboard, Research Gap Dashboard. Add inline properties throughout. |
| **Templater** | Templates exist but underused | Create: Strategy template, Backtest Result template, Near-Miss template, Regime template, MOC template. Wire as folder templates. |
| **smart-connections** | Active (`.smart-env/` exists) | Already provides AI-powered link suggestions. Use to find missing connections in batch. |

### 4.2 Recommended New Plugins

| Plugin | Priority | Why | Cost |
|--------|----------|-----|------|
| **ExcaliBrain** | High | Interactive graph visualization with typed edges. Shows the ontology as a navigable tree. Pairs with our typed YAML links. | Free |
| **Dataview (update)** | High | Ensure latest version supports inline properties and `TABLE WITHOUT ID` for cleaner tables. | Free |
| **Juggl** | Medium | Advanced interactive graph — better for large graphs. Only if ExcaliBrain insufficient with 1,475+ nodes. | Free |
| **Calendar** | Low | Visual timeline for market briefings and journal entries. Nice but not critical. | Free |

### 4.3 Not Recommended (Yet)

| Plugin | Why Not |
|--------|---------|
| Synapses | Overlaps with smart-connections, adds complexity |
| Bases | New Obsidian feature, still experimental |
| Any paid plugin | Constraint: free tooling only |

## 5. Data Enrichment Opportunities (Free)

| Source | What It Adds | How It Strengthens the Graph |
|--------|-------------|---------------------------|
| **FRED API** (free, no key) | Macro series: VIX, treasury yields, unemployment, CPI | Creates Regime nodes with quantitative backing. Weekly cron job fetches → writes regime notes. |
| **Computed from existing data** | Correlation clusters, volatility regimes, breadth indicators | Derived from yfinance/Hyperliquid data we already cache. Creates Factor nodes. |
| **SEC EDGAR filings** (free) | Sector rotation signals, insider trading | Lightweight fetch for universe tickers. Creates Event nodes. |

## 6. Summary of Biggest Gaps

Ranked by impact on the graph-as-second-brath goal:

1. **No edges between HermesForge's own artifacts** — strategies, ADRs, risk rules, and agents exist as isolated islands. The graph is 80% Murphy book → Murphy book links.
2. **No regime, backtest-result, or failure-mode nodes** — the most important analytical outputs (what worked, what didn't, in what environment) are not in the graph as queryable nodes.
3. **No inline Dataview properties** — the 0 inline properties count means we can't query relationships from within note bodies. This limits Dataview's power significantly.
4. **No MOCs** — no navigation layer between folders and files. A visitor (human or agent) can't traverse from "Swing Trading" → "Trend-Following" → "STR-I" → "Phase 1B/2 results" without knowing the folder structure.
5. **Murphy book (1,257 notes) is a disconnected flat list** — 80% have no links. This is the largest knowledge asset but the least navigable.
6. **No graph-query-before-hypothesis workflow** — the Discovery Cycle doesn't check what's been tried before. New hypotheses are created without querying prior art.

## Next Steps

This inventory feeds directly into the **Second-Brain Elevation Plan** (step 2) which will propose concrete, low-risk changes to address these gaps without touching the live trading path.