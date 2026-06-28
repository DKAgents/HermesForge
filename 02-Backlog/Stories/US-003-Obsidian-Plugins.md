---
id: US-003-Obsidian-Plugins
type: user-story
epic: "[[Epics/EPIC-001-Foundation]]"
status: done
priority: high
effort: S
created: 2026-06-27
updated: 2026-06-27
assigned_to: hermes
tags: [backlog, story, obsidian, plugins]
---

# US-003: Configure Obsidian Plugins

## Story
**As a** developer,  
**I want** Obsidian configured with the right plugins,  
**So that** I can use templates, daily notes, and query the vault with Dataview.

## Acceptance Criteria
- [x] Templates plugin enabled and pointed to `Templates/` folder
- [x] Daily Notes plugin enabled, pointed to `09-Journal/`, using `Daily-Log-Template`
- [x] Dataview community plugin installed (v0.5.68) and enabled
- [x] DataviewJS enabled for advanced queries
- [x] Dashboard created at `00-Meta/DASHBOARD.md` with live backlog/ADR/agent queries
- [x] New notes default to `09-Journal/` folder

## What Was Configured
| Plugin | Config File | Setting |
|---|---|---|
| Templates (core) | `.obsidian/templates.json` | Folder: `Templates/` |
| Daily Notes (core) | `.obsidian/daily-notes.json` | Folder: `09-Journal/`, Template: `Daily-Log-Template` |
| Dataview (community) | `.obsidian/plugins/dataview/` | v0.5.68, DataviewJS enabled |
| App defaults | `.obsidian/app.json` | New notes → `09-Journal/`, live preview on |

## Definition of Done
- [x] All plugins configured via `.obsidian/` config files on VPS
- [x] Dashboard note created with live Dataview queries
- [x] Story documented in vault
