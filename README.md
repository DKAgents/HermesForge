# HermesForge Trading System

> A professional-grade, secure, and continuously improving trading system powered by Hermes agents.

## Quick Start

This vault lives on the VPS at `~/HermesForge`. Access it from your Mac via SSHFS mount.

```bash
# Mount from Mac (example)
sshfs root@<your-vps-ip>:/root/HermesForge ~/HermesForge
```

## Vault Structure

| Folder | Purpose |
|---|---|
| `00-Meta/` | System context, mission, conventions |
| `01-Agents/` | Subagent profiles and coordination rules |
| `02-Backlog/` | User stories, epics, and acceptance criteria |
| `03-ADRs/` | Architecture Decision Records |
| `04-ForgeLoop/` | Forge Loop design, run logs, reflections |
| `05-Research/` | Market research, model research |
| `06-Strategies/` | Trading strategies, backtests, live configs |
| `07-Risk/` | Risk rules, guardian decisions, incident logs |
| `08-Knowledge/` | Skills, learnings, how-tos |
| `09-Journal/` | Daily logs, session notes |
| `Templates/` | Reusable note templates |

## Key Files
- [`00-Meta/HERMES_CONTEXT.md`](00-Meta/HERMES_CONTEXT.md) — Start here. Full system context.
- [`04-ForgeLoop/FORGE_LOOP.md`](04-ForgeLoop/FORGE_LOOP.md) — How the improvement loop works.
- [`02-Backlog/BACKLOG_INDEX.md`](02-Backlog/BACKLOG_INDEX.md) — Current work queue.

## Safety Rules
⚠️ All trading functionality starts in **paper mode**.  
⚠️ Human approval required before any live execution changes.  
⚠️ The Risk & Safety Guardian has veto power on capital decisions.
# Clean PR Test - Tue Jun 30 03:00:35 AM UTC 2026
