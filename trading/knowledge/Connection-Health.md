---
type: connection-health
updated: 2026-09-28T05:28:23Z
tags: [connection-weaver, knowledge-graph, dashboard]
---

# Connection Health Dashboard

## Run Summary
| Metric | Last Run | Total |
|--------|----------|-------|
| Notes examined | 5 | 1060 |
| Connections created | 8 | 296 |
| Review queue | 294 | 294 |
| Avg score | 3.1 | — |

## Graph Density Signals
- Total wikilinks in vault: ~5358
- Total notes: 2533
- Avg degree per note: 2.115
- Notes with links: 1098 (43.4%)
- Orphan notes (no links): 1434 (56.6%)

## Weakly Connected Areas
- `trading/research/Market-Intelligence` — 19 notes, avg degree 0.0
- `campaigns/2026-09-aegis-rebuild` — 50 notes, avg degree 0.0
- `code/forge-loop` — 41 notes, avg degree 0.0
- `code/forge-loop/Maintenance` — 74 notes, avg degree 0.0
- `code/forge-loop/Decay` — 16 notes, avg degree 0.0

## Recent Discoveries (last run: 2026-09-28T05:28:23Z)
- **03-ADRs/ADR-001-Model-Routing-Strategy.md** → **07-Risk/RISK_RULES.md** (score 4.0): The model routing strategy in ADR-001 may need to incorporate risk-based constraints (e.g., using cheaper/faster models for low-risk tasks and more expensive ones for high-risk analyses) as defined in the risk rules, making the two notes interdependent for safe automation.
- **03-ADRs/ADR-001-Model-Routing-Strategy.md** → **00-Meta/SECOND-BRAIN-ELEVATION-PLAN.md** (score 4.0): The ADR defines a concrete routing strategy for model calls, which directly supports the vault's evolution into a living knowledge graph by ensuring that automation decisions are context-aware and cost-optimized — a key concern when elevating from static docs to active reasoning nodes.
- **03-ADRs/ADR-001-Model-Routing-Strategy.md** → **03-ADRs/ADR-005-Stage-Based-Model-Floors-and-Red-Team.md** (score 5.0): ADR-005 explicitly extends ADR-001 by addressing the gap between agent-based routing and task complexity, introducing stage-based floors and red team review to refine the routing strategy.
- **03-ADRs/ADR-002-Paper-Trading-First.md** → **07-Risk/RISK_RULES.md** (score 4.0): ADR-002 mandates Risk Guardian approval before live trading; linking to RISK_RULES.md provides the specific risk criteria and enforcement details that the Risk Guardian uses, making the policy actionable.
- **03-ADRs/ADR-002-Paper-Trading-First.md** → **03-ADRs/ADR-004-Phase1-Validation-Framework.md** (score 4.0): ADR-004's validation framework is a prerequisite step before strategies can enter the paper trading phase mandated by ADR-002, establishing a clear sequence in the deployment pipeline.
- **03-ADRs/ADR-003-Strategy-Schema.md** → **trading/knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/rules/EN028-10-and-50-day-moving-average-crossover.md** (score 4.0): This moving-average crossover rule is a concrete example of the type of trading strategy that ADR-003's schema would need to represent, validate, and track from paper to live. Linking them helps ground the abstract schema in an actual strategy note.
- **03-ADRs/ADR-003-Strategy-Schema.md** → **08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/indicators/N038-double-crossover-method-5-and-20-day-combination.md** (score 4.0): The ADR defines a schema requiring strategies to be traceable to specific evidence; this indicator note is a concrete piece of evidence that could be linked to a strategy, demonstrating the schema's application.
- **03-ADRs/ADR-003-Strategy-Schema.md** → **08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/indicators/N037-triple-crossover-method-4-9-18-day-moving-average.md** (score 4.0): The ADR defines how strategies should be structured and validated, while the candidate note is a concrete trading strategy/indicator that would fall under that schema. Linking them grounds the abstract ADR in a real example and supports retrieval of strategy instances governed by the schema.

## Reflection Notes
- Run 190: Created 1 connections from 5 notes. Avg score: 4.1.
- Run 195: Created 1 connections from 5 notes. Avg score: 3.7.
- Run 205: Created 1 connections from 5 notes. Avg score: 4.4.
- Run 210: Created 5 connections from 5 notes. Avg score: 3.0.
- Run 212: Created 8 connections from 5 notes. Avg score: 3.1.
