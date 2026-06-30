---
id: EPIC-002
type: epic
status: backlog
created: 2026-06-27
updated: 2026-06-30
tags: [epic, research, strategy, swing-trading, position-trading, crypto, stocks]
---

# EPIC-002: Market Research & Strategy Discovery

## Goal

Research trading strategies, market conditions, and technical tools for swing and position trading across US stocks and cryptocurrency. Output is a curated strategy shortlist with documented rationale stored in `03-Research/`.

---

## Stories

| ID | Story | Status |
|---|---|---|
| US-010 | Research swing trading strategies for stocks (momentum, breakouts, pullbacks) | ⬜ Backlog |
| US-011 | Research crypto swing/position trading strategies and risk considerations | ⬜ Backlog |
| US-012 | Analyze current macro environment — market regime (trending/ranging/risk-on/risk-off) | ⬜ Backlog |
| US-013 | Research options strategies for swing and position trades (debit spreads, directional calls/puts) | ⬜ Backlog |
| US-014 | Survey backtesting libraries supporting stocks + crypto (vectorbt, backtrader) | ⬜ Backlog |
| US-015 | Research risk-adjusted return metrics for swing/position trading (Sharpe, Sortino, max drawdown) | ⬜ Backlog |
| US-016 | Research crypto data sources and APIs (Binance, Coinbase, CoinGecko) | ⬜ Backlog |
| US-017 | Research stock screener tools for swing trade setups (Finviz, TradingView scans) | ⬜ Backlog |

---

## Definition of Done

- [ ] At least 3 distinct swing trading strategies documented with entry/exit rules and risk profile (stocks)
- [ ] At least 2 crypto swing/position strategies documented with crypto-specific risk notes
- [ ] Macro environment analysis note written and dated in `03-Research/`
- [ ] Options strategy research covers both swing (≤30 DTE) and position (60-90 DTE) timeframes
- [ ] One backtesting library selected and justified; installation verified on VPS
- [ ] Performance metrics chosen (Sharpe, Sortino, max drawdown at minimum) and defined in `07-Risk/`
- [ ] Crypto data sources evaluated and preferred API documented
- [ ] Stock screener approach documented with example scan criteria
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- Stock swing trading: focus on momentum (moving average crossovers, relative strength), breakout setups, and pullback-to-support entries.
- Crypto: higher volatility requires adjusted position sizing (0.5% risk per CR-001). Focus on BTC, ETH, and top-20 only.
- Options for swing trades: debit spreads or naked calls/puts, ≤30 DTE. For position trades: 60-90 DTE directional.
- Backtesting library recommendation: **vectorbt** for speed; verify GPU availability on VPS. Must support both stock and crypto OHLCV data.
- Macro inputs: Fed rate path, VIX level, market regime (trend vs. chop), sector rotation signals, crypto dominance.
