---
id: US-074
epic: EPIC-011
type: story
status: backlog
created: 2026-07-20
points: 5
tags: [hyperliquid, testnet, oco, risk]
depends-on: US-073
---

# US-074: SL/TP Trigger Order Management (Manual OCO)

## Story
As the execution system, I need to manage stop-loss and take-profit as separate trigger orders (since Hyperliquid has no native bracket/OCO), so that a testnet position has both legs protected and only one leg remains active if the other fills.

## Acceptance Criteria
- [ ] After entry fill confirmed, place both SL and TP trigger orders
- [ ] Watch for either leg filling; on fill, cancel the other leg (manual OCO logic)
- [ ] State persisted (not just in-memory) so a process restart doesn't lose track of which legs are pending — this is exactly the gap that US-075's reconciliation job exists to catch
- [ ] Unit test: simulate TP fill, verify SL cancellation is attempted

## Definition of Done
- Manual OCO logic tested against testnet (one full round-trip: entry -> TP fill -> SL auto-cancelled)
- State persistence verified across a simulated process restart
- Committed to main
