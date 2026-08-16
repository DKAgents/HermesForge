#!/usr/bin/env python3
"""
liquidity_heatmap.py — BTC Liquidity Depth Heatmap

Fetches L2 orderbook data from OKX (100 levels) and Hyperliquid (20 levels),
aggregates bid/ask depth by price level, and generates a visual heatmap
showing where pools of resting liquidity sit.

This shows:
  - Bid walls (support — where market makers are buying)
  - Ask walls (resistance — where market makers are selling)
  - Cumulative depth by price tier
  - OI overlay from both exchanges

Output: PNG heatmap saved to ~/.hermes/market_data/heatmaps/

Usage:
    python3 liquidity_heatmap.py                    # generate heatmap
    python3 liquidity_heatmap.py --coin BTC         # specify coin (default BTC)
    python3 liquidity_heatmap.py --json             # output JSON only
    python3 liquidity_heatmap.py --post             # post to Discord
"""
import json
import time
import urllib.request
import urllib.error
import sys
import os
import pathlib
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OUTPUT_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "heatmaps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OKX_CT_VAL = 0.01  # BTC per OKX contract


# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------

def fetch_okx_orderbook(symbol="BTC-USDT-SWAP", depth=100):
    """Fetch OKX L2 orderbook (up to 100 levels). Returns (bids, asks) as lists of (price, size_btc, usd)."""
    url = f"https://www.okx.com/api/v5/market/books?instId={symbol}&sz={depth}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesForge/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("code") != "0" or not data.get("data"):
            return [], []
        book = data["data"][0]
        bids = []
        for b in book.get("bids", []):
            px = float(b[0])
            contracts = float(b[1])
            size_btc = contracts * OKX_CT_VAL
            usd = px * size_btc
            bids.append((px, size_btc, usd))
        asks = []
        for a in book.get("asks", []):
            px = float(a[0])
            contracts = float(a[1])
            size_btc = contracts * OKX_CT_VAL
            usd = px * size_btc
            asks.append((px, size_btc, usd))
        return bids, asks
    except Exception as e:
        print(f"  [WARN] OKX orderbook fetch failed: {e}", file=sys.stderr)
        return [], []


def fetch_hyperliquid_orderbook(coin="BTC"):
    """Fetch Hyperliquid L2 book (20 levels). Returns (bids, asks) as lists of (price, size_btc, usd)."""
    url = "https://api.hyperliquid.xyz/info"
    payload = json.dumps({"type": "l2Book", "coin": coin}).encode()
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "HermesForge/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        levels = data.get("levels", [[], []])
        bids = []
        for b in levels[0] if len(levels) > 0 else []:
            px = float(b["px"])
            size_btc = float(b["sz"])
            usd = px * size_btc
            bids.append((px, size_btc, usd))
        asks = []
        for a in levels[1] if len(levels) > 1 else []:
            px = float(a["px"])
            size_btc = float(a["sz"])
            usd = px * size_btc
            asks.append((px, size_btc, usd))
        return bids, asks
    except Exception as e:
        print(f"  [WARN] Hyperliquid orderbook fetch failed: {e}", file=sys.stderr)
        return [], []


def fetch_okx_oi(symbol="BTC-USDT-SWAP"):
    """Fetch OKX total open interest in USD."""
    url = f"https://www.okx.com/api/v5/public/open-interest?instId={symbol}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HermesForge/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("code") == "0" and data.get("data"):
            return float(data["data"][0].get("oiUsd", 0))
    except Exception as e:
        print(f"  [WARN] OKX OI fetch failed: {e}", file=sys.stderr)
    return 0


