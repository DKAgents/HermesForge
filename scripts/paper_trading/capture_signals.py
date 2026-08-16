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
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "research"))

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
                       dry_run: bool, summary: dict, regime: dict = None,
                       strategy_directives: dict = None) -> None:
    """Shared scan+capture loop, used for both stock and crypto data sources."""
    for strategy_id, scan_fn in PAPER_STRATEGIES.items():
        # Check regime-aware strategy directives
        if strategy_directives:
            # Match strategy_id (e.g. "STR-B-macd-histogram-divergence") to directive keys (e.g. "STR-B")
            strat_prefix = strategy_id.split("-")[0] if "-" in strategy_id else strategy_id
            directive = strategy_directives.get(f"STR-{strat_prefix}") if strat_prefix else None
            if not directive:
                # Try direct match
                directive = strategy_directives.get(strategy_id)
            if directive and directive.get("action") == "suppress":
                print(f"\nScanning {strategy_id} ({asset_class})... SUPPRESSED by regime selector")
                print(f"  Reason: {directive.get('reason', '')}")
                summary.setdefault("suppressed_by_regime", 0)
                summary["suppressed_by_regime"] += 1
                continue
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
            
            # Apply regime-aware risk multiplier
            if strategy_directives:
                strat_prefix = strategy_id.split("-")[0] if "-" in strategy_id else strategy_id
                directive = strategy_directives.get(f"STR-{strat_prefix}") or strategy_directives.get(strategy_id)
                if directive:
                    mult = directive.get("risk_multiplier", 1.0)
                    risk_pct = round(risk_pct * mult, 2)
                    if mult != 1.0:
                        print(f"  Regime adjustment: risk {mult:.1f}x → {risk_pct}%")

            # US-111: Portfolio Risk Guard — DISABLED during testing phase
            # Re-enable once we have 50+ closed trades for strategy validation.
            # See portfolio_risk_guard.py for production limits (8 pos, 7% heat, 3 sector, circuit breaker).
            pass  # Risk guard disabled — let all trades through for data collection

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
                "direction": latest.get("direction", "long"),
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

            # Tag with market regime context
            if regime:
                try:
                    tag_signal(trade_dict, regime)
                except Exception:
                    pass  # regime tagging is optional

            # Tag with liquidity sweep context (US-107 + US-108 tiered)
            # US-108: Tiered mode — STR-D requires sweep, STR-A/B/I get boost mode
            try:
                sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "data"))
                from sweep_timing_filter import check_sweep_alignment
                sweep_result = check_sweep_alignment(
                    ticker, entry_price, latest.get("direction", "long"),
                    asset_class, interval="5m", mode="require",
                    strategy_id=strategy_id,  # US-108: tiered mode selection
                )
                trade_dict["sweep_found"] = sweep_result["sweep_found"]
                trade_dict["sweep_aligned"] = sweep_result["sweep_found"]
                trade_dict["sweep_direction"] = sweep_result["sweep_direction"]
                trade_dict["sweep_quality"] = sweep_result["sweep_quality"]
                trade_dict["sweep_level_type"] = sweep_result.get("sweep_level_type")
                trade_dict["sweep_description"] = sweep_result["description"]
                
                # In require mode: skip signal if no sweep found
                # (STR-D uses require mode; STR-A/B/I use boost mode and won't block)
                if sweep_result["action"] == "block":
                    summary.setdefault("skipped_no_sweep", 0)
                    summary["skipped_no_sweep"] += 1
                    print(f"  SKIP (no sweep): {strategy_id}/{ticker} — {sweep_result['description'][:80]}")
                    continue
                elif sweep_result["action"] == "boost":
                    trade_dict["notes"] = (trade_dict.get("notes", "") + 
                        f" | Sweep confirmed: {sweep_result['sweep_direction']} "
                        f"(quality {sweep_result['sweep_quality']}/100)")
            except Exception as e:
                pass  # sweep filter is optional — don't block on error

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

    # Fetch market regime once for all signals
    regime = None
    try:
        from regime_filter import get_regime, tag_signal
        print("Fetching market regime data...")
        regime = get_regime()
        print(f"  Regime: stock={regime['stock_regime']}, crypto={regime['crypto_regime']}, overall={regime['overall']}")
        if regime.get("vix"):
            print(f"  VIX={regime['vix'].get('current', 0):.1f}, DXY trend={regime.get('dxy', {}).get('trend', '?')}, F&G={regime.get('fear_greed', {}).get('value', 0)}")
    except Exception as e:
        print(f"  Warning: regime filter unavailable ({e}) — signals will not be tagged")

    # Fetch regime-aware strategy directives
    strategy_directives = {}
    try:
        from regime_strategy_selector import get_strategy_directives
        print("Fetching strategy directives...")
        dir_result = get_strategy_directives()
        strategy_directives = dir_result.get("directives", {})
        print(f"  Posture: {dir_result.get('overall_posture', '?').upper()}")
        for sid, d in strategy_directives.items():
            print(f"  {sid}: {d['action']} (risk x{d['risk_multiplier']:.1f}) — {d.get('reason', '')[:80]}")
    except Exception as e:
        print(f"  Warning: strategy selector unavailable ({e}) — running all strategies at default risk")

    if include_stocks:
        print("Loading cached stock market data...")
        stock_data = load_all_stocks()
        if stock_data:
            print(f"Loaded {len(stock_data)} stock tickers.")
            _scan_and_capture(stock_data, "stock", "yfinance", dry_run, summary, regime, strategy_directives)
        else:
            print("No cached stock data found (run fetch_data.py first) -- skipping stocks.")

    if include_crypto:
        print("\nLoading cached crypto market data...")
        crypto_data = load_all_crypto()
        if crypto_data:
            print(f"Loaded {len(crypto_data)} crypto symbols.")
            _scan_and_capture(crypto_data, "crypto", "hyperliquid", dry_run, summary, regime, strategy_directives)
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
