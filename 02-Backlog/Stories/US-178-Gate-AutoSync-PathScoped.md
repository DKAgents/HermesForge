---
type: user-story
epic: EPIC-014
priority: P2
status: backlog
created: 2026-11-01
tags: [git-hygiene, automation]
---

# US-178 — Gate the auto-sync process to path-scoped commits

## Problem

The background "auto: sync scripts and campaigns" process committed with `git add -A`, sweeping unrelated `.bak` files and `cache/` into history (commit 7547a580), violating the path-scoped-commit rule.

## Fix

Gate that auto-sync process to commit only its own paths (path-scoped `git add <paths>`), never `git add -A` / `.`. `.gitignore` already now ignores `*.bak` and `cache/` (from the prior hygiene fix), but the sync process itself must stop blanket-staging.

## Acceptance

- The sync process commits only its declared paths.
- A synthetic run demonstrates no unrelated files (`.bak`, `cache/`, other scripts) enter its commit.