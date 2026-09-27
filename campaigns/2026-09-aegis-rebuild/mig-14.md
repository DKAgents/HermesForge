# MIG-14: Move 08-Knowledge → trading/knowledge

**Date**: 2026-09-27

**Moved**: `08-Knowledge/` → `trading/knowledge/` (Connection-Health, Insights, KNOWLEDGE-MOC, Learnings, Skills, Trading-Systems).

**Scripts updated** (11):
- `scripts/build_index.py` — `VAULT_DIS` entry + docstring
- `scripts/check_frontmatter.py` — `SCAN_DIS` entry
- `scripts/dedup_notes.py` — `VAULT_DIS` entry
- `scripts/discover_connections.py` — `INSIGHTS_DIR`, `KNOWLEDGE_DIR`, docstring
- `scripts/embed_vault.py` — `VAULT_DIS` entry
- `scripts/extract_lessons.py` — `KNOWLEDGE_DIR`
- `scripts/generate_wikilinks.py` — `KNOWLEDGE_DIR`
- `scripts/maintain_vault.py` — `VAULT_DIS` entry, `MURPHY_DIR`
- `scripts/tag_vault_topics.py` — path + docstring + arg help
- `scripts/validate_strategy.py` — list entry
- `scripts/vault_connection_weaver.py` — `HEALTH_PATH` + docstring

**Not touched**: `capture_signals.py` (verified no reference to 08-Knowledge).

**Not moved**: `06-Strategies`.

**Rollback**: `git revert` of this commit.