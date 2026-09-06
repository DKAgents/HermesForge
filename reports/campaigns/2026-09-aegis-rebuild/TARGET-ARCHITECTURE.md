---
type: target-architecture
campaign: 2026-09-aegis-rebuild
status: DEGRADED
generated_utc: 2026-09-06
display_tz: America/Los_Angeles
---

# Target Architecture — HermesForge

Three layers only. Proposals below; Aegis does not implement. Deletions are
withheld this run (DEGRADED brief) except where an explicit replacement is named
and evidence is direct.

---

## Layer 1 — Effectiveness

- **One persist API.** All writers go through a single append-only journal API.
  `trades.csv` becomes a *derived projection* rebuilt from the journal, never
  the source of truth. Replaces: the current `trade_log.py` whole-file rewrite
  model. (US-123)
- **One exit monitor / one exit authority.** Exactly one process may close a
  position. STR-Q intraday (`b9fb0af`, */5) and Trade Monitor (`d1e07c`, 60m)
  must not both close. Options (for the coder + risk-guardian to decide, not
  Aegis): (a) Trade Monitor owns all closes and STR-Q sweep only emits
  entry/stop-adjust signals; or (b) an explicit ownership key per strategy so
  each open trade has exactly one closer. Replaces: the dual-closer split.
  (US-125)
- **Seeder + filter.** Keep the reject-heavy filter (it is working as designed).
  Add a *coded* candidate seeder so generation is not ad-hoc, with promotion
  gated by Risk Guardian and walk-forward OOS. 0% promotion past WATCH is
  acceptable only if the gates are real and a seeder exists. (US-127)
- **Publisher-owned alerts stay publisher-owned.** No exit-alert or embed code
  moves out of publisher's 9 files. Aegis files stories; publisher owns edits.

## Layer 2 — Robustness

- **Append-only journal** (JSONL or SQLite WAL; no DELETE/UPDATE on fact rows).
  Guards: refuse empty payload, refuse row-count regression, refuse backward
  `signal_id` or timestamp. (US-123)
- **Snapshots ≥ 35 days on-box**, plus an **off-VPS copy**, plus a **weekly
  restore drill** that actually reconstructs `trades.csv` from the journal and
  diffs it. Replaces: ad-hoc `.bak` files and "git push == backup." (US-126)
- **Same protection class for `crosspost_state.json`** — guard + snapshot.
  Publisher-owned; publisher implements. (US-131)
- **Structured logs / RCA / cron evidence must not be purged** by Vault
  Maintenance before their retention window. Confirm retention ≥ snapshot
  horizon. (US-129)
- **F&G fetch fail-closed.** A stale regime feed must disable regime-conditional
  sizing rather than silently pass. (US-128)
- **Git stores code + manifests only** (`sha256`, rows, `last_id`) — not the
  live data file as the backup mechanism.

## Layer 3 — Efficiency

Guidance only; no cron/profile deletions sequenced this run (need US-124).

- Fewer *hot* profiles over time, but **never collapse publisher or Risk
  Guardian** — both are monopolies by invariant.
- Trading and consulting are *surfaces*, not always-hot judgment loops.
- Red-team may run on-demand (T3 flash already), not standing.
- Documenter may become a coder skill rather than a standing profile —
  evaluate once inventory exists.
- No-agent for all non-judgment work (already 8/21 — extend after measurement).
- Per-profile tool allowlists (no `all`) — cannot specify without inventory.
- Do NOT merge unrelated crons into mega-jobs on 8 GB RAM.
- Every new Hermes feature adopted must delete a workaround (see release delta).

---

## Migration trains (fixed order — do not schedule 4/5 ahead of 0)

**Train 0 — Survive (all filed this run):**
US-124 (build inventory/cost — unblocks everything), US-123 (journal + derived
CSV), US-126 (snapshots + off-box + restore drill), US-125 (single exit
authority), US-128 (F&G fail-closed), US-129 (vault retention audit),
US-131 (crosspost_state protection).

**Train 1 — Thin runtime (DEFERRED until US-124):**
per-profile tool allowlists, mechanical crons → no-agent (extend beyond current
8), weaver cadence decision (measured), worktree prune, context caps.

**Train 2 — Unify trading I/O (depends on US-123):**
one persist API adopted by all writers, one exit authority live (US-125), PnL
recomputed from journal + manifests.

**Train 3 — Strategy factory:**
US-127 coded seeder; keep reject-heavy filter; red-team + backtester + Risk
Guardian in the promotion loop.

**Train 4 — Swarm diet (DEFERRED until US-124):**
fewer standing profiles; Discord is output-only. No profile DELETE without
inventory evidence.

**Train 5 — Release adopt:**
US-130 (evaluate crosspost overlap), plus native primitives from the release
delta that each delete a workaround. Behind a `hermes update --plan` receipt.

Token-budget table: see `TOKEN-RAM-BUDGET.md`.
