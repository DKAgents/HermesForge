---
id: US-004-Git-Vault
type: user-story
epic: "[[Epics/EPIC-001-Foundation]]"
status: done
priority: high
effort: S
created: 2026-06-27
updated: 2026-06-27
assigned_to: hermes
tags: [backlog, story, git, vault]
---

# US-004: Set Up Git Repo for Vault Version Control

## Story
**As a** developer,  
**I want** the vault tracked in git,  
**So that** I have a full history of changes and can recover from mistakes.

## Acceptance Criteria
- [x] Git repo initialized at `~/HermesForge`
- [x] Branch named `main`
- [x] `.gitignore` excludes: macOS junk, workspace.json, plugin binaries, secrets, large data files
- [x] Plugin manifests committed (version pins) but not binaries
- [x] First commit includes all 47 vault files
- [x] `git status` shows clean working tree

## Commit
`e462aa4` — Bootstrap: vault created, profiles defined, backlog seeded, Forge Loop designed

## Notes
- Obsidian on Mac auto-installed: obsidian-git, templater, obsidian-tasks plugins
- Plugin manifests tracked in git (version pins); main.js/styles.css excluded (large, auto-downloaded)
- Remote origin not yet set — add GitHub/GitLab remote when ready

## Definition of Done
- [x] Repo initialized, branch = main
- [x] .gitignore in place
- [x] Clean first commit
- [ ] Remote origin configured (optional — do when ready to push)
