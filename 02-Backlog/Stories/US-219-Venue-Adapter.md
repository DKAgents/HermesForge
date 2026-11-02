---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: architect
tags: [execution, abstraction, hyperliquid, adr]
---

# US-219 — Venue adapter interface (design-only; keep Hyperliquid wired)

## Description
Abstract the executor behind a venue adapter interface (place/cancel/stop/positions/fills) so a live venue can be swapped by config without changing strategy code. Keep all existing live safety invariants. **Design only — no live enablement.** The architect drafts an ADR; implementation waits for human approval.

**Binding constraint: remain hooked to Hyperliquid.** HL stays the default/primary venue (the existing `live_executor.py` targeting `api.hyperliquid.xyz` + `create_agent_key.py` agent-custody path must never be severed). The adapter is additive — it wraps HL, not replaces it. `LIVE_TRADING_ENABLED` stays off.

## Acceptance Criteria
- ADR drafted: adapter interface (place/cancel/stop/positions/fills) + the rule that HL is the default venue and its integration is preserved.
- All live safety invariants restated (kill-switch blocks OPEN only; fail-closed protective stop; size-cap defense-in-depth; `LIVE_TRADING_ENABLED` explicit).
- No live enablement; implementation gated on human approval.

## Owner / RACI
- Owner (A): architect · Responsible (R): coder (after approval) · Consulted (C): risk-guardian · Informed (I): orchestrator, human