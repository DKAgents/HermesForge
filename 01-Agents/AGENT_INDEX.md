---
type: agent-index
created: 2026-06-27
updated: 2026-06-27
tags: [agents, index]
---

# HermesForge Agent Index

## Overview
HermesForge uses 8 specialized subagent profiles, each running as an isolated Hermes profile on the VPS. The Orchestrator coordinates all others.

## Agent Roster

| Agent | Profile Name | Status | Primary Responsibility |
|---|---|---|---|
| Orchestrator | `orchestrator` | ✅ Defined | Coordinates the Forge Loop, delegates work |
| Architect | `architect` | ✅ Defined | System design, ADRs, technical decisions |
| Coder / Implementer | `coder` | ✅ Defined | Feature implementation, tests |
| Researcher | `researcher` | ✅ Defined | Market & model research |
| Risk & Safety Guardian | `risk-guardian` | ✅ Defined | Risk review, veto power on capital decisions |
| Backtester & Validator | `backtester` | ✅ Defined | Strategy validation against historical data |
| Documenter / Curator | `documenter` | ✅ Defined | Vault maintenance, skill extraction |
| Product Owner | `product-owner` | ✅ Defined | Backlog management, story refinement |

## Profiles To Create
> Run: `hermes profile create <name>` for each agent below

```bash
hermes profile create orchestrator
hermes profile create architect
hermes profile create coder
hermes profile create researcher
hermes profile create risk-guardian
hermes profile create backtester
hermes profile create documenter
hermes profile create product-owner
```

## Profile Locations
Once created: `~/.hermes/profiles/<name>/`

Each profile should have a `SOUL.md` or system prompt that embeds the agent's role, constraints, and responsibilities from its profile doc in this vault.

## Coordination Model
- All agents report through the Orchestrator
- Risk Guardian has independent escalation path to human
- No agent modifies live trading config without human approval
- See [[04-ForgeLoop/FORGE_LOOP]] for delegation routing table
