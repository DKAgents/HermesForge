---
id: EPIC-012
type: epic
status: backlog
created: 2026-07-20
updated: 2026-07-20
carved_from: EPIC-008
tags: [epic, alpaca, paper-trading, stocks, execution]
---

# EPIC-012: Alpaca Paper Trading Integration

## Goal

Connect to Alpaca's paper trading API for stock-side execution, using native bracket orders (entry+SL+TP as one OCO group — simpler than Hyperliquid's manual leg management). Logs into the same unified trade schema as EPIC-010/EPIC-011 so stock and crypto paper trades are directly comparable.

## Stories

| Story | Title | Status |
|---|---|---|
| US-077 | Alpaca Paper Account + API Key Wiring | ⬜ Backlog |
| US-078 | Native Bracket Order Placement | ⬜ Backlog |
| US-079 | Trade Logging into Unified Schema (US-065) | ⬜ Backlog |
| US-080 | Market-Hours Scheduling (9:30-4:00 ET) | ⬜ Backlog |

## Definition of Done
- Alpaca paper account connected, authenticated
- Can place bracket orders (entry+stop+target) for stock signals from strategies A, B, D
- Trades logged in the exact same schema as crypto paper trades (US-065) for apples-to-apples comparison
- Scheduling respects market hours; no attempted stock orders outside 9:30 AM-4:00 PM ET

## Out of Scope
- Live capital (EPIC-008)
- Crypto (EPIC-011)
