---
id: US-030-Risk-Rules
type: user-story
epic: "[[Epics/EPIC-004-Risk]]"
status: done
priority: high
effort: M
created: 2026-06-30
updated: 2026-06-30
assigned_to: hermes
tags: [backlog, story, risk, done]
---

# US-030: Define and Document All Risk Rules

## Story
**As a** Risk Guardian,  
**I want** all risk rules clearly defined and documented,  
**So that** every agent and trade decision has an unambiguous safety framework to operate within.

## Acceptance Criteria
- [x] Master risk rules document created in `07-Risk/RISK_RULES.md`
- [x] 7 rule sections covering: Position Sizing, Options, Loss Limits, Paper Trading, Execution, Monitoring, Prohibited Activities
- [x] 35+ individual rules with clear IDs (PS-001, OP-001, LL-001, etc.)
- [x] Position sizing guide with worked examples at multiple account sizes
- [x] Incident log template created
- [x] Escalation criteria defined (autonomous vs. human-required)
- [x] Guardian decisions log created for audit trail
- [x] Rule change process documented

## Files Created
| File | Purpose |
|---|---|
| `07-Risk/RISK_RULES.md` | Master rules (v1.0) |
| `07-Risk/POSITION_SIZING.md` | Sizing formulas + examples |
| `07-Risk/INCIDENT_LOG.md` | Living violation log |
| `07-Risk/ESCALATION_CRITERIA.md` | Guardian escalation triggers |
| `07-Risk/GUARDIAN_DECISIONS.md` | Auditable decision log |

## Definition of Done
- [x] All files created and committed to vault
- [x] Risk Guardian profile can reference these rules
- [ ] US-032 (position size calculator) — next story to implement the rules in code
