---
id: ADR-004
type: decision
status: accepted
date: 2026-07-20
deciders: [HermesForge Orchestrator, User]
tags: [adr, validation, backtesting, phase1, swing-trading]
topic: adrs
confidence: high
has_quotes: false
source: HermesForge ADR
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
| **Kill criteria** | avg R < 0.2 (frictionless) — frequency is NOT a kill reason | Low-frequency strategies with positive edge contribute to a diversified portfolio. The goal is surfacing high-probability trades across many strategies, not requiring each to fire often. |
| **Watch band** | avg R 0.2–0.4 (frictionless) OR signals < 12/year with positive edge | Survives with caution flag; low-frequency strategies need Phase 1B to confirm edge survives costs |
| **Pass criteria** | avg R >= 0.6 AND positive in >= 2 of 3 sub-periods | Sub-period check guards against regime-specific flukes. No minimum signal frequency required. |
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

## Amendment 1 — Asset-Class Independence Rule (2026-08-03)

### Context
The original framework was stocks-first with crypto deferred. As strategies were deployed on both stocks and crypto in the live pipeline, an implicit rule emerged: a strategy survives if it passes on **either** asset class, and is restricted to the passing class when it fails on the other. This amendment makes that rule explicit.

### Decision

| Rule | Definition |
|---|---|
| **Per-asset-class evaluation** | Each strategy is validated independently on stocks and crypto. Results on one asset class do not influence the verdict on the other. |
| **Survival criterion** | A strategy SURVIVES (LIVE or WATCH) if it passes validation on **at least one** asset class. It is KILLED only if it fails the kill criteria on **all** tested asset classes. |
| **Asset-class restriction** | If a strategy passes on one asset class but fails on another, it is **restricted** to the passing asset class only. The failing asset class is disabled in the pipeline. |
| **Kill criteria (per asset class)** | avg R < 0.2 (frictionless) on that asset class. A strategy is killed globally only if this is true for ALL tested asset classes. |
| **Watch criteria (per asset class)** | avg R 0.2-0.4 OR signals < 12/year with positive edge on that asset class. |
| **Pass criteria (per asset class)** | avg R >= 0.6 AND positive in >= 2 of 3 sub-periods on that asset class. |
| **Cross-sectional strategies** | Strategies that require multiple assets by design (e.g., STR-P) are evaluated only on the asset class they are built for. |
| **Insufficient data** | If a strategy cannot be walk-forward validated due to insufficient signals (< 10 across the test period), it retains its Phase 1A status (WATCH if positive edge, KILL if not) with an explicit note. |

### Consequences
- STR-I is KILLED on crypto (Sharpe 0.151, Phase 1B/2) but PASSED on stocks → **restricted to stocks only**.
- STR-B must be validated on crypto to determine if it remains active there.
- STR-P is crypto-only by design → evaluated on crypto only.
- STR-D was tested in Phase 1A on stocks (WATCH) but never walk-forward validated → must be validated.
- STR-L has insufficient signals for walk-forward → retains WATCH status with explicit note.

## Related Decisions
- ADR-002: Paper Trading First (superseded by this more structured framework)
- ADR-003: Strategy Schema (strategies being validated)
