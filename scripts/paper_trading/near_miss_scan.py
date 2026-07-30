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

Parallelized (2026-07-28): uses ProcessPoolExecutor to scan all
(strategy × asset_class) combinations in parallel across CPU cores.
Each worker loads its own data from parquet cache (avoids pickling
large DataFrames). Scales to 1000+ instruments within 300s cron limit.

Usage:
    python3 near_miss_scan.py                  # top 3 stocks+crypto
    python3 near_miss_scan.py --top 5
    python3 near_miss_scan.py --stocks-only
    python3 near_miss_scan.py --crypto-only
"""

import sys
import argparse
import pathlib
import os
import concurrent.futures

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from fetch_data import load_all as load_all_stocks           # noqa: E402
from fetch_crypto_data import load_all as load_all_crypto     # noqa: E402
from near_miss_tracker import filter_near_misses                            # noqa: E402

STRATEGY_NAMES = [
    "STR-A-ma-pullback-fibonacci",
    "STR-B-macd-histogram-divergence",
    "STR-D-sr-role-reversal",
]

NEAR_ZERO_RR = 0.01  # effectively disables the RR gate so we see raw candidates

# Cache paths (workers load their own data to avoid pickling DataFrames)
STOCK_CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
CRYPTO_CACHE_DIR = STOCK_CACHE_DIR / "crypto"
VALID_SIGNAL_START = "2019-04-01"

# How many chunks to split each (strategy × asset_class) batch into.
# More chunks = better load balancing, more overhead. 3 is good for 3 CPUs.
CHUNKS_PER_BATCH = 3


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


# ── Worker function (runs in separate process) ──────────────────────────────

def _scan_chunk(task: dict) -> list[dict]:
    """
    Worker process: scan a chunk of tickers for one strategy.

    Loads data from parquet cache (avoids pickling DataFrames across
    process boundaries). Patches MIN_RR, scans, returns near-misses.

    task keys: strategy_name, tickers (list[str]), asset_class,
               cache_dir (str), original_rr (float)
    """
    import pandas as pd

    strategy_name = task["strategy_name"]
    tickers = task["tickers"]
    asset_class = task["asset_class"]
    cache_dir = pathlib.Path(task["cache_dir"])
    original_rr = task["original_rr"]

    # Import the scanner module by strategy name
    if strategy_name == "STR-A-ma-pullback-fibonacci":
        import scanners.scanner_a_ma_pullback as scanner
    elif strategy_name == "STR-B-macd-histogram-divergence":
        import scanners.scanner_b_macd_divergence as scanner
    elif strategy_name == "STR-D-sr-role-reversal":
        import scanners.scanner_d_sr_reversal as scanner
    else:
        return []

    # Patch MIN_RR to loosen the RR gate (this is per-process, no race)
    scanner.MIN_RR = NEAR_ZERO_RR

    results = []
    for ticker in tickers:
        # Load from parquet cache
        parquet_path = cache_dir / f"{ticker}.parquet"
        if not parquet_path.exists():
            continue
        try:
            df = pd.read_parquet(parquet_path)
            if asset_class == "stock":
                df = df[df.index >= VALID_SIGNAL_START]
        except Exception:
            continue
        if len(df) < 100:
            continue

        try:
            signals = scanner.scan(df, ticker)
        except Exception:
            continue
        if not signals:
            continue

        latest = signals[-1]
        most_recent_bar_date = str(df.index[-1])[:10]
        if str(latest["date"])[:10] != most_recent_bar_date:
            continue  # not today's bar

        rr = _rr_from_signal(latest)
        if rr is None:
            continue
        if rr >= original_rr:
            continue  # actually qualifies — not a near miss

        results.append({
            "strategy_id": strategy_name,
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

    return results


# ── Orchestration ───────────────────────────────────────────────────────────

def _get_original_rr(strategy_name: str) -> float:
    """Get the original MIN_RR for a strategy (before patching)."""
    if strategy_name == "STR-A-ma-pullback-fibonacci":
        import scanners.scanner_a_ma_pullback as s
    elif strategy_name == "STR-B-macd-histogram-divergence":
        import scanners.scanner_b_macd_divergence as s
    elif strategy_name == "STR-D-sr-role-reversal":
        import scanners.scanner_d_sr_reversal as s
    else:
        return 3.0
    return s.MIN_RR


def _build_tasks(stock_tickers: list[str], crypto_tickers: list[str],
                  include_stocks: bool, include_crypto: bool) -> list[dict]:
    """Build task list: one task per (strategy × asset_class × chunk)."""
    tasks = []

    for strategy_name in STRATEGY_NAMES:
        original_rr = _get_original_rr(strategy_name)

        if include_stocks and stock_tickers:
            # Split stock tickers into chunks for load balancing
            chunk_size = max(1, len(stock_tickers) // CHUNKS_PER_BATCH)
            for i in range(0, len(stock_tickers), chunk_size):
                chunk = stock_tickers[i:i + chunk_size]
                tasks.append({
                    "strategy_name": strategy_name,
                    "tickers": chunk,
                    "asset_class": "stock",
                    "cache_dir": str(STOCK_CACHE_DIR),
                    "original_rr": original_rr,
                })

        if include_crypto and crypto_tickers:
            chunk_size = max(1, len(crypto_tickers) // CHUNKS_PER_BATCH)
            for i in range(0, len(crypto_tickers), chunk_size):
                chunk = crypto_tickers[i:i + chunk_size]
                tasks.append({
                    "strategy_name": strategy_name,
                    "tickers": chunk,
                    "asset_class": "crypto",
                    "cache_dir": str(CRYPTO_CACHE_DIR),
                    "original_rr": original_rr,
                })

    return tasks


def scan_near_misses_parallel(include_stocks: bool = True,
                               include_crypto: bool = True) -> list[dict]:
    """Run near-miss scan in parallel across CPU cores."""
    stock_tickers = list(load_all_stocks().keys()) if include_stocks else []
    crypto_tickers = list(load_all_crypto().keys()) if include_crypto else []

    tasks = _build_tasks(stock_tickers, crypto_tickers, include_stocks, include_crypto)

    if not tasks:
        return []

    n_workers = min(os.cpu_count() or 2, len(tasks))
    all_results = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_scan_chunk, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                print(f"  Worker error: {e}", file=sys.stderr)

    all_results.sort(key=lambda r: r["rr_gap"])

    # Filter out tickers whose previously-posted near-miss already stopped out
    # (the trade already played out — no point showing it again)
    all_results = filter_near_misses(all_results, STOCK_CACHE_DIR)

    return all_results


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

    all_results = scan_near_misses_parallel(
        include_stocks=include_stocks,
        include_crypto=include_crypto,
    )

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
