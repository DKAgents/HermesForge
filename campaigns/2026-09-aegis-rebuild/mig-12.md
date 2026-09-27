# MIG-12: Move 09-Journal → trading/journal

**Date**: 2026-09-27

**Moved**: `09-Journal/` → `trading/journal/` (00-Lesson-Index, Bootstrap entries, daily journals, Lessons/).

**Scripts updated** (5):
- `scripts/check_frontmatter.py` — `SCAN_DIS` entry
- `scripts/extract_lessons.py` — list entry + docstring
- `scripts/maintain_vault.py` — `VAULT_DIS` entry + comment
- `scripts/dedup_notes.py` — `VAULT_DIS` entry
- `scripts/paper_trading/extract_lessons.py` — `LESSONS_DIR` path

**Not moved**: `06-Strategies`, `08-Knowledge`.

**Rollback**: `git revert` of this commit.