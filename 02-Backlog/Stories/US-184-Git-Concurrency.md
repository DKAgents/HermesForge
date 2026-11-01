---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-11-01
tags: [git-hygiene, automation, concurrency]
---

# US-184 — Serialize/route the background git writers

## Problem

Multiple background processes commit to the same repo independently — `hermes-git-sync` (auto-sync, every 15 min), `vault-weaver`, and ad-hoc coder commits — racing with orchestrator operations. This caused: the v2 `git rm` being reversed by a concurrent restore, a possible mid-work `push` of uncommitted files, and interleaved "auto: sync" commits splitting work across commits.

## Fix

Investigate and gate the background git writers so they (a) never `git add -A`/ broader paths than their own scope, (b) don't race concurrent commits (a shared lock / serialization), and (c) never push on their own (only the push-only cron pushes). Concretely: constrain `hermes-git-sync` to its declared paths (already partially done via SYNC_PATHS) and add a commit lock, and route `vault-weaver` the same.

## Acceptance

- A synthetic concurrent-commit test shows no interleaving / no `add -A` sweep.
- Documented which processes write to git + their exact scoped paths.