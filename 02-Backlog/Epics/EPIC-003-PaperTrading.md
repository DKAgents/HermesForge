---
id: EPIC-003
type: epic
status: backlog
created: 2026-06-27
updated: 2026-06-27
tags: [epic, paper-trading, engine, alpaca, ibkr]
---

# EPIC-003: Paper Trading Engine

## Goal

Build a fully functional paper trading engine that executes strategies from EPIC-002 in a risk-free simulated environment. The engine integrates with a paper trading API (Alpaca Paper or IBKR Paper), enforces position sizing rules, tracks performance, and produces automated daily reports. Strategies must demonstrate positive risk-adjusted returns in paper mode before any live trading is considered.

---

## Stories

| Story | Title | Status |
|-------|-------|--------|
| **US-020** | Integrate with paper trading API (Alpaca paper or IBKR paper) | ⬜ Backlog |
| **US-021** | Implement position sizing module (max 1% capital per trade) | ⬜ Backlog |
| **US-022** | Build trade execution wrapper with paper-mode safety rail | ⬜ Backlog |
| **US-023** | Create performance tracking dashboard (P&L, win rate, Sharpe) | ⬜ Backlog |
| **US-024** | Implement automated daily P&L report to Discord | ⬜ Backlog |
| **US-025** | Build paper trading backtest comparison tool | ⬜ Backlog |

---

## Definition of Done

- [ ] Paper trading API connection authenticated and tested; can place/cancel mock orders
- [ ] Position sizing module rejects any trade exceeding 1% of simulated capital
- [ ] Trade execution wrapper has a `PAPER_MODE=true` flag that hard-prevents live order routing
- [ ] Performance dashboard shows real-time P&L, win rate, Sharpe ratio, and max drawdown
- [ ] Daily P&L summary auto-posts to the configured Discord channel via webhook
- [ ] Backtest comparison tool produces a side-by-side report: backtest vs. paper live results
- [ ] At least one complete strategy run for ≥5 trading days in paper mode without errors
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- **API choice:** Alpaca Paper is simpler to set up (REST API, no TWS required). IBKR Paper is more realistic for options fills. Recommend starting with Alpaca, migrating to IBKR when strategy is validated.
- **Safety rail design:** `PAPER_MODE` env var + code-level assertion in execution wrapper. Must be impossible to accidentally route a live order from paper engine.
- **Discord reporting:** use a simple webhook POST; no bot required. Report format: daily PnL, open positions, biggest winner/loser.
- **Backtest comparison:** helps detect overfitting early — if paper results diverge significantly from backtest assumptions, flag for Researcher review.
