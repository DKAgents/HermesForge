#!/usr/bin/env python3
"""
capture_sweep_signals.py
========================
HermesForge US-107 — Live intraday liquidity sweep signal capture.

Runs on 5-minute interval during market hours, detects liquidity sweeps,
opens paper trades for high-quality confirmed sweeps, and monitors exits.

This is the intraday companion to the daily capture_signals.py:
- capture_signals.py runs once daily on daily bars (STR-A/B/D/I)
- capture_sweep_signals.py runs every 5 min on intraday bars (STR-Q)

Usage:
    python3 capture_sweep_signals.py              # live capture
    python3 capture_sweep_signals.py --dry-run    # show what would open
    python3 capture_sweep_signals.py --crypto-only
    python3 capture_sweep_signals.py --stocks-only

Cron: every 5 minutes during market hours (9:25 AM - 4:05 PM ET, 7 days for crypto)
"""

import sys
import os
import json
import time
import argparse
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

# Path setup
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))

from detect_liquidity_sweeps import (
    scan_symbol_for_sweeps, SweepEvent,
)
from fetch_intraday_crypto import get_intraday_candles
from fetch_intraday_stocks import get_intraday_bars

import trade_log
import position_sizing

# US-108: Import tiered filter for equal_lows exclusion on stocks
from sweep_timing_filter import _filter_valid_sweeps, PREMIUM_LEVEL_TYPES, EXCLUDED_STOCK_LEVEL_TYPES

STRATEGY_ID = "STR-Q-liquidity-sweep"
EXAMPLE_ACCOUNT_SIZE = 100_000

# Minimum quality score for live capture
MIN_QUALITY = 50

# Risk per trade
RISK_PCT = 1.0

# Discord alert channels (from memory)
DISCORD_STOCK_SETUPS_CHANNEL = "1528555538848153640"
DISCORD_CRYPTO_SETUPS_CHANNEL = "1528555885310513213"
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

# Universe
CRYPTO_SYMBOLS = [
    "BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK",
    "SUI", "APT", "TIA", "SEI", "INJ", "RNDR",
]

STOCK_SYMBOLS = [
    "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
    "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
]


def _is_market_open(asset_type: str) -> bool:
    """Check if market is open for the given asset type."""
    now = datetime.now(timezone.utc)
    
    if asset_type == "crypto":
        return True  # crypto trades 24/7
    
    # Stocks: 9:30 AM - 4:00 PM ET = 13:30 - 20:00 UTC
    # Allow a few minutes buffer on each side
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()
    
    if weekday >= 5:  # Saturday/Sunday
        return False
    
    current_minutes = hour * 60 + minute
    return 13 * 60 + 25 <= current_minutes <= 20 * 60 + 5


def _calculate_position_size(entry_price: float, stop_price: float, risk_pct: float) -> float:
    """Calculate position size in units."""
    risk_per_unit = abs(entry_price - stop_price)
    if risk_per_unit <= 0:
        return 0
    return round((EXAMPLE_ACCOUNT_SIZE * risk_pct / 100) / risk_per_unit, 4)


# ── US-108: Discord Alert Posting ────────────────────────────────────────────

