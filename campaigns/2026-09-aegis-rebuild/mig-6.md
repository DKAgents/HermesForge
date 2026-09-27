# MIG-6: Move 04-ForgeLoop → code/forge-loop

**Date**: 2026-09-27

**Moved**: `04-ForgeLoop/` → `code/forge-loop/` (45+ files — Discovery,
Maintenance, audit reports, edge factory results, X-scout, Forge logs).

**Scripts updated** (8):
- `scripts/cron/scout_x_wrapper.py` — `CANDIDATES_FILE`
- `scripts/discover_connections.py` — `DISCOVERY_DIR`
- `scripts/maintain_vault.py` — `LOG_DIR`
- `scripts/validation/walk_forward_us114.py` — `OUTPUT_PATH`
- `scripts/validation/str_y_parameter_sweep.py` — `FORGE_LOOP_DIR`
- `scripts/validation/edge_factory.py` — `RESULTS_DIR`
- `scripts/validation/scout_x_strategies.py` — `FORGE_DIR`
- `scripts/validation/walk_forward_us115.py` — `OUTPUT_PATH`

**Not moved**: `05-Research`, `06-Strategies`, `07-Risk`, `08-Knowledge`.

**Rollback**: `git revert` of this commit.