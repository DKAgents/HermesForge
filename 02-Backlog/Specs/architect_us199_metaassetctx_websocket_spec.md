# Architect Spec — US-199 (Persistent websocket for metaAndAssetCtxs)

Date: 2026-11-02
Author: Architect (HermesForge)
Status: DESIGN ONLY — endpoint/channel + reconnect/backfill + store schema +
cadence + failure handling. No pipeline code, no cron, no .env changes.
Awaiting sign-off.
Epic: EPIC-017 (Gauntlet Pipeline Productionization), Phase 1 (Data depth)
Scope: replace/depth-extend the HOURLY snapshot ingest of `metaAndAssetCtxs`
with a PERSISTENT websocket listener so mark/oracle basis + OI + funding accrue
continuously (minute-level or finer) instead of once/hour.

Ground truth read:
- 02-Backlog/Stories/US-199-Persistent-MetaWebsocket.md
- scripts/data/hl_assetctx_store.py (existing hourly snapshot store; asset_ctx table)
- reports/gauntlet-pipeline-diagnostic-2026-11-02.md §2 (HL data table + the
  "no history endpoint → real basis gated ~weeks; hourly snapshot" flag)
- EPIC-017 hard constraints (consistent fail-closed posture; 403/geo-blocks permanent)

Summary of the defect this fixes: the real mark-oracle basis and per-coin OI
needed to feed G1 (size-relative depth), G3 (bar-level realistic fills), and the
funding/basis decomposition (US-185 §2.3) are only as deep as the HOURLY
snapshot. An hourly `metaAndAssetCtxs` poll is a coarse, poll-driven series;
anything faster than hourly (intra-hour basis dislocations, OI spikes, funding
premium moves) is invisible. A persistent listener converts this from a "snapshot
log" into a "continuous history."

---

# PART 1 — Endpoint & channel

## 1.1 Endpoint

    wss://api.hyperliquid.xyz/ws

Same host as the info endpoint already in use. Websocket (not a polling POST).

## 1.2 Channel

Primary subscription target: the Hyperliquid asset-context push channel, referred
to here as **`activeAssetCtx`** (canonical HL name for the stream that pushes
updated asset contexts: per-coin `funding`, `openInterest`, `markPx`, `oraclePx`,
`dayNtlVlm`, `premium`, `impactPxs`, etc.).

**FLAG / OPEN (must verify live before implement):** the exact channel name and
its push cadence/semantics are NOT yet confirmed against the live HL websocket
from this repo. The diagnostic already recorded that HL's websocket REJECTS some
channels (`liquidation` is not public). Therefore:

- Before implementation, a read-only probe MUST confirm `activeAssetCtx` (or the
  equivalent) subscribes successfully and returns the fields the store needs
  (`markPx`, `oraclePx`, `funding`, `openInterest`).
- If the push channel is unavailable or does not emit the required fields at the
  required cadence, the FALLBACK is a finer-grained POLL of the existing
  `metaAndAssetCtxs` POST (e.g. every 60s), NOT a fabricated bar. This fallback
  preserves correctness (no fabricated data) at the cost of "push" → "fine poll";
  the store schema (§3) and gap-backfill (§2) are designed to be identical under
  either transport.

## 1.3 Message shape (expected, to verify)

Each push carries an array of per-coin asset contexts. The listener extracts, per
non-delisted coin: `{coin, time, mark_px, oracle_px, funding, premium,
open_interest}` — the identical fields the hourly `parse_snapshot` already emits,
so the store is transport-agnostic.

---

# PART 2 — Reconnect & gap-backfill strategy

No data loss on reconnect is an explicit acceptance criterion. Design:

1. **Monotonic sequence, no overwrite.** Every appended row is keyed
   `(coin, time)` with `INSERT OR IGNORE` (existing store idiom). Re-delivery of
   the same `(coin, time)` after a reconnect is a no-op, not a duplicate.

2. **Reconnect with backfill.** On disconnect:
   - exponential backoff reconnect (e.g. 1s → 2s → 4s → capped 30s), forever
     (the process is a daemon, not a cron that gives up).
   - on reconnect, record the **last persisted `time`** per coin and issue a
     `metaAndAssetCtxs` POST (the REST endpoint) to backfill the gap between
     the last persisted timestamp and now, BEFORE resuming `INSERT OR IGNORE`
     appends from the live stream.
   - the backfill is the authoritative repair; the stream appends only forward
     from the reconnection point. `INSERT OR IGNORE` makes overlap harmless.

3. **Gap detection is explicit, not inferred.** A background loop periodically
   (e.g. every 5 min) checks per-coin `max(time)` against wall-clock to detect a
   silent gap (stream up but not delivering). A detected gap triggers the same
   REST backfill rather than being left silent. This is the defense-in-depth the
   user has repeatedly required: a silent gap must be *surfaced and repaired*,
   not ignored.

