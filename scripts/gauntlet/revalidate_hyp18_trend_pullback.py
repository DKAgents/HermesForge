"""revalidate_hyp18_trend_pullback.py — HYP-18 trend+pullback+momentum M5 scalp.

INDEPENDENT VERIFICATION (fast-fail) of a web-mined retail-TA scalping kit.
Pre-registered operationalization is FIXED in
trading/strategies/Hypotheses/HYP-18-trend-pullback-momentum-scalp.md:

  * Trend context: close > EMA(50) on M5 (longs in trend direction).
  * Pullback + momentum confirmation -> long.
  * Exit: +1.5R TP or 1-ATR/wick stop.

G0 cost-first KILL (pre-registered): median M5 |move| after the entry vs
4x all-in taker cost (12 bps crypto round-trip, fee_source). If the typical
5m move cannot clear friction, STOP — no G3 fill-realism run, no G4/G5.

Data: Hyperliquid's OWN 5m bars (persistent store, US-197), source='hyperliquid'
only (no okx_proxy — this is same-venue verification). Binding window is the
HL-native retention floor + accumulation: ~20d (~5.8k bars) for BTC and ETH.

No look-ahead (G0 is a pure data screen). Cost charged once via fee_source.
No leverage. LIVE off. Writes ONE trial to data/gauntlet/trials.jsonl.

Usage: python3 revalidate_hyp18_trend_pullback.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent), str(_THIS_DIR.parent / "data")):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import hl_bar_store as store                               # noqa: E402
import trials_ledger as ledger                             # noqa: E402
from fee_source import get_round_trip_bps                  # noqa: E402

# ── Pre-registered constants (FIXED) ────────────────────────────────────────
INSTRUMENTS = ["BTC", "ETH"]       # top-liquidity per hypothesis
TIMEFRAME = "5m"
GROSS_MULTIPLIER = 4.0             # G0: median |move| vs 4x all-in cost
FORWARD_HORIZONS = [1, 3, 5, 10]   # supporting forward-move horizons (bars)
ATR_PERIOD = 14                    # 1-ATR stop distance reference


def _median_abs_move(closes: np.ndarray) -> float:
    """median(|close[i]-close[i-1]|/close[i-1]) * 1e4 in bps (G0 module metric)."""
    moves = np.abs(np.diff(closes)) / closes[:-1] * 10000.0
    return float(np.median(moves))


def _median_forward_move(closes: np.ndarray, h: int) -> float:
    """median |h-bar forward return| in bps."""
    fwd = np.abs(closes[h:] / closes[:-h] - 1.0) * 10000.0
    return float(np.median(fwd))


def _median_atr_pct(df) -> float:
    """median ATR-14 as % of price, in bps."""
    c = df["close"].astype(float)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    tr = np.maximum(h.diff().abs(), np.maximum((h - l).abs(), l.diff().abs()))
    atr = tr.rolling(ATR_PERIOD).mean()
    return float(np.nanmedian(atr / c * 10000.0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-18 trend+pullback+momentum M5 scalp — G0 fast-fail ===\n")

    rtb = get_round_trip_bps("crypto")
    threshold = GROSS_MULTIPLIER * rtb
    print(f"crypto round-trip cost (fee_source) = {rtb:.1f} bps")
    print(f"G0 threshold (4x all-in taker)      = {threshold:.1f} bps\n")

    per_instrument: dict = {}
    any_pass = False
    for t in INSTRUMENTS:
        df = store.read_bars(t, TIMEFRAME)
        df = df[df["source"] == "hyperliquid"].reset_index(drop=True)
        if df.empty:
            print(f"{t}: NO hyperliquid 5m bars — skipping")
            per_instrument[t] = {"n_bars": 0}
            continue
        closes = df["close"].astype(float).to_numpy()
        n = len(closes)
        med1 = _median_abs_move(closes)
        fwd = {f"fwd{h}": _median_forward_move(closes, h) for h in FORWARD_HORIZONS}
        atr = _median_atr_pct(df)
        cost_drag_r = rtb / atr if atr > 0 else float("inf")

        passes = med1 >= threshold
        any_pass = any_pass or passes

        per_instrument[t] = {
            "n_bars": n,
            "min_ts": int(df["ts"].min()),
            "max_ts": int(df["ts"].max()),
            "median_abs_move_1bar_bps": round(med1, 4),
            "median_forward_move_bps": {f"{h}bar": round(v, 4) for h, v in fwd.items()},
            "median_atr14_bps": round(atr, 4),
            "cost_drag_R_per_trade": round(cost_drag_r, 4),
        }

        print(f"{t}: {n} HL-native 5m bars")
        print(f"  median |1-bar move|      = {med1:6.2f} bps  vs 4x cost {threshold:.0f} bps")
        for h in FORWARD_HORIZONS[1:]:
            print(f"  median |{h}-bar fwd move| = {fwd[f'fwd{h}']:6.2f} bps")
        print(f"  median ATR-14 (1-ATR stop)= {atr:6.2f} bps")
        print(f"  cost drag per trade       = {cost_drag_r:6.2f} R  (12 bps / 1-ATR stop)")
        print(f"  -> G0 {'PASS' if passes else 'FAIL'}")
        print()

    g0_pass = any_pass
    print("=" * 60)
    if not g0_pass:
        print("G0 KILL TRIGGERED: median M5 |move| cannot clear 4x all-in taker cost.")
        print("FAST-FAIL — no G3 fill-realism, no G4/G5 escalation.")
    else:
        print("G0 passed unexpectedly — would proceed to G3.")
    print("=" * 60)

    # ── write trial (counts toward G5 regardless of fast-fail) ─────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "trend_pullback_momentum_scalp_M5",
        "instruments": INSTRUMENTS,
        "timeframe": TIMEFRAME,
        "venue": "hyperliquid",
        "entry": "close>EMA50 + pullback + momentum confirmation -> long",
        "exit": "+1.5R TP or 1-ATR/wick stop",
        "g0": {"metric": "median_abs_move_1bar_bps", "threshold": "4x all-in taker",
               "round_trip_bps": rtb, "threshold_bps": threshold},
        "cost": "fee_source_round_trip",
        "leverage": "none",
        "live": "off",
    }, sort_keys=True).encode()).hexdigest()
    universe_str = ",".join(sorted(INSTRUMENTS))
    universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()

    result = {
        "construction": "trend_pullback_momentum_scalp_M5",
        "gate_reached": "G0",
        "g0_pass": bool(g0_pass),
        "fast_fail": not g0_pass,
        "round_trip_bps": round(rtb, 4),
        "g0_threshold_bps": round(threshold, 4),
        "per_instrument": per_instrument,
        "trade_count": 0,           # no G3 run on fast-fail
        "avg_r": None,
        "no_lookahead": True,
        "leverage": "none",
        "live": "off",
        "data_window_note": "HL-native 5m only (~20d, ~5.8k bars BTC/ETH); source='hyperliquid'",
    }

    # period from observed data
    all_min = min(per_instrument[t].get("min_ts") for t in INSTRUMENTS
                  if per_instrument[t].get("min_ts"))
    all_max = max(per_instrument[t].get("max_ts") for t in INSTRUMENTS
                  if per_instrument[t].get("max_ts"))
    period_start = pd_ts_date(all_min)
    period_end = pd_ts_date(all_max)

    if not args.no_write:
        e = ledger.increment_trial("HYP-18", param_hash, universe_hash,
                                   period_start, period_end, result)
        print(f"\nwrote trial HYP-18  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


def pd_ts_date(ts_ms: int) -> str:
    import pandas as pd
    return pd.to_datetime(ts_ms, unit="ms").strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())
