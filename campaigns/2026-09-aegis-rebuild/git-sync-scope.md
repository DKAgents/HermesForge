# Git sync scope

Date: 2026-09-27
/usr/local/sbin/hermes-git-sync adds scripts and campaigns only.
.env is ignored (.gitignore:45).
config.yaml is not in the add list. Do not add it. It may hold a token.
Trade history is not in the add list. Leave it out.
Off-box backup remains the copy for data that git must not store.

## US-178 (2026-11-01): path-scoped commit gate

The sync script now declares its paths explicitly via a `SYNC_PATHS=(scripts
campaigns)` array and MUST NOT use `git add -A` / `git add .`. Blanket staging
swept unrelated `.bak` and `cache/` files into history (commit 7547a580); those
are now also gitignored (`*.bak`, `*.bak.*`, `cache/`). A synthetic run confirms
only `scripts/` and `campaigns/` files enter the commit — `.bak`, `cache/`, and
repo-root files are excluded.
