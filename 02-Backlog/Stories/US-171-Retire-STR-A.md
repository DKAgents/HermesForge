---
type: user-story
epic: EPIC-014
priority: P1
status: backlog
created: 2026-11-01
tags: [strategy-status, governance]
---

# US-171 — Retire STR-A + reconcile Active/KILLED conflict

## Problem

STR-A (ma-pullback-fibonacci) is simultaneously "Active" (Active/ folder, promoted 2026-09-20) and "KILLED" (regime selector). It has no backtest and no completed paper trade — a governance artifact, not a strategy.

## Fix

Retire STR-A: move it out of Active, mark Deprecated (or reconcile the two registries to a single agreed status), and remove any live/watched registration.

## Acceptance

- STR-A has exactly one status in all registries (no Active-vs-KILLED contradiction).
- It is no longer eligible for live paper/watch.