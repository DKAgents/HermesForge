---
type: hermes-release-delta
campaign: 2026-09-aegis-rebuild
status: DEGRADED
generated_utc: 2026-09-06
display_tz: America/Los_Angeles
---

# Hermes Release Delta

## Installed (FACT, hermes-version.md)

- Hermes Agent **v0.20.6 (2026.8.27)**, upstream ref 26350357
- Install: git, `/usr/local/lib/hermes-agent`, Python 3.11.15, OpenAI SDK 2.24.0
- **Update available: 5917 commits behind** — `hermes update` offered
- No `hermes update --plan` receipt supplied in the brief

## Framing

The skill authority pins compatibility at "Hermes Agent >=0.20.6", so the
installed version meets the campaign floor. But a **5917-commit gap** is itself a
robustness risk: unknown behavioral and default changes. The rule stands —
adopt a native primitive **only if it deletes a Forge workaround** — and the
upgrade itself must be staged carefully.

Upgrade-campaign success = **net deletion**.

## The three questions (evaluated, not rubber-stamped)

**1. What custom Forge code duplicates a native primitive?**

Candidates to evaluate against current Hermes (cannot confirm without a
`--plan` receipt and changelog for the 5917 commits):

- `crosspost_webhook_all.sh` / `webhook_crosspost.sh` vs native **signed
  outbound webhooks** — if Hermes now signs and fans out webhooks natively, the
  two crosspost scripts (`61cccd`, `356f3c`) could collapse to config. Publisher
  owns these — evaluate in US-130 (Train 5), do not delete blind.
- Ad-hoc state files vs native **cron notepads / continuity** — weekly research
  (`9202661`) is a legitimate notepad candidate; 5-minute heartbeats (STR-Q
  class) must NOT get persistent notepads (invariant).
- `cron_watchdog.py` vs native **monitor-mode skip-LLM** — if a native
  change-detector exists, the custom watchdog may thin.
- Custom model-review script vs native model-routing telemetry.

**2. What native primitive removes a cron, profile, or state file?**

- Native webhook signing → removes one crosspost cron (if truly redundant).
- `hermes update --plan` receipts → replace ad-hoc upgrade tracking.
- Worktree prune → housekeeping, no data risk.
- Kanban as control plane with Discord publish-only → could reduce dead-channel
  ambiguity (Phase C) — but publisher owns Discord I/O.

Each of these is a **candidate**, not a decision. None is actioned this run.

**3. What new default is unsafe on 8 GB if left on?**

Unknown across 5917 commits. This is the primary reason to stage the update
behind a `--plan` receipt and a durability baseline. Specifically watch for:
new always-on skills, larger default context windows, increased default
concurrency, or memory/notepad-on-by-default — any of which pressures 8 GB RAM.

## Recommendation (sequencing, not implementation)

1. Do **not** run `hermes update` until Train 0 durability lands (journal +
   snapshots + off-box + restore drill). An upgrade mid-flight on a
   rewrite-the-world trades.csv is the exact hazard that produced the Sep 1–5
   loss.
2. Generate a `hermes update --plan` receipt; attach it to the next campaign
   brief's `hermes-version.md`.
3. Adopt native primitives one at a time, each PR deleting the workaround it
   replaces, each behind a Train-5 story. Publisher-owned adoptions (webhooks)
   are publisher's to implement.
