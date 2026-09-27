# DESIGN — US-119: Liquidation Listener, Webhook Integration, and MCP Server

**Architect:** HermesForge Architect Agent (T2, glm-5.2)
**Date:** 2026-08-18
**Status:** DESIGN ONLY (no implementation)
**Ticket:** US-119

---

## 0. Problem Summary

HermesForge currently lacks real-time market event detection for crypto. We have the data fetchers
(fetch_hyperliquid_metrics.py, liquidity_heatmap.py) and the Discord posting infrastructure
(embed_publisher.py, webhook_utils.py, alert_publisher.py), but nothing connects them in a
live, event-driven pipeline. The three systems designed here form a closed loop:

1. A daemon that polls Hyperliquid + OKX and detects liquidation cascades, funding extremes, and OI spikes.
2. A Hermes webhook subscription that receives those events, runs an agent analysis, and posts alerts.
3. An MCP server that exposes HermesForge trading data as tools the agent can call during analysis.

Prerequisites identified during codebase audit:
- Hermes gateway is running (active since 2026-07-29) with Discord + Telegram enabled.
- Webhook platform is NOT yet enabled — must add `platforms.webhook.enabled: true` to config.yaml.
- `mcp` Python SDK v2.0.0 is installed in the Hermes venv (`/usr/local/lib/hermes-agent/venv/`).
- DISCORD_CRYPTO_CHANNEL_ID=1528555885310513213 is set in .env (matches the requested channel).
- Hyperliquid API works from this VPS; OKX works; Binance/Bybit are geo-blocked (per memory notes).

---

## 1. Architecture Diagram (ASCII)

```
                        EXTERNAL APIS
                        ============
                   Hyperliquid (free)          OKX (free)
                   /api/hyperliquid.xyz/info   www.okx.com/api/v5
                        |                          |
                        v                          v
                  +-----------------------------------+
                  |     liq_listener.py (daemon)      |
                  |     (systemd service, 12s poll)    |
                  |                                   |
                  |  CascadeDetector                  |
                  |    3+ liqs / 60s / same coin+dir  |
                  |  FundingExtremeDetector           |
                  |    top/bottom 5% of 30d range     |
                  |  OISpikeDetector                  |
                  |    >5% change in 1 hour            |
                  |                                   |
                  |  On event: POST to webhook URL    |
                  +-----------------------------------+
                        |
                        | HTTP POST (JSON payload)
                        v
                  +-----------------------------------+
                  |  Hermes Gateway (port 8644)        |
                  |  webhook route: /webhooks/liq     |
                  |  (HMAC-signed, auto-generated)    |
                  +-----------------------------------+
                        |
                        | triggers agent run
                        v
                  +-----------------------------------+
                  |  Hermes Agent (self-contained)     |
                  |  Prompt: analyze event, check     |
                  |  trades.csv exposure, call MCP     |
                  |  tools, post to Discord if high   |
                  |  severity, log to JSONL            |
                  |                                   |
                  |  MCP tools available:              |
                  |    fetch_oi(coin)                 |
                  |    fetch_funding_rate(coin)        |
                  |    fetch_liquidations(coin,limit)  |
                  |    fetch_orderbook(coin, depth)    |
                  |    fetch_regime()                 |
                  |    get_open_trades()              |
                  +-----------------------------------+
                        |                    |
          +-------------+                    +-------------+
          |                                            |
          v                                            v
  +---------------+                        +-----------------+
  | Discord Bot   |                        | JSONL log file  |
  | #crypto-setups|                        | ~/.hermes/      |
  | (high sev)    |                        | liquidation_    |
  +---------------+                        | events.jsonl    |
                                           +-----------------+
                        ^
                        |
                  +-----------------------------------+
                  |  hermesforge_mcp_server.py         |
                  |  (stdio MCP server, subprocess)   |
                  |                                   |
                  |  Wraps existing fetchers:         |
                  |   - fetch_hyperliquid_metrics.py  |
                  |   - liquidity_heatmap.py           |
                  |   - regime_filter.py              |
                  |   - trades.csv reader              |
                  +-----------------------------------+
                        |
                        | stdio JSON-RPC
                        v
                  +-----------------------------------+
                  |  Hermes MCP client                |
                  |  (hermes mcp add hermesforge ...)  |
                  +-----------------------------------+
```

---

## 2. System 1: Liquidation Listener + Webhook Trigger

### 2.1 File Location

`~/HermesForge/scripts/listeners/liq_listener.py`

### 2.2 Data Sources

| Source | Endpoint | Data | Rate Limit | Status from VPS |
|--------|----------|------|------------|-----------------|
| Hyperliquid | POST /info `{"type":"l2Book"}` | L2 orderbook (20 levels) | None documented | Works |
| Hyperliquid | POST /info `{"type":"metaAndAssetCtxs"}` | OI, funding, mark price | None documented | Works |
| Hyperliquid | POST /info `{"type":"fundingHistory"}` | Funding rate history | None documented | Works |
| OKX | GET /api/v5/public/liquidation-orders | Liquidation orders | 20 req/2s per IP | Works |
| OKX | GET /api/v5/public/open-interest | OI in USD | 20 req/2s per IP | Works |
| OKX | GET /api/v5/public/funding-rate | Current funding rate | 20 req/2s per IP | Works |

Note: Hyperliquid does not expose a liquidation feed directly. Liquidations are observable
as rapid OI drops + large trades. For OKX, the liquidation-orders endpoint provides explicit
liq data. The listener combines both: OKX for explicit liquidations, Hyperliquid for OI/funding.

### 2.3 Detection Logic

#### 2.3.1 Cascade Detector

