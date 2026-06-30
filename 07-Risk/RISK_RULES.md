---
id: RISK-RULES-V1
type: risk-framework
version: 1.0
status: active
created: 2026-06-30
updated: 2026-06-30
owner: risk-guardian
tags: [risk, rules, framework, trading]
---

# HermesForge Risk Rules v1.0

## Overview
These rules govern ALL trading activity in HermesForge. They apply in paper mode and live mode. No agent may override these rules without explicit human approval and a new ADR.

## Rule Hierarchy
1. Human override (always wins)
2. Risk Guardian veto
3. These written rules
4. Agent judgment

## Section 1: Position Sizing Rules
- Rule PS-001: Maximum single position risk = 1% of total capital. Hard limit, no exceptions.
- Rule PS-002: Maximum total portfolio risk at any time = 5% of total capital.
- Rule PS-003: Maximum single options contract exposure = 2% of total capital (notional).
- Rule PS-004: Position size must be calculated BEFORE entry, never estimated.
- Rule PS-005: When in doubt, size down. Never size up to "make back" losses.

## Section 2: Options-Specific Rules (QQQ/SQQQ)
- Rule OP-001: Only trade liquid options (open interest > 1000, bid-ask spread < 5% of mid)
- Rule OP-002: No naked short options in paper or live mode without explicit ADR
- Rule OP-003: Maximum days to expiration for new entries: 30 DTE
- Rule OP-004: Close or roll positions at 21 DTE to avoid gamma risk unless thesis is confirmed
- Rule OP-005: No 0DTE trades until 90 days of paper trading history with positive expectancy
- Rule OP-006: Monitor delta, theta, vega on all open positions daily
- Rule OP-007: Maximum portfolio delta exposure: +/- 200 delta equivalent

## Section 3: Loss Limits
- Rule LL-001: Daily loss limit = 2% of total capital. Stop trading for the day if hit.
- Rule LL-002: Weekly loss limit = 5% of total capital. Stop trading for the week if hit.
- Rule LL-003: Single trade max loss = 1% of capital (links to PS-001)
- Rule LL-004: Drawdown alert at 10% from equity peak — mandatory Risk Guardian review
- Rule LL-005: Drawdown circuit breaker at 15% from equity peak — halt all trading, human review required

## Section 4: Paper Trading Requirements
- Rule PT-001: ALL new strategies must run in paper mode for minimum 30 days before live consideration
- Rule PT-002: Paper trading results must show positive expectancy (Sharpe > 0.5) over minimum 20 trades
- Rule PT-003: Paper mode results must be documented in 06-Strategies/Backtests/ before live review
- Rule PT-004: Risk Guardian must sign off before ANY strategy exits paper mode
- Rule PT-005: Human must give explicit written approval before live deployment

## Section 5: Execution Rules
- Rule EX-001: No market orders on options — use limit orders only
- Rule EX-002: Never chase a fill — if limit order not filled within 2 minutes, reassess
- Rule EX-003: No trading in the first 15 minutes after market open (9:30-9:45 ET)
- Rule EX-004: No trading in the last 5 minutes before market close (3:55-4:00 ET) except to close expiring positions
- Rule EX-005: All execution code defaults to paper_mode=True (see ADR-002)

## Section 6: Monitoring Requirements
- Rule MO-001: Open positions must be reviewed at least once per trading day
- Rule MO-002: Daily P&L report delivered to Discord (see US-024)
- Rule MO-003: Greeks (delta, theta, vega) monitored for all options positions
- Rule MO-004: Alert triggered if any position moves against thesis by >50% of max loss
- Rule MO-005: Weekly performance review every Friday — Sharpe, win rate, max drawdown

## Section 7: Prohibited Activities
- Rule PR-001: No leverage — ever
- Rule PR-002: No shorting individual stocks
- Rule PR-003: No trading on insider information or material non-public information
- Rule PR-004: No automated live execution without human approval
- Rule PR-005: No adding to losing positions (no averaging down)
- Rule PR-006: No holding leveraged ETF positions overnight (3x ETFs etc)

## Rule Change Process
1. Any agent may PROPOSE a rule change
2. Risk Guardian reviews and recommends
3. ADR must be created documenting the change
4. Human must explicitly approve
5. Rules version number incremented

## Version History
| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-06-30 | Initial rules — bootstrap phase |