4. **No fabricated bars.** If both the stream AND the REST backfill fail for a
   window, that window is recorded as a **gap marker** (a row with
   `mark_px=NULL`/`source='gap'`, or a separate `data_gaps` table) — it is NEVER
   filled with interpolated, last-known-good, or synthetic values. Downstream
   consumers read NULL as "no data," not "step function."

---

# PART 3 — Store schema

Extend the existing `hl_assetctx_store` (`assetctx.db`) rather than create a
parallel store, so the funding/basis decomposition (US-185 §2.3) reads ONE series.

```sql
-- extended asset_ctx (adds source + cadence provenance; existing columns kept)
CREATE TABLE IF NOT EXISTS asset_ctx (
    coin          TEXT    NOT NULL,
    time          INTEGER NOT NULL,   -- ms epoch (snapshot/push time)
    mark_px       REAL,
    oracle_px     REAL,
    funding       REAL,
    premium       REAL,
    open_interest REAL,
    source        TEXT    NOT NULL DEFAULT 'poll',   -- 'ws' | 'poll' | 'backfill'
    PRIMARY KEY (coin, time)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_assetctx_coin_time ON asset_ctx (coin, time);

-- optional gap ledger (fail-closed transparency; only written when both
-- transports fail for a window — never a fabricated data row)
CREATE TABLE IF NOT EXISTS assetctx_gaps (
    coin      TEXT    NOT NULL,
    gap_start INTEGER NOT NULL,
    gap_end   INTEGER NOT NULL,
    detected  INTEGER NOT NULL,
    PRIMARY KEY (coin, gap_start)
);
```

`source` provenance (`ws`/`poll`/`backfill`) is new and lets audit distinguish
live-push rows from backfilled rows. `premium` is retained for provenance only
(it is the impact-price premium, NOT a creditable basis — binding, per US-185
§2.2; the creditable basis is always `(mark_px - oracle_px)/oracle_px`).

---

# PART 4 — Cadence

- Push cadence: whatever HL emits (expected on the order of seconds to ~tens of
  seconds for `activeAssetCtx`; VERIFY). The listener does not throttle; it
  persists every emitted snapshot (or, if HL is bursty, downsamples to ≥1s with
  `INSERT OR IGNORE` absorbing excess).
- **Required achievable resolution: minute-level or finer** (acceptance
  criterion). The store must end with ≥1 row/coin/minute with no gaps over a
  24h soak.
- Fallback poll cadence (if push unavailable): 60s.

---

# PART 5 — Failure handling (fail-closed)

1. **Process is a systemd/daemon, not a cron job** (US-199 explicit). A cron
   cannot hold a websocket open. `Restart=always` + the reconnect/backfill loop
   in §2.
2. **Fail-closed on malformed/partial messages:** a malformed frame is dropped
   and logged; it is never partially parsed into fabricated rows. If a frame is
   unparseable, nothing is written for that frame.
3. **No last-known-good extrapolation:** on any transport failure, NULL/gap
   markers are written (or the gap ledger updated), never synthetic continuity.
4. **Downstream consumers must be gap-aware:** any consumer of
   `read_basis(coin)` must treat NULL/`source='gap'` rows as "no observation,"
   never carry-forward. (Matches ADR-010's fail-closed bar policy for G7.)
5. **Resource bounds:** the listener is single-connection, single-process; no
   unbounded memory queue. If it cannot drain writes fast enough, it DROPS the
   oldest queued snapshot and logs a `write_lag` warning (never blocks the
   socket and never writes out-of-order — time-monotonic `INSERT OR IGNORE` keeps
   correctness).

---

# PART 6 — Assumptions & open questions

- Q1 **Channel name unverified.** `activeAssetCtx` is the assumed HL channel; the
  exact name, subscription request shape, and push cadence MUST be confirmed by a
  read-only probe before the coder implements. The fallback (60s poll) is the
  correct-and-safe default if the channel is wrong/missing. OPEN.
- Q2 **Push cadence / downsample policy.** Whether HL pushes every asset on every
  tick (bursty) or at a fixed heartbeat is unverified; the ≥1s-downsample/INSERT
  OR IGNORE policy assumes burstiness. OPEN.
- Q3 **Whether `openInterest` needs the long/short split.** HL `metaAndAssetCtxs`
  gives TOTAL OI only (diagnostic §2, verified). This listener does NOT solve the
  long/short split; that remains derived (oi_delta) or needs Coinglass. OUT of
  scope, flagged to set expectations.
- Q4 **Retention.** The existing store is forward-accumulating with no stated
  retention. OPEN — is indefinite retention acceptable, or does the continuous
  stream need a retention/rollup policy to bound disk?
- Q5 The gap-ledger table (`assetctx_gaps`) is new; confirm it is wanted now or
  defer (NULL rows in `asset_ctx` can carry the same signal without a second
  table). OPEN.

END OF DESIGN.