```
WINDOW = 60 seconds
MIN_LIQUIDATIONS = 3

Maintain a rolling deque per (coin, direction):
  key = (coin, side)  where side = "long" | "short"
  entries = deque of (timestamp, size_usd) within last 60s

On each poll cycle:
  for each new liquidation from OKX:
    key = (coin, side)
    append (now, size_usd) to deque[key]
    prune entries older than 60s
    if len(deque[key]) >= MIN_LIQUIDATIONS:
      total_size = sum(entry.size for entry in deque[key])
      severity = "high" if total_size > 1_000_000 else "medium"
      fire_webhook({
        event_type: "cascade",
        coin: coin,
        direction: side,
        count: len(deque[key]),
        size_usd: total_size,
        timestamp: now_iso,
        severity: severity,
        source: "okx"
      })
      clear deque[key]  # prevent re-fire for same cascade
```

#### 2.3.2 Funding Extreme Detector

```
ROLLING_WINDOW_DAYS = 30
EXTREME_PERCENTILE = 5  # top 5% or bottom 5%

Maintain a 30-day rolling funding history per coin (persisted to disk):
  ~/.hermes/market_data/liquidation_listener/funding_history_{coin}.json

On each poll cycle (or every 5th cycle to reduce load):
  for each coin in UNIVERSE:
    current_rate = fetch current funding (Hyperliquid metaAndAssetCtxs)
    append (now, current_rate) to rolling history
    prune entries older than 30 days
    if len(history) < 100: skip (insufficient data)

    rates = [entry.rate for entry in history]
    p95 = percentile(rates, 95)
    p5 = percentile(rates, 5)

    if current_rate >= p95:
      severity = "high" if current_rate >= p99 else "medium"
      fire_webhook({
        event_type: "funding_extreme",
        coin: coin,
        direction: "positive",  # crowded long
        rate: current_rate,
        percentile: 95 or 99,
        rolling_window_days: 30,
        timestamp: now_iso,
        severity: severity,
        source: "hyperliquid"
      })
    elif current_rate <= p5:
      severity = "high" if current_rate <= p1 else "medium"
      fire_webhook({
        event_type: "funding_extreme",
        coin: coin,
        direction: "negative",  # crowded short
        rate: current_rate,
        percentile: 5 or 1,
        rolling_window_days: 30,
        timestamp: now_iso,
        severity: severity,
        source: "hyperliquid"
      })
```

#### 2.3.3 OI Spike Detector

```
SNAPSHOT_INTERVAL = 3600 seconds (1 hour)
THRESHOLD_PCT = 5.0

Maintain hourly OI snapshots per coin:
  ~/.hermes/market_data/liquidation_listener/oi_snapshots_{coin}.json
  Format: [{timestamp, oi_usd}]

On each poll cycle:
  current_oi = fetch OI (Hyperliquid metaAndAssetCtxs or OKX)
  for each coin:
    last_snapshot = most recent snapshot >1h old
    if last_snapshot exists:
      pct_change = (current_oi - last_snapshot.oi_usd) / last_snapshot.oi_usd * 100
      if abs(pct_change) >= THRESHOLD_PCT:
        direction = "up" if pct_change > 0 else "down"
        severity = "high" if abs(pct_change) >= 10 else "medium"
        fire_webhook({
          event_type: "oi_spike",
          coin: coin,
          direction: direction,
          pct_change: pct_change,
          current_oi: current_oi,
          previous_oi: last_snapshot.oi_usd,
          timestamp: now_iso,
          severity: severity,
          source: "hyperliquid"
        })

  # Save hourly snapshot (only one per hour per coin)
  if no snapshot exists for this coin in the last hour:
    append (now, current_oi) to snapshots
```

### 2.4 Webhook Payload Contract

All events share a common envelope:

```json
{
  "event_type": "cascade|funding_extreme|oi_spike",
  "coin": "BTC",
  "direction": "long|short|up|down|positive|negative",
  "size_usd": 1234567.89,
  "timestamp": "2026-08-18T14:30:00Z",
  "severity": "high|medium|low",
  "source": "hyperliquid|okx",
  "details": {
    // event-specific fields
  }
}
```

Event-specific `details`:

```json
// cascade
"details": {"count": 4, "window_seconds": 60}

// funding_extreme
"details": {"rate": 0.0008, "percentile": 99, "rolling_window_days": 30}

// oi_spike
"details": {"pct_change": 7.2, "current_oi": 1234567890, "previous_oi": 1151789450}
```

### 2.5 Resilience Design

The daemon must never crash. Every external call is wrapped in try/except with backoff:

```
Backoff strategy (per source):
  - Connection error: wait 5s, retry up to 3 times, then skip cycle
  - HTTP 429 (rate limit): wait 60s, then resume
  - HTTP 5xx: wait 10s, retry 2 times, then skip cycle
  - JSON parse error: log, skip cycle, continue
  - Any unexpected exception: log full traceback, continue (never crash)

Reconnect:
  - requests.Session with HTTPAdapter(max_retries=3) and urllib3 Retry
  - Session is recreated if a persistent connection error occurs

Logging:
  - RotatingFileHandler at ~/.hermes/logs/liq_listener.log
  - Max 10MB per file, 5 rotations
  - Log level INFO for normal operation, DEBUG for troubleshooting
  - Each poll cycle logs: timestamp, coins checked, events detected (if any)

State persistence:
  - Rolling deques for cascade detection are in-memory (rebuilt on restart)
  - Funding history is persisted to JSON (survives restart)
  - OI snapshots are persisted to JSON (survives restart)
  - On restart, in-memory deques are empty — cascades may be missed for
    the first 60 seconds after restart. This is acceptable.
```

### 2.6 Systemd Service

File: `/etc/systemd/system/hermesforge-liq-listener.service`

