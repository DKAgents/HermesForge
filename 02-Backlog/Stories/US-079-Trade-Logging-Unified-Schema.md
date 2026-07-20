---
id: US-079
epic: EPIC-012
type: story
status: backlog
created: 2026-07-20
points: 2
tags: [alpaca, logging, schema]
depends-on: US-065, US-078
---

# US-079: Trade Logging into Unified Schema

## Story
As the system operator, I need Alpaca paper trades logged into the exact same schema as crypto/manual paper trades (US-065), so that stock and crypto performance are directly comparable.

## Acceptance Criteria
- [ ] Alpaca fills (entry, SL/TP resolution) write to `trades.csv` using `trade_log.py` from US-065 — no separate schema
- [ ] `asset_class` and `data_source` fields correctly populated (`stock`, `alpaca`)
- [ ] Reconciliation between Alpaca's own fill records and the local trade log — confirm no drift

## Definition of Done
- Alpaca trades appear in the same trades.csv as other paper trades
- Reconciliation check passes on at least one test trade
- Committed to main
