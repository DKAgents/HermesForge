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
from scanners.scanner_r_alligator import scan as scan_r         # noqa: E402
from scanners.scanner_t_head_shoulders import scan as scan_t    # noqa: E402
from scanners.scanner_u_double_top_bottom import scan as scan_u  # noqa: E402
from scanners.scanner_v_triangles import scan as scan_v          # noqa: E402
from scanners.scanner_w_flags_pennants import scan as scan_w     # noqa: E402
from scanners.scanner_x_parabolic_sar import scan as scan_x     # noqa: E402
from scanners.scanner_y_adx_dmi import scan as scan_y            # noqa: E402
from scanners.scanner_z_stochastic import scan as scan_z         # noqa: E402
from scanners.scanner_aa_williams_r import scan as scan_aa       # noqa: E402
from scanners.scanner_ab_obv_divergence import scan as scan_ab   # noqa: E402
from scanners.scanner_ac_cci import scan as scan_ac              # noqa: E402
from scanners.scanner_ad_keltner import scan as scan_ad          # noqa: E402
from scanners.scanner_ae_4week_rule import scan as scan_ae      # noqa: E402
from scanners.scanner_af_candlestick import scan as scan_af      # noqa: E402
from scanners.scanner_ag_wedge import scan as scan_ag            # noqa: E402
from scanners.scanner_aj_intermarket import scan as scan_aj       # noqa: E402

# Autonomous-pipeline deployed strategy (2026-08-16): VIX term-structure
# contango breakout — walk-forward validated OOS ROBUST EDGE (see
# 06-Strategies/Hypotheses/STR-20260816-vix-vrp-contango-breakout.md).
from scanners.scanner_vix_vrp_contango import scan as scan_vixc  # noqa: E402

# Autonomous-pipeline deployed strategy (2026-08-18): Low-correlation regime
# stock picker — Phase 1A positive (mean_r=0.092, p=0.0, all 3 sub-periods
# positive). Deployed WATCH with 0.5% risk. See
# 06-Strategies/Hypotheses/STR-20260818-lowcorr-regime.md.
from scanners.scanner_lowcorr_regime import scan as scan_lowcorr  # noqa: E402

import trade_log  # noqa: E402
import position_sizing  # noqa: E402
from fetch_crypto_data import load_all as load_all_crypto  # noqa: E402

# Strategy note frontmatter id -> scan fn
# Paper trading covers A, B, D, I, R-S through R-AJ (C is a confirmed Phase 1A kill).
PAPER_STRATEGIES = {
    "STR-A-ma-pullback-fibonacci":     scan_a,
    "STR-B-macd-histogram-divergence": scan_b,
    "STR-D-sr-role-reversal":          scan_d,
    "STR-I-adaptive-trend":            scan_i,
    "STR-R-alligator":                 scan_r,
    "STR-T-head-shoulders":            scan_t,
    "STR-U-double-top-bottom":         scan_u,
    "STR-V-triangles":                 scan_v,
    "STR-W-flags-pennants":            scan_w,
    "STR-X-parabolic-sar":             scan_x,
    "STR-Y-adx-dmi":                   scan_y,
    "STR-Z-stochastic":                scan_z,
    "STR-AA-williams-r":               scan_aa,
    "STR-AB-obv-divergence":           scan_ab,
    "STR-AC-cci":                      scan_ac,
    "STR-AD-keltner":                  scan_ad,
    "STR-AE-4week":                    scan_ae,
    "STR-AF-candlestick":              scan_af,
    "STR-AG-wedge":                    scan_ag,

    "STR-AJ-intermarket":              scan_aj,

    # Autonomous-pipeline deployed (2026-08-16): VIX contango breakout.
    # Watch-level risk (0.5%) — see 06-Strategies/Hypotheses/STR-20260816-vix-vrp-contango-breakout.md
    "STR-VIXC-vix-contango-breakout":  scan_vixc,

    # Autonomous-pipeline deployed (2026-08-18): Low-correlation regime stock picker.
    # Watch-level risk (0.5%) — Phase 1A mean_r=0.092 p=0.0, in-sample-with-costs 0.072,
    # positive in all 3 sub-periods. Walk-forward incomplete (compute-bound on 529-stock
    # correlation matrix). See 06-Strategies/Hypotheses/STR-20260818-lowcorr-regime.md
    "STR-LOWCORR-lowcorr-regime":     scan_lowcorr,
}

