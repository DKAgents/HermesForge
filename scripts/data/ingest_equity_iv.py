"""ingest_equity_iv.py — HermesForge US-187: equity ATM implied volatility (yfinance).

Daily ingestion of ATM IV per traded stock into iv_store.equity_atm_iv. Reads the
``impliedVolatility`` column yfinance already returns for each option strike
(IBKR sourced) — NO Black-Scholes solve (§2.3). Per ticker, per snapshot:

  * pick the expiry nearest a FIXED 30-calendar-day target (flag F-E resolved
    to ~30d, not the ~35d options_recommender default),
  * ATM strike = nearest underlying (spot from fast_info.lastPrice or
    previousClose),
  * atm_iv = average(call.impliedVolatility, put.impliedVolatility) at ATM.

IV RANK is derived at READ from the accumulated 252-snapshot (1y daily) series,
never stored as a row. yfinance is rate-limited and occasionally flaky, so each
ticker is idempotent-append + skip-on-empty (NEVER fabricate a chain).

EQUITY UNIVERSE — deviation note (spec §2.3 pointed at hermes_config.universe,
which is CRYPTO-ONLY and read-only). The traded stock universe lives in
capture_sweep_signals.py STOCK_SYMBOLS (the live STR-Q sweep list). Reused here
verbatim as the single load-bearing equity list; not re-listed anywhere else.

Usage:
    python3 ingest_equity_iv.py [--dry-run] [--ticker AAPL NVDA ...]
"""

from __future__ import annotations

import argparse
import sys
import time
import pathlib
import datetime as _dt
import warnings

import yfinance as yf

import iv_store

# yfinance 1.7.0 + pandas 3.1.0 emit a noisy inplace-deprecation warning on
# every chain fetch. Suppress it (our code uses no inplace ops) so the daily
# cron output stays "summary + failures" only.
warnings.filterwarnings("ignore", message=".*inplace.*")

# Traded stock universe = STR-Q sweep (capture_sweep_signals.STOCK_SYMBOLS).
EQUITY_UNIVERSE = [
    "SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META",
    "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST",
]

TARGET_DTE = 30                  # flag F-E: fixed ~30d ATM IV target
DAY_BUCKET_MS = 24 * 3600 * 1000
SLEEP_BETWEEN_TICKERS = 0.3


def _day_bucket(now_ms: int) -> int:
    """UTC-midnight bucket so re-runs the same calendar day are idempotent."""
    return (now_ms // DAY_BUCKET_MS) * DAY_BUCKET_MS


def _now_ms() -> int:
    return int(time.time() * 1000)


def _nearest_expiry(expirations, target_dte: int = TARGET_DTE):
    """Expiry date string (from t.options) closest to target_dte calendar days."""
    today = _dt.datetime.now(_dt.timezone.utc).date()
    best, best_diff = None, float("inf")
    for exp_str in expirations:
        try:
            d = _dt.datetime.strptime(exp_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        dte = (d - today).days
        diff = abs(dte - target_dte)
        if diff < best_diff:
            best, best_diff = exp_str, diff
    return best


def _atm_iv(ticker: str) -> dict | None:
    """Fetch ATM IV for one ticker. Returns {ticker, ts, atm_iv, spot, expiry}
    or None if the chain is empty/flaky (skip, never fabricate)."""
    t = yf.Ticker(ticker)
    try:
        expirations = t.options
        info = t.fast_info
        spot = info.get("lastPrice") or info.get("previousClose")
    except Exception:
        return None
    if not expirations or not spot:
        return None

    exp_str = _nearest_expiry(expirations)
    if exp_str is None:
        return None
    try:
        chain = t.option_chain(exp_str)
    except Exception:
        return None

    calls, puts = chain.calls, chain.puts
    if calls.empty or puts.empty:
        return None

    # ATM strike = nearest underlying across the call grid (calls/puts share it).
    atm_strike = calls.iloc[(calls["strike"] - spot).abs().argmin()]["strike"]
    c = calls[calls["strike"] == atm_strike]
    p = puts[puts["strike"] == atm_strike]
    if c.empty or p.empty:
        return None
    try:
        c_iv = float(c["impliedVolatility"].iloc[0])
        p_iv = float(p["impliedVolatility"].iloc[0])
    except (TypeError, ValueError, IndexError):
        return None
    if not (0.0 < c_iv < 20.0) or not (0.0 < p_iv < 20.0):
        return None  # IV is a fraction; reject implausible/missing values
    atm_iv = 0.5 * (c_iv + p_iv)
    return {"ticker": ticker, "ts": _day_bucket(_now_ms()),
            "atm_iv": atm_iv, "spot": float(spot), "expiry": exp_str}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest equity ATM IV (yfinance) into iv_store.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ticker", nargs="*", default=list(EQUITY_UNIVERSE))
    args = parser.parse_args()

    # F-E: atm_iv stored as a FRACTION (yfinance impliedVolatility is 0.xx);
    # convert to % at ingest so the store is uniformly percent units (like
    # Deribit mark_iv). Read path (iv_rank) expects %.
    mode = "DRY-RUN" if args.dry_run else "INGEST"
    conn = iv_store.open_store()
    try:
        ok = 0
        total = 0
        for i, ticker in enumerate(args.ticker):
            row = _atm_iv(ticker)
            if row is None:
                print(f"  {ticker}: skip (empty/flaky chain)")
            elif args.dry_run:
                print(f"  {ticker}: would insert atm_iv={row['atm_iv']*100:.1f}% "
                      f"spot={row['spot']} expiry={row['expiry']}")
                ok += 1
            else:
                row["atm_iv"] = row["atm_iv"] * 100.0   # fraction -> percent
                n = iv_store.append_equity_atm_iv(conn, [row])
                ok += 1
                total += n
            if i < len(args.ticker) - 1:
                time.sleep(SLEEP_BETWEEN_TICKERS)
    finally:
        conn.close()
    if args.dry_run:
        print(f"[{mode}] {ok}/{len(args.ticker)} tickers resolved")
    else:
        print(f"[{mode}] {ok}/{len(args.ticker)} tickers ok, new_rows={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())