def fetch_hyperliquid_oi(coin="BTC"):
    """Fetch Hyperliquid open interest for a coin (assetCtx)."""
    url = "https://api.hyperliquid.xyz/info"
    payload = json.dumps({"type": "metaAndAssetCtxs"}).encode()
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "HermesForge/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        # metaAndAssetCtxs returns [meta, assetCtxs] where meta has universe list
        if not isinstance(data, list) or len(data) < 2:
            return 0
        universe = data[0].get("universe", []) if isinstance(data[0], dict) else []
        ctxs = data[1] if isinstance(data[1], list) else []
        for u, ctx in zip(universe, ctxs):
            if isinstance(u, dict) and u.get("name") == coin and isinstance(ctx, dict):
                oi = float(ctx.get("openInterest", 0))
                mark = float(ctx.get("markPx", 0))
                return oi * mark  # OI in USD (oi is in coin units)
    except Exception as e:
        print(f"  [WARN] Hyperliquid OI fetch failed: {e}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_liquidity(okx_bids, okx_asks, hl_bids, hl_asks, bin_size=50):
    """
    Aggregate all orderbook levels into price bins.
    bin_size: dollar width of each bin (e.g., $50 for BTC).
    Returns dict with bid_bins, ask_bins, mid_price, total_bid_usd, total_ask_usd.
    """
    # Determine mid price from best bid/ask across both sources
    all_bids = okx_bids + hl_bids
    all_asks = okx_asks + hl_asks
    if not all_bids or not all_asks:
        return None

    best_bid = max(b[0] for b in all_bids)
    best_ask = min(a[0] for a in all_asks)
    mid_price = (best_bid + best_ask) / 2

    # Aggregate into bins
    bid_bins = {}  # bin_center -> total_usd
    ask_bins = {}

    for px, size_btc, usd in all_bids:
        bin_center = round(px / bin_size) * bin_size
        bid_bins[bin_center] = bid_bins.get(bin_center, 0) + usd

    for px, size_btc, usd in all_asks:
        bin_center = round(px / bin_size) * bin_size
        ask_bins[bin_center] = ask_bins.get(bin_center, 0) + usd

    total_bid_usd = sum(bid_bins.values())
    total_ask_usd = sum(ask_bins.values())

    return {
        "mid_price": mid_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "bid_bins": bid_bins,
        "ask_bins": ask_bins,
        "total_bid_usd": total_bid_usd,
        "total_ask_usd": total_ask_usd,
        "okx_bid_levels": len(okx_bids),
        "okx_ask_levels": len(okx_asks),
        "hl_bid_levels": len(hl_bids),
        "hl_ask_levels": len(hl_asks),
        "bin_size": bin_size,
    }


# ---------------------------------------------------------------------------
# Heatmap generation
# ---------------------------------------------------------------------------

def generate_heatmap_png(data, coin="BTC", output_path=None):
    """Generate a visual heatmap PNG showing liquidity depth by price level."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np

    if data is None:
        print("  [ERROR] No data to plot", file=sys.stderr)
        return None

    mid = data["mid_price"]
    bid_bins = data["bid_bins"]
    ask_bins = data["ask_bins"]
    bin_size = data["bin_size"]

    # Sort bins by price
    bid_prices = sorted(bid_bins.keys(), reverse=True)  # high to low (descending from mid)
    ask_prices = sorted(ask_bins.keys())  # low to high (ascending from mid)

    bid_values = [bid_bins[p] for p in bid_prices]
    ask_values = [ask_bins[p] for p in ask_prices]

    # Build combined view: asks above mid, bids below mid
    # Display as horizontal bar chart with color intensity = liquidity
    fig, ax = plt.subplots(figsize=(12, 14), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    # Colors: asks (red/orange), bids (green/teal)
    # Intensity based on relative size
    max_val = max(max(bid_values) if bid_values else 1, max(ask_values) if ask_values else 1)

    # Plot asks (above mid price, going up)
    for i, (px, val) in enumerate(zip(ask_prices, ask_values)):
        intensity = val / max_val
        color = plt.cm.OrRd(0.3 + intensity * 0.7)
        ax.barh(i + len(bid_values), val, height=0.8, color=color, edgecolor="#0f0f1e", linewidth=0.5)
        # Price label
        if val > max_val * 0.05:  # Only label significant levels
            ax.text(val + max_val * 0.01, i + len(bid_values),
                    f"${px:,.0f}  ${val/1000:.0f}K", va="center", fontsize=7,
                    color="#ff6b6b", fontweight="bold")

    # Plot bids (below mid price, going down)
    for i, (px, val) in enumerate(zip(bid_prices, bid_values)):
        intensity = val / max_val
        color = plt.cm.YlGn(0.3 + intensity * 0.7)
        ax.barh(len(bid_values) - 1 - i, val, height=0.8, color=color,
                edgecolor="#0f0f1e", linewidth=0.5)
        if val > max_val * 0.05:
            ax.text(val + max_val * 0.01, len(bid_values) - 1 - i,
                    f"${px:,.0f}  ${val/1000:.0f}K", va="center", fontsize=7,
                    color="#51cf66", fontweight="bold")

    # Mid price line
    ax.axhline(y=len(bid_values) - 0.5, color="#ffd700", linewidth=2, linestyle="--", alpha=0.8)
    ax.text(max_val * 1.15, len(bid_values) - 0.5, f"MID ${mid:,.0f}",
            va="center", fontsize=10, color="#ffd700", fontweight="bold")

    # Labels
    total_bid = data["total_bid_usd"]
    total_ask = data["total_ask_usd"]
    title = f"{coin} Liquidity Depth Heatmap\n"
    title += f"Bids: ${total_bid/1e6:.2f}M  |  Asks: ${total_ask/1e6:.2f}M  |  Imbalance: {(total_bid-total_ask)/1e6:+.2f}M"
    ax.set_title(title, fontsize=13, color="#e0e0e0", fontweight="bold", pad=15)
    ax.set_xlabel("Liquidity (USD)", fontsize=10, color="#a0a0a0")
    ax.set_ylabel("Price Level", fontsize=10, color="#a0a0a0")

    # Remove y-axis tick labels (we use inline labels)
    ax.set_yticks([])
    ax.tick_params(axis="x", colors="#a0a0a0")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333")
    ax.spines["bottom"].set_color("#333")

    # Legend
    legend_text = (
        f"Sources: OKX ({data['okx_bid_levels']}+{data['okx_ask_levels']} levels) + "
        f"Hyperliquid ({data['hl_bid_levels']}+{data['hl_ask_levels']} levels)\n"
        f"Bin size: ${bin_size}  |  "
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    fig.text(0.5, 0.01, legend_text, ha="center", fontsize=8, color="#666")

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])

    if output_path is None:
        output_path = OUTPUT_DIR / f"{coin}_liquidity_heatmap.png"
    else:
        output_path = pathlib.Path(output_path)

    plt.savefig(str(output_path), dpi=150, facecolor="#1a1a2e", bbox_inches="tight")
    plt.close()
    return output_path


# ---------------------------------------------------------------------------
# Text summary
# ---------------------------------------------------------------------------

def generate_text_summary(data, oi_okx=0, oi_hl=0, coin="BTC"):
    """Generate a text summary of liquidity concentrations."""
    if data is None:
        return "No data available."

    mid = data["mid_price"]
    bid_bins = data["bid_bins"]
    ask_bins = data["ask_bins"]

    # Top 5 bid walls (support)
    top_bids = sorted(bid_bins.items(), key=lambda x: x[1], reverse=True)[:5]
    top_asks = sorted(ask_bins.items(), key=lambda x: x[1], reverse=True)[:5]

    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  {coin} LIQUIDITY DEPTH ANALYSIS")
    lines.append(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"{'='*60}")
    lines.append(f"")
    lines.append(f"  Mid Price: ${mid:,.1f}")
    lines.append(f"  Total Bid Liquidity: ${data['total_bid_usd']/1e6:.2f}M")
    lines.append(f"  Total Ask Liquidity: ${data['total_ask_usd']/1e6:.2f}M")
    imbalance = (data['total_bid_usd'] - data['total_ask_usd']) / 1e6
    lines.append(f"  Bid/Ask Imbalance: ${imbalance:+.2f}M")
    if oi_okx or oi_hl:
        lines.append(f"")
        lines.append(f"  Open Interest:")
        if oi_okx:
            lines.append(f"    OKX: ${oi_okx/1e9:.2f}B")
        if oi_hl:
            lines.append(f"    Hyperliquid: ${oi_hl/1e6:.0f}M")
        total_oi = oi_okx + oi_hl
        lines.append(f"    Combined: ${total_oi/1e9:.2f}B")
        lines.append(f"    OI/Liquidity Ratio: {total_oi/data['total_bid_usd']:.1f}x")
    lines.append(f"")
    lines.append(f"  🟢 TOP BID WALLS (Support):")
    for px, val in top_bids:
        pct_away = (px - mid) / mid * 100
        lines.append(f"    ${px:>10,.0f}  ${val/1000:>6.0f}K  ({pct_away:+.2f}%)")
    lines.append(f"")
    lines.append(f"  🔴 TOP ASK WALLS (Resistance):")
    for px, val in top_asks:
        pct_away = (px - mid) / mid * 100
        lines.append(f"    ${px:>10,.0f}  ${val/1000:>6.0f}K  ({pct_away:+.2f}%)")
    lines.append(f"")
    lines.append(f"  Sources: OKX ({data['okx_bid_levels']}+{data['okx_ask_levels']}) + "
                 f"Hyperliquid ({data['hl_bid_levels']}+{data['hl_ask_levels']})")
    lines.append(f"  Bin size: ${data['bin_size']}")
    lines.append(f"{'='*60}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(coin="BTC", bin_size=50, output_png=True, output_json=False):
    """Fetch data, aggregate, and generate outputs."""
    okx_symbol = f"{coin}-USDT-SWAP" if coin != "BTC" else "BTC-USDT-SWAP"

    print(f"Fetching {coin} orderbook data...")

    # Fetch orderbooks
    okx_bids, okx_asks = fetch_okx_orderbook(okx_symbol, depth=100)
    print(f"  OKX: {len(okx_bids)} bids, {len(okx_asks)} asks")

    hl_bids, hl_asks = fetch_hyperliquid_orderbook(coin)
    print(f"  Hyperliquid: {len(hl_bids)} bids, {len(hl_asks)} asks")

    # Fetch OI
    oi_okx = fetch_okx_oi(okx_symbol)
    oi_hl = fetch_hyperliquid_oi(coin)
    print(f"  OI: OKX ${oi_okx/1e9:.2f}B, Hyperliquid ${oi_hl/1e6:.0f}M")

    # Aggregate
    data = aggregate_liquidity(okx_bids, okx_asks, hl_bids, hl_asks, bin_size=bin_size)
    if data is None:
        print("ERROR: No orderbook data available from any source.", file=sys.stderr)
        return None

    # Output
    if output_json:
        json_data = {
            "coin": coin,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mid_price": data["mid_price"],
            "total_bid_usd": data["total_bid_usd"],
            "total_ask_usd": data["total_ask_usd"],
            "bid_bins": data["bid_bins"],
            "ask_bins": data["ask_bins"],
            "oi_okx": oi_okx,
            "oi_hl": oi_hl,
        }
        print(json.dumps(json_data, indent=2))

    if output_png:
        png_path = generate_heatmap_png(data, coin=coin)
        if png_path:
            print(f"  Heatmap saved: {png_path}")
        else:
            print("  [WARN] Heatmap generation failed", file=sys.stderr)

    # Text summary
    summary = generate_text_summary(data, oi_okx=oi_okx, oi_hl=oi_hl, coin=coin)
    print(summary)

    return {
        "data": data,
        "oi_okx": oi_okx,
        "oi_hl": oi_hl,
        "summary": summary,
        "png_path": str(generate_heatmap_png(data, coin=coin)) if output_png else None,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BTC Liquidity Depth Heatmap")
    parser.add_argument("--coin", default="BTC", help="Coin symbol (default: BTC)")
    parser.add_argument("--bin", type=int, default=5, help="Bin size in USD (default: 5)")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    parser.add_argument("--no-png", action="store_true", help="Skip PNG generation")
    args = parser.parse_args()

    result = run(
        coin=args.coin,
        bin_size=args.bin,
        output_png=not args.no_png,
        output_json=args.json,
    )
    if result is None:
        sys.exit(1)
