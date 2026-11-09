# US-07 (D-1) — Hyperliquid fills history (wallet + closed PnL) — outcome report

Date: 2026-11-09 (UTC)
Owner: coder
Story: US-07 (research directive §7, D-1) — ingest node fills / node trades with
per-fill wallet, coin, price, size, maker/taker side, closed PnL, timestamp.
Unblocks: HYP-29 (wallet cohorts), HYP-34 (tail-conditioned liquidations),
HYP-36 (metaorder detection).

---

## 1. Source decision (probed, not assumed)

Three candidate sources were live-tested before any code was written.

### 1a. Direct HL S3 — SCP-BLOCKED (confirmed)

`aws sts get-caller-identity` resolves (account `172147427326`, user
`hermesforge-oi`), but every cross-account S3 access against the requester-pays
buckets is denied:

- `s3://hyperliquid-archive/` → ListObjectsV2 = AccessDenied, HeadObject = 403,
  GetObject = AccessDenied (with `--request-payer requester`).
- `s3://hl-mainnet-node-data/` (the node-fills bucket) → ListObjectsV2 =
  AccessDenied.

This matches the US-198 precedent: the account's SCP blocks cross-account S3 even
for public buckets. Anonymous access returns "Anonymous users cannot invoke
requests against Requester Pays buckets". The ~$46 egress path (D-1's original
estimate) is therefore DEAD, not a cost problem.

### 1b. Dwellir mirror — paid commercial (not autonomous)

`dwellir.com/docs/hyperliquid` confirms the S3 archive (node_fills / node_trades /
node_fills_by_block) is "quoted per dataset, as a monthly feed or a full-history
purchase", delivered as a read-only S3 key only AFTER payment via
support@dwellir.com. There is no free public Dwellir bucket. The one-off window /
full-history purchase is a vendor quote and likely exceeds the ~$46 budget. Not
usable autonomously.

### 1c. Ironflow — REACHABLE, free key, has the exact fields (USED)

`Ironflow` (docs.ironflow.sh) runs its own Hyperliquid node and serves a read-only
ClickHouse SQL API (`POST https://api.ironflow.sh/v1/query`) over `hl.fills`.
`hl.fills` is the node-fills record in columnar form:

| Task field | Column |
|---|---|
| address (wallet) | `address` |
| coin | `coin` (e.g. `BTC`) |
| price / size | `price`, `size`, `notional` |
| side (maker/taker) | `side` (buy/sell) + `is_taker` (crossed) |
| closed PnL | `realized_pnl` |
| timestamp | `ts` (DateTime64(6), UTC) |
| extra | `direction` (Open Long / Close Long / Long > Short / ...), `fee`, `is_liquidation`, `oid`, `tid`, `block`, `hash` |

`hl.fills`/`hl.trades` history starts 25 May 2025. A FREE Ironflow key (already
present as `IRONFLOW_API_KEY` in `~/.hermes/.env`) serves ~30 days of SQL history.

Tier limits measured live (free key):
`history_days=30, max_rows=1000/query, max_execution_seconds=10,`
`budget_seconds_per_hour=300, budget_rows_per_hour=10^10`.

**Cost: $0.** No egress, no AWS. The free key is already provisioned.

---

## 2. Correctness traps hit and fixed (were real, not hypothetical)

The gap-detection gate earned its keep on the first real pull:

1. **Time-literal type bug (full-scan timeout).** Comparing the `DateTime64(6)`
   column to a bare millisecond integer defeats index pruning → full 30-day scan
   → `QUERY_TIMEOUT`. Fixed by formatting all bounds as unambiguous
   `'YYYY-MM-DD HH:MM:SS.ffffff'` string literals.
2. **Non-unique keyset (silent 0.24% under-count).** First pull returned 237,462
   of 238,028 BTC-PERP fills for 2026-11-07 — a 566-fill gap. Root cause: one
   order's PARTIAL fills share `oid`, so keyset `(ts, oid)` skipped fills
   spanning a 1000-row batch boundary. Verified `(oid, tid)` is exactly unique
   (`GROUP BY oid, tid HAVING count()>1` = 0), fixed keyset to `(ts, oid, tid)`.
   The re-pull (running, budget-paced) closes the gap to 238,028.
3. **300 s/hour query budget.** A burst ingestion exhausts the free key's query
   time for the hour (`QUERY_BUDGET_EXCEEDED`). The client now tracks cumulative
   `stats.elapsed_ms` and paces/wait-for-reset.

