# HYP-16 (high-OI expansion + trend) — DATA-GATED verdict

Date: 2026-11-02 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-16-high-OI-expansion.md (pre-registered, thresholds FIXED)

VERDICT: DATA-GATED — neither H1 nor H2 was run. The pre-registered data gate
(>~200d usable OI history per coin, top-30 coverage) is not met. No OI was
fabricated, price-proxied, or vendor-proxied. No thresholds were tuned (nothing
ran, so there is nothing to tune — G5 intact).

---

## 1. OI data assessment (verified against the stores on disk, not the reports)

Three candidate OI sources were audited directly via Python/sqlite3:

### (a) HL funding store — `~/.hermes/market_data/hl_funding/funding.db`
- Table `funding`: columns = `coin, time, funding_rate, premium`.
- **NO open-interest field.** `fundingHistory` returns hourly funding rate + premium
  only, not OI.
- Coverage: 35 coins, ~400 days hourly (9,616 rows/coin; 2025-09-27 -> 2026-11-02).
- Deep in time but **does not carry OI**. Cannot serve H1/H2.

### (b) HL assetctx store — `~/.hermes/market_data/hl_assetctx/assetctx.db`
- Table `asset_ctx` **does have** `open_interest` (and markPx -> oi_usd derivable).
- 179 coins. BUT history is **~19.5 hours only** (2026-11-01 23:00 -> 2026-11-02
  18:27; 787 hourly snapshots/coin). Forward-accumulating (US-199 listener went
  live ~2026-11-01); `metaAndAssetCtxs` has NO history endpoint.
- This is the ONLY native OI store, and it is effectively empty in time.

### (c) Snapshot-only artifacts
- `~/.hermes/market_data/oi_state.json` and `liquidation_proxy_state.json`:
  single CURRENT OI snapshot (TTL-overwritten), no history series.
- `hyperliquid_metrics/funding_*.parquet`: funding-rate caches, not OI.
- No OKX historical-OI endpoint is wired in the repo (grep for
  `rubik/open-interest-volume/history` = 0 matches; only a live `open-interest`
  snapshot fetcher in liquidity_heatmap.py).

### Depth / coverage summary
| Source | OI field? | OI history depth | Coins |
|---|---|---|---|
| funding store | NO (funding + premium only) | n/a | 35, ~400d |
| assetctx store | YES | ~19.5 h | 179 |
| oi_state / liq_proxy_state | YES (snapshot) | single point, TTL | ~33 |

Result: usable OI-history depth = **~19.5 hours** for all coins. Requirement:
~200 days. GATE NOT MET — by a factor of ~250x.

---

## 2. H1 (expansion: "high OI -> big move") — NOT RUN

The regime definition requires `OI >= 90th pct of trailing 90d`. That needs at a
minimum ~90 days of OI history per coin. Available: ~19.5 h. There is no series
to compute a trailing-90d percentile from. The coach's core claim — "OI
particularly high -> price ripe for a big move" — cannot be evaluated.

## 3. H2 (directional alpha) — NOT RUN

Same blocker: the extreme-OI entry condition is incomputable. Net expectancy,
edge-minus-taker-minus-funding, out-of-sample CPCV, PBO, DSR — none can be
populated honestly. No gate result (G4/G5 not reached; nothing was tested, so
nothing is "failed" either).

## 4. OI-history backfill needed (the only honest paths)

There is **no native HL OI-history endpoint**. `fundingHistory` omits OI;
`metaAndAssetCtxs` is snapshot-only. Options, in order of validity:

1. **requester-pays S3 `hyperliquid-archive`** — the only deep HL OI archive,
   but STOPPED (HTTP 403; this deployment has no billable AWS account — see
   US-198). Unblocking this is a credential/account decision, not a code change.
2. **Forward accumulation** — the US-199 `hl_assetctx_listener` is already
   running and appending hourly. At ~24 snapshots/day it will clear the ~200d
   gate around mid-2027. This is the honest, zero-fabrication path; HYP-16
   re-opens automatically then.
3. **Cross-venue OKX OI** — REJECTED as a proxy here. HYP-16's data gate forbids
   substituting OI, and cross-venue positioning is not "the coin's HL OI". It
   would be a different (vendor) regime, not a re-run of the registered test.

No trial was written to data/gauntlet/trials.jsonl: a data gate is a STOP before
any backtest, and a synthetic trial row (invented avg_r/pf/pbo) would itself be
a data-fabrication / G5 violation. There is no result to log.

---

## 5. Overall verdict on the coach's method (honest, not adjudicated)

The high-OI positioning thesis is **untested, not rejected**. The mechanism
(extreme OI = crowded positioning = forced-unwind exit liquidity) is coherent and
belongs to the positioning-signal class the pipeline has not yet covered — but
it is currently unverifiable because the OI history it depends on does not exist
on this deployment. The claim "OI high -> big move" remains a prior, not a fact.
It should not inform any live or paper decision until the US-190/198 backfill
question (S3 auth) or the forward-accumulation window resolves it.