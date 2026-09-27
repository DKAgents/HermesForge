# MIG-5: Move 04-Strategies → trading/strategy-catalog

**Date**: 2026-09-27

**Moved**: `04-Strategies/` → `trading/strategy-catalog/` (contains
phase1a-results.md, STR-20260908-SKEW-PREDICTED-vault-note.md,
STR-20260917-CAP-BOTTOM-vault-note.md, strq-variants.md,
t1-discovered-strategies.md, vault-strategy-ideas.md).

**Script updated**: `scripts/validation/run_phase1a_batch.py` —
`OUTPUT_PATH` and docstring changed to `trading/strategy-catalog/`.

**Zero other scripts** reference `04-Strategies/`.

**04-ForgeLoop, 05-Research, 06-Strategies**: not moved, not merged.

**Rollback**: `git revert` of this commit.