EXAMPLE_ACCOUNT_SIZE = 100_000  # matches scripts/discord/config.py convention

# STR-AJ fires correlated signals across all stocks on macro triggers — limit concentration
MAX_INTERMARKET_POSITIONS = 3

# Batch-mode strategies (cross-sectional scanners that take the full data dict,
# not per-ticker). These are called once with `scan_fn(data)` and produce signals
# for multiple tickers at once.
BATCH_STRATEGIES = {"STR-LOWCORR-lowcorr-regime"}


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

        # Strategies that are long-only for stocks, bidirectional for crypto
        scanner_kwargs = {}
        long_only_stocks = {"STR-I-adaptive-trend", "STR-R-alligator",
                           "STR-T-head-shoulders",
                           "STR-U-double-top-bottom", "STR-V-triangles",
                           "STR-W-flags-pennants", "STR-X-parabolic-sar",
                           "STR-Y-adx-dmi", "STR-Z-stochastic",
                           "STR-AA-williams-r", "STR-AB-obv-divergence",
                           "STR-AC-cci", "STR-AD-keltner", "STR-AE-4week",
                           "STR-AF-candlestick", "STR-AG-wedge",
                           "STR-AJ-intermarket"}
        if strategy_id in long_only_stocks:
            scanner_kwargs["long_only"] = (asset_class == "stock")

        # ── Batch-mode strategies (cross-sectional scanners) ───────────────
        # These take the full data dict and return signals for multiple tickers.
        if strategy_id in BATCH_STRATEGIES:
            try:
                all_batch_signals = scan_fn(data, latest_only=True)
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{strategy_id} (batch) scan error: {e}")
                continue

            if not all_batch_signals:
                continue

            # Filter for signals on the most recent bar date
            most_recent_bar_date = str(list(data.values())[0].index[-1])[:10]
            recent_batch = [s for s in all_batch_signals
                            if str(s.get("date", ""))[:10] == most_recent_bar_date]

            for latest in recent_batch:
                ticker = latest.get("ticker", "")
                df = data.get(ticker)
                if df is None:
                    continue

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
                    "quality_tier": "",
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
                        pass

                if dry_run:
                    summary["opened"] += 1
                    summary["opened_trades"].append(trade_dict)
                    print(f"  WOULD OPEN: {strategy_id}/{ticker} @ {entry_price} ({entry_date})")
                else:
                    try:
                        trade_id = trade_log.open_trade(trade_dict)
                        summary["opened"] += 1
                        trade_dict["trade_id"] = trade_id
                        print(f"  OPENED: {strategy_id}/{ticker} @ {entry_price} ({entry_date})")
                    except Exception as e:
                        summary["errors"] += 1
                        summary["error_details"].append(f"{strategy_id}/{ticker} open error: {e}")
            continue  # Skip per-ticker loop for batch strategies

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

            # STR-AJ concentration control: STR-AJ fires correlated signals across
            # all stocks on macro triggers (DXY/TNX risk-on) — cap at 3 concurrent
            # positions to avoid portfolio concentration in a single macro bet.
            if strategy_id == "STR-AJ-intermarket":
                aj_open_count = len(trade_log.get_open_trades(strategy_id="STR-AJ-intermarket"))
                if aj_open_count >= MAX_INTERMARKET_POSITIONS:
                    summary.setdefault("skipped_aj_concentration", 0)
                    summary["skipped_aj_concentration"] += 1
                    print(f"  SKIP: {strategy_id}/{ticker} — STR-AJ concentration limit "
                          f"({aj_open_count}/{MAX_INTERMARKET_POSITIONS} open)")
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
