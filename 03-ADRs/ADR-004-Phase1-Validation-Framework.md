---
id: ADR-004
type: decision
status: accepted
date: 2026-07-20
deciders: [HermesForge Orchestrator, User]
tags: [adr, validation, backtesting, phase1, swing-trading]
---

# ADR-004: Phase 1 Strategy Validation Framework

## Status
**Accepted** — 2026-07-20

## Context

HermesForge has four validated swing strategy hypotheses. The limiting factor is no longer strategy definition — it is validation. Before committing to full backtesting infrastructure or live trading, a disciplined fast-path validation is needed to:
1. Confirm signals appear with meaningful frequency
2. Confirm rough edge exists before costs
3. Identify which strategies are worth deeper work
4. Answer the highest-value Open Questions efficiently

DCA strategies are explicitly deferred to backlog. Swing trading is the primary focus.

## Decision

Adopt a three-sub-phase validation structure before full backtesting:

### Phase 1A — Fast Reality Check
- Build signal scanners for all four swing strategies
- Operationalize all discretionary rules into precise, coded definitions
- Measure signal frequency and rough outcome distributions on historical data
- Apply pass/kill criteria to identify which strategies advance

### Phase 1B — Focused Research on Survivors
- Only strategies that survive Phase 1A continue
- Run pre-registered perturbations on the highest-value Open Questions only
- Use walk-forward sub-period analysis (not full walk-forward optimization)
- Targeted Bar Replay on interesting or problematic setups
- No broad parameter grid searches — prefer robust simple variations

### Phase 1C — Execution Validation
- Higher-throughput paper trading (not rate-limited to 2/week)
- Focus on executability and qualitative issues that scanners cannot detect
- Feed results into the self-improvement loop via extract_lessons.py

### Phase 2 — Full Backtesting
- Only after Phase 1 rules have stabilized and shown sufficient promise
- Vectorbt or similar event-driven framework

## Locked Decisions

| Decision | Value | Rationale |
|---|---|---|
| **Universe** | Top 100 S&P 500 stocks by avg dollar volume | Liquid, well-behaved data, realistic fills |
| **Direction — Strategies A, C, D** | Long-only | Rules as written are long-oriented; adding short adds complexity before validation |
| **Direction — Strategy B** | Bidirectional | Explicitly designed as bidirectional |
| **Kill criteria** | < 12 signals/year OR avg R < 0.2 (frictionless) | Below either = drop or major revision before Phase 1B |
| **Watch band** | 12–24 signals/year OR avg R 0.2–0.4 | Survives with caution flag; needs attention in Phase 1B |
| **Pass criteria** | ≥ 25 signals/year AND avg R ≥ 0.6 AND positive in ≥ 2 of 3 sub-periods | Sub-period check guards against regime-specific flukes |
| **Costs** | Phase 1A frictionless; flag avg R < 0.5 for friction sensitivity check | Clean signal first |
| **Market** | US stocks first; crypto deferred to Phase 1B if stocks validate | Matches primary trading focus |
| **Risk envelope** | 1% per trade, max 5 concurrent positions, max 5% portfolio heat | Conservative for hypothesis phase |
| **Data source** | yfinance daily OHLCV | Free, sufficient for Phase 1A |
| **Data pull** | Oct 2018 onward; discard signals before Apr 2019 | Allows 90-day indicator warm-up before first valid signal |
| **Sub-periods** | Period 1: Apr 2019–Dec 2021 (bull). Period 2: Jan 2022–Dec 2023 (bear/recovery). Period 3: Jan 2024–present (current) | Regime diversity: bull, bear/rate-hike, post-recovery |
| **Survivorship note** | Top 100 today ≠ top 100 in 2019; flag as Phase 1A limitation | Acceptable bias for reality check; address in Phase 1B if needed |

## Consequences

- Faster path from strategy notes to validated/rejected status (weeks not months)
- Discretionary rules must be operationalized precisely — rules that cannot be coded cannot be applied consistently
- Phase 1A results are directional, not definitive — frictionless, survivorship-biased, limited universe
- Strategies in the watch band (not killed, not passing cleanly) require judgment call before Phase 1B
- DCA layer is explicitly out of scope until Phase 1 is complete

## Related Decisions
- ADR-002: Paper Trading First (superseded by this more structured framework)
- ADR-003: Strategy Schema (strategies being validated)
