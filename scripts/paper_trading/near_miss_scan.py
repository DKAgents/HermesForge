#!/usr/bin/env python3
"""
near_miss_scan.py — HermesForge end-of-day fallback report.

If capture_signals.py finds 0 qualifying trades for a given day, this
script reports the "closest" candidates: setups that passed every
structural rule of a strategy (maturity gates, narrowing/divergence
checks, resistance-touch checks, etc.) on TODAY's bar, but fell short
of the strategy's minimum reward:risk ratio (MIN_RR = 3.0 for all of
A/B/D). Ranked by how close their actual R:R came to the 3.0 bar.

This does NOT relax any structural rule -- only the final RR gate is
loosened (to a near-zero floor) so we can see what *would* have
qualified if RR had been the only thing standing in the way. Every
other rule (MACD maturity bars, histogram narrowing, prior-swing
divergence, resistance touch/break, ATR-based stop) is enforced
exactly as in the real scanners, because those are the module-level
functions imported directly -- only the MIN_RR constant is patched.

Usage:
    python3 near_miss_scan.py                  # top 3 stocks+crypto
    python3 near_miss_scan.py --top 5
    python3 near_miss_scan.py --stocks-only
    python3 near_miss_scan.py --crypto-only
"""

import sys
import argparse
import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from fetch_data import load_all as load_all_stocks           # noqa: E402
from fetch_crypto_data import load_all as load_all_crypto     # noqa: E402
import scanners.scanner_a_ma_pullback as scanner_a            # noqa: E402
import scanners.scanner_b_macd_divergence as scanner_b        # noqa: E402
import scanners.scanner_d_sr_reversal as scanner_d            # noqa: E402

STRATEGIES = {
    "STR-A-ma-pullback-fibonacci":     scanner_a,
    "STR-B-macd-histogram-divergence": scanner_b,
    "STR-D-sr-role-reversal":          scanner_d,
}

NEAR_ZERO_RR = 0.01  # effectively disables the RR gate so we see raw candidates


def _rr_from_signal(sig: dict) -> float | None:
    """Recompute actual R:R for a signal dict, direction-aware."""
    entry = sig.get("entry_price")
    stop = sig.get("stop_price")
    target = sig.get("target_price")
    if entry is None or stop is None or target is None:
        return None
    direction = sig.get("direction", "long")
    if direction == "short":
        risk = stop - entry
        reward = entry - target
    else:
        risk = entry - stop
        reward = target - entry
    if risk <= 0:
        return None
    return reward / risk


def _scan_near_misses(data: dict, asset_class: str) -> list[dict]:
    results = []
    for strategy_id, module in STRATEGIES.items():
        original_rr = module.MIN_RR
        module.MIN_RR = NEAR_ZERO_RR  # loosen ONLY the RR gate
        try:
            for ticker, df in data.items():
                try:
                    signals = module.scan(df, ticker)
                except Exception:
                    continue
                if not signals:
                    continue
                latest = signals[-1]
                most_recent_bar_date = str(df.index[-1])[:10]
                if str(latest["date"])[:10] != most_recent_bar_date:
                    continue  # not today's bar -- not relevant to "today's near misses"

                rr = _rr_from_signal(latest)
                if rr is None:
                    continue
                if rr >= original_rr:
                    continue  # this one actually qualifies for real -- not a "near miss"

                results.append({
                    "strategy_id": strategy_id,
                    "ticker": ticker,
                    "asset_class": asset_class,
                    "direction": latest.get("direction", "long"),
                    "date": str(latest["date"])[:10],
                    "entry_price": latest["entry_price"],
                    "stop_price": latest["stop_price"],
                    "target_price": latest["target_price"],
                    "achieved_rr": round(rr, 2),
                    "required_rr": original_rr,
                    "rr_gap": round(original_rr - rr, 2),
                })
        finally:
            module.MIN_RR = original_rr  # always restore, even on error
    return results


def main():
    ap = argparse.ArgumentParser(description="End-of-day near-miss fallback report")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--stocks-only", action="store_true")
    ap.add_argument("--crypto-only", action="store_true")
    ap.add_argument("--json", action="store_true",
                     help="Emit machine-readable JSON split by asset class "
                          "(for the daily_publish cron fallback), instead of "
                          "human-readable text.")
    args = ap.parse_args()

    include_stocks = not args.crypto_only
    include_crypto = not args.stocks_only

    all_results = []

    if include_stocks:
        if not args.json:
            print("Loading cached stock data...")
        stock_data = load_all_stocks()
        all_results += _scan_near_misses(stock_data, "stock")

    if include_crypto:
        if not args.json:
            print("Loading cached crypto data...")
        crypto_data = load_all_crypto()
        all_results += _scan_near_misses(crypto_data, "crypto")

    all_results.sort(key=lambda r: r["rr_gap"])

    if args.json:
        import json as _json
        stock_top = [r for r in all_results if r["asset_class"] == "stock"][: args.top]
        crypto_top = [r for r in all_results if r["asset_class"] == "crypto"][: args.top]
        print(_json.dumps({
            "stock_near_misses": stock_top,
            "crypto_near_misses": crypto_top,
        }, indent=2, default=str))
        return

    top_n = all_results[: args.top]

    print(f"\n{'='*70}")
    print(f"Near-miss candidates found: {len(all_results)}  (showing top {len(top_n)})")
    print(f"{'='*70}")
    for rank, r in enumerate(top_n, 1):
        print(f"\n#{rank}: {r['ticker']} ({r['asset_class']}) -- {r['strategy_id']}")
        print(f"    direction: {r['direction']}  |  date: {r['date']}")
        print(f"    entry: {r['entry_price']}  stop: {r['stop_price']}  target: {r['target_price']}")
        print(f"    achieved R:R: {r['achieved_rr']}  (needed {r['required_rr']})  gap: {r['rr_gap']}")

    if not top_n:
        print("\nNo near-miss candidates found either -- today's bar had zero setups")
        print("that even cleared the structural rules, regardless of R:R.")

    return top_n


if __name__ == "__main__":
    main()
