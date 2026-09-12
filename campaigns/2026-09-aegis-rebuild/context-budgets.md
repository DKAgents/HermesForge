# US-139: HermesForge Context Budgets

**Date:** 2026-09-12 17:30 UTC  
**Method:** Measured skill descriptions, system prompt estimates, memory allocation from live session context. All profiles share the same skill directory (90 SKILL.md files, ~935 KB total on disk).

## Per-profile context budget (before session history)

| Component | Size | Notes |
|-----------|------|-------|
| System prompt + tool schemas | ~15.0 KB | Hermes rules, SOUL.md, tool definitions |
| Skill descriptions (90 skills) | ~3.7 KB | One-line descriptions from `available_skills` block |
| Skill format overhead | ~5.3 KB | Indentation, delimiters, categories |
| **Subtotal (fixed)** | **~24.0 KB** | Same for all 11 main profiles |
| Memory (MEMORY.md) | ~1.9 KB | Orchestrator only; others have no memory |
| User profile (USER.md) | ~1.3 KB | Orchestrator only; others share via system prompt |
| Session history | variable | Compaction applied; grows per conversation |
| **Total (orchestrator)** | **~27.2 KB + session** | |

## Profile inventory

| Profile | Skills | Config | Toolset Filter | Context (before session) |
|---------|--------|--------|---------------|--------------------------|
| orchestrator | 90 | none | none | 27.2 KB + session |
| publisher | 90 | none | none | 24.0 KB + session |
| coder | 90 | none | none | 24.0 KB + session |
| risk-guardian | 90 | none | none | 24.0 KB + session |
| researcher | 90 | none | none | 24.0 KB + session |
| trading | 90 | none | none | 24.0 KB + session |
| product-owner | 90 | none | none | 24.0 KB + session |
| architect | 90 | none | none | 24.0 KB + session |
| backtester | 90 | none | none | 24.0 KB + session |
| consulting | 90 | none | none | 24.0 KB + session |
| documenter | 90 | none | none | 24.0 KB + session |
| red-team | 81 | yes (306B) | none | 23.0 KB + session |
| aegis-auditor | 2 | yes (2125B) | none | 14.8 KB + session |

## Waste analysis

Every profile loads all 90 skills even though most need only 3-5:

| Profile | Actually uses | Wasted skills | Wasted description chars |
|---------|--------------|---------------|--------------------------|
| risk-guardian | governance (1) | 89/90 | ~3,772 B |
| publisher | discord, social-media, content (3-5) | ~85/90 | ~3,600 B |
| coder | software-dev, devops, github (5-8) | ~82/90 | ~3,470 B |
| trading | crypto, research, data-science (3-5) | ~85/90 | ~3,600 B |
| researcher | research, mlops (5-8) | ~82/90 | ~3,470 B |
| product-owner | note-taking, governance (2-3) | ~87/90 | ~3,690 B |
| backtester | data-science, mlops (2-3) | ~87/90 | ~3,690 B |

Total wasted across 11 profiles: ~40 KB of skill descriptions loaded per conversation turn. At 30 turns per session, that's ~1.2 MB of wasted context per session across the swarm.

## Optimization path

### P0 — Toolset allowlists (already started)
- Publisher: `terminal, read_file, search_files, discord, discord_admin`
- Risk-guardian: `terminal, read_file, search_files`
- Vault Connection Weaver: `terminal, read_file, search_files` (done, US-138)

### P1 — Skill allowlists (biggest win)
Each profile should load only relevant skills. Example:
- risk-guardian → `governance` (1 skill)
- publisher → `discord-trade-signal-publishing`, `content-automation-workflow`, `hermesforge-pipeline-maintenance` (3 skills)
- coder → `software-development-workflows`, `data-integrity-patterns`, `github-repo-management` (3 skills)

Saves ~3.6 KB per profile. Over 11 profiles: ~40 KB per turn.

### P2 — Shared rather than copied skills
All 11 heavy profiles have full copies of skills/ under `/root/.hermes/profiles/<name>/skills/`. If Hermes supports a shared skill path, switching to symlinks would save disk (~10 MB) but not context.

### P3 — Lazy-load skills
Hermes loads skill descriptions at session start. If it supported lazy-loading (only scan skills when user asks), skill descriptions wouldn't occupy context on every turn.

## Current aegis-auditor baseline

The lightest profile is aegis-auditor: 2 skills, custom config, 14.8 KB context. This is the target for other profiles. At 14.8 KB vs 24 KB, the auditor has 38% more context available for reasoning before hitting limits.

## Recommendations

1. **Immediate:** Add toolset allowlists to all profiles (US-119 pattern)
2. **Short-term:** Create skill subsets per profile — each loads only 3-5 relevant skills (saves 3.6 KB per profile, 40 KB per turn across swarm)
3. **Long-term:** Investigate Hermes lazy-load or shared skill directory support