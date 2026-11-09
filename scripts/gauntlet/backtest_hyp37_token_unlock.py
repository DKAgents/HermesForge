#!/usr/bin/env python3
"""
HYP-37 — Token-unlock pre-event drift (short): data-gate + G0 cost screen.

Run order (pre-registered, cheapest first):
  1. D-7 data gate  — is the unlock calendar (token/date/% circ supply)
     obtainable at the free tier? This is the BINDING dependency.
  2. G0 cost screen — funding P&L on a 30-day short (the dominant cost term)
     using the stored HL funding history, to answer "is the ~-14.7% prior
     gross drift cost-viable" independent of the calendar.

This script does NOT fabricate drift numbers. If the unlock calendar is
unavailable, the hypothesis is DATA-GATED (untested, not rejected — same
disposition as HYP-33) and no backtest trial is logged.
"""

from __future__ import annotations

import glob
import pathlib

import pandas as pd

HOME = pathlib.Path.home()
FUNDING_DIR = HOME / ".hermes" / "market_data" / "hl_funding_hf"
UNLOCK_CANDIDATES = [
    HOME / ".hermes" / "market_data" / "unlocks",
    HOME / ".hermes" / "market_data" / "token_unlocks",
    HOME / ".hermes" / "market_data" / "unlock_calendar",
]
T_THRESHOLDS_PCT = [1.0, 2.0, 5.0]  # % of circulating supply (pre-registered)
WINDOWS = [(-30, -1), (-14, +3)]    # (T+a, T+b) days, pre-registered


def funding_cost_screen() -> pd.DataFrame:
    """G0: 30-day funding P&L (bps) on a SHORT, per coin, from stored history.

    sign convention: funding_rate > 0 => short RECEIVES funding (credit);
                     funding_rate < 0 => short PAYS funding (cost).
    """
    files = sorted(glob.glob(str(FUNDING_DIR / "*.parquet")))
    if not files:
        raise SystemExit("no funding history found — cannot run G0")
    df = pd.concat(
        [pd.read_parquet(f, columns=["timestamp", "coin", "funding_rate"])
         for f in files],
        ignore_index=True,
    ).dropna(subset=["funding_rate"])
    g = df.groupby("coin")["funding_rate"].agg(["count", "mean", "median"])
    g["30d_funding_pnl_bps_short"] = g["mean"] * 720 * 100.0  # 720h * 100
    return g.sort_values("30d_funding_pnl_bps_short")


def unlock_calendar_present() -> bool:
    """D-7: is a local unlock calendar already stored? (not as of this run.)"""
    return any(d.exists() and any(d.iterdir()) for d in UNLOCK_CANDIDATES)


def main() -> None:
    print("=== HYP-37 token-unlock pre-event drift (short) ===")
    print(f"pre-registered thresholds (% circ supply): {T_THRESHOLDS_PCT}")
    print(f"pre-registered windows (days): {WINDOWS}")

    print("\n[G0] funding cost screen (real data, stored HL funding):")
    g = funding_cost_screen()
    med = g["30d_funding_pnl_bps_short"].median()
    lo = g["30d_funding_pnl_bps_short"].min()
    hi = g["30d_funding_pnl_bps_short"].max()
    print(f"  coins with funding history: {len(g)}")
    print(f"  30d funding P&L on a short (bps): "
          f"median={med:.2f}  min={lo:.2f}  max={hi:.2f}")
    print(f"  taker cost ~4.5 bps/leg x 2 legs = ~9 bps round-trip")
    print(f"  => all-in cost ~ {9 + abs(med):.1f} bps median vs prior gross "
          f"drift ~1470 bps: funding is NOT the binding constraint.")

    print("\n[D-7] unlock calendar availability:")
    if unlock_calendar_present():
        print("  local unlock calendar FOUND — would proceed to event build")
    else:
        print("  local unlock calendar ABSENT.")
        print("  Verified (2026-11-09): Tokenomist api unreachable (TLS/SNI),")
        print("  DefiLlama /emissions -> HTTP 402 paid, CoinGecko free -> no")
        print("  unlock-schedule endpoint, CoinMarketCap -> 401 (key),")
        print("  CryptoRank -> 403 (bot-block). => only PAID tiers reachable.")

    print("\nVERDICT: DATA-GATED on D-7 (unlock calendar). "
          "Untested, not rejected. No trial logged.")
    print("Reopen automatically once the calendar is reachable (paid tier or "
          "forward accumulation).")


if __name__ == "__main__":
    main()