```ini
[Unit]
Description=HermesForge Liquidation Listener — crypto event detection daemon
After=network-online.target hermes-gateway.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/HermesForge
ExecStart=/usr/local/lib/hermes-agent/venv/bin/python3 /root/HermesForge/scripts/listeners/liq_listener.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=WEBHOOK_URL=http://localhost:8644/webhooks/liq
Environment=WEBHOOK_SECRET=${WEBHOOK_SECRET}

# Resource limits
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

The `Restart=always` + `RestartSec=10` ensures the daemon comes back within 10s
of any crash. `MemoryMax=512M` prevents a memory leak from OOMing the host.
`CPUQuota=50%` prevents a tight loop from starving the gateway.

### 2.7 Config

The listener reads from environment variables (all have safe defaults):

```
POLL_INTERVAL=12          # seconds between poll cycles
UNIVERSE=BTC,ETH,SOL,...  # comma-separated coin list
WEBHOOK_URL=http://localhost:8644/webhooks/liq
WEBHOOK_SECRET=auto       # HMAC secret for signing POST
CASCADE_WINDOW=60        # seconds
CASCADE_MIN=3            # min liquidations for cascade
FUNDING_WINDOW_DAYS=30   # rolling window for funding extremes
FUNDING_PERCENTILE=5     # top/bottom percentile
OI_THRESHOLD_PCT=5.0     # OI change threshold
LOG_DIR=~/.hermes/logs
STATE_DIR=~/.hermes/market_data/liquidation_listener
```

---

## 3. System 2: Hermes Webhook Integration

### 3.1 Prerequisite: Enable Webhook Platform

Before subscribing, the webhook platform must be enabled in Hermes config:

```yaml
# Add to ~/.hermes/config.yaml under platforms:
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "${WEBHOOK_SECRET}"
```

Then restart the gateway: `hermes gateway restart --system`

### 3.2 Webhook Subscription Command

```bash
hermes webhook subscribe liq \
  --prompt "$(cat ~/HermesForge/scripts/webhooks/liq_prompt.txt)" \
  --events "cascade,funding_extreme,oi_spike" \
  --description "Crypto liquidation cascade / funding extreme / OI spike event handler" \
  --deliver discord \
  --deliver-chat-id 1528555885310513213 \
  --skills crypto-market-data
```

Key flags:
- `--prompt`: Self-contained agent prompt (see 3.4) with {dot.notation} payload refs.
- `--events`: The event types the webhook accepts (filter on incoming POST body).
- `--deliver discord --deliver-chat-id 1528555885310513213`: The agent output is
  delivered to Discord #crypto-setups when the agent generates a response.
- `--skills crypto-market-data`: Loads the existing skill with Hyperliquid/OKX API refs.
- `--secret`: Auto-generated HMAC secret (matches what the listener uses).

### 3.3 Webhook Payload Flow

```
liq_listener.py
  -> POST http://localhost:8644/webhooks/liq
     Headers: X-Hermes-Signature: sha256=...
     Body: {"event_type": "cascade", "coin": "BTC", ...}

Hermes Gateway
  -> Verify HMAC signature
  -> Parse event_type, match against --events filter
  -> Render prompt template with {event_type}, {coin}, {direction}, etc.
  -> Launch agent with rendered prompt + loaded skills + MCP tools
  -> Agent runs: analyze event, call MCP tools, decide severity, output message
  -> Agent output delivered to Discord #crypto-setups (if agent produces output)
```

### 3.4 Self-Contained Agent Prompt

File: `~/HermesForge/scripts/webhooks/liq_prompt.txt`

```
You are a crypto market event analyst for HermesForge. A real-time market
event has been detected by the liquidation listener daemon.

EVENT DATA:
  event_type: {event_type}
  coin: {coin}
  direction: {direction}
  severity: {severity}
  source: {source}
  timestamp: {timestamp}

Your tasks:
1. Call get_open_trades() to check if we have any open paper positions on {coin}.
   If we do, note the direction and whether this event is favorable or adverse
   to our position.

2. Call fetch_funding_rate("{coin}") to get current funding context if the event
   is a funding extreme or cascade. This provides additional context.

3. Call fetch_oi("{coin}") to get current open interest if the event is an OI
   spike or cascade. Compare to event data.

4. Analyze the event:
   - For cascades: A cascade of longs (direction=long) means longs are being
     force-liquidated, which is bearish. A cascade of shorts is bullish. The
     severity field tells you the magnitude.
   - For funding extremes: Extreme positive funding = crowded long, potential
     long squeeze risk. Extreme negative = crowded short, potential short
     squeeze. The percentile tells you how extreme.
   - For OI spikes: Rapid OI increase + price up = new positions opening
     (momentum). OI decrease = positions closing (unwind). Large OI spikes
     with no price move can precede volatility expansion.

5. If severity is "high", compose a Discord alert message with:
   - Event type and coin (bold)
   - Direction and magnitude
   - Impact on any open paper trades we have (from step 1)
   - Recommended action: "reduce position", "tighten stop", "monitor closely",
     or "no open position — informational"
   - Keep it concise (3-5 lines max)

6. If severity is "medium" or "low", output a brief one-line summary. The
   deliver system will post it to Discord only if the agent produces output.

7. Log the event analysis as a single line of JSON to
   ~/.hermes/market_data/liquidation_events.jsonl using the terminal tool:
   echo '{"timestamp":"...","event_type":"...","coin":"...","analysis":"...","recommended_action":"..."}' >> ~/.hermes/market_data/liquidation_events.jsonl

