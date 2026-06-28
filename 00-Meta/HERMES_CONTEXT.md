---
title: HERMES_CONTEXT
type: meta
created: 2026-06-27
updated: 2026-06-27
status: active
tags: [meta, context, system]
---

# HermesForge — System Context

## Mission
Build a professional-grade, secure, observable, and continuously improving trading system powered by Hermes agents. The system is well-architected, heavily documented in this Obsidian second brain, and built iteratively through the Forge Loop.

## Core Philosophy
- **Vault-first**: The Obsidian vault is the long-term structured memory of the system. Every decision, learning, and plan lives here.
- **Paper-first**: All trading functionality starts in paper trading mode. No live capital until the Risk & Safety Guardian signs off.
- **Human-in-the-loop**: Approval required before any change to execution or risk parameters.
- **Iterative improvement**: The Forge Loop continuously selects work, delegates, executes, and reflects.
- **Evidence-based**: Decisions are backed by data. ADRs document the why behind every major choice.

## System Overview

```
Human ↔ Orchestrator Agent
              │
    ┌─────────┼──────────┐
    ↓         ↓          ↓
Architect   Researcher  Risk Guardian
    ↓         ↓          ↓
Coder    Backtester  Documenter
              ↓
        Product Owner (Backlog)
```

## Key Locations
| Resource | Path |
|---|---|
| Vault root | `~/HermesForge` (VPS) |
| Hermes profiles | `~/.hermes/profiles/` |
| Hermes config | `~/.hermes/config.yaml` |
| Backlog | `02-Backlog/` |
| ADRs | `03-ADRs/` |
| Forge Loop | `04-ForgeLoop/` |
| Agent Profiles | `01-Agents/Profiles/` |

## Current Phase
**Phase 0: Bootstrap** — Vault created, profiles defined, initial backlog seeded. Forge Loop being established.

## Active Constraints
- All trading logic in **paper mode** only
- No leverage
- Max single-position risk: 1% of capital
- Human approval required for any live execution changes
- ADR required for all major architectural decisions

## Model Routing Strategy
- **Bootstrap phase**: Claude Sonnet 4.6 via OpenRouter (quality bias)
- **Future**: Custom ModelRouter skill that learns from outcomes (cost vs. quality optimization)
- **MOA**: Reserved for high-value, high-complexity tasks only

## Last Updated By
Hermes Agent — Bootstrap Mission execution (2026-06-27)
