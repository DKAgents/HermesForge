# Automation Standards

This document defines the standards that Hermes and other automated processes should follow when creating scripts, cron jobs, or any form of automation in the HermesForge system.

## 1. Script Location

All Hermes-related scripts should be placed in:
~/bin/hermes/

Recommended subfolders:
- `git/` — Git-related automation
- `trading/` — Trading bots and data pipelines
- `maintenance/` — Cleanup, backups, health checks
- `templates/` — Reusable script templates

## 2. Script Requirements

Every script should:

- Start with `#!/bin/bash`
- Use `set -euo pipefail`
- Load `keychain` if it needs SSH or Git access
- Write logs to `~/logs/hermes/`
- Be executable (`chmod +x`)
- Have a clear, descriptive name

## 3. Cron Jobs

- Cron jobs should call scripts in `~/bin/hermes/`
- Always load the SSH key via keychain when Git access is needed
- Use full paths
- Log output to `~/logs/hermes/`

## 4. Git Workflow

- Use the Feature Branch + Pull Request + Auto-Merge pattern (see `git-workflow-standards.md`)
- Prefer Squash + Auto-Merge for automated PRs
- Never push directly to `main` from automation

## 5. Logging

- All automated scripts should write logs
- Use consistent log file naming: `~/logs/hermes/script-name-YYYYMMDD.log`
- Include timestamps and clear success/failure messages

## 6. Error Handling

- Scripts should fail fast on errors (`set -e`)
- Critical failures should be logged and ideally reported (e.g. via Discord)