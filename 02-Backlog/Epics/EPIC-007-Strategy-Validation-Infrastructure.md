---
id: EPIC-007
type: epic
status: in-progress
created: 2026-07-20
updated: 2026-07-20
tags: [epic, validation, swing-trading, phase1]
---

# EPIC-007: Strategy Validation Infrastructure

## Goal

Move the four validated swing strategy hypotheses from "defined" to "validated or rejected" through a fast, disciplined three-phase validation process. Build the infrastructure required for Phase 1A (signal scanning) and Phase 1B (focused research). Phase 1C (paper trading) reuses existing infrastructure.

## Why This Epic Exists

Strategy definition is complete. The limiting factor is now validation. Without this epic, strategies remain theoretical indefinitely and the self-improvement loop has no real trading data to learn from.

## Stories

| Story | Title | Phase | Status |
|-------|-------|-------|--------|
| US-054 | Universe + Data Pipeline | 1A | ⬜ Backlog |
| US-055 | Signal Scanner — All Four Strategies | 1A | ⬜ Backlog |
| US-056 | Phase 1A Results Analysis + Kill/Pass Decisions | 1A | ⬜ Backlog |
| US-057 | Paper Trade Log Infrastructure (Phase 1C) | 1C | ⬜ Backlog |

## Out of Scope
- DCA strategy layer (deferred to backlog)
- Full vectorbt/backtrader backtesting (Phase 2 — separate epic)
- Crypto validation (deferred until US stocks complete)
- Live trading infrastructure (Phase 3 — separate epic)

## Definition of Done
- At least one strategy has passed Phase 1A criteria (≥25 signals/year, avg R ≥ 0.6, positive in 2 of 3 sub-periods)
- Kill/pass decision documented for all four strategies
- Paper trade log infrastructure ready for Phase 1C
- All results committed to vault

## Related ADRs
- ADR-004: Phase 1 Validation Framework (locked decisions)
