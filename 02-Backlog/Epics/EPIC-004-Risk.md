---
id: EPIC-004
type: epic
status: backlog
created: 2026-06-27
updated: 2026-06-27
tags: [epic, risk, safety, guardian, position-sizing]
---

# EPIC-004: Risk & Safety Framework

## Goal

Define and implement a comprehensive risk and safety framework that governs all trading activity — paper and (eventually) live. This includes codified risk rules, a Risk Guardian agent review step in the Forge Loop, hard-limit position sizing enforcement, an incident logging process, and clear escalation criteria that gate any transition to live trading or increased position sizes on human approval.

---

## Stories

| Story | Title | Status |
|-------|-------|--------|
| **US-030** | Define and document all risk rules in `07-Risk/` | ⬜ Backlog |
| **US-031** | Implement Risk Guardian review workflow in Forge Loop | ⬜ Backlog |
| **US-032** | Build position size calculator with hard limits | ⬜ Backlog |
| **US-033** | Create incident log template and process | ⬜ Backlog |
| **US-034** | Define escalation criteria for human approval | ⬜ Backlog |

---

## Definition of Done

- [ ] All risk rules written in `07-Risk/RISK_RULES.md` (max position size, max daily loss, max drawdown halt threshold, no overnight holds, etc.)
- [ ] Risk Guardian subagent profile exists and is invoked as a mandatory Forge Loop step before any strategy promotion
- [ ] Position size calculator module is unit-tested with hard-limit assertions; raises exception on breach
- [ ] Incident log template exists at `07-Risk/INCIDENT_LOG_TEMPLATE.md`; at least one drill incident logged
- [ ] Escalation criteria document written: specifies exact conditions requiring human sign-off (e.g., drawdown > 5%, transition to live, position size increase)
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- **Core risk rules (draft):** Max 1% capital per trade, max 3% daily loss (halt trading), max 10% drawdown (halt + human review), no overnight option positions, no trading within 15 min of major economic announcements.
- **Risk Guardian role:** Reviews each proposed strategy change or parameter update for risk-rule compliance before Orchestrator approves promotion to paper trading.
- **Incident log:** Even paper trading incidents (e.g., runaway order loop, API error causing missed stop) should be logged and reviewed — builds the discipline before live trading.
- **Human escalation:** All escalation triggers must produce a Discord alert + require a vault note with human sign-off before the system continues.
