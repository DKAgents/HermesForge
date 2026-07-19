---
type: backlog-index
created: 2026-06-27
updated: 2026-06-27
tags: [backlog]
---

# HermesForge Backlog Index

This index tracks all epics and user stories for the HermesForge Trading System. Each epic groups related stories toward a major system capability milestone.

---

## Epics

| Epic | Status | Description | Stories |
|------|--------|-------------|---------|
| [[Epics/EPIC-001-Foundation\|EPIC-001]] | 🟡 In Progress | Setting up vault, Hermes profiles, and core infrastructure | US-001 → US-006, US-063 |
| [[Epics/EPIC-002-Research\|EPIC-002]] | ⬜ Backlog | Research swing/position trading strategies for US stocks and crypto | US-010 → US-017 |
| [[Epics/EPIC-003-PaperTrading\|EPIC-003]] | ⬜ Backlog | Building and validating strategies in paper mode (stocks + crypto) | US-020 → US-026 |
| [[Epics/EPIC-004-Risk\|EPIC-004]] | ⬜ Backlog | Implementing risk rules, position sizing, and guardian workflow | US-030 → US-034 |
| [[Epics/EPIC-005-ForgeLoop\|EPIC-005]] | 🟡 In Progress | Automating the continuous improvement loop | US-040 → US-044 |

---

## Current Sprint / Top Priorities

1. [[Stories/US-001-SSHFS-Mount|US-001]] — Set up SSHFS mount on Mac to access VPS vault
2. [[Stories/US-002-Hermes-Profiles|US-002]] — Create Hermes profile for each subagent
3. **US-040** — Design and document Forge Loop v1 *(see 04-ForgeLoop/)*
4. **US-041** — Implement cron-driven Forge Loop scheduler
5. **US-042** — Build vault-reading capability for Orchestrator

---

## Backlog Health

- **Total Epics:** 5
- **Total Stories Defined:** 25 (US-001–US-006, US-010–US-017, US-020–US-026, US-030–US-034, US-040–US-044)
- **In Progress:** EPIC-001 (Foundation), EPIC-005 (Forge Loop)
- **Backlog / Not Started:** EPIC-002, EPIC-003, EPIC-004
- **Story Readiness:** US-001 and US-002 are fully groomed with acceptance criteria. Stories US-003 through US-044 need individual story files written before sprint assignment.
- **Next Grooming Action:** Write story files for US-003–US-006 and US-040–US-044 to unlock EPIC-001 and EPIC-005 sprint work.
- **Blockers:** SSHFS mount (US-001) must be completed before Obsidian on Mac can be used for daily vault editing.
