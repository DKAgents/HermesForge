---
id: EPIC-010
type: epic
status: in-progress
created: 2026-07-20
updated: 2026-07-20
supersedes: EPIC-003
tags: [epic, paper-trading, automation, self-improvement]
---

# EPIC-010: Automatic Paper Trading Engine

## Goal

Automatically capture every signal produced by the daily scanners (EPIC-009) as a tracked paper trade, log full trade context, monitor outcomes daily using intraday high/low checks against cached OHLCV, and feed closed-trade results into the self-improvement loop (US-053). Covers both stock and crypto data sources. Supersedes the older EPIC-003 draft, which pre-dated the scanner/signal architecture and assumed manual entry.

## Locked Decisions (2026-07-20, user-approved)

| Decision | Value |
|---|---|
| Strategies paper-traded | A, B, D (not C — confirmed kill in Phase 1A). Independent of `publish_enabled` — paper trading has a lower bar than Discord alerting. |
| Position sizing | Each strategy's own validated sizing matrix — Strategy B uses its Level×Weekly-gate matrix (0.25%-1.0%); Strategy A and D use flat 1% per PS-001. |
| Outcome-check method | Intraday high/low checks against the daily OHLC bar (not close-only) — catches stop/target wicks without needing tick data. |
| Crypto universe | BTC, ETH, SOL (fixed set for now; expand later if paper trading validates the approach). |
| Concurrency limit | Max 1 open paper trade per (strategy, ticker) pair. A new signal on an already-open setup is skipped/logged as duplicate. |
| Portfolio heat | Enforce ADR-004 risk envelope: max 5 concurrent positions, max 5% aggregate heat. |

## Stories

| Story | Title | Status |
|---|---|---|
| US-065 | Unified Trade Log Schema (stocks + crypto) | ✅ Done |
| US-066 | Automatic Signal Capture Hook | ✅ Done |
| US-067 | Position Sizing & Portfolio Heat Enforcement | ✅ Done |
| US-068 | Outcome Tracking Engine (stocks, intraday H/L) | ✅ Done |
| US-069 | Crypto Data Source Integration (BTC/ETH/SOL) | ✅ Done |
| US-070 | Self-Improvement Loop Wiring (extract_lessons.py) | ✅ Done |
| US-071 | Paper Trading Performance Report (Discord) | ⬜ Backlog |

## Definition of Done
- Every signal from strategies A, B, D (stocks) and the crypto universe automatically becomes a tracked open paper trade — zero manual entry
- Outcome tracking correctly detects target/stop/time-stop hits using intraday high/low, closes trades, computes realized R
- Position sizing matches each strategy's validated matrix; portfolio heat and max-position limits enforced
- Closed trades automatically feed `extract_lessons.py`
- Daily/weekly performance summary posts to Discord
- At least 5 trading days of live automatic operation without errors

## Out of Scope
- Real broker/exchange order placement (EPIC-011, EPIC-012)
- Live capital execution (EPIC-008, still blocked)
- DCA strategies (backlog, deferred)
