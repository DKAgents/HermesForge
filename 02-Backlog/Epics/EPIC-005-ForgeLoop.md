---
id: EPIC-005
type: epic
status: in-progress
created: 2026-06-27
updated: 2026-06-27
tags: [epic, forge-loop, automation, orchestrator, cron]
---

# EPIC-005: Forge Loop Automation

## Goal

Automate the HermesForge continuous improvement cycle — the Forge Loop — so that the Orchestrator agent regularly reviews system performance, delegates research and improvement tasks to subagents, writes findings back to the vault, and extracts reusable skills. The loop runs on a cron schedule, reads vault context, journals session outputs, and surfaces skill improvements without requiring constant human prompting.

---

## Stories

| Story | Title | Status |
|-------|-------|--------|
| **US-040** | Design and document Forge Loop v1 *(see `04-ForgeLoop/`)* | ✅ Done |
| **US-041** | Implement cron-driven Forge Loop scheduler | 🟡 In Progress |
| **US-042** | Build vault-reading capability for Orchestrator | 🟡 In Progress |
| **US-043** | Implement automatic session journaling to vault | ⬜ Backlog |
| **US-044** | Build Forge Loop reflection and skill extraction step | ⬜ Backlog |

---

## Definition of Done

- [ ] Forge Loop v1 design is documented in `04-ForgeLoop/` and reviewed ✅
- [ ] Cron job (or equivalent scheduler) triggers Forge Loop at the configured interval (e.g., daily at 06:00 UTC)
- [ ] Orchestrator can read vault markdown files as context before dispatching subagent tasks
- [ ] Every Forge Loop session produces a dated journal entry in `05-Journal/`
- [ ] Reflection step extracts at least one candidate skill or improvement per loop iteration and opens a story/task for it
- [ ] Forge Loop runs end-to-end at least 3 times without manual intervention
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- **US-040 is complete:** See `04-ForgeLoop/FORGE_LOOP_V1.md` for the canonical loop design.
- **Scheduler approach:** Use Linux `cron` via a Hermes cron config, or a small Python scheduler process managed by `systemd`. Prefer Hermes native cron if the platform supports it.
- **Vault reading:** Orchestrator needs a skill or tool that lists and reads vault markdown files — enables context-aware task delegation (e.g., read last 3 journal entries before deciding what to work on next).
- **Journaling:** Each session should auto-write a structured note to `05-Journal/YYYY-MM-DD-forge-loop.md` with: tasks delegated, subagents used, key findings, skills extracted.
- **Skill extraction:** After each loop, the Orchestrator reviews session output for reusable patterns and, if found, drafts a new skill file for human review before promotion.
