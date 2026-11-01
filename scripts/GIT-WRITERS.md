# Git writers — inventory & scoped paths

Every background process that writes to the HermesForge git repo MUST route its
add+commit through `scripts/git_commit_paths.py`, the single shared helper. That
helper:

- stages ONLY the explicit `--path` arguments (never `git add -A` / `git add .`),
- commits ONLY those paths (path-scoped `git commit -- <paths>`; ignores any
  unrelated pre-staged index entries), and
- serializes all concurrent writers via one exclusive `flock`
  (`~/.hermes/vault_maintenance/git_commit.lock`).
- It NEVER pushes.

Pushing is owned exclusively by the push-only cron.

## Writers

| Process | Schedule | Scope (paths) | Commit | Push |
|---|---|---|---|---|
| `hermes-git-sync` (`/usr/local/sbin/hermes-git-sync`) | system cron, every 15 min | `scripts/`, `campaigns/` | `auto: sync scripts and campaigns` | none (push-only cron pushes) |
| `vault_connection_weaver.py --commit` | Hermes cron (weaver job) | linked seed notes + `trading/knowledge/Connection-Health.md` | `vault-weaver: <ts> — ...` | none |
| `maintain_vault.py` | Hermes cron | vault dirs + `scripts/wikilink_report.json` | `vault-maintenance: <ts> — ...` | none |
| `snapshot_restore.py` (`_commit_data_manifest`) | aegis cron | `reports/campaigns/2026-09-aegis-rebuild/data-manifest.md` | `aegis: <ts> — data-manifest status update` | none |
| `daily_git_push.sh` | Hermes cron, 3am UTC | (no staging) | (no commit) | **push-only** — the sole pusher |

## Rules

- Background writers: scoped paths, no push, shared lock (route via
  `git_commit_paths.py`).
- Only `daily_git_push.sh` pushes (`git push origin main`), gated on unpushed
  commits.
- Ad-hoc human/engineer commits remain path-scoped and do not push mid-work.