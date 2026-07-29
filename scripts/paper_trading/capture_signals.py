#!/usr/bin/env python3
"""
capture_signals.py — HermesForge EPIC-010 (US-066, extended in US-069)

Runs the daily scanners for strategies A, B, D (independent of Discord
publish_enabled flags -- paper trading has its own, lower bar) against
BOTH stock data (yfinance cache) and crypto data (Hyperliquid cache,
BTC/ETH/SOL) and automatically opens a paper trade for every qualifying
fresh signal.

Usage:
    python3 capture_signals.py --dry-run     # show what would be opened
    python3 capture_signals.py               # actually opens trades
    python3 capture_signals.py --stocks-only
    python3 capture_signals.py --crypto-only
"""

import sys
import json
import argparse
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from fetch_data import load_all as load_all_stocks  # noqa: E402
from scanners.scanner_a_ma_pullback import scan as scan_a       # noqa: E402
from scanners.scanner_b_macd_divergence import scan as scan_b   # noqa: E402
from scanners.scanner_d_sr_reversal import scan as scan_d       # noqa: E402
from scanners.scanner_i_adaptive_trend import scan as scan_i    # noqa: E402

import trade_log  # noqa: E402
import position_sizing  # noqa: E402
from fetch_crypto_data import load_all as load_all_crypto  # noqa: E402

# Strategy note frontmatter id -> scan fn
# Paper trading covers A, B, D, I (C is a confirmed Phase 1A kill -- excluded).
PAPER_STRATEGIES = {
    "STR-A-ma-pullback-fibonacci":     scan_a,
    "STR-B-macd-histogram-divergence": scan_b,
    "STR-D-sr-role-reversal":          scan_d,
    "STR-I-adaptive-trend":            scan_i,
}

EXAMPLE_ACCOUNT_SIZE = 100_000  # matches scripts/discord/config.py convention


def _get_risk_pct(strategy_id: str, signal_dict: dict) -> float:
    """Real per-strategy sizing (US-067): B's Level x Weekly-gate matrix, A/D flat 1%."""
    return position_sizing.get_risk_pct(strategy_id, signal_dict)


def _scan_and_capture(data: dict, asset_class: str, data_source: str,
                       dry_run: bool, summary: dict) -> None:
    """Shared scan+capture loop, used for both stock and crypto data sources."""
    for strategy_id, scan_fn in PAPER_STRATEGIES.items():
        print(f"\nScanning {strategy_id} ({asset_class})...")

        # Scanner I (AdaptiveTrend) is long-only for stocks, bidirectional for crypto.
        scanner_kwargs = {}
        if strategy_id == "STR-I-adaptive-trend":
            scanner_kwargs["long_only"] = (asset_class == "stock")

        for ticker, df in data.items():
            try:
                signals = scan_fn(df, ticker, **scanner_kwargs)
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{strategy_id}/{ticker} ({asset_class}) scan error: {e}")
                continue

            if not signals:
                continue

            latest = signals[-1]
            most_recent_bar_date = str(df.index[-1])[:10]
            if str(latest["date"])[:10] != most_recent_bar_date:
                continue  # stale/historical signal, not actionable today

            summary["signals_found"] += 1

            if trade_log.has_open_trade(strategy_id, ticker):
                summary["skipped_already_open"] += 1
                print(f"  SKIP: {strategy_id}/{ticker} already has an open paper trade")
                continue

            entry_date = str(latest["date"])[:10]
            risk_pct = _get_risk_pct(strategy_id, latest)

            allowed, heat_reason = position_sizing.check_portfolio_heat(risk_pct)
            if not allowed:
                summary.setdefault("skipped_heat_limit", 0)
                summary["skipped_heat_limit"] += 1
                print(f"  SKIP (heat limit): {strategy_id}/{ticker} -- {heat_reason}")
                continue

            entry_price = latest["entry_price"]
            stop_price = latest["stop_price"]
            risk_per_unit = abs(entry_price - stop_price)
            position_size_units = (
                round((EXAMPLE_ACCOUNT_SIZE * risk_pct / 100) / risk_per_unit, 4)
                if risk_per_unit else 0
            )

            trade_dict = {
                "strategy_id": strategy_id,
                "ticker": ticker,
                "asset_class": asset_class,
                "data_source": data_source,
                "direction": latest["direction"],
                "signal_id": f"{strategy_id}_{ticker}_{entry_date}",
                "entry_date": entry_date,
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": latest["target_price"],
                "position_size_pct": risk_pct,
                "position_size_units": position_size_units,
                "quality_tier": "",  # filled in by alert_publisher's tier logic if available
                "subperiod": latest.get("subperiod", "n/a"),
                "confirmation_level": latest.get("confirmation_level", ""),
                "weekly_gate_scaling": latest.get("weekly_gates_passing", ""),
                "notes": "",
            }

            if dry_run:
                summary["opened"] += 1
                summary["opened_trades"].append(trade_dict)
                print(f"  WOULD OPEN: {strategy_id}/{ticker} @ {entry_price} ({entry_date})")
            else:
                try:
                    trade_id = trade_log.open_trade(trade_dict)
                    summary["opened"] += 1
                    trade_dict["trade_id"] = trade_id
                    summary["opened_trades"].append(trade_dict)
                    print(f"  OPENED: {trade_id}")
                except ValueError as e:
                    summary["errors"] += 1
                    summary["error_details"].append(str(e))


def capture(dry_run: bool = False, include_stocks: bool = True, include_crypto: bool = True) -> dict:
    summary = {
        "signals_found": 0,
        "opened": 0,
        "skipped_already_open": 0,
        "errors": 0,
        "opened_trades": [],
        "error_details": [],
    }

    if include_stocks:
        print("Loading cached stock market data...")
        stock_data = load_all_stocks()
        if stock_data:
            print(f"Loaded {len(stock_data)} stock tickers.")
            _scan_and_capture(stock_data, "stock", "yfinance", dry_run, summary)
        else:
            print("No cached stock data found (run fetch_data.py first) -- skipping stocks.")

    if include_crypto:
        print("\nLoading cached crypto market data...")
        crypto_data = load_all_crypto()
        if crypto_data:
            print(f"Loaded {len(crypto_data)} crypto symbols.")
            _scan_and_capture(crypto_data, "crypto", "hyperliquid", dry_run, summary)
        else:
            print("No cached crypto data found (run fetch_crypto_data.py first) -- skipping crypto.")

    return summary


def main():
    ap = argparse.ArgumentParser(description="HermesForge automatic paper trade signal capture")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be opened without writing to trades.csv")
    ap.add_argument("--stocks-only", action="store_true")
    ap.add_argument("--crypto-only", action="store_true")
    args = ap.parse_args()

    include_stocks = not args.crypto_only
    include_crypto = not args.stocks_only

    summary = capture(dry_run=args.dry_run, include_stocks=include_stocks, include_crypto=include_crypto)

    print(f"\n{'='*60}")
    print(f"SUMMARY: {summary['signals_found']} signals found, "
          f"{summary['opened']} {'would open' if args.dry_run else 'opened'}, "
          f"{summary['skipped_already_open']} skipped (already open), "
          f"{summary.get('skipped_heat_limit', 0)} skipped (heat limit), "
          f"{summary['errors']} errors")
    for err in summary.get("error_details", []):
        print(f"  ERROR: {err}")

    print(f"\n--- JSON ---")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
