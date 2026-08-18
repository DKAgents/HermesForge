#!/usr/bin/env python3
"""
hermesforge_mcp_server.py — MCP server exposing HermesForge trading data tools.

Exposes the following tools via stdio transport for Hermes MCP integration:
- fetch_oi(coin) — current open interest for a coin
- fetch_funding_rate(coin) — current funding rate
- fetch_liquidations(coin, limit) — recent liquidation events (proxy)
- fetch_orderbook(coin, depth) — L2 orderbook snapshot
- fetch_regime() — current market regime
- get_open_trades() — open paper trading positions

Usage with Hermes:
    hermes mcp add hermesforge --command python3 --args scripts/monitoring/hermesforge_mcp_server.py

Requirements:
    pip install mcp  # or use the hermes venv which has it
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Data fetchers (reuse existing logic)
# ---------------------------------------------------------------------------

def _hyperliquid_request(payload):
    """Make a POST request to Hyperliquid API."""
    url = "https://api.hyperliquid.xyz/info"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "HermesForge-MCP/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def fetch_oi(coin: str) -> dict:
    """Get current open interest for a coin from Hyperliquid."""
    data = _hyperliquid_request({"type": "metaAndAssetCtxs"})
    if not isinstance(data, list) or len(data) < 2:
        return {"error": "No data"}
    universe = data[0].get("universe", []) if isinstance(data[0], dict) else []
    ctxs = data[1] if isinstance(data[1], list) else []
    for u, ctx in zip(universe, ctxs):
        if isinstance(u, dict) and u.get("name", "").upper() == coin.upper():
            if isinstance(ctx, dict):
                oi = float(ctx.get("openInterest", 0))
                mark = float(ctx.get("markPx", 0))
                return {
                    "coin": coin,
                    "open_interest_coin": oi,
                    "mark_price": mark,
                    "open_interest_usd": oi * mark,
                    "funding_rate": float(ctx.get("funding", 0)),
                    "max_leverage": int(u.get("maxLeverage", 0)),
                }
    return {"error": f"Coin {coin} not found"}


def fetch_funding_rate(coin: str) -> dict:
    """Get current funding rate for a coin."""
    oi_data = fetch_oi(coin)
    if "error" in oi_data:
        return oi_data
    rate = oi_data.get("funding_rate", 0)
    return {
        "coin": coin,
        "funding_rate": rate,
        "funding_pct_8h": rate * 100,
        "annualized_pct": rate * 3 * 365,
        "interpretation": "longs_paying" if rate > 0 else "shorts_paying",
        "risk": "long_squeeze" if rate > 0.001 else "short_squeeze" if rate < -0.001 else "neutral",
        "open_interest_usd": oi_data.get("open_interest_usd", 0),
        "mark_price": oi_data.get("mark_price", 0),
    }


def fetch_orderbook(coin: str, depth: int = 20) -> dict:
    """Get L2 orderbook snapshot from Hyperliquid."""
    data = _hyperliquid_request({"type": "l2Book", "coin": coin})
    levels = data.get("levels", [[], []])
    bids = levels[0] if len(levels) > 0 else []
    asks = levels[1] if len(levels) > 1 else []
    
    bid_list = [{"price": float(b["px"]), "size": float(b["sz"]), "usd": float(b["px"]) * float(b["sz"])}
                for b in bids[:depth]]
    ask_list = [{"price": float(a["px"]), "size": float(a["sz"]), "usd": float(a["px"]) * float(a["sz"])}
                for a in asks[:depth]]
    
    total_bid_usd = sum(b["usd"] for b in bid_list)
    total_ask_usd = sum(a["usd"] for a in ask_list)
    best_bid = bid_list[0]["price"] if bid_list else 0
    best_ask = ask_list[0]["price"] if ask_list else 0
    mid = (best_bid + best_ask) / 2 if best_bid and best_ask else 0
    
    return {
        "coin": coin,
        "mid_price": mid,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": best_ask - best_bid,
        "total_bid_usd": total_bid_usd,
        "total_ask_usd": total_ask_usd,
        "imbalance_usd": total_bid_usd - total_ask_usd,
        "bids": bid_list,
        "asks": ask_list,
    }


def fetch_regime() -> dict:
    """Get current market regime from the regime filter."""
    import pathlib
    sys.path.insert(0, str(pathlib.Path("/root/HermesForge/scripts")))
    try:
        from data.regime_filter import get_regime
        regime = get_regime()
        return {
            "regime": regime.get("overall", "unknown"),
            "confidence": regime.get("confidence", 0),
            "components": regime.get("components", {}),
            "timestamp": regime.get("timestamp", ""),
        }
    except Exception as e:
        return {"error": f"Regime filter error: {e}"}


def get_open_trades() -> dict:
    """Get open paper trading positions from trades.csv."""
    import csv
    trades_path = "/root/HermesForge/scripts/paper_trading/trades.csv"
    try:
        open_trades = []
        with open(trades_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "open":
                    open_trades.append({
                        "trade_id": row.get("trade_id", ""),
                        "ticker": row.get("ticker", ""),
                        "direction": row.get("direction", ""),
                        "entry_price": row.get("entry_price", ""),
                        "stop_price": row.get("stop_price", ""),
                        "target_price": row.get("target_price", ""),
                        "strategy": row.get("strategy", ""),
                        "asset_class": row.get("asset_class", ""),
                        "data_source": row.get("data_source", ""),
                    })
        return {"count": len(open_trades), "trades": open_trades}
    except Exception as e:
        return {"error": f"Failed to read trades: {e}"}


def fetch_all_oi() -> dict:
    """Get OI for all tracked coins."""
    data = _hyperliquid_request({"type": "metaAndAssetCtxs"})
    if not isinstance(data, list) or len(data) < 2:
        return {"error": "No data"}
    universe = data[0].get("universe", []) if isinstance(data[0], dict) else []
    ctxs = data[1] if isinstance(data[1], list) else []
    coins = {}
    for u, ctx in zip(universe, ctxs):
        if not isinstance(u, dict) or not isinstance(ctx, dict):
            continue
        name = u.get("name", "")
        oi = float(ctx.get("openInterest", 0))
        mark = float(ctx.get("markPx", 0))
        if oi * mark > 1_000_000:  # Only coins with >$1M OI
            coins[name] = {
                "oi_usd": oi * mark,
                "funding_rate": float(ctx.get("funding", 0)),
                "mark_price": mark,
            }
    return {"total_coins": len(coins), "coins": coins}


# ---------------------------------------------------------------------------
# MCP Server (stdio transport)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "fetch_oi",
        "description": "Get current open interest for a cryptocurrency from Hyperliquid",
        "inputSchema": {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL)"},
            },
            "required": ["coin"],
        },
    },
    {
        "name": "fetch_funding_rate",
        "description": "Get current funding rate for a cryptocurrency from Hyperliquid",
        "inputSchema": {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol (e.g., BTC, ETH, SOL)"},
            },
            "required": ["coin"],
        },
    },
    {
        "name": "fetch_orderbook",
        "description": "Get L2 orderbook snapshot from Hyperliquid",
        "inputSchema": {
            "type": "object",
            "properties": {
                "coin": {"type": "string", "description": "Coin symbol"},
                "depth": {"type": "integer", "description": "Number of levels (default 20, max 20)"},
            },
            "required": ["coin"],
        },
    },
    {
        "name": "fetch_regime",
        "description": "Get current market regime from the HermesForge regime filter",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_open_trades",
        "description": "Get all open paper trading positions from HermesForge",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "fetch_all_oi",
        "description": "Get open interest for all Hyperliquid coins with >$1M OI",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

TOOL_HANDLERS = {
    "fetch_oi": lambda args: fetch_oi(args.get("coin", "")),
    "fetch_funding_rate": lambda args: fetch_funding_rate(args.get("coin", "")),
    "fetch_orderbook": lambda args: fetch_orderbook(args.get("coin", "BTC"), min(args.get("depth", 20), 20)),
    "fetch_regime": lambda args: fetch_regime(),
    "get_open_trades": lambda args: get_open_trades(),
    "fetch_all_oi": lambda args: fetch_all_oi(),
}


def handle_request(request):
    """Handle a JSON-RPC request and return a response."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hermesforge-mcp", "version": "1.0.0"},
            }
        }
    elif method == "notifications/initialized":
        return None  # notification, no response
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)
        if handler:
            try:
                result = handler(tool_args)
                return {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }
    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    else:
        return {
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }


def main():
    """Main MCP server loop — reads JSON-RPC from stdin, writes to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()