Do NOT suggest entering new trades. Do NOT recommend position sizes. This is
an alert and exposure-check system only. If we have open positions at risk,
say so clearly.
```

### 3.5 Event-to-Prompt Variable Mapping

The Hermes webhook system uses {dot.notation} to reference fields from the
incoming JSON payload. The prompt template above uses flat field names for
clarity. The actual mapping:

| Prompt Variable | Payload Path |
|-----------------|-------------|
| {event_type} | event_type |
| {coin} | coin |
| {direction} | direction |
| {severity} | severity |
| {source} | source |
| {timestamp} | timestamp |
| {size_usd} | size_usd |
| {details.count} | details.count |
| {details.rate} | details.rate |
| {details.percentile} | details.percentile |
| {details.pct_change} | details.pct_change |

### 3.6 JSONL Event Log

File: `~/.hermes/market_data/liquidation_events.jsonl`

Each line is a complete JSON object, appended by the agent at the end of each
run:

```json
{"timestamp":"2026-08-18T14:30:00Z","event_type":"cascade","coin":"BTC","direction":"long","severity":"high","source":"okx","size_usd":2500000,"details":{"count":4,"window_seconds":60},"analysis":"Long liquidation cascade on BTC — 4 liquidations totaling $2.5M in 60s. Bearish signal. We have an open BTC long (STR-AA-williams-r). Position is at risk — consider tightening stop.","recommended_action":"tighten stop","open_positions":["STR-AA-williams-r_BTC_2026-08-17"]}
```

This file is append-only and used for historical analysis. It can be loaded
as a pandas DataFrame via `pd.read_json(..., lines=True)` for backtesting
event-driven strategies.

---

## 4. System 3: MCP Server for HermesForge Trading Data

### 4.1 Overview

An MCP (Model Context Protocol) server that exposes HermesForge's existing data
fetchers as tools available to any Hermes agent run. The server uses stdio
transport — Hermes spawns it as a subprocess and communicates via JSON-RPC
over stdin/stdout.

### 4.2 File Location

`~/HermesForge/scripts/mcp/hermesforge_mcp_server.py`

### 4.3 MCP Server Registration

```bash
hermes mcp add hermesforge \
  --command /usr/local/lib/hermes-agent/venv/bin/python3 \
  --args /root/HermesForge/scripts/mcp/hermesforge_mcp_server.py \
  --connect-timeout 10
```

This adds a persistent MCP server config to `~/.hermes/config.yaml`. Hermes
spawns the server as a subprocess on agent startup and discovers its tools
via the standard MCP initialize/list_tools handshake.

### 4.4 Tool Specifications

Six tools exposed via the MCP protocol:

#### Tool 1: fetch_oi

```
Name: fetch_oi
Description: Fetch current open interest for a crypto coin from Hyperliquid.
Returns OI in USD, raw OI in coin units, and mark price.
Parameters:
  coin (string, required): Coin symbol, e.g. "BTC", "ETH", "SOL"
Returns:
  {
    "coin": "BTC",
    "open_interest_usd": 1234567890.0,
    "open_interest_raw": 19400.5,
    "mark_price": 63600.0,
    "source": "hyperliquid",
    "timestamp": "2026-08-18T14:30:00Z"
  }
```

Implementation: Calls `fetch_open_interest()` from `fetch_hyperliquid_metrics.py`,
returns the coin's entry. Falls back to `fetch_okx_oi()` from
`liquidity_heatmap.py` if Hyperliquid returns empty.

#### Tool 2: fetch_funding_rate

```
Name: fetch_funding_rate
Description: Fetch current funding rate and 7-day history for a crypto coin.
Returns the current rate, 7-day average, and extreme classification.
Parameters:
  coin (string, required): Coin symbol
Returns:
  {
    "coin": "BTC",
    "current_rate": 0.000085,
    "current_rate_pct": 0.0085,
    "avg_7d": 0.000072,
    "extreme": "neutral",          // "positive_extreme" | "negative_extreme" | "neutral"
    "history_7d": [                // last 7 entries
      {"timestamp": "...", "rate": 0.000085},
      ...
    ],
    "source": "hyperliquid",
    "timestamp": "..."
  }
```

Implementation: Calls `fetch_funding_history(coin, hours=168)` and
`fetch_open_interest()` from `fetch_hyperliquid_metrics.py`. Uses the
existing `get_funding_summary()` logic for extreme classification.

#### Tool 3: fetch_liquidations

```
Name: fetch_liquidations
Description: Fetch recent liquidation orders from OKX for a specific coin.
Parameters:
  coin (string, required): Coin symbol (e.g. "BTC")
  limit (integer, optional, default 20): Max liquidations to return (1-100)
Returns:
  {
    "coin": "BTC",
    "liquidations": [
      {
        "side": "long",           // "long" | "short" (which side got liquidated)
        "size_contracts": 12.5,
        "size_btc": 0.125,
        "size_usd": 7950.0,
        "price": 63600.0,
        "timestamp": "2026-08-18T14:29:00Z"
      },
      ...
    ],
    "count": 20,
    "source": "okx",
    "timestamp": "..."
  }
```

Implementation: Calls OKX `/api/v5/public/liquidation-orders?instId={coin}-USDT-SWAP&uly=`
endpoint. Parses the response and normalizes to the above schema. Uses
`OKX_CT_VAL` constant from `liquidity_heatmap.py` for contract size conversion.

Note: OKX liquidation endpoint uses `state=volved` param for filled
liquidations. The implementation must handle pagination via the `after`
cursor if limit > 20.

#### Tool 4: fetch_orderbook

```
Name: fetch_orderbook
Description: Fetch L2 orderbook depth from OKX (up to 100 levels) and
Hyperliquid (20 levels). Returns aggregated bid/ask depth.
Parameters:
  coin (string, required): Coin symbol
  depth (integer, optional, default 20): Number of levels per side (max 100 for OKX)