def _post_str_q_alert(trade_dict: dict, sweep) -> bool:
    """Post a STR-Q alert embed to the appropriate Discord channel.
    
    Posts to #crypto-setups or #stock-setups based on asset class.
    Returns True if posted successfully.
    """
    if not DISCORD_BOT_TOKEN:
        print("  ⚠️ DISCORD_BOT_TOKEN not set — skipping Discord alert")
        return False
    
    symbol = trade_dict["ticker"]
    asset_class = trade_dict.get("asset_class", "crypto")
    direction = trade_dict.get("direction", "long")
    entry_price = trade_dict["entry_price"]
    stop_price = trade_dict["stop_price"]
    target_price = trade_dict["target_price"]
    
    channel_id = DISCORD_CRYPTO_SETUPS_CHANNEL if asset_class == "crypto" else DISCORD_STOCK_SETUPS_CHANNEL
    
    risk = abs(entry_price - stop_price)
    reward = abs(target_price - entry_price)
    rr = reward / risk if risk > 0 else 0
    stop_pct = (risk / entry_price * 100) if entry_price else 0
    
    # Day-of-week color
    import datetime as _dt
    day_colors = {
        0: 0x3498db, 1: 0x2ecc71, 2: 0xe67e22, 3: 0x9b59b6,
        4: 0xe74c3c, 5: 0x1abc9c, 6: 0xf1c40f,
    }
    color = day_colors.get(_dt.datetime.utcnow().weekday(), 0x58a6ff)
    
    def _fmt(p):
        if abs(p) < 1.0: return f"${p:.6f}"
        elif abs(p) < 100.0: return f"${p:.4f}"
        else: return f"${p:.2f}"
    
    direction_emoji = "🟢" if direction == "long" else "🔴"
    direction_label = "LONG" if direction == "long" else "SHORT"
    
    embed = {
        "title": f"📊 STR-Q Liquidity Sweep — {symbol}",
        "description": (
            f"{direction_emoji} **{direction_label}** | Intraday 5m | "
            f"Sweep: {sweep.direction} at **{sweep.level_type}**\n"
            f"Quality: **{sweep.quality_score}/100** | Confirmation: {sweep.confirmation}"
        ),
        "color": color,
        "fields": [
            {"name": "📍 Entry", "value": _fmt(entry_price), "inline": True},
            {"name": "🛑 Stop", "value": f"{_fmt(stop_price)} ({stop_pct:.1f}% risk)", "inline": True},
            {"name": "🎯 Target", "value": _fmt(target_price), "inline": True},
            {"name": "⚖️ R:R", "value": f"{rr:.1f}:1", "inline": True},
            {"name": "🏷️ Level Type", "value": sweep.level_type, "inline": True},
            {"name": "⏱️ Time Stop", "value": "75 min (15 bars)", "inline": True},
            {"name": "Sweep Details", "value": (
                f"• Penetration: {sweep.penetration_atr:.2f} ATR\n"
                f"• Wick ratio: {sweep.wick_ratio:.2f}\n"
                f"• Volume surge: {sweep.volume_surge:.2f}x\n"
                f"• Level: {_fmt(sweep.level_price)}"
            ), "inline": False},
            {"name": "Indicator Confluence", "value": (
                "**Liquidity Sweep confluence:**\n"
                f"• Price swept {sweep.level_type} level then reversed → institutional liquidity grab confirmed\n"
                f"• Sweep direction: {sweep.direction} → alignment with trade direction\n"
                f"• Quality score: {sweep.quality_score}/100 → data-driven scoring (level type weighted)\n"
                f"• Stop behind sweep wick → tight risk, minimal adverse excursion\n"
                f"• 3R target → favorable risk-reward ratio\n"
                f"• 5-minute intraday execution → precise timing, post-sweep entry"
            ), "inline": False},
        ],
        "footer": {"text": "HermesForge STR-Q Intraday Pipeline"},
        "timestamp": _dt.datetime.utcnow().isoformat() + "Z",
    }
    
    payload = {"embeds": [embed]}
    
    import subprocess
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        url,
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        response = json.loads(result.stdout)
        if "id" in response:
            print(f"  📢 Discord alert posted to channel {channel_id}")
            return True
        else:
            print(f"  ⚠️ Discord post failed: {result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"  ⚠️ Discord post error: {e}")
        return False


def _process_sweeps(sweeps: list, symbol: str, asset_type: str, dry_run: bool, summary: dict) -> None:
    """Process detected sweeps and open trades."""
    # US-108: Filter equal_lows on stocks (34.6% WR, overestimated in small sample)
    filtered_sweeps = _filter_valid_sweeps(sweeps, asset_type, strategy_id=STRATEGY_ID)
    
    for sweep in filtered_sweeps:
        if sweep.quality_score < MIN_QUALITY:
            continue
        
        if sweep.confirmation != "confirmed":
            continue
        
        # Skip if already have an open trade for this symbol
        if trade_log.has_open_trade(STRATEGY_ID, symbol):
            summary["skipped_already_open"] += 1
            continue
        
        # Map sweep direction to trade direction
        direction = "long" if sweep.direction == "bullish" else "short"
        
        entry_price = sweep.entry_price
        stop_price = sweep.stop_price
        target_price = sweep.target_price
        risk_per_unit = abs(entry_price - stop_price)
        
        if risk_per_unit <= 0:
            continue
        
        position_size_units = _calculate_position_size(entry_price, stop_price, RISK_PCT)
        
        # Create trade ID with timestamp for intraday uniqueness
        entry_time = pd.Timestamp(sweep.timestamp)
        entry_date = entry_time.strftime("%Y-%m-%d")
        time_suffix = entry_time.strftime("%H%M")
        trade_id = f"{STRATEGY_ID}_{symbol}_{entry_date}_{time_suffix}"
        
        trade_dict = {
            "strategy_id": STRATEGY_ID,
            "ticker": symbol,
            "asset_class": asset_type,
            "data_source": "hyperliquid" if asset_type == "crypto" else "yfinance",
            "direction": direction,
            "signal_id": trade_id,
            "entry_date": entry_date,
            "entry_price": round(entry_price, 6),
            "stop_price": round(stop_price, 6),
            "target_price": round(target_price, 6),
            "position_size_pct": RISK_PCT,
            "position_size_units": position_size_units,
            "quality_tier": f"sweep_q{sweep.quality_score}",
            "subperiod": f"intraday_{sweep.interval}",
            "confirmation_level": sweep.confirmation,
            "weekly_gate_scaling": "",
            "notes": (
                f"Sweep: {sweep.direction} at {sweep.level_type} "
                f"${sweep.level_price:.2f} | Pen: {sweep.penetration_atr:.2f} ATR | "
                f"Wick: {sweep.wick_ratio:.2f} | Vol: {sweep.volume_surge:.2f}x | "
                f"Quality: {sweep.quality_score}/100"
            ),
        }
        
        if dry_run:
            summary["opened"] += 1
            summary["opened_trades"].append(trade_dict)
            print(f"  WOULD OPEN: {trade_id} ({direction}) @ ${entry_price:.2f}")
            print(f"    Stop: ${stop_price:.2f} | Target: ${target_price:.2f} | R:R 3:1")
            print(f"    {trade_dict['notes']}")
        else:
            try:
                # Write directly to avoid has_open_trade check with unique trade_id
                trade_id = trade_log.open_trade(trade_dict)
                summary["opened"] += 1
                trade_dict["trade_id"] = trade_id
                summary["opened_trades"].append(trade_dict)
                print(f"  OPENED: {trade_id} ({direction}) @ ${entry_price:.2f}")
                
                # US-108: Post Discord alert to #stock-setups or #crypto-setups
                _post_str_q_alert(trade_dict, sweep)
            except ValueError as e:
                summary["skipped_already_open"] += 1


def capture(dry_run: bool = False, include_stocks: bool = True, include_crypto: bool = True) -> dict:
    """Main capture loop."""
    summary = {
        "scanned": 0,
        "signals_found": 0,
        "opened": 0,
        "skipped_already_open": 0,
        "errors": 0,
        "opened_trades": [],
        "sweeps_detected": [],
    }
    
    # ── Crypto ──
    if include_crypto:
        print("\n── Crypto Sweep Scan (5m) ──")
        for symbol in CRYPTO_SYMBOLS:
            if not _is_market_open("crypto"):
                pass  # always open
            try:
                sweeps = scan_symbol_for_sweeps(symbol, "5m", "crypto", lookback_bars=200)
                summary["scanned"] += 1
                
                # Filter to most recent sweeps only (last 3 bars = 15 min)
                if sweeps:
                    recent_sweeps = []
                    now_ts = pd.Timestamp.now(tz="UTC")
                    for s in sweeps:
                        sweep_time = pd.Timestamp(s.timestamp)
                        if (now_ts - sweep_time).total_seconds() < 900:  # last 15 min
                            recent_sweeps.append(s)
                    
                    if recent_sweeps:
                        summary["signals_found"] += len(recent_sweeps)
                        for s in recent_sweeps:
                            summary["sweeps_detected"].append({
                                "symbol": symbol,
                                "direction": s.direction,
                                "level_type": s.level_type,
                                "quality": s.quality_score,
                                "confirmation": s.confirmation,
                            })
                            print(f"  {symbol}: {s.direction} sweep at {s.level_type} "
                                  f"Q={s.quality_score}/100 ({s.confirmation})")
                        
                        _process_sweeps(recent_sweeps, symbol, "crypto", dry_run, summary)
            except Exception as e:
                summary["errors"] += 1
                print(f"  {symbol}: ERROR - {e}")
    
    # ── Stocks ──
    if include_stocks:
        if not _is_market_open("stock"):
            print("\n── Stock Sweep Scan: MARKET CLOSED (stocks) ──")
        else:
            print("\n── Stock Sweep Scan (5m) ──")
            for symbol in STOCK_SYMBOLS:
                try:
                    sweeps = scan_symbol_for_sweeps(symbol, "5m", "stock", lookback_bars=200)
                    summary["scanned"] += 1
                    
                    if sweeps:
                        recent_sweeps = []
                        now_ts = pd.Timestamp.now(tz="UTC")
                        for s in sweeps:
                            sweep_time = pd.Timestamp(s.timestamp)
                            if (now_ts - sweep_time).total_seconds() < 900:
                                recent_sweeps.append(s)
                        
                        if recent_sweeps:
                            summary["signals_found"] += len(recent_sweeps)
                            for s in recent_sweeps:
                                summary["sweeps_detected"].append({
                                    "symbol": symbol,
                                    "direction": s.direction,
                                    "level_type": s.level_type,
                                    "quality": s.quality_score,
                                    "confirmation": s.confirmation,
                                })
                                print(f"  {symbol}: {s.direction} sweep at {s.level_type} "
                                      f"Q={s.quality_score}/100 ({s.confirmation})")
                            
                            _process_sweeps(recent_sweeps, symbol, "stock", dry_run, summary)
                except Exception as e:
                    summary["errors"] += 1
                    print(f"  {symbol}: ERROR - {e}")
    
    return summary


def monitor_exits():
    """
    Check open STR-Q trades and close them if price has hit target/stop/time stop.
    Called on each 5m cycle.
    """
    rows = trade_log._read_all_rows()
    open_trades = [r for r in rows if r.get("strategy_id") == STRATEGY_ID and r.get("status") == "open"]
    
    if not open_trades:
        return {"checked": 0, "closed": 0, "closures": []}
    
    result = {"checked": 0, "closed": 0, "closures": []}
    
    for trade in open_trades:
        result["checked"] += 1
        ticker = trade["ticker"]
        asset_class = trade["asset_class"]
        direction = trade["direction"]
        entry_price = float(trade["entry_price"])
        stop_price = float(trade["stop_price"])
        target_price = float(trade["target_price"])
        entry_date = trade["entry_date"]
        
        # Get current price
        try:
            if asset_class == "crypto":
                df = get_intraday_candles(ticker, "5m", lookback_bars=5)
            else:
                df = get_intraday_bars(ticker, "5m", lookback_bars=5)
            
            if len(df) == 0:
                continue
            
            current_price = float(df["close"].iloc[-1])
            current_high = float(df["high"].iloc[-1])
            current_low = float(df["low"].iloc[-1])
            
            exit_reason = None
            exit_price = None
            
            if direction == "long":
                if current_low <= stop_price:
                    exit_reason = "stop"
                    exit_price = stop_price
                elif current_high >= target_price:
                    exit_reason = "target"
                    exit_price = target_price
            else:  # short
                if current_high >= stop_price:
                    exit_reason = "stop"
                    exit_price = stop_price
                elif current_low <= target_price:
                    exit_reason = "target"
                    exit_price = target_price
            
            # Time stop: 15 bars = 75 min
            if exit_reason is None:
                entry_time = pd.Timestamp(entry_date, tz="UTC")
                elapsed = (pd.Timestamp.now(tz="UTC") - entry_time).total_seconds()
                if elapsed > 75 * 60:  # 75 minutes
                    exit_reason = "time"
                    exit_price = current_price
            
            if exit_reason:
                # Calculate R
                if direction == "long":
                    risk = entry_price - stop_price
                    r = (exit_price - entry_price) / risk if risk > 0 else 0
                else:
                    risk = stop_price - entry_price
                    r = (entry_price - exit_price) / risk if risk > 0 else 0
                
                # Close trade
                trade["status"] = "closed"
                trade["exit_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                trade["exit_price"] = round(exit_price, 6)
                trade["exit_reason"] = exit_reason
                trade["r_multiple"] = round(r, 3)
                
                result["closed"] += 1
                result["closures"].append({
                    "trade_id": trade["trade_id"],
                    "ticker": ticker,
                    "exit_reason": exit_reason,
                    "r_multiple": round(r, 3),
                    "exit_price": round(exit_price, 6),
                })
                print(f"  CLOSED: {trade['trade_id']} ({exit_reason}) R={r:.3f}")
        except Exception as e:
            print(f"  Monitor error for {ticker}: {e}")
    
    # Write updated rows
    if result["closed"] > 0:
        for closure in result["closures"]:
            for row in rows:
                if row["trade_id"] == closure["trade_id"]:
                    row["status"] = "closed"
                    row["exit_date"] = closure["exit_price"]  # simplified
                    row["exit_price"] = closure["exit_price"]
                    row["exit_reason"] = closure["exit_reason"]
                    row["r_multiple"] = closure["r_multiple"]
                    break
        trade_log._write_all_rows(rows)
    
    return result


def main():
    ap = argparse.ArgumentParser(description="HermesForge STR-Q intraday sweep signal capture")
    ap.add_argument("--dry-run", action="store_true", help="Show what would open without writing to trades.csv")
    ap.add_argument("--stocks-only", action="store_true")
    ap.add_argument("--crypto-only", action="store_true")
    ap.add_argument("--monitor-only", action="store_true", help="Only monitor open trades for exits")
    args = ap.parse_args()
    
    if args.monitor_only:
        print("=== STR-Q Exit Monitor ===")
        result = monitor_exits()
        print(f"Checked: {result['checked']}, Closed: {result['closed']}")
        for c in result["closures"]:
            print(f"  {c['trade_id']}: {c['exit_reason']} R={c['r_multiple']:.3f}")
        return
    
    include_stocks = not args.crypto_only
    include_crypto = not args.stocks_only
    
    print(f"=== STR-Q Intraday Sweep Capture ({datetime.now(timezone.utc).isoformat()}) ===")
    
    # Monitor exits first
    print("\n── Exit Monitor ──")
    exit_result = monitor_exits()
    if exit_result["checked"] > 0:
        print(f"  Checked {exit_result['checked']} open trades, closed {exit_result['closed']}")
    
    # Capture new signals
    summary = capture(dry_run=args.dry_run, include_stocks=include_stocks, include_crypto=include_crypto)
    
    print(f"\n{'='*50}")
    print(f"SUMMARY: {summary['scanned']} scanned, {summary['signals_found']} sweeps found, "
          f"{summary['opened']} {'would open' if args.dry_run else 'opened'}, "
          f"{summary['skipped_already_open']} skipped, {summary['errors']} errors")
    
    print(f"\n--- JSON ---")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()