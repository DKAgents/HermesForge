# MIG-8: Move 05-Research → trading/research

**Date**: 2026-09-27

**Moved**: `05-Research/` → `trading/research/` (contains Edge-Candidates,
Market-Intelligence, Markets, Models, Strategy-Validation).

**Scripts updated** (4):
- `scripts/research/hype_strategy.py` — `REPORT_DIR`
- `scripts/research/edge_discovery_engine.py` — `EDGE_CANDIDATES_DIR`
- `scripts/check_frontmatter.py` — `SCAN_DIRS` entry
- `scripts/maintain_vault.py` — `VAULT_DIRS` entry

**Not moved**: `06-Strategies`, `07-Risk`, `08-Knowledge`, `09-Journal`.

**Rollback**: `git revert` of this commit.