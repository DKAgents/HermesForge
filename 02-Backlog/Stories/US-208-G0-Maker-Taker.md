---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: architect
tags: [gauntlet, gates, cost, adr]
---

# US-208 — G0: model maker vs taker separately

## Description
Model maker vs taker execution separately in G0; allow maker-only strategies to use maker cost with a fill-probability haircut. **Requires a new ADR before the cost-model change takes effect.**

## Acceptance Criteria
- G0 cost screen accepts a maker or taker execution mode.
- Maker-only strategies use maker cost (1.5 bps) with an explicit fill-probability haircut (maker fill not guaranteed).
- ADR records the maker-cost admission + haircut rule.

## Owner / RACI
- Owner (A): architect · Responsible (R): coder · Consulted (C): backtester, risk-guardian · Informed (I): orchestrator