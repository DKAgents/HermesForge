# Data Inventory — HermesForge feeds

Owner: researcher (ground truth: coder) · Story: US-201 (EPIC-017 Phase 1)
Date: 2026-11-02 (UTC)

Purpose: one authoritative note enumerating every data feed HermesForge ingests
(venue, endpoint, fields, granularity, depth, refresh/SLA, source label), mapped
to the hypotheses/strategies each feed unblocks — with proxies and gaps flagged
explicitly. Nothing here is synthetic; every row maps to a store/parquet on disk
or a verified live endpoint. See also `reports/gauntlet-pipeline-diagnostic-2026-11-02.md`
§2 for the pre-US-197/198/200 snapshot this note supersedes.

---

## 1. Feeds

| # | Venue | Endpoint / feed | Fields | Granularity | Depth | Refresh / SLA | Source label |
|---|---|---|---|---|---|---|---|
| 1 | Hyperliquid | `info` `candleSnapshot` → `hl_bar_store` (`bars_5m.db`, `bars_1d.db`) | OHLCV + trade count (`t,o,h,l,c,v,n`) | 5m (trading), 1d | 5m: ~17d HL-native **+ ~139d via OKX backfill**; 1d: ~4yr direct | 13:10 UTC daily (5m,1d) | `hyperliquid` / `okx_proxy` |
| 2 | Hyperliquid | `info` `fundingHistory` → `hl_funding_store` | hourly `funding_rate`, `premium` | hourly | ~400d backfill, accumulating | 13:15 UTC daily | `hyperliquid` |
| 3 | Hyperliquid | `info` `metaAndAssetCtxs` → `hl_assetctx_store` | `markPx`, `oraclePx` (real basis), `openInterest` (TOTAL only), `day_ntl_vlm`, `prev_day_px` | snapshot | forward-accumulating (no history endpoint) | hourly (`0 * * * *`) | `hyperliquid` |
| 4 | OKX (proxy) | `funding-rate`, `ticker`, `history-candles`, `liquidation` | HL↔OKX funding spread + price basis; candle history (backfill); liquidation events | hourly / 5m / event | basis ~90d; candles ~139d; liq forward | basis 30-min; liq `*/5` | `okx_proxy` |
| 5 | Deribit | `get_volatility_index_data` (DVOL) + options chain `mark_iv` | DVOL index, ATM IV term structure | hourly | ~30d (just began) — **GATED** | `15 * * * *` | `deribit` |
| 6 | Equities | Alpaca (data) + yfinance `option_chain` | OHLC parquet; ATM `impliedVol` → IV rank | 5m / daily | multi-year parquet; IV forward | daily | `alpaca` / `yfinance` |
| 7 | Polymarket | market feed | macro/political market prices | event | forward | 12:30 UTC daily | `polymarket` |
| 8 | LunarCrush | `api4/public` `coins/:id/v1`, `topic/:topic/v1`, `stocks/:sym/v1` | `galaxy_score`, `sentiment`, `trend`, `volatility`, `total_posts`, interactions, market data | daily snapshot | forward (snapshot accumulation → dated parquet) | 13:20 UTC daily (US-200) | `lunarcrush` |

Store roots (outside git): `~/.hermes/market_data/{hl_bars,hl_funding,hl_assetctx,lunarcrush}/`.

---

## 2. Hypothesis / strategy mapping (which feed unblocks what)

| Feed | Unblocks |
|---|---|
| 5m bars (#1) | HYP-02 OI-confirmed breakout · HYP-03 cascade exhaustion · HYP-04 settlement drift · HYP-06 BTC-beta reversion · HYP-07 Asia/EU session · HYP-10 new-listing drift · **STR-Q** intraday |
| 1d bars (#1) | HYP-05 cross-sectional perp momentum · **xsmom** (US-182) |
| Deep 5m via OKX proxy (#4) | any multi-month 5m backtest >17d (proxy-labeled) |
| funding (#2) | HYP-01 funding-extreme unwind · HYP-05 momentum funding filter · HYP-10 listing skew · **funding carry** (US-179/185) |
| assetctx basis/OI (#3) | HYP-01 (OI) · HYP-02 (OI) · HYP-08 oracle-mark dislocation · **funding carry** (real mark-oracle basis, US-185) |
| OKX liq proxy (#4) | HYP-03 cascade exhaustion (cross-venue only) |
| Deribit IV (#5) | HYP-09 vol compression/expansion · **short-vol / VRP** (US-181) |
| Equities (#6) | equity-side strategies (IV rank) |
| Polymarket (#7) | macro/political non-crypto edge |
| LunarCrush (#8) | social-sentiment divergence (CAND-20260814) · hHype strategy · confluence (compute_confluence) |

---

## 3. Proxies (flagged)

- **OKX-for-Hyperliquid deep 5m** (#1 via #4): the only source of 5m bars older
  than the HL ~17d floor is OKX `history-candles`, persisted labeled
  `source=okx_proxy` (US-198). Depth ≈ 139d. This is a DIFFERENT VENUE — basis
  is verified to within ~0.1% for the 32 mapped perps, but it is not HL-native
  and is always label-visible.
- **OKX-for-Hyperliquid liquidations** (#4): no HL-native feed exists; HL↔OKX
  liquidation events are a cross-venue proxy only.
- **OI-delta quadrant**: derived from total-OI changes (proxies new-money vs
  de-risking; no true long/short split).

## 4. Gaps (flagged — no data, no workaround)

- **No Hyperliquid public liquidation feed** (websocket rejects `liquidation`;
  `metaAndAssetCtxs` gives total OI only).
- **No Hyperliquid long/short OI split** — total OI only.
- **Hyperliquid S3 deep-history archive is requester-pays** (`hyperliquid-archive`
  rejects anonymous: HTTP 403) — needs a billable AWS account; this deployment
  has none, so the S3 backfill path is STOPPED (US-198) and OKX proxy is the
  fallback.
- **Binance / Bybit are 403 (permanent)** — cross-venue basis is HL↔OKX only.
- **LunarCrush free/limited tier** — only the `bitcoin` topic returns full
  sentiment metrics in limited mode; other tracked topics return NaN (US-200).

## 5. Retention / growth

- 5m store is append-only and unbounded (US-197): ~10,080 bars/day, ~0.4 GB/yr.
- Funding ~90–400d backfilled, accumulating; assetctx/IV/liq/sentiment forward.