Returns:
  {
    "coin": "BTC",
    "mid_price": 63600.0,
    "best_bid": 63599.5,
    "best_ask": 63600.5,
    "total_bid_usd": 5234567.89,
    "total_ask_usd": 4987654.32,
    "imbalance_usd": 246913.57,
    "top_5_bids": [{"price": 63599.5, "size_usd": 120000}, ...],
    "top_5_asks": [{"price": 63600.5, "size_usd": 95000}, ...],
    "sources": ["okx", "hyperliquid"],
    "timestamp": "..."
  }
```

Implementation: Calls `fetch_okx_orderbook(symbol, depth)` and
`fetch_hyperliquid_orderbook(coin)` from `liquidity_heatmap.py`. Uses the
existing `aggregate_liquidity()` function to merge. Returns top 5 walls
per side instead of full bins (keeps response small for MCP transport).

#### Tool 5: fetch_regime

```
Name: fetch_regime
Description: Fetch current market regime classification from cached data.
Returns the full regime dict including VIX, DXY, SPY trend, breadth,
fear/greed, and correlation components.
Parameters: none
Returns:
  {
    "overall": "risk_on",
    "stock_regime": "risk_on",
    "crypto_regime": "neutral",
    "confidence": 0.82,
    "data_freshness": "fresh",
    "vix": {"current": 14.25, "regime": "low", ...},
    "dxy": {"current": 99.67, "trend": "falling", ...},
    "spy_trend": {"close": 777.28, "trend": "uptrend", ...},
    "breadth": {"pct_above_50ma": 68.0, ...},
    "fear_greed": {"value": 34, "classification": "Fear", ...},
    "correlation": {"correlation_regime": "normal", ...},
    "timestamp": "..."
  }
```

Implementation: Calls `get_regime()` from `regime_filter.py`. This is the
US-116 module that reads from cached parquet files. No live API calls.

#### Tool 6: get_open_trades

```
Name: get_open_trades
Description: Get all open paper trades from the HermesForge trade log.
Optionally filter by ticker or asset class.
Parameters:
  ticker (string, optional): Filter by ticker symbol (e.g. "BTC")
  asset_class (string, optional): Filter by "stock" or "crypto"
Returns:
  {
    "count": 5,
    "trades": [
      {
        "trade_id": "STR-AA-williams-r_BTC_2026-08-17",
        "short_id": "",
        "strategy_id": "STR-AA-williams-r",
        "ticker": "BTC",
        "asset_class": "crypto",
        "direction": "long",
        "entry_date": "2026-08-17",
        "entry_price": 63600.0,
        "stop_price": 61633.85,
        "target_price": 66918.0,
        "status": "open",
        "entry_status": "pending"
      },
      ...
    ]
  }
```

Implementation: Reads `trades.csv` directly using the `csv` module (no
pandas dependency for the MCP server). Filters rows where `status == "open"`.
Optional filters by ticker or asset_class if provided.

### 4.5 MCP Server Implementation Skeleton

```python
#!/usr/bin/env python3
"""
hermesforge_mcp_server.py — MCP server exposing HermesForge trading data tools.

Stdio transport. Hermes spawns this as a subprocess via `hermes mcp add`.

Uses the official `mcp` Python SDK (v2.0.0, already installed in the
Hermes venv at /usr/local/lib/hermes-agent/venv/).
"""

import sys
import os
import json
import csv
import pathlib
from datetime import datetime, timezone

# Add HermesForge scripts to path for importing existing fetchers
HERMESFORGE = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(HERMESFORGE / "scripts" / "data"))
sys.path.insert(0, str(HERMESFORGE / "scripts" / "paper_trading"))

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

# HermesForge imports (lazy-loaded inside tool handlers to avoid
# import errors at startup if a dependency is missing)
app = Server("hermesforge")

TRADES_CSV = HERMESFORGE / "scripts" / "paper_trading" / "trades.csv"

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="fetch_oi",
            description="Fetch current open interest for a crypto coin from Hyperliquid.",
            inputSchema={
                "type": "object",
                "properties": {
                    "coin": {"type": "string", "description": "Coin symbol e.g. BTC, ETH, SOL"},
                },
                "required": ["coin"],
            },
        ),
        Tool(
            name="fetch_funding_rate",
            description="Fetch current funding rate and 7-day history for a crypto coin.",
            inputSchema={
                "type": "object",
                "properties": {
                    "coin": {"type": "string", "description": "Coin symbol"},
                },
                "required": ["coin"],
            },
        ),
        # ... fetch_liquidations, fetch_orderbook, fetch_regime, get_open_trades
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "fetch_oi":
            result = await _handle_fetch_oi(arguments)
        elif name == "fetch_funding_rate":
            result = await _handle_fetch_funding_rate(arguments)
        elif name == "fetch_liquidations":
            result = await _handle_fetch_liquidations(arguments)
        elif name == "fetch_orderbook":
            result = await _handle_fetch_orderbook(arguments)
        elif name == "fetch_regime":
            result = await _handle_fetch_regime()
        elif name == "get_open_trades":
            result = await _handle_get_open_trades(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e), "tool": name}

    return [TextContent(type="text", text=json.dumps(result, default=str, indent=2))]

# --- Tool handlers (each wraps an existing HermesForge function) ---

