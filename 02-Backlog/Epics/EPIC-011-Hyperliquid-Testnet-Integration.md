---
id: EPIC-011
type: epic
status: backlog
created: 2026-07-20
updated: 2026-07-20
carved_from: EPIC-008
tags: [epic, hyperliquid, testnet, crypto, execution]
---

# EPIC-011: Hyperliquid Testnet Integration

## Goal

Stand up a dedicated agent wallet on the VPS, connect to Hyperliquid testnet, and gain the ability to place and manage paper/testnet crypto trades with basic reconciliation and order management. This is testnet-only — no real capital, no mainnet connection. Carved out of the old EPIC-008 (which conflated testnet paper trading with live capital execution).

## Locked Decisions (2026-07-20, user-approved)

| Decision | Value |
|---|---|
| Reconciliation failure mode | **Alert only** — if the agent detects a dangling position (e.g. entry filled, SL/TP leg missing due to crash/disconnect), it alerts and requires manual review. **No automatic close-to-flat action**, even on testnet. This sets the pattern intentionally for later live behavior. |
| Wallet | Dedicated agent wallet (EIP-712), separate from the user's main wallet. Never holds real funds. |
| Crypto universe | BTC, ETH, SOL (matches EPIC-010's paper trading universe) |

## Stories

| Story | Title | Status |
|---|---|---|
| US-072 | Hyperliquid Agent Wallet Setup (testnet) | ⬜ Backlog |
| US-073 | Testnet Market Data + Order Placement | ⬜ Backlog |
| US-074 | SL/TP Trigger Order Management (manual OCO — no native bracket) | ⬜ Backlog |
| US-075 | Reconciliation Job (alert-only on dangling orders) | ⬜ Backlog |
| US-076 | Crypto Strategy Adaptation (which strategies apply to which pairs) | ⬜ Backlog |

## Definition of Done
- Agent wallet created, authenticated against Hyperliquid testnet
- Can place entry orders and manage SL/TP as separate trigger orders
- Reconciliation job runs on startup + periodically, detects dangling single-leg positions, alerts via Discord — takes no closing action automatically
- At least one full round-trip testnet trade (entry -> SL or TP -> close) logged in the same schema as EPIC-010

## Known Risk
Hyperliquid has no native OCO bracket — if only the entry leg fills and the agent crashes before placing SL/TP, the position sits unprotected until reconciliation runs and a human acts on the alert. This is a deliberate, approved risk for testnet; must be revisited before EPIC-008 live capital work considers Hyperliquid.

## Out of Scope
- Mainnet / real capital (EPIC-008)
- Alpaca / stocks (EPIC-012)
