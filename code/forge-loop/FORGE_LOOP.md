---
title: The Forge Loop
type: system-design
created: 2026-06-27
updated: 2026-06-27
status: v1-active
tags: [forge-loop, orchestration, system]
---

# The Forge Loop

## Overview
The Forge Loop is the continuous improvement engine of HermesForge. It runs on a schedule (or on-demand) and executes the following phases:

1. **Read** — Load context from the Obsidian vault (HERMES_CONTEXT.md, top backlog stories)
2. **Select** — Choose 1-3 stories to work on this iteration based on priority and dependencies
3. **Delegate** — Route each story to the appropriate subagent profile
4. **Execute** — Subagents do the work (research, coding, backtesting, etc.)
5. **Review** — Orchestrator reviews outputs, Risk Guardian reviews anything risk-related
6. **Document** — Results written back to vault (stories updated, journal entry created, skills extracted)
7. **Reflect** — Orchestrator reflects on what went well/poorly and updates the loop design if needed

## Loop Diagram (ASCII)
```
┌─────────────────────────────────────────────────────┐
│                  THE FORGE LOOP                      │
├─────────────────────────────────────────────────────┤
│  1. READ vault → HERMES_CONTEXT + top backlog       │
│         ↓                                           │
│  2. SELECT 1-3 stories (priority + dependencies)    │
│         ↓                                           │
│  3. DELEGATE to appropriate subagent profiles       │
│         ↓                                           │
│  4. EXECUTE (Research / Code / Backtest / Document) │
│         ↓                                           │
│  5. REVIEW outputs + Risk Guardian check            │
│         ↓                                           │
│  6. DOCUMENT results back to vault + journal        │
│         ↓                                           │
│  7. REFLECT → update loop, extract skills           │
│         ↓                                           │
│     [human notified of outcomes]                    │
└─────────────────────────────────────────────────────┘
```

## Trigger Conditions
- **Manual**: Human asks Hermes to 'run the Forge Loop'
- **Scheduled**: Cron job (configurable, e.g. daily at 8am UTC)
- **Event-driven**: Specific trigger (e.g. after a backtest completes)

## Story Selection Rules
- Always prefer stories with status: ready over in-progress
- Never start a story blocked by an incomplete dependency
- Risk-related stories get elevated priority
- Never select more than 3 stories per loop iteration

## Delegation Routing Table
| Story Type | Primary Agent | Secondary Agent |
|---|---|---|
| Research task | Researcher | — |
| Architecture decision | Architect | Orchestrator |
| Implementation | Coder | Architect |
| Backtest | Backtester | Researcher |
| Risk review | Risk Guardian | Human |
| Documentation | Documenter | — |
| Backlog refinement | Product Owner | Human |

## Human Touchpoints
- Orchestrator notifies human in Discord after each loop iteration
- Human approval required before any story that affects live execution
- Human can reprioritize backlog at any time by telling the Orchestrator

## Loop Cadence (v1)
- Bootstrap phase: On-demand (human-triggered)
- Phase 1+: Daily automated run + on-demand

## Version History
| Version | Date | Changes |
|---|---|---|
| v1 | 2026-06-27 | Initial design — manual trigger, 7-phase loop |
