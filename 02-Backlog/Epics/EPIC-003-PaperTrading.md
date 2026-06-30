---
id: EPIC-003
type: epic
status: backlog
created: 2026-06-27
updated: 2026-06-30
tags: [epic, paper-trading, engine, alpaca, crypto, swing-trading, position-trading]
---

# EPIC-003: Paper Trading Engine

## Goal

Build a fully functional paper trading engine that executes swing and position trading strategies from EPIC-002 across US stocks and cryptocurrency in a risk-free simulated environment. The engine enforces asset-specific position sizing rules (1% stocks, 0.5% crypto), classifies trades by style (swing vs. position), tracks performance, and produces automated daily reports. Strategies must demonstrate positive risk-adjusted returns in paper mode before any live trading is considered.

---

## Stories

| ID | Story | Status |
|---|---|---|
| US-020 | Integrate with paper trading API for stocks (Alpaca paper trading) | ⬜ Backlog |
| US-021 | Research crypto paper trading options (exchange testnet vs simulation) | ⬜ Backlog |
| US-022 | Implement position sizing module (1% stocks, 0.5% crypto hard limits) | ⬜ Backlog |
| US-023 | Build trade entry/exit logging with swing vs position trade classification | ⬜ Backlog |
| US-024 | Create performance tracking dashboard (P&L, win rate, Sharpe by market/style) | ⬜ Backlog |
| US-025 | Implement automated daily P&L report to Discord | ⬜ Backlog |
| US-026 | Build thesis documentation workflow for position trades | ⬜ Backlog |

---

## Definition of Done

- [ ] Paper trading API connection authenticated and tested for stocks; can place/cancel mock orders
- [ ] Crypto paper trading approach selected (testnet or simulation) and documented
- [ ] Position sizing module enforces 1% limit for stocks and 0.5% limit for crypto — rejects violations
- [ ] Trade log captures: ticker, market (stock/crypto), style (swing/position), entry, exit, P&L, hold duration
- [ ] Performance dashboard shows P&L, win rate, Sharpe ratio, and max drawdown — segmented by market and style
- [ ] Daily P&L summary auto-posts to the configured Discord channel via webhook
- [ ] Position trades require a thesis note linked in the trade log before entry is permitted
- [ ] Trade execution wrapper has a `PAPER_MODE=true` flag that hard-prevents live order routing
- [ ] At least one complete strategy run for ≥5 trading days in paper mode without errors
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- **Stock API:** Alpaca Paper is simpler to set up (REST API, no TWS required). Good starting point for stock swing/position trades.
- **Crypto paper trading:** Binance testnet or Coinbase sandbox are options. Alternatively, simulate fills against live price feeds without a testnet.
- **Position sizing:** Two-tier system — stocks at 1% risk (PS-001), crypto at 0.5% risk (CR-001). Module must enforce both.
- **Swing vs. Position classification:** Logged at trade entry. Swing trades auto-flagged if held beyond 10 days without explicit reclassification.
- **Thesis workflow:** Position trades require a markdown thesis note in `05-Trades/Theses/` before entry is logged. Swing trades exempt.
- **Safety rail design:** `PAPER_MODE` env var + code-level assertion in execution wrapper. Must be impossible to accidentally route a live order from paper engine.
- **Discord reporting:** use a simple webhook POST; no bot required. Report format: daily PnL, open positions, biggest winner/loser, segmented by stocks/crypto.