def _handle_fetch_oi(args: dict) -> dict:
    from fetch_hyperliquid_metrics import fetch_open_interest
    coin = args["coin"]
    oi_data = fetch_open_interest()
    if coin in oi_data:
        d = oi_data[coin]
        return {
            "coin": coin,
            "open_interest_usd": d["open_interest"] * d.get("mark_price", 0),
            "open_interest_raw": d["open_interest"],
            "mark_price": d.get("mark_price", 0),
            "source": "hyperliquid",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    # Fallback to OKX
    from liquidity_heatmap import fetch_okx_oi
    okx_symbol = f"{coin}-USDT-SWAP"
    oi_usd = fetch_okx_oi(okx_symbol)
    return {"coin": coin, "open_interest_usd": oi_usd, "source": "okx", ...}

# ... similar handlers for other tools

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 4.6 Dependency Management

The MCP server must run in the Hermes venv (`/usr/local/lib/hermes-agent/venv/`)
because that's where `mcp` SDK is installed. The existing fetchers
(`fetch_hyperliquid_metrics.py`, `liquidity_heatmap.py`) depend on `requests`
and `pandas` which must be available in that venv.

Check: `pip show requests pandas` in the Hermes venv — if missing, install
via `pip install requests pandas` in the venv. The `regime_filter.py` module
has a numpy/pandas guard (degrades gracefully if unavailable).

The `--command` in `hermes mcp add` must point to the Hermes venv python:
`/usr/local/lib/hermes-agent/venv/bin/python3`

---

## 5. File Structure (All New Files)

```
~/HermesForge/
├── scripts/
│   ├── listeners/                    # NEW directory
│   │   └── liq_listener.py           # System 1: liquidation listener daemon
│   ├── mcp/                          # NEW directory
│   │   └── hermesforge_mcp_server.py  # System 3: MCP server
│   └── webhooks/                     # NEW directory
│       └── liq_prompt.txt            # System 2: self-contained agent prompt
├── 04-ForgeLoop/
│   └── DESIGN-architect-US119-liquidation-webhook-mcp.md  # THIS FILE

/etc/systemd/system/
└── hermesforge-liq-listener.service  # NEW: systemd unit

~/.hermes/
├── config.yaml                        # MODIFIED: enable webhook platform
├── logs/
│   └── liq_listener.log               # NEW: daemon log (rotating)
└── market_data/
    └── liquidation_listener/          # NEW: state directory
        ├── funding_history_{coin}.json
        ├── oi_snapshots_{coin}.json
        └── liquidation_events.jsonl   # Event log (written by agent)
```

---

## 6. Error Handling Strategy

### 6.1 Liquidation Listener (System 1)

| Error Scenario | Detection | Recovery | Log Level |
|----------------|-----------|----------|-----------|
| Hyperliquid API down | requests.ConnectionError / Timeout | Retry 3x with 5s backoff, skip cycle, continue | WARNING |
| OKX API down | Same | Same | WARNING |
| OKX rate limit (429) | HTTP 429 response | Sleep 60s, resume | WARNING |
| Hyperliquid rate limit | HTTP 429 | Sleep 30s, resume | WARNING |
| JSON parse error | json.JSONDecodeError | Log raw response (first 500 chars), skip cycle | ERROR |
| Webhook POST fails | requests.ConnectionError to localhost:8644 | Retry 3x with 2s backoff, then queue event for next cycle | WARNING |
| Webhook auth fails | HTTP 401/403 from gateway | Log, continue (gateway may be restarting) | ERROR |
| State file corrupt | json.JSONDecodeError on load | Rename to .corrupt, start fresh | ERROR |
| Disk full | IOError on write | Log, continue (state is in-memory until disk recovers) | ERROR |
| Unhandled exception | catch-all in main loop | Log full traceback, sleep 5s, continue | ERROR |

The main loop structure:

```python
while True:
    try:
        poll_cycle()
    except Exception as e:
        logger.exception(f"Unhandled error in poll cycle: {e}")
        time.sleep(5)  # brief pause before retrying
    else:
        time.sleep(POLL_INTERVAL)
```

This guarantees the daemon never exits due to an unhandled exception.

### 6.2 Webhook Agent (System 2)

| Error Scenario | Detection | Recovery |
|----------------|-----------|----------|
| MCP tool call fails | Tool returns {"error": "..."} | Agent sees error in tool output, proceeds with available data |
| MCP server not started | Tool call timeout | Agent notes tool unavailable, falls back to event data only |
| trades.csv missing | get_open_trades returns {"error": "..."} | Agent notes no trade data available |
| Discord delivery fails | Gateway logs delivery error | Event still logged to JSONL (step 7 in prompt) |
| Agent itself crashes | Gateway catches agent exit | Gateway logs error, event is lost (acceptable — daemon will re-detect if condition persists) |

Key principle: The agent prompt is designed to degrade gracefully. Each step
is independent — if MCP tools fail, the agent still analyzes the event from
the payload data alone. If Discord fails, the JSONL log still captures the
analysis. The system degrades but does not break.

### 6.3 MCP Server (System 3)

| Error Scenario | Detection | Recovery |
|----------------|-----------|----------|
| Upstream API down (Hyperliquid/OKX) | requests exception in handler | Return {"error": "...", "source": "...", "timestamp": "..."} |
| Invalid coin parameter | Empty result from API | Return {"error": "No data for coin {coin}", "coin": coin} |
| Import error (missing dependency) | ImportError at handler call | Return {"error": "Module not available: {module}"} |
| trades.csv missing | FileNotFoundError | Return {"error": "Trade log not found", "path": str(TRADES_CSV)} |
| MCP protocol error | Malformed JSON-RPC | SDK handles — returns error response to client |
| Server crash | Process exits | Hermes respawns the subprocess on next agent run |

Every tool handler returns a dict (never raises). Errors are encoded in the
response body as {"error": "..."} so the agent sees a clear message. The
catch-all in `call_tool()` ensures no handler exception escapes to the MCP
protocol layer.

---

## 7. Testing Approach

### 7.1 Liquidation Listener Tests

Test file: `~/HermesForge/scripts/listeners/test_liq_listener.py`

```python
# Unit tests (pytest):
# 1. test_cascade_detector_basic: Feed 3 liquidations in 50s, assert cascade fires
# 2. test_cascade_detector_window: Feed 3 liquidations in 70s, assert no cascade (window expired)
# 3. test_cascade_detector_direction_split: 2 long + 1 short in 60s, assert no cascade
# 4. test_funding_extreme_p95: Build 100-entry history, inject p95 value, assert fires
# 5. test_funding_extreme_neutral: Inject median value, assert no fire
# 6. test_funding_extreme_insufficient_data: 50-entry history, assert no fire
# 7. test_oi_spike_up: Previous OI=100M, current=107M, assert fires (7% > 5%)
# 8. test_oi_spike_below_threshold: 3% change, assert no fire
# 9. test_webhook_payload_format: Assert JSON schema of fired events
# 10. test_state_persistence: Save/load funding history, verify round-trip

# Integration tests (mock HTTP):
# 11. test_okx_liquidation_parse: Mock OKX response, assert correct parsing
# 12. test_hyperliquid_oi_parse: Mock metaAndAssetCtxs response, assert correct parsing
# 13. test_webhook_post: Mock localhost:8644, assert POST is sent with correct payload
# 14. test_retry_on_connection_error: Mock connection error, assert retry logic

# Soak test (manual, 24h):
# 15. Run daemon for 24h, verify:
#     - No crashes (check journalctl for restarts)
#     - Log file rotating correctly
#     - State files being written
#     - At least some poll cycles completing (even if no events)
```

### 7.2 MCP Server Tests

Test file: `~/HermesForge/scripts/mcp/test_hermesforge_mcp.py`

```python
# Unit tests (pytest, using mcp client):
# 1. test_list_tools: Connect to server, call list_tools, assert 6 tools returned
# 2. test_fetch_oi_btc: Call fetch_oi("BTC"), assert response has open_interest_usd > 0
# 3. test_fetch_oi_invalid: Call fetch_oi("NONEXISTENT"), assert error in response
# 4. test_fetch_funding_rate_btc: Call fetch_funding_rate("BTC"), assert current_rate present
# 5. test_fetch_liquidations_btc: Call fetch_liquidations("BTC", 5), assert count <= 5
# 6. test_fetch_orderbook_btc: Call fetch_orderbook("BTC", 20), assert mid_price > 0
# 7. test_fetch_regime: Call fetch_regime(), assert "overall" key present
# 8. test_get_open_trades: Call get_open_trades(), assert count >= 0
# 9. test_get_open_trades_filter: Call get_open_trades(ticker="BTC"), assert all trades have ticker=BTC
# 10. test_error_handling: Call unknown tool, assert error response

# Integration test (via hermes mcp test):
# 11. hermes mcp test hermesforge — verify Hermes can connect and list tools
```

### 7.3 Webhook Integration Tests

```bash
# 1. Test webhook endpoint with curl:
hermes webhook test liq --payload '{"event_type":"cascade","coin":"BTC","direction":"long","severity":"high","source":"okx","timestamp":"2026-08-18T14:30:00Z","size_usd":2500000,"details":{"count":4,"window_seconds":60}}'

# 2. Verify agent runs and posts to Discord #crypto-setups
# 3. Verify JSONL entry appears in ~/.hermes/market_data/liquidation_events.jsonl
# 4. Test with severity=medium — should produce shorter output
# 5. Test with severity=low — should still log to JSONL
```

### 7.4 End-to-End Test

```bash
# 1. Start MCP server in background
python3 ~/HermesForge/scripts/mcp/hermesforge_mcp_server.py &

# 2. Verify MCP tools work
hermes mcp test hermesforge

# 3. Start listener daemon
python3 ~/HermesForge/scripts/listeners/liq_listener.py &

# 4. Manually trigger a test event via curl (if no real events occur):
curl -X POST http://localhost:8644/webhooks/liq \
  -H "Content-Type: application/json" \
  -H "X-Hermes-Signature: sha256=..." \
  -d '{"event_type":"oi_spike","coin":"ETH","direction":"up","severity":"medium","source":"hyperliquid","timestamp":"2026-08-18T14:30:00Z","details":{"pct_change":7.2,"current_oi":5000000000,"previous_oi":4665000000}}'

# 5. Verify:
#    - Agent runs (check gateway logs)
#    - Discord message posted to #crypto-setups (if severity high)
#    - JSONL entry written
#    - MCP tools were called by the agent (check for tool call traces)
```

---

## 8. Integration Points with Existing HermesForge Code

### 8.1 Code Reuse Map

| New Component | Reuses From | How |
|---------------|-------------|-----|
| liq_listener.py | `fetch_hyperliquid_metrics.py` | import `fetch_open_interest()`, `fetch_funding_history()` for OI/funding polling |
| liq_listener.py | `liquidity_heatmap.py` | import `fetch_okx_oi()`, `fetch_okx_orderbook()` for OKX data |
| hermesforge_mcp_server.py | `fetch_hyperliquid_metrics.py` | import `fetch_open_interest()`, `fetch_funding_history()`, `get_funding_summary()` |
| hermesforge_mcp_server.py | `liquidity_heatmap.py` | import `fetch_okx_orderbook()`, `fetch_hyperliquid_orderbook()`, `aggregate_liquidity()`, `fetch_okx_oi()` |
| hermesforge_mcp_server.py | `regime_filter.py` | import `get_regime()` for fetch_regime tool |
| hermesforge_mcp_server.py | `trades.csv` | direct CSV read for get_open_trades tool |
| liq_prompt.txt | `crypto-market-data` skill | loaded via `--skills` flag, gives agent API reference |
| Webhook delivery | Discord gateway | `--deliver discord --deliver-chat-id 1528555885310513213` uses existing gateway |

### 8.2 No Modifications to Existing Files

This design does NOT modify any existing HermesForge code. It only:
- Creates new files (liq_listener.py, hermesforge_mcp_server.py, liq_prompt.txt)
- Adds a webhook platform config to ~/.hermes/config.yaml (new key under platforms)
- Adds a systemd service file (external to the repo)

Existing modules are imported, not modified. This follows the US-114 lesson:
the US-116 regime_filter and US-115 market_structure modules were designed the
same way (new files, no modifications to existing scanner code).

### 8.3 Config Changes Required

1. **~/.hermes/config.yaml** — Add webhook platform:
```yaml
platforms:
  discord:
    streaming: false
  telegram:
    streaming: true
  webhook:                          # NEW
    enabled: true
    extra:
      port: 8644
      secret: "auto-generated-by-hermes-gateway-setup"
```

2. **~/.hermes/.env** — Add webhook secret:
```
WEBHOOK_SECRET=<generated-by-hermes-webhook-subscribe>
```

3. **Gateway restart** required after config change:
```
hermes gateway restart --system
```

This is a risky step (briefly disconnects Discord/Telegram). The user must
trigger this manually per the user profile rule: "user personally triggers
the final risky step (e.g. restart), agent never does."

---

## 9. Implementation Order (for Coder)

The three systems have dependencies: MCP server must exist before the webhook
agent can call its tools. The listener can be built independently but needs
the webhook endpoint to fire events to.

Recommended order:

1. **MCP Server** (System 3) — No runtime dependencies, can be built and
   tested standalone via `hermes mcp test`.
   - Create `scripts/mcp/hermesforge_mcp_server.py`
   - Register with `hermes mcp add hermesforge ...`
   - Test with `hermes mcp test hermesforge`
   - Verify all 6 tools return data

2. **Webhook Platform + Subscription** (System 2) — Requires gateway restart
   (user-triggered). The MCP server must be registered first so the agent
   has tools available.
   - Enable webhook platform in config.yaml
   - User restarts gateway
   - Create `scripts/webhooks/liq_prompt.txt`
   - Run `hermes webhook subscribe liq ...`
   - Test with `hermes webhook test liq --payload ...`

3. **Liquidation Listener** (System 1) — Requires the webhook endpoint to
   be live (System 2 must be operational).
   - Create `scripts/listeners/liq_listener.py`
   - Create systemd service file
   - `systemctl daemon-reload && systemctl enable hermesforge-liq-listener`
   - User starts the service: `systemctl start hermesforge-liq-listener`
   - Monitor with `journalctl -u hermesforge-liq-listener -f`

---

## 10. Risk Considerations

### 10.1 API Rate Limits

- OKX: 20 requests per 2 seconds per IP. With a 12-second poll cycle and 10
  coins, we make ~10-20 requests per cycle (liquidation orders per coin +
  OI per coin). This is well within limits. The listener should batch OKX
  requests and add a 100ms delay between per-coin calls as a safety margin.
- Hyperliquid: No documented rate limit. The existing fetchers make
  concurrent calls without issues. 12-second polling is conservative.

### 10.2 Gateway Restart Risk

Enabling the webhook platform requires restarting the Hermes gateway. This
briefly disconnects Discord and Telegram. The restart takes ~5 seconds.
The user must trigger this manually — the agent never restarts the gateway.

### 10.3 False Positives

- Cascade detector: 3 liquidations in 60 seconds is a low bar for high-volume
  coins (BTC, ETH). During volatile periods, this may fire frequently.
  Mitigation: the `size_usd` threshold for severity=high ($1M) filters out
  small cascades. Medium severity cascades are logged but only posted to
  Discord if the agent produces output (which it always does).
- Funding extreme: 30-day rolling window with 5th/95th percentile. This
  is a statistical threshold, not a fixed one. It adapts to regimes but
  may fire more often during trending markets.
- OI spike: 5% in 1 hour. Large coins rarely move 5% OI in an hour. Small
  coins (ENA, PUMP) may trigger more often. The UNIVERSE config allows
  excluding volatile small caps if false positives are excessive.

### 10.4 MCP Server as Single Point of Failure

If the MCP server crashes during an agent run, tool calls will fail and the
agent falls back to analyzing event data from the payload alone. This is
acceptable — the agent prompt is designed to work with or without MCP tools.
Hermes respawns the MCP subprocess on the next agent invocation.

### 10.5 No Autonomous Trading

Per SOUL.md hard rules: this system never executes trades. It detects
market events, alerts on exposure risk, and logs for analysis. The agent
prompt explicitly forbids suggesting new trades or position sizes. The
"recommended_action" in the JSONL log is advisory only ("tighten stop",
"monitor closely") — the user decides whether to act.

---

## 11. ADR-001 Tier Compliance

This design is authored at T2 (glm-5.2, architect profile) per the user's
hard rule: "Coder+architect=T2 hard floor." Implementation must be routed
through the 8-profile HermesForge swarm (orchestrator/architect/coder/
researcher/risk-guardian/backtester) with proper ADR-001 tier assignments.

The design is intentionally modular: each system can be implemented and
tested independently, reducing integration risk. The coder should implement
in the order specified in Section 9.

---

## 12. Open Questions for the User

1. **Webhook port**: Is 8644 acceptable, or is another port in use? (Default
   from Hermes docs, no conflict found on this VPS.)
2. **Coin universe**: The listener defaults to the 10-coin CRYPTO_UNIVERSE
   from fetch_hyperliquid_metrics.py (BTC, ETH, SOL, AVAX, LINK, DOGE, ARB,
   OP, SUI, BNB). Should this be expanded or narrowed?
3. **OKX liquidation endpoint**: OKX's `/api/v5/public/liquidation-orders`
   has been documented but not tested from this VPS. The coder should verify
   it works (OKX generally works from here per memory notes) before building
   the cascade detector around it. If it returns 403, we fall back to
   Hyperliquid-only (OI drops as a liquidation proxy).
4. **Gateway restart timing**: The webhook platform enable requires a
   gateway restart. When should this be scheduled to minimize disruption?
   (Recommended: low-traffic period, e.g. 02:00 UTC.)