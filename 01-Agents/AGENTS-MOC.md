---
type: moc
topic: agents
created: 2026-07-30
updated: 2026-07-30
tags: [moc, agents, navigation]
---

# Agents MOC

Navigation hub for all HermesForge agent profiles.

## Agent Roster

```dataview
TABLE role, tools
FROM "01-Agents/Profiles"
SORT file.name ASC
```

## Forge Loop

The [[FORGE_LOOP]] coordinates all agents through a 7-phase cycle:
1. Read vault context
2. Select backlog stories
3. Delegate to subagents
4. Execute
5. Review (Risk Guardian veto)
6. Document results
7. Reflect

## Related
- [[AGENT_INDEX]]
- [[FORGE_LOOP]]
- [[DECISIONS-MOC]]