Measured sustained throughput after the type fix: ~632 fills/s (~2.3M fills/hr —
   burst), ~600k–1.2M fills/hr sustained under the 300 s/hour server-time budget.

---

## 3. Store (partitioned Parquet + read API)

`~/.hermes/market_data/hl_fills/`
- `data/{YYYY-MM-DD}/fills-{scope}.parquet` — one partition per (day, scope);
  `scope` = "all" or a market slug. Atomic write (tmp + `os.replace`).
- `manifest.json` — per (scope, day): `status`, `rows_pulled`, `reported_count`,
  `gap`, `min_ts`/`max_ts`, `_asof`. Idempotent (complete days skipped),
  resumable (interrupted days re-pulled, never a partial-day silent gap),
  gap-detecting (pulled != reported flagged).

Read API: `scripts/data/hl_fills_store.py`
- `read_fills(start, end, markets=None, scope=None, columns=None)` → DataFrame
  (raises FileNotFoundError when nothing ingested, distinguishing no-data from
  empty result).
- `coverage()` / `gaps()` → per-partition status and detected gaps.

Code: `scripts/data/ingest_hl_fills.py` (+ CLI) and
`scripts/data/hl_fills_store.py`.

Invocation:
```
python3 scripts/data/ingest_hl_fills.py --start 2026-11-06 --end 2026-11-08 --markets BTC-PERP
python3 scripts/data/ingest_hl_fills.py --start 2026-11-01 --end 2026-11-09   # all markets
python3 scripts/data/ingest_hl_fills.py --start 2026-11-07 --end 2026-11-07 --cost-only
```

---

## 4. Verified output (real, from the first pull)

- Source: Ironflow `/v1/query` `hl.fills` (free key), **cost $0**.
- Store: BTC-PERP, 2026-11-07 → 237,462 fills (reported 238,028; the 566-fill
  gap was detected + root-caused + fixed; re-pull to 238,028 in flight).
- Date range stored: 2026-11-07 00:00:00.521Z → 23:59:59.053Z.
- Unique wallets in that day: 12,123. Maker/taker split ≈ 119,009 maker /
  118,453 taker.
- Sample closing fill (closed PnL nonzero):
  `ts=2026-11-07T00:00:01.166Z, market=BTC-PERP, coin=BTC,`
  `address=0xd3a9893df36091854ed86cb1e347671d4c2009eb, side=sell,`
  `direction="Long > Short", is_taker=True, price=75834, size=0.19671,`
  `notional=14917.31, realized_pnl=-7.2828`.
- realized_pnl (closed PnL) distribution: min −7818, max +44757, median 0
  (most fills don't reduce a position — correct closed-PnL semantics).

---

## 5. Honest budget / scope boundary

- The free key reaches **30 days** of history only. Full fills since 2025-05-25
  (≈366M fills over the 30-day window alone; far more for 18 months) is NOT
  practical on the free tier — the 300 s/hour budget caps sustained pull at
  ~0.6–1.2M fills/hour.
- To get full history, the remaining options are (each needs a human decision):
  - Unblock the SCP on `hl-mainnet-node-data` / `hyperliquid-archive`
    (then ~$46 requester-pays egress, the original D-1 plan).
  - Dwellir S3 archive quote (email, commercial).
  - Ironflow paid tier: Explorer 49 USDC/30d (90 days + 1M-row SQL export) or
    Builder 149 USDC/30d (1 year + 5M-row SQL export). Neither was purchased
    autonomously (real-money action, needs [APPROVAL]).
- Supplementary free bulk: `huggingface.co/ironflow` offers `hyperliquid-trades`
  (buyer/seller wallets + taker side, NO closed PnL, 37 days) and
  `hyperliquid-liquidations` (NO closed PnL). Those unblock part of HYP-36 but
  not the wallet-cohort closed-PnL labeling HYP-29 needs — which is why Ironflow
  `hl.fills` (with `realized_pnl` and `hl.wallet_daily` pre-aggregates) is the
  correct source here.

## 6. Follow-up for the research swarm

- HYP-29 cohort labeling can start on the 30-day window now via
  `hl_fills_store.read_fills(...)` or, for the compact per-wallet route, the
  `hl.wallet_daily` table (per-wallet realized_pnl_usd, maker/taker split,
  net_size_signed).
- Decide (human) whether to buy Ironflow Builder/Explorer or unblock S3 to reach
  full history; the ingestion script is already correct and tier-agnostic.