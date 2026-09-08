---
id: US-138
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-07
priority: P2
tags: [backlog, story, efficiency, weaver, tier, toolset-allowlist, cost]
campaign: 2026-09-aegis-rebuild
train: 1
owner_profile: coder
model_floor: no-agent
points: 3
depends_on: US-124
---

# US-138 — Right-size the Vault Connection Weaver (tier, cadence, toolset allowlist)

- **Train:** 1
- **Priority:** P2
- **Owner profile:** coder
- **Model floor:** no-agent (implementation is a cron-def + measurement change)
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need the Vault Connection Weaver's model tier, cadence, and
toolset scope justified by measured output quality, so that the fleet's single
largest cost item is not a T2 job with unrestricted tools producing near-zero
recent yield.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (second pass, 2026-09-07 UTC):

- FACT (cost): Weaver (`98edbe73d115`) is the **only T2 cron**
  (`deepseek-v4-pro`), every 240m, 180 runs/month, **$1.18/mo — the single
  largest LLM cost item** (65% of all LLM cron spend; total fleet LLM spend is
  ~$1.81/mo per `cost-30d.md`).
- FACT (toolsets): in the default profile's `jobs.json` the weaver's
  `enabled_toolsets` is **`None`** — i.e. it inherits the full toolset. Protocol
  Phase D requires per-cron/profile allowlists and states enabled toolsets
  "must not be `all`." Every other agent cron reviewed pins a toolset (e.g.
  Connection Discovery pins `['terminal']`).
- FACT (yield): `~/.hermes/vault_weaver/state.json` — 90 total runs,
  204 total connections created (~2.3/run lifetime). Recent examined-notes all
  show `connections_written: 0` despite `connections_found: 3–5`
  (e.g. STR-20260730-atr-contraction-breakout: found 5, written 0, score 5.0).
  Recent campaign commits corroborate: "run 90, 0 connections."
- INFERENCE: recent marginal value per T2 run is approaching zero while cost is
  fixed. Either the write path is gated too hard (a bug — high value, wrong
  fix), or genuine new connections are exhausted (low value, demote/slow it).
  Either way the current T2 + unrestricted-toolset + 240m shape is unjustified.

Protocol explicitly says: "Batch or demote Vault Connection Weaver off
T2-every-4h unless measured quality requires it." The measurement now exists and
does not justify the current shape.

## Acceptance

- [ ] Toolset allowlist applied to the weaver (e.g. `['terminal']` or the
      minimal set it actually uses) — `enabled_toolsets` is never `None`/all.
- [ ] A 10-run quality comparison T2 (`deepseek-v4-pro`) vs T3
      (`deepseek-v4-flash`) on identical note batches, scored on connections
      *written* (not merely found) and false-link rate.
- [ ] Decision recorded: (a) if `connections_written: 0` is a gating bug, fix
      the write path and keep the tier the quality test justifies; (b) if new
      connections are genuinely exhausted, demote to T3 and/or lengthen cadence
      (e.g. every 12–24h) — each option names the projected $/mo.
- [ ] Cadence/tier change (if any) applied via cron update by the owner of the
      default profile's cron surface — **not by Aegis**.
- [ ] Rollback recorded.

## Forbidden

- No live-soul edits
- No publisher-file edits
- No truncate/replace of history files (weaver writes wikilinks into vault notes
  additively; do not rewrite note bodies destructively)
- No credentials in output
- Aegis does not edit the cron definition — this story hands the change to the
  cron-surface owner with the evidence attached

## Rollback

Restore prior cron definition (T2, 240m, no toolset allowlist) from the
`.curator_backups/` cron-jobs snapshot. Toolset allowlist is additive and
reversible; no data mutated.
