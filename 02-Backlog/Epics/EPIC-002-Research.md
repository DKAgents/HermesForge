---
id: EPIC-002
type: epic
status: backlog
created: 2026-06-27
updated: 2026-06-27
tags: [epic, research, strategy, options, QQQ]
---

# EPIC-002: Market Research & Strategy Discovery

## Goal

Conduct structured research to identify and document trading strategies appropriate for QQQ/SQQQ options. This includes understanding the current macro environment, evaluating backtesting tooling, selecting risk-adjusted performance metrics, and specifying the options greeks monitoring requirements that will feed into the paper trading engine. Output is a curated strategy shortlist with documented rationale stored in `03-Research/`.

---

## Stories

| Story | Title | Status |
|-------|-------|--------|
| **US-010** | Research QQQ/SQQQ options strategies (0DTE, spreads, momentum) | ⬜ Backlog |
| **US-011** | Analyze current macro environment for QQQ direction bias | ⬜ Backlog |
| **US-012** | Research OpenRouter model pricing/quality benchmarks for agent routing | ⬜ Backlog |
| **US-013** | Survey backtesting libraries (backtrader, vectorbt, zipline-reloaded) | ⬜ Backlog |
| **US-014** | Research risk-adjusted return metrics (Sharpe, Sortino, max drawdown) | ⬜ Backlog |
| **US-015** | Document options greeks monitoring requirements | ⬜ Backlog |

---

## Definition of Done

- [ ] At least 3 distinct QQQ/SQQQ options strategies documented with entry/exit rules and risk profile
- [ ] Macro environment analysis note written and dated in `03-Research/`
- [ ] OpenRouter model benchmark table exists and is referenced by ModelRouter skill
- [ ] One backtesting library selected and justified; installation verified on VPS
- [ ] Performance metrics chosen (Sharpe, Sortino, max drawdown at minimum) and defined in `07-Risk/`
- [ ] Options greeks monitoring spec written (which greeks, thresholds, monitoring frequency)
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- QQQ strategies of interest: 0DTE credit spreads, momentum breakout, mean-reversion scalps, protective puts on SQQQ as hedge.
- Macro inputs: Fed rate path, VIX level, QQQ 20-day trend, sector rotation signals.
- Backtesting library recommendation: **vectorbt** for speed on options-like simulations; verify GPU availability on VPS.
- OpenRouter routing research feeds directly into EPIC-001 US-005 (ModelRouter skill).
