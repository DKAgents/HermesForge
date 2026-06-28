---
id: EPIC-001
type: epic
status: in-progress
created: 2026-06-27
updated: 2026-06-27
tags: [epic, foundation, infrastructure]
---

# EPIC-001: Foundation & Vault

## Goal

Establish the complete foundational infrastructure for HermesForge: the Obsidian vault on the VPS, SSHFS remote access from Mac, a dedicated Hermes agent profile for each subagent, Obsidian plugin configuration, git version control for the vault, and the initial ModelRouter skill skeleton. This epic must be substantially complete before any other epic can proceed reliably.

---

## Stories

| Story | Title | Status |
|-------|-------|--------|
| [[../Stories/US-001-SSHFS-Mount\|US-001]] | Set up SSHFS mount on Mac to access VPS vault | 🟡 In Progress |
| [[../Stories/US-002-Hermes-Profiles\|US-002]] | Create Hermes profile for each subagent | 🟡 In Progress |
| **US-003** | Configure Obsidian with recommended plugins (Dataview, Templates, Daily Notes) | ⬜ Backlog |
| **US-004** | Set up git repo for vault version control | ⬜ Backlog |
| **US-005** | Create ModelRouter skill skeleton | ⬜ Backlog |
| **US-006** | Document SSHFS mount procedure in vault | ⬜ Backlog |

---

## Definition of Done

- [ ] SSHFS mount is working from Mac; Obsidian opens vault successfully over SSHFS
- [ ] All 8 subagent Hermes profiles exist with appropriate `SOUL.md` / system prompts
- [ ] Obsidian has Dataview, Templates, and Daily Notes plugins installed and configured
- [ ] Vault is tracked in a git repository with an initial commit and `.gitignore`
- [ ] ModelRouter skill skeleton exists and is loadable by the Orchestrator profile
- [ ] SSHFS mount procedure is written up and stored in the vault (e.g., `06-Runbooks/`)
- [ ] All story acceptance criteria verified and stories marked ✅ Done

---

## Notes

- SSHFS on macOS requires **macFUSE** + **SSHFS** (homebrew: `brew install macfuse sshfs` or the osxfuse/macfuse packages).
- Hermes profiles live at `~/.hermes/profiles/<name>/` on the VPS.
- Recommended git remote: a private GitHub/GitLab repo or a bare repo on the same VPS as a second location.
