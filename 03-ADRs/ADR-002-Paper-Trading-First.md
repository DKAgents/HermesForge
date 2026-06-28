---
id: ADR-002
type: adr
status: accepted
created: 2026-06-27
deciders: [human, risk-guardian]
tags: [adr, safety, paper-trading]
---

# ADR-002: Paper Trading First Policy

## Status
accepted

## Context
HermesForge is building an automated trading system. Without guardrails, there is risk of premature live execution, financial loss, and hard-to-reverse mistakes.

## Decision
All trading functionality MUST start in paper trading mode. No strategy may be deployed to a live account until it has:

1. Passed backtesting validation (Backtester agent sign-off)
2. Run in paper mode for a minimum of 30 days with documented results
3. Been reviewed and approved by the Risk Guardian
4. Received explicit human approval

**Code-level enforcement:** All execution wrappers default to `paper_mode=True`. Live mode requires an explicit flag that cannot be set by any agent without human confirmation.

## Rationale
- Protects capital during system development
- Allows strategy validation without financial risk
- Establishes trust in the system before live deployment
- Aligns with the SOUL.md safety constraints

## Consequences
**Positive:**
- Capital protected during bootstrap and validation
- System builds track record before going live

**Negative:**
- Slower path to live trading
- Paper trading does not capture real slippage/liquidity

## Review Date
2027-01-01 — revisit after 6 months of paper trading results
