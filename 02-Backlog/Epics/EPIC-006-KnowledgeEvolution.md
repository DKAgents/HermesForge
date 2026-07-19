---
id: EPIC-006
type: epic
status: backlog
created: 2026-06-30
updated: 2026-06-30
tags: [epic, knowledge, rag, automation, self-improvement, wikilinks, strategy]
---

# EPIC-006: Automated Knowledge Evolution

## Goal

Transform the HermesForge vault from a static knowledge repository into a living, self-improving system. The vault should automatically maintain itself as new knowledge is added, actively discover non-obvious connections across trading concepts, structure strategies with evidence links, and write lessons from trading activity back into the knowledge base — closing the loop between experience and knowledge.

This epic is the intelligence layer on top of the vault infrastructure built in EPIC-001 and EPIC-008. It enables the Forge Loop (EPIC-005) to reason over a continuously improving knowledge base rather than a frozen snapshot.

---

## Stories

| ID | Story | Status |
|---|---|---|
| US-050 | Automate Ongoing Vault Maintenance | ⬜ Backlog |
| US-051 | Novel Connection Discovery Engine | ⬜ Backlog |
| US-052 | Living Strategy Layer | ⬜ Backlog |
| US-053 | Self-Improvement Feedback Loop | ⬜ Backlog |

---

## Definition of Done

- [ ] Vault re-indexes and re-embeds automatically on new content
- [ ] Connection discovery surfaces ≥1 actionable novel insight per week
- [ ] At least 2 complete strategy notes exist with full evidence links
- [ ] At least one backtest/paper trade lesson written back to vault end-to-end
- [ ] All stories accepted and documented

---

## Dependencies

- **Requires:** EPIC-001 (vault + git), US-008 (Murphy ingestion pipeline, FTS/embedding indexes)
- **Enables:** EPIC-002 (strategies informed by discovered connections), EPIC-005 (Forge Loop reads richer vault)
