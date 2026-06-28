---
id: US-002
type: story
epic: EPIC-001
status: in-progress
priority: high
created: 2026-06-27
updated: 2026-06-27
tags: [story, foundation, hermes-profiles, subagents, orchestrator]
---

# US-002: Create Hermes Profile for Each Subagent

## User Story

**As** the HermesForge Orchestrator,
**I want** each subagent to have its own dedicated Hermes profile,
**so that** agents have isolated configurations, skills, memory, and system prompts — preventing cross-contamination and enabling specialised behaviour per role.

---

## Acceptance Criteria

- [ ] A Hermes profile exists for each of the 8 HermesForge subagents (see list below)
- [ ] Each profile has an appropriate `SOUL.md` (or equivalent system prompt) that defines the agent's role, responsibilities, and constraints
- [ ] Profiles are isolated — no cross-profile memory leakage (each profile's `memories/` is independent)
- [ ] Each profile has a `skills/` directory; role-specific skills are loaded only in the relevant profile
- [ ] Profile creation and naming convention is documented in the vault (e.g., `01-Architecture/Profiles.md`)
- [ ] Orchestrator profile can reference and delegate to other profiles by name

---

## The 8 Subagent Profiles

| Profile Name | Role |
|---|---|
| `orchestrator` | Top-level coordinator; runs the Forge Loop and delegates tasks |
| `researcher` | Market research, strategy discovery, macro analysis |
| `strategist` | Strategy design, parameter tuning, backtesting oversight |
| `coder` | Writing and reviewing trading engine code, skills, and tools |
| `risk-guardian` | Risk rule compliance review; gates strategy promotion |
| `analyst` | Performance analysis, reporting, dashboard maintenance |
| `journalist` | Session journaling, vault writing, documentation |
| `model-router` | Selects the optimal OpenRouter model for each task type |

---

## Technical Notes

- Hermes profiles live at `~/.hermes/profiles/<profile-name>/` on the VPS.
- Each profile directory should contain: `SOUL.md`, `skills/`, `memories/`, `plugins/` (if needed).
- `SOUL.md` is the persistent system prompt injected at the start of every session for that profile.
- Use `hermes --profile <name>` to invoke a specific profile.
- For the Forge Loop, the Orchestrator will spawn subagent sessions programmatically — ensure CLI invocation works cleanly for each profile.

---

## Dependencies

- Hermes Agent installed and working on VPS
- Base `default` profile confirmed working

## Related

- Epic: [[../Epics/EPIC-001-Foundation|EPIC-001]]
- Dependency for: **US-005** (ModelRouter skill — needs `model-router` profile to exist first)
- Dependency for: **EPIC-005** (Forge Loop automation — all profiles must exist before loop can delegate)
