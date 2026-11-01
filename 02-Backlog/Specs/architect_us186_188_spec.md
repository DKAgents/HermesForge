# Architect Spec — US-186 / US-187 / US-188 (Three Data-Acquisition Feeds)

Date: 2026-11-01
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, no posts, no cron, no .env touched. Awaiting sign-off.
Epic: EPIC-016
Scope: endpoint-level + response-schema + field-mapping + store-schema + cadence, for three
new persistent ingestion feeds. Concrete enough for a coder to implement without re-deriving.

Two of the three stories carry a source ASSUMPTION that does not survive live probing. These
are flagged at the top because they change the data model, not just the wiring:

  F-A  US-186 assumes a Hyperliquid websocket `liquidation` stream exists. IT DOES NOT.
       Live probe (wss://api.hyperliquid.xyz/ws) rejects `liquidation`, `liquidations`,
       `allLiquidations`, `liquidated` with "Error parsing JSON into valid websocket
       request". The `WsLiquidation` type in HL docs appears ONLY inside `WsUserEvent`
       (your OWN account's liquidation) and `WsUserNonFundingLedgerUpdates` (user ledger)
       — both user-privileged, not a public market-wide feed. See §1.3 for the correct
       free source (OKX public liquidation-orders) and a derived HL-native proxy.

  F-B  US-186 (and US-185) assume per-side OI / long-short ratio is obtainable. IT IS NOT.
       `metaAndAssetCtxs` exposes only TOTAL `openInterest` (base units) — no longOI,
       no shortOI, no long/short ratio. See §1.2 for the field map and the derived
       OI-delta quadrant proxy (already built in oi_delta.py).

All other assumptions (Deribit DVOL/IV, OKX funding/ticker/liquidations, yfinance chains)
were verified LIVE and the exact field names below are copied from real responses.

---

## 0. Ground truth read (verified — do not re-derive)

Files read in full:
- 02-Backlog/Stories/US-186, US-187, US-188
- 02-Backlog/Stories/US-177, US-185 (+ prior specs architect_us177_spec.md, architect_us185_spec.md)
- scripts/data/hl_bar_store.py, hl_funding_store.py, ingest_hl_bars.py, ingest_hl_funding.py
- scripts/data/okx_proxy.py (HL_TO_OKX map — REUSE, do not re-derive)
- scripts/gauntlet/oi_delta.py, liquidation_pressure.py
- scripts/discord/options_recommender.py (yfinance chain access — reuse its yf.Ticker pattern)
- scripts/hermes_config/universe.py (CRYPTO_UNIVERSE, 35 tickers)
- scripts/system_doctor/resolve_python.sh (Rule 1d interpreter)

LIVE API PROBES (read-only; scratch dir; no state written):

  P1. HL `POST https://api.hyperliquid.xyz/info {"type":"metaAndAssetCtxs"}` →
      `[meta, assetCtxs]`. assetCtxs[i] fields (confirmed, index-aligned with meta.universe):
        funding, openInterest, prevDayPx, dayNtlVlm, premium, oraclePx, markPx, midPx,
        impactPxs (2-el), dayBaseVlm.
      NO per-side OI. `openInterest` in BASE units; OI-USD = openInterest * markPx.

  P2. HL websocket `wss://api.hyperliquid.xyz/ws`, subscribe `{"type":"activeAssetCtx",
      "coin":"BTC"}` → `{channel:"activeAssetCtx", data:{coin, ctx:{...same fields as P1...}}}`.
      This is a LIVE streaming twin of metaAndAssetCtxs (push, no polling). Liquidation
      subscription rejected (F-A). NOTE: websockets lib present in resolved venv; no
      websocket-client (only `websockets` asyncio).

  P3. Deribit `public/get_volatility_index_data?currency=BTC&start_timestamp&end_timestamp
      &resolution=3600` → `result.data` = array of OHLC candles `[ts, open, high, low, close]`
      (DVOL, vol-index points ~40). Retains ~30d; hourly resolution=3600 is cheapest.

  P4. Deribit `public/get_instruments?currency=BTC&kind=option&expired=false` → 956 active
      instruments, each `{instrument_name:"BTC-13NOV26-83000-P", strike, expiration_timestamp,
      option_type, ...}`. `public/get_book_summary_by_currency?currency=BTC&kind=option` →
      per-instrument `{instrument_name, mark_iv, underlying_price, open_interest, volume, ...}`
      (mark_iv IS the IV surface in %). NOTE: book_summary does NOT carry `strike`/`expiration`
      (encoded in instrument_name) — join on instrument_name to get_instruments for strike/expiry.

  P5. OKX `public/funding-rate?instId=BTC-USDT-SWAP` → `{fundingRate, nextFundingRate,
      fundingTime, nextFundingTime, premium, interestRate, minFundingRate, maxFundingRate,
      settFundingRate, method:"current_period", ...}`. OKX funding is 8-HOURLY
      (fundingTime → nextFundingTime = 28800000 ms). HL funding is HOURLY — see §3.3 normalization.
      `public/funding-rate-history?instId=&limit=` → `{fundingRate, fundingTime, realizedRate}`
      (realized 8h history, paginated) — deep backfill source.

  P6. OKX `public/liquidation-orders?instType=SWAP&uly=BTC-USDT&state=filled` → `data[]` where
      each entry `{instId, uly, instType, totalLoss, details:[{side:"buy"|"sell",
      posSide:"long"|"short", sz (contracts), bkPx, ts, time}]}`. `posSide` IS the liquidated
      position side (long/short) — exactly the liq_side US-186 asks for. FREE. Requires `uly`
      or `instFamily` (not instId). Shallow rolling window (recent records only, no deep history).

  P7. OKX `market/ticker?instId=BTC-USDT-SWAP` → `{last, askPx, bidPx, open24h, high24h,
      low24h, volCcy24h, vol24h, ts, ...}`. `market/history-candles` already used by okx_proxy
      (verified working, not 403).

  P8. yfinance (v1.7.0 in resolved venv): `t.option_chain(exp_str)` → `chain.calls` /
      `chain.puts` DataFrames carrying an `impliedVolatility` column (IBKR-sourced IV per strike)
      in ADDITION to lastPrice/bid/ask — no need to re-solve Black-Scholes for IV (§2.3).
      Spot from `t.fast_info.lastPrice` / `previousClose` (already done in options_recommender).

Interpreter: cron wrappers MUST use `resolve_python.sh` (Rule 1d); resolved venv has
`requests`, `pandas`, `yfinance`, `websockets`; NO websocket-client.

Import direction (one-way, acyclic) — SHARED with the planned US-185 store:
  ingest_hl_assetctx(.py)      -> hl_assetctx_store(.py) + hermes_config.universe
  ingest_okx_liq(.py)          -> hl_positioning_store(.py)         [standalone, okx only]
  ingest_deribit_iv(.py)       -> iv_store(.py)                      [standalone, deribit only]
  ingest_equity_iv(.py)        -> iv_store(.py) + hermes_config.universe(equity)
  ingest_crossvenue_basis(.py) -> basis_store(.py) + okx_proxy.HL_TO_OKX + hl_funding_store
                                  + hl_assetctx_store
  funding_carry.py             -> hl_funding_store + hl_assetctx_store + basis_store (+fee,g3)

---

# PART 1 — US-186: Liquidation + OI Positioning Feed

## 1.1 Open interest + positioning (source: HL metaAndAssetCtxs — REUSE the planned store)

The OI/positioning half is EXACTLY the metaAndAssetCtxs snapshot already designed under
US-185 §2.3 (`hl_assetctx_store.py`, store dir `~/.hermes/market_data/hl_assetctx/`).
DO NOT create a parallel store. EXTEND hl_assetctx_store's `asset_ctx` table with the
three additional fields this story adds, so ONE snapshot ingestion serves both US-185
(basis) and US-186 (positioning). This is the single most important reuse in the design.

Field mapping (assetCtxs → stored columns), exact names:

  assetCtxs.openInterest  -> open_interest   REAL   (BASE units; OI-USD derived at read)
  assetCtxs.dayNtlVlm     -> day_ntl_vlm     REAL   (USD notional volume, trailing 24h)
  assetCtxs.dayBaseVlm    -> day_base_vlm    REAL   (base-asset volume, trailing 24h)
  assetCtxs.prevDayPx     -> prev_day_px     REAL
  assetCtxs.funding       -> funding         REAL   (current hourly, decimal)
  assetCtxs.premium       -> premium         REAL   (impact-price premium, provenance only)
  assetCtxs.markPx        -> mark_px         REAL
  assetCtxs.oraclePx      -> oracle_px       REAL

## 1.2 Long/short ratio — NOT AVAILABLE (flag F-B) + derived proxy

HL exposes no per-side OI. `long_oi` / `short_oi` / `long_short_ratio` columns must be
stored as NULL (explicit absence), NOT synthesized. The accepted proxy is the OI-DELTA
quadrant, already implemented in `gauntlet/oi_delta.py`:

  classify_oi_delta(price_change_pct, oi_change_pct) -> NEW_LONGS | SHORT_COVERING
      | NEW_SHORTS | LONG_LIQUIDATION | neutral

This is DERIVED at read time from the accumulated OI + markPx series (oi_change_pct from
consecutive snapshots, price_change_pct from markPx), not stored. The store's job is only
to accumulate the markPx + openInterest series that makes the derivation valid going forward.

Consequence for funding_carry (US-185 consumer): OI conditioning becomes
"ΔOI vs Δprice quadrant + OI level + dayNtlVlm participation", NOT a long/short ratio.

## 1.3 Liquidation events / levels — correct source (F-A)

Hyperliquid has NO public liquidation history endpoint and NO public liquidation websocket.
The three honest options, in order:

  (1) HL-NATIVE DERIVED (no new source, no events):
      Cascade detection already exists in gauntlet/liquidation_pressure.py
      (`detect_cascade`: outsized wick + cumulative OI drop > -3% + funding snap toward
      zero → long_squeeze/short_squeeze; `estimate_liquidation_clusters` needs a
      feeds of {price,size,side} liq dicts that WE DON'T HAVE natively). This path only
      produces "liquidation pressure" flags, not counts/sizes. Keep as the no-new-source floor.

  (2) OKX PUBLIC LIQUIDATION FEED (FREE, recommended for actual events) — P6:
      GET https://www.okx.com/api/v5/public/liquidation-orders?instType=SWAP&uly=<ULY>&state=filled
      uly = the OKX underlying (e.g. "BTC-USDT"), derived from okx_proxy.HL_TO_OKX[coin]
      by stripping the "-SWAP" suffix (instId "BTC-USDT-SWAP" → uly "BTC-USDT").
      Response per entry:
        instId, uly, instType, totalLoss,
        details:[{ side:"buy"|"sell",       // closing-order side (buy = short liq)
                   posSide:"long"|"short",  // LIQUIDATED position side  <-- liq_side
                   sz:<contracts>,          // size in contracts (NOT base units)
                   bkPx:<bankruptcy px>,
                   ts:<ms epoch> }]
      Mapping to US-186 schema:
        liq_side   = details.posSide  ("long"|"short")
        liq_size   = details.sz       (contracts; convert to USD = sz * ctVal * px, where
                                       ctVal is per-instrument contract multiplier — obtain
                                       from GET /api/v5/public/instruments?instType=SWAP
                                       `ctVal`, cached once; do NOT hardcode)
        liq_price  = details.bkPx
        liq_ts     = details.ts
      LIMITATION (must ride the data): this is a CROSS-VENUE (OKX) feed with a SHALLOW
      rolling window (most-recent records only, no deep history). It measures OKX leverage
      flush, not HL. It is the best free structured liquidation source, but is NOT a
      substitute for HL-native events (which do not exist publicly).

  (3) PAID third party (flagged, NOT in scope): Coinglass liquidation API is the canonical
      multi-venue liquidation feed but is a paid subscription. Out of scope now; the schema
      below is forward-compatible if a paid source is later approved.

## 1.4 Store schema (new `hl_positioning_store.py` — liquidation events only)

OI/positioning lives in hl_assetctx_store (extended, §1.1). The ONLY new table/DB for
US-186 is liquidation events:

Module: scripts/data/hl_positioning_store.py (stdlib sqlite3 + pathlib; pandas read)
  STORE_DIR = ~/.hermes/market_data/hl_positioning/
  DB_NAME   = "liquidations.db"

  CREATE TABLE IF NOT EXISTS liq_events (
      inst_id   TEXT    NOT NULL,   -- OKX instId e.g. 'BTC-USDT-SWAP'
      ts        INTEGER NOT NULL,   -- details.ts, ms epoch
      pos_side  TEXT    NOT NULL,   -- 'long' | 'short'   (liquidated side)
      side      TEXT    NOT NULL,   -- 'buy' | 'sell'      (closing order side)
      sz        REAL    NOT NULL,   -- contracts
      sz_usd    REAL,               -- sz * ctVal * px (derived at ingest)
      bk_px     REAL,               -- bankruptcy price
      PRIMARY KEY (inst_id, ts, pos_side, side, sz)
  ) WITHOUT ROWID;
  CREATE INDEX IF NOT EXISTS idx_liq_inst_ts ON liq_events (inst_id, ts);
  CREATE TABLE IF NOT EXISTS ingest_state (inst_id TEXT PRIMARY KEY,
      last_poll_ts INTEGER NOT NULL, last_run TEXT NOT NULL);

  DEDUP: OKX details rows carry no unique order id. Composite PK (inst_id, ts, pos_side,
  side, sz) is the best-effort key; a same-ms same-size same-side duplicate is
  astronomically unlikely but possible — accept the residual (flag F-C). `INSERT OR IGNORE`
  gives idempotent append exactly like the existing stores.

Function surface (mirror hl_funding_store idioms): open_store(), append_liqs(), upsert_state(),
last_poll_ts(), read_liqs(inst_id, start, end) -> DataFrame, coverage().

## 1.5 Ingestion + cadence

  OI/positioning: shared `ingest_hl_assetctx.py` (US-185 §2.3) — hourly cron, no_agent,
  resolve_python.sh, POST metaAndAssetCtxs once per hour returns all 235 coins, append
  snapshot, upsert state. NO change to cadence because US-186 extends the same snapshot.

  Liquidations: new `ingest_okx_liq.py`. REST-only, SHALLOW rolling window ⇒ hourly polling
  would silently MISS most events. Two supported cadences (both idempotent):

    (a) [recommended default] 5-min no_agent cron poll of
        public/liquidation-orders (per uly, over the okx_proxy.HL_TO_OKX universe).
        Captures the majority of events; accepted that intra-window gaps are possible and
        the feed is inherently "recent-window" not exhaustive. Cron expr "*/5 * * * *".

    (b) [only if exhaustiveness is required] a long-running OKX websocket listener
        (channel "liquidation-orders") writing the same SQLite. This DEVIATES from the
        no_agent-cron pattern (needs a persistent process) and requires SIGN-OFF (F-D).
        Not recommended until US-186's consumer actually needs per-event completeness.

  Universe for (a): iterate okx_proxy.HL_TO_OKX values (skip None → PAXG/kBONK/kPEPE/kSHIB
  have no OKX twin; they get no liquidation feed — honest gap, same policy as okx_proxy).

  CT-VAL: fetch once per session (GET /api/v5/public/instruments?instType=SWAP, read ctVal
  per instId) with a filesystem cache (~/.hermes/market_data/okx_ctval.json, TTL 24h),
  then sz_usd = sz * ctVal * bkPx at ingest. Failure to resolve ctVal ⇒ store sz_usd = NULL
  (do NOT fabricate a contract multiplier).

---

# PART 2 — US-187: Options IV Surface

Two disjoint sub-feeds (crypto via Deribit, equities via yfinance), one store.

## 2.1 Crypto — Deribit DVOL (vol-index level; timing gate for US-181)

Endpoint: GET https://www.deribit.com/api/v2/public/get_volatility_index_data
  params: currency=BTC|ETH, resolution=3600 (hourly) or 60 (minutely),
          start_timestamp, end_timestamp (ms epoch).
Response: result.data = [ [ts, open, high, low, close], ... ]  (DVOL index OHLC, unit = %).
  DVOL ~40 today (P3). `currency=BTC` → DVOL; `currency=ETH` → ETH DVOL.

Cadence: hourly cron appends the latest DVOL candle(s) into `dvol_index`. resolution=3600
is cheapest and sufficient for a vol-of-vol level gate; drop to resolution=60 only if US-181
later wants intraday vol-of-vol. Idempotent via (currency, ts) PK. Deep backfill ~30d on
first run (Deribit bounds the reach).

## 2.2 Crypto — ATM IV term structure (Deribit option chain)

Two calls, joined on instrument_name:

  (A) GET public/get_instruments?currency=BTC&kind=option&expired=false
      → per instrument: instrument_name, strike, expiration_timestamp, option_type, is_active.
      Use to build expiry × strike grid.

  (B) GET public/get_book_summary_by_currency?currency=BTC&kind=option
      → per instrument: instrument_name, mark_iv (%), underlying_price, open_interest, volume.

ATM IV per expiry: for each expiry, pick the strike nearest underlying_price, average the
call+put mark_iv at that strike (Deribit BTC/ETH options are "reversed" (coin-settled) but
mark_iv is directly quoted — no BS solve needed). Store one row per (currency, expiry):

  atm_iv   = 0.5*(call.mark_iv + put.mark_iv) at the ATM strike
  dte      = (expiration_timestamp - now_ms)/(86400000)
  spot     = underlying_price (from book_summary)

Term structure = the set of (dte, atm_iv) rows across expiries at one snapshot time.

## 2.3 Equities — yfinance ATM IV + IV rank

Source (already proven in options_recommender.py:370-405):
  t = yf.Ticker(ticker); expirations = t.options; chain = t.option_chain(exp_str);
  spot = t.fast_info.lastPrice or previousClose
  chain.calls / chain.puts carry `impliedVolatility` per strike (IBKR-sourced) — READ IT,
  do not re-solve Black-Scholes (options_recommender solves IV because it needs GREEKS;
  US-187 only needs the IV level, which yfinance already returns).

Per ticker per snapshot:
  pick nearest expiry to a fixed target DTE (reuse options_recommender._compute_optimal_dte
  default ~35d, or a fixed 30d target — flag F-E), take ATM strike (nearest underlying),
  atm_iv = average(call.impliedVolatility, put.impliedVolatility).

IV RANK: computed at READ time from the accumulated atm_iv series, not stored as a row:
  iv_rank = (atm_iv_now - min_252d) / (max_252d - min_252d), rolling 252 snapshots.
Store the raw atm_iv daily so the rank is computable retroactively. Optionally materialize
iv_rank at read for the consumer.

Equity universe: the traded stock universe (hermes_config.universe — reuse; do NOT re-list).
yfinance is rate-limited and occasionally flaky ⇒ idempotent append + skip-on-empty (never
fabricate), consistent with the existing fetch_short_interest/fetch_intermarket pattern.

## 2.4 Store schema (new `iv_store.py`)

Module: scripts/data/iv_store.py (stdlib sqlite3 + pathlib; pandas read)
  STORE_DIR = ~/.hermes/market_data/iv_surface/
  DB_NAME   = "iv_surface.db"

  CREATE TABLE IF NOT EXISTS dvol_index (
      currency  TEXT    NOT NULL,   -- 'BTC' | 'ETH'
      ts        INTEGER NOT NULL,   -- Deribit candle ts, ms
      open      REAL, high REAL, low REAL, close REAL,
      PRIMARY KEY (currency, ts)
  ) WITHOUT ROWID;

  CREATE TABLE IF NOT EXISTS crypto_atm_iv (
      currency  TEXT    NOT NULL,   -- 'BTC' | 'ETH'
      ts        INTEGER NOT NULL,   -- snapshot time, ms
      expiry    INTEGER NOT NULL,   -- expiration_timestamp ms
      dte       REAL    NOT NULL,
      atm_iv    REAL    NOT NULL,   -- % (e.g. 38.0)
      spot      REAL,
      PRIMARY KEY (currency, expiry, ts)
  ) WITHOUT ROWID;
  CREATE INDEX IF NOT EXISTS idx_crypto_atm_iv_ts ON crypto_atm_iv (currency, ts);

  CREATE TABLE IF NOT EXISTS equity_atm_iv (
      ticker    TEXT    NOT NULL,
      ts        INTEGER NOT NULL,   -- snapshot time, ms
      atm_iv    REAL    NOT NULL,   -- % ;  NULL permitted if chain empty (don't fabricate)
      spot      REAL,
      expiry    TEXT,               -- chosen expiry date string (provenance)
      PRIMARY KEY (ticker, ts)
  ) WITHOUT ROWID;
  CREATE INDEX IF NOT EXISTS idx_equity_atm_iv_ts ON equity_atm_iv (ticker, ts);

  ingest_state tables per sub-feed (currency / ticker keys), as in prior stores.

Function surface (per sub-feed, mirroring hl_funding_store): open_store(), append_*(),
upsert_state(), last_ts(), read_*() -> DataFrame, coverage().

## 2.5 Ingestion jobs + cadence

  ingest_deribit_iv.py  — hourly cron (no_agent, resolve_python.sh): fetch DVOL + rebuild
      ATM IV term structure (A+B above) for BTC and ETH, append dvol_index + crypto_atm_iv.
      Both are cheap GETs; ~3-4 requests/hour total. First run backfills DVOL ~30d.
  ingest_equity_iv.py   — daily cron (no_agent, resolve_python.sh): hourly/daily ATM IV per
      equity ticker. Daily is sufficient for IV rank (252-snapshot window = 1y of daily rows);
      yfinance's rate limits make hourly equity polling fragile for marginal benefit.

Both idempotent (PK dedup), skip on empty, exit non-zero only on hard failure (network down
across retries), matching the existing ingest scripts.

---

# PART 3 — US-188: Cross-Venue Basis Feed (HL vs OKX)

Standing limitation first: Binance/Bybit are 403 (per standing note) — DO NOT re-attempt.
This feed is HL-vs-OKX only. A third venue is explicitly out of scope.

## 3.1 OKX funding (source + schema) — P5

  Current-period rate:
    GET https://www.okx.com/api/v5/public/funding-rate?instId=<INST>   (one per instId)
    → fundingRate (current period, 8h), nextFundingRate, fundingTime, nextFundingTime,
      premium, interestRate, minFundingRate, maxFundingRate, settFundingRate, method.

  Realized history (backfill):
    GET https://www.okx.com/api/v5/public/funding-rate-history?instId=<INST>&before=&after=&limit=100
    → fundingRate, fundingTime (ms, 8h boundary), realizedRate. Paginate backward via before.

  NOTE: OKX funding cadence is 8-HOURLY; HL funding is HOURLY. Both stored raw, normalized
  only in the join (§3.3).

## 3.2 OKX price (source + schema) — P7

  Spot/mark proxy:
    GET https://www.okx.com/api/v5/market/ticker?instId=<INST>
    → last, askPx, bidPx, open24h, high24h, low24h, volCcy24h, vol24h, ts, sodUtc0, sodUtc8.

  `last` is the trade price; `askPx`/`bidPx` give execution realism. For basis we store
  `last` and, where useful, `bidPx`/`askPx` for the spread.

## 3.3 HL side + join computation

HL funding: from hl_funding_store (hourly fundingHistory, already deep).
HL price/mark: from hl_assetctx_store markPx/oraclePx snapshots (US-185 §2.3 / §1.1).

Join (per coin, per snapshot time ts):

  funding_spread_apr = annualize_hl - annualize_okx
      annualize_hl  = HL_hourly_rate * 8760                     (per-hour → per-year)
      annualize_okx = OKX_8h_rate * (365*3)                     (per-8h  → per-year)
      store both the raw rates AND the APR spread (in percent, not bps — flag unit).

  price_basis_bps = (hl_mark - okx_last) / okx_last * 1e4       (signed bps)

  funding_spread_per_period (optional, for the 8h trader) = HL hourly rate * 8 - OKX 8h rate.

Symbol mapping: reuse okx_proxy.HL_TO_OKX (32/35 mapped; PAXG + kilo coins → None, skip with
labeled gap). uly for liquidity (US-186) and instId for funding/ticker both derive from it.

## 3.4 Store schema (new `basis_store.py`)

Module: scripts/data/basis_store.py (stdlib sqlite3 + pathlib; pandas read)
  STORE_DIR = ~/.hermes/market_data/cross_venue_basis/
  DB_NAME   = "basis.db"

  -- RAW OKX funding (8h realized history, deep backfill)
  CREATE TABLE IF NOT EXISTS okx_funding (
      inst_id        TEXT    NOT NULL,   -- 'BTC-USDT-SWAP'
      ts             INTEGER NOT NULL,   -- fundingTime ms (8h boundary)
      funding_rate   REAL    NOT NULL,   -- realizedRate (8h decimal)
      premium        REAL,               -- current premium (funding-rate endpoint only)
      PRIMARY KEY (inst_id, ts)
  ) WITHOUT ROWID;

  -- OKX price snapshots (for the price basis leg)
  CREATE TABLE IF NOT EXISTS okx_ticker (
      inst_id  TEXT    NOT NULL,
      ts       INTEGER NOT NULL,   -- snapshot time ms
      last     REAL, bid REAL, ask REAL,
      PRIMARY KEY (inst_id, ts)
  ) WITHOUT ROWID;

  -- COMPUTED cross-venue join (the deliverable metric, per coin per snapshot)
  CREATE TABLE IF NOT EXISTS cross_venue_basis (
      coin               TEXT    NOT NULL,   -- HL canonical coin ('BTC')
      ts                 INTEGER NOT NULL,   -- snapshot time ms (hourly)
      hl_funding_apr     REAL,               -- annualized HL hourly rate (percent)
      okx_funding_apr    REAL,               -- annualized OKX 8h rate (percent)
      funding_spread_apr REAL,               -- hl - okx (percent)
      hl_mark            REAL,
      okx_last           REAL,
      price_basis_bps    REAL,               -- (hl_mark - okx_last)/okx_last * 1e4
      PRIMARY KEY (coin, ts)
  ) WITHOUT ROWID;
  CREATE INDEX IF NOT EXISTS idx_cvb_coin_ts ON cross_venue_basis (coin, ts);

  ingest_state (per coin).

Function surface (mirror existing): open_store(), append_okx_funding(), append_okx_ticker(),
append_basis(), upsert_state(), last_ts(), read_okx_funding(), read_ticker(), read_basis().

## 3.5 Ingestion job + cadence

  New ingest_crossvenue_basis.py, hourly cron (no_agent, resolve_python.sh):
    1. For each mapped coin (okx_proxy.HL_TO_OKX): fetch OKX funding-rate (current 8h) +
       funding-rate-history (backfill realized 8h, paginate backward the first run) ->
       okx_funding. Fetch OKX market/ticker -> okx_ticker.
    2. Read HL funding (hl_funding_store latest hourly) + HL markPx (hl_assetctx_store
       latest snapshot), compute the join, append cross_venue_basis.
    3. Realized OKX funding-rate-history backfill goes ~last 90d (free, paginated) on first
       run; after that hourly appends the 3 daily 8h settlements.

  Cadence: hourly for the price basis + spread (matches HL's hourly funding). The OKX 8h
  funding only changes 3x/day but the HL leg changes hourly, so the spread snapshot is
  meaningful hourly. This store feeds funding_carry (US-185) as the "real carry metric".

---

## 5. Cross-cutting: resolved ambiguities, flags, implementation order

### 5.1 Ambiguities RESOLVED (with default)
  A1  HL liquidation source -> does not exist publicly; OKX public/liquidation-orders is the
      free structured event feed; HL-native = derived cascade flags (§1.3).
  A2  Long/short ratio -> not available; store NULLs; OI-delta quadrant is the proxy (§1.2).
  A3  OI/positioning store -> EXTEND hl_assetctx_store (shared with US-185), not a new store
      (§1.1).
  A4  IV source currency vs equity -> Deribit (crypto) + yfinance impliedVolatility column
      (equity); no Black-Scholes solve needed (§2).
  A5  IV rank window -> 252 snapshots (1y daily); derived at read, raw atm_iv stored (§2.3).
  A6  Funding spread units/normalization -> HL hourly vs OKX 8h, both annualized; spread in
      APR percent (§3.3).

### 5.2 Flags (need decision / sign-off)
  F-A  No HL public liquidation feed (verified). Accept OKX cross-venue events + derived
      proxy, or fund Coinglass later.
  F-B  No long/short OI ratio on HL. Confirm OI-delta quadrant proxy is acceptable.
  F-C  OKX liq_details have no unique id; dedup key is heuristic (inst_id, ts, pos_side,
      side, sz). Residual duplicate risk accepted.
  F-D  Websocket liquidation listener (exhaustive) needs a persistent process + sign-off;
      default is 5-min REST polling (may miss intra-window events).
  F-E  Equity ATM IV target DTE: default ~30d (or reuse options_recommender DTE); needs a
      one-line confirmation.
  F-F  Binance/Bybit 403 (standing) — third venue out of scope; not re-attempted.

### 5.3 Implementation order (each a path-scoped green commit, py_compile clean)
  1. hl_assetctx_store.py (US-185 §2.3) EXTENDED with day_ntl_vlm/day_base_vlm/prev_day_px
     + unit test (append same (coin,time) twice -> 2nd inserts 0, golden read).
  2. ingest_hl_assetctx.py + wrapper + hourly cron (shared US-185/US-186 OI+positioning).
  3. hl_positioning_store.py + ingest_okx_liq.py + ctval resolver + wrapper + 5-min cron.
  4. iv_store.py + ingest_deribit_iv.py (+ BTC/ETH) + hourly cron.
  5. iv_store equity path + ingest_equity_iv.py + daily cron.
  6. basis_store.py + ingest_crossvenue_basis.py + hourly cron.
  7. Wire consumers: funding_carry reads basis_store (cross-venue spread) + hl_assetctx
     (OI conditioning); US-181 reads dvol_index/crypto_atm_iv for the vol-of-vol gate.

No edits to publisher / embed / posting / trades.csv / universe.py content in any commit.
universe.py is READ (imported), not written.

END OF DESIGN.