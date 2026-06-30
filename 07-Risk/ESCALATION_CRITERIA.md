---
type: risk-escalation
created: 2026-06-30
tags: [risk, escalation, guardian]
---

# Risk Guardian Escalation Criteria

## When the Risk Guardian Acts Autonomously (No Human Needed)
- Rejecting a strategy that violates a hard rule (PS-001, LL-001, PR-001, etc.)
- Flagging a position that has breached the 50% max loss alert (MO-004)
- Approving routine paper trading position reviews
- Logging incidents with severity Low

## When the Risk Guardian Escalates to Human (Required)
| Trigger | Rule | Action |
|---|---|---|
| Daily loss limit hit (2%) | LL-001 | Notify human, halt trading day |
| Weekly loss limit hit (5%) | LL-002 | Notify human, halt trading week |
| Drawdown alert (10% from peak) | LL-004 | Notify human, mandatory review meeting |
| Drawdown circuit breaker (15%) | LL-005 | Halt ALL trading, human decision required |
| Any strategy proposed for live deployment | PT-004/005 | Full human review and written approval |
| Rule change proposed | — | Human approval + ADR required |
| Novel risk situation not covered by rules | — | Human judgment required |
| Incident severity High or Critical | — | Immediate human notification |

## Escalation Format
When escalating to human, the Risk Guardian sends a Discord message with:
1. 🔺 ESCALATION tag
2. Rule triggered
3. Current exposure / loss figures
4. Recommended action
5. Decision required by: [timeframe]

## Response SLA
- Critical: Human must respond within 1 hour
- High: Human must respond within 4 hours  
- Medium: Human must respond within 24 hours
- Low: Logged, no response required
