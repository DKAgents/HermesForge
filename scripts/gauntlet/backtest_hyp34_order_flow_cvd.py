"""backtest_hyp34_order_flow_cvd.py — HYP-34 order-flow imbalance (CVD).

Read-only research driver. HYP-34 pre-registers the classic microstructure
signal: CUMULATIVE VOLUME DELTA (CVD = cumulative aggressive-buy − aggressive-
sell notional) and its short-window rate-of-change, tested as a TAKER to see
whether a melt-maker's edge survives taker cost.

DATA-REALITY DISCLOSURE (first-class finding, not a footnote):
  The FUll tick-trades dataset referenced in HYP-34's data_dependencies
  ("~/.hermes/market_data (ironflow/hyperliquid-trades), 5.8GB daily files")
  is **NOT on disk**. Exhaustive search (find / -type f -size +3G; +100M
  parquet; -iname '*ironflow*'|'*hyperliquid-trades*'|'*trades*'; maxdepth
  scans) finds no such dataset. The ONLY aggressor-side (buy/sell) tick source
  present is the LIQUIDATION fills store
  (~/.hermes/market_data/hl_liquidations_hf/data/fills/*.parquet, 18 months,
  2025-05-25 → 2026-10-31). A liquidation is a forced taker order — its `side`
  IS the aggressor direction (a short-liquidation is closed by aggressive BUYS;
  a long-liquidation by aggressive SELLS) — but it is the *forced-flow subset*
  of aggressive flow, NOT full order flow.

  Consequently this driver tests a **liquidation-flow CVD** (the forced
  component of CVD) as the closest available proxy, and reports the full-CVD
  question as UNMEASURABLE with the data on disk. This is a data-availability
  boundary, not a tuning choice.

Pre-registered operationalization (FIXED — no tuning):
  * Signal: CVD level C[t] = cumsum(buy−sell notional); primary tradable signal
    = its short-window change  D[t] = C[t] − C[t−K]  (the net flow of the
    trailing K bars). Sign(D) → same-direction continuation over next h bars.
  * Intraday arm: BTC-PERP only (ETH/SOL 5m bars begin 2026-10-15 → <16d
    overlap, insufficient — same data constraint as HYP-27). K = 12 bars (1h);
    horizons h ∈ {1, 6, 12} bars = 5m/30m/1h (entry = bar-t close).
  * Daily arm: BTC-PERP + ETH-PERP pooled, full 18-month window; daily marks
    from crypto/BTC.parquet + crypto/ETH.parquet. K ∈ {1d, 3d} trailing net;
    horizon h = 1d (entry = day-t close).
  * Arms (both reported): H1 continuation (taker, sign(D)*ret) and H2 reversal
    (maker-side capture, −sign(D)*ret). pnl_H2 == −pnl_H1 by construction.
  * Cost: taker round-trip 11.5bps intraday (2×4.5bps taker + 2.5bps adverse
    slip) / 12bps 1d (add 0.5bps funding), charged ONCE per leg per rebalance;
    maker round-trip 3bps (2×1.5bps maker), no funding credited (conservative —
    the maker's spread income is NOT credited, only the fee charged). G0
    fail-closed hurdle = 45bps gross/leg. No leverage. LIVE off.

Writes one trials-ledger entry per (arm, horizon) with a FRESH param_hash.

Usage: python3 backtest_hyp34_order_flow_cvd.py [--no-write]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import pathlib
import sqlite3
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trials_ledger as ledger                              # noqa: E402
from fee_source import get_round_trip_bps, get_taker_bps, get_maker_bps  # noqa: E402

FILLS_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_liquidations_hf" / "data" / "fills"
BARS_DB = pathlib.Path.home() / ".hermes" / "market_data" / "hl_bars" / "bars_5m.db"
CRYPTO_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "crypto"

# ── Pre-registered constants (FIXED — no tuning) ─────────────────────────────
MARKET = "BTC-PERP"
TICKER = "BTC"
INTRA_K = 12                   # CVD rate-of-change window (bars) = 1h
INTRA_HORIZONS = (1, 6, 12)    # 5m / 30m / 1h
DAILY_K = (1, 3)               # trailing nets (days) for the slower 1d version
DAILY_HOLD = 1                 # 1d forward
TAKER_BPS = 4.5                # per leg (fee_source crypto base-tier floor)
MAKER_BPS = 1.5
SLIP_BPS = 2.5
FUNDING_BPS_1D = 0.5
COST_RT_INTRADAY = 2 * TAKER_BPS + SLIP_BPS            # 11.5bps
COST_RT_1D = 2 * TAKER_BPS + SLIP_BPS + FUNDING_BPS_1D  # 12bps
COST_MAKER_RT = 2 * MAKER_BPS                           # 3bps
G0_HURDLE_BPS = 45.0            # fail-closed 4x anchor


# ────────────────────────────────────────────────────────────────────────────
def _load_fills(markets: list[str]) -> pd.DataFrame:
    """Liquidation fills -> [market, ts_ms, buy, sell] for the given markets."""
    files = sorted(pathlib.Path(FILLS_DIR).glob("*.parquet"))
    if not files:
        raise SystemExit(f"no liquidation fills under {FILLS_DIR}")
    fcols = ["timestamp", "market", "side", "notional_usd"]
    f = pd.concat([pd.read_parquet(p, columns=fcols) for p in files],
                  ignore_index=True)
    f = f[f["market"].isin(markets)].copy()
    f["ts_ms"] = f["timestamp"].astype("int64")
    f["buy"] = np.where(f["side"] == "buy", f["notional_usd"], 0.0)
    f["sell"] = np.where(f["side"] == "sell", f["notional_usd"], 0.0)
    return f[["market", "ts_ms", "buy", "sell"]]


def _tstat(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return 0.0
    sd = x.std(ddof=1)
    return float(x.mean() / (sd / np.sqrt(len(x)))) if sd > 0 else 0.0


def _decluster(idx: np.ndarray, h: int) -> np.ndarray:
    """Keep indices separated by >= h bars (conservative effective-N)."""
    kept, last = [], -10 ** 12
    for i in idx:
        if int(i) - last >= h:
            kept.append(int(i))
            last = int(i)
    return np.array(kept, dtype=int)


# ── Intraday (BTC 5m) ────────────────────────────────────────────────────────
def build_intraday() -> pd.DataFrame:
    f = _load_fills([MARKET])
    f["bucket"] = (f["ts_ms"] // 300_000) * 300_000
    grp = (f.groupby("bucket", sort=False).agg(buy=("buy", "sum"), sell=("sell", "sum"))
           .reset_index())
    grp["net"] = grp["buy"] - grp["sell"]

    con = sqlite3.connect(BARS_DB)
    bars = pd.read_sql_query(
        f"SELECT ts, close FROM bars WHERE ticker='{TICKER}' ORDER BY ts", con)
    con.close()

    df = bars.merge(grp[["bucket", "buy", "sell", "net"]],
                    left_on="ts", right_on="bucket", how="left").drop(columns="bucket")
    for c in ("buy", "sell", "net"):
        df[c] = df[c].fillna(0.0)
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def intraday_signals(df: pd.DataFrame, k: int) -> pd.DataFrame:
    df = df.copy()
    df["cvd"] = df["net"].cumsum()                 # C[t] level
    df["roc"] = df["net"].rolling(k, min_periods=k).sum()   # D[t] = C[t]-C[t-k]
    return df


# ── Daily (BTC + ETH) ────────────────────────────────────────────────────────
def build_daily() -> pd.DataFrame:
    f = _load_fills(["BTC-PERP", "ETH-PERP"])
    f["day"] = pd.to_datetime(f["ts_ms"], unit="ms", utc=True).dt.normalize()
    f["ticker"] = f["market"].str.replace("-PERP", "", regex=False)
    net = (f.groupby(["ticker", "day"], sort=False)
            .agg(buy=("buy", "sum"), sell=("sell", "sum")).reset_index())
    net["net"] = net["buy"] - net["sell"]

    rows = []
    for tick in ("BTC", "ETH"):
        px = pd.read_parquet(CRYPTO_DIR / f"{tick}.parquet")
        close = px["close"].rename("close")
        idx = pd.to_datetime(close.index).tz_localize("UTC").rename("day")
        c = close.copy(); c.index = idx
        n = net[net["ticker"] == tick].set_index("day")
        merged = (c.to_frame().join(n[["buy", "sell", "net"]], how="left")
                  .sort_index())
        for col in ("buy", "sell", "net"):
            merged[col] = merged[col].fillna(0.0)
        merged["ticker"] = tick
        rows.append(merged.reset_index())
    df = pd.concat(rows, ignore_index=True).sort_values(["ticker", "day"]).reset_index(drop=True)
    return df


def daily_signals(df: pd.DataFrame, k: int) -> pd.DataFrame:
    out = []
    for tick, g in df.groupby("ticker", sort=False):
        g = g.sort_values("day").copy()
        g["cvd"] = g["net"].cumsum()
        g["roc"] = g["net"].rolling(k, min_periods=k).sum()
        out.append(g)
    return pd.concat(out, ignore_index=True)


# ── Raw + traded evaluation ──────────────────────────────────────────────────
def forward_return_close(close: np.ndarray, h: int) -> np.ndarray:
    return np.roll(close, -h) / close - 1.0


def run_traded(sig: np.ndarray, sig_valid: np.ndarray, ret: np.ndarray,
               roll: np.ndarray, h: int, direction: str, cost_bps: float) -> dict:
    """sig = sign(D) (+1/-1); ret = forward return; roll = cumprod return for R."""
    mask = sig_valid & np.isfinite(ret)
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return {"n": 0, "gross_bps": np.nan, "net_bps": np.nan, "t_stat": 0.0,
                "t_indep": 0.0, "win": np.nan, "n_indep": 0, "g0": False,
                "sum_net_bps": np.nan}
    s = sig[idx]
    r = ret[idx]
    pnl = s * r if direction == "continuation" else -s * r
    gross_bps = float(np.mean(pnl)) * 1e4
    net_bps = float(np.mean(pnl - cost_bps / 1e4)) * 1e4
    t = _tstat(pnl)
    indep = _decluster(idx, h)
    pnl_i = pnl[np.isin(idx, indep)]
    t_indep = _tstat(pnl_i)
    win = float((pnl > 0).mean())
    g0 = gross_bps >= G0_HURDLE_BPS
    return {"n": int(len(pnl)), "gross_bps": gross_bps, "net_bps": net_bps,
            "t_stat": t, "t_indep": t_indep, "win": win,
            "n_indep": int(len(indep)), "g0": bool(g0),
            "sum_net_bps": float(np.sum(pnl - cost_bps / 1e4)) * 1e4}


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    xv, yv = x[m], y[m]
    if len(xv) < 2:
        return float("nan")
    xv = xv - xv.mean(); yv = yv - yv.mean()
    d = np.sqrt((xv ** 2).sum() * (yv ** 2).sum())
    return float((xv * yv).sum() / d) if d > 0 else float("nan")


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    taker = get_taker_bps("crypto")
    maker = get_maker_bps("crypto")
    rtb = get_round_trip_bps("crypto")
    print("=== HYP-34 order-flow imbalance (CVD) -> short-horizon continuation ===\n")
    print(f"fee_source: taker {taker:.1f}bps/leg, maker {maker:.1f}bps/leg, "
          f"round-trip all-in {rtb:.1f}bps")
    print(f"intraday cost {COST_RT_INTRADAY:.1f}bps RT; 1d cost {COST_RT_1D:.1f}bps RT; "
          f"maker-side {COST_MAKER_RT:.1f}bps RT; G0 hurdle {G0_HURDLE_BPS:.0f}bps")
    print("DATA DISCLOSURE: full tick-trades dataset ABSENT from disk -> this is a\n"
          "  LIQUIDATION-FLOW CVD (forced-flow proxy), not full order-flow CVD.\n")

    ledger_entries = []

    # ── 1. Intraday (BTC 5m) ─────────────────────────────────────────────────
    print("===== INTRADAY BTC (5m CVD) =====\n")
    df = build_intraday()
    df = intraday_signals(df, INTRA_K)
    fill_max = int(df.loc[df["net"] != 0, "ts"].max())
    df = df[df["ts"] <= fill_max].reset_index(drop=True)
    import datetime as _dt
    span = (str(_dt.datetime.fromtimestamp(int(df.ts.min()) / 1000, _dt.UTC).date()),
            str(_dt.datetime.fromtimestamp(int(df.ts.max()) / 1000, _dt.UTC).date()))
    print(f"bars: {len(df)} ({span[0]} -> {span[1]})  K={INTRA_K} bars (1h)")
    print(f"flow-bearing bars: {int((df['net']!=0).sum())} / {len(df)}")

    close = df["close"].to_numpy()
    roc = df["roc"].to_numpy()
    cvd = df["cvd"].to_numpy()
    valid = df["roc"].notna().to_numpy()

    print("\n  raw relationship (Pearson corr of CVD level / ROC vs fwd return):")
    for h in INTRA_HORIZONS:
        r = forward_return_close(close, h)
        print(f"    h={h*5:>2}m: corr(cvd_level, ret) = {_pearson(cvd, r):+.4f}   "
              f"corr(roc, ret) = {_pearson(roc, r):+.4f}")

    print("\n  traded arms (BTC intraday):")
    print(f"  {'arm':>4} {'horizon':>7} | {'gross':>9} {'net_taker':>10} "
          f"{'t_indep':>8} {'win':>6} {'n':>7} {'G0?':>4}")
    for h in INTRA_HORIZONS:
        r = forward_return_close(close, h)
        sig = np.sign(roc)
        sv = valid & (sig != 0)
        for direction, dlabel, cost in [("continuation", "H1", COST_RT_INTRADAY),
                                        ("reversal", "H2", COST_MAKER_RT)]:
            res = run_traded(sig, sv, r, r, h, direction, cost)
            label = "taker" if direction == "continuation" else "maker"
            print(f"  {dlabel} {h*5:>5}m | {res['gross_bps']:>+9.3f} "
                  f"{res['net_bps']:>+10.3f} {res['t_indep']:>+8.2f} "
                  f"{res['win']:>6.3f} {res['n']:>7} {'Y' if res['g0'] else 'N':>4}")
            ledger_entries.append({
                "arm": "intraday", "direction": direction, "horizon_bars": h,
                "horizon_min": h * 5, "k_bars": INTRA_K, "res": res,
                "period": span, "universe": "BTC",
            })

    # ── 2. Daily (BTC + ETH, full 18mo) ──────────────────────────────────────
    print("\n===== DAILY (BTC + ETH, full window) =====\n")
    ddf = build_daily()
    d_span = (str(ddf["day"].min().date()), str(ddf["day"].max().date()))
    print(f"daily panel: {d_span[0]} -> {d_span[1]}  ({ddf.shape[0]} rows)")
    for k in DAILY_K:
        d = daily_signals(ddf, k)
        # restrict to signal-measurable window (K-day warmup) and fills span
        close_all = d["close"].to_numpy()
        roc_all = d["roc"].to_numpy()
        valid_all = d["roc"].notna().to_numpy()
        print(f"\n  K={k}d trailing net (slower version):")
        # forward 1d return per day, pooled across ticker via concat order
        r_all = np.full_like(close_all, np.nan)
        for tick in ("BTC", "ETH"):
            sub = d[d["ticker"] == tick].reset_index(drop=True)
            c = sub["close"].to_numpy()
            rr = forward_return_close(c, DAILY_HOLD)
            idxs = d.index[d["ticker"] == tick]
            r_all[idxs] = rr
        print(f"    corr(cvd_level, ret1d) = {_pearson(d['cvd'].to_numpy(), r_all):+.4f}   "
              f"corr(roc, ret1d) = {_pearson(roc_all, r_all):+.4f}")
        sig = np.sign(roc_all)
        sv = valid_all & (sig != 0) & np.isfinite(r_all)
        print(f"    traded (1d fwd):")
        for direction, dlabel, cost in [("continuation", "H1", COST_RT_1D),
                                        ("reversal", "H2", COST_MAKER_RT)]:
            res = run_traded(sig, sv, r_all, r_all, DAILY_HOLD, direction, cost)
            label = "taker" if direction == "continuation" else "maker"
            print(f"      {dlabel} ({label}): gross {res['gross_bps']:+.3f} bps  "
                  f"net {res['net_bps']:+.3f} bps  t_indep {res['t_indep']:+.2f}  "
                  f"win {res['win']:.3f}  n {res['n']}  G0 {'Y' if res['g0'] else 'N'}")
            ledger_entries.append({
                "arm": "daily", "direction": direction, "horizon_days": DAILY_HOLD,
                "k_days": k, "res": res, "period": d_span, "universe": "BTC+ETH",
            })

    # ── 3. Trials ledger writes (fresh param_hash per cell) ──────────────────
    universe_hash_intra = hashlib.sha256(f"{MARKET}/{TICKER}".encode()).hexdigest()
    universe_hash_daily = hashlib.sha256("BTC-PERP+ETH-PERP".encode()).hexdigest()
    print("\n===== 3. Trials ledger writes =====\n")
    for e in ledger_entries:
        r = e["res"]
        universe_hash = universe_hash_intra if e["arm"] == "intraday" else universe_hash_daily
        param_dict = {
            "signal": "liquidation_flow_cvd_roc",
            "signal_def": ("sign of short-window CVD change (forced buy−sell notional "
                           "accumulated over trailing K bars), NOT full order-flow CVD "
                           "— full trades dataset absent from disk"),
            "arm": e["arm"],
            "direction": e["direction"],
            "data_source": ("hl_liquidations_hf fills (forced flow) + "
                            "hl_bars 5m / crypto daily marks"),
        }
        if e["arm"] == "intraday":
            param_dict["horizon_bars"] = e["horizon_bars"]
            param_dict["horizon_min"] = e["horizon_min"]
            param_dict["k_bars"] = INTRA_K
            param_dict["cost_bps"] = COST_RT_INTRADAY if e["direction"] == "continuation" else COST_MAKER_RT
        else:
            param_dict["horizon_days"] = DAILY_HOLD
            param_dict["k_days"] = e["k_days"]
            param_dict["cost_bps"] = COST_RT_1D if e["direction"] == "continuation" else COST_MAKER_RT
        param_dict.update({
            "taker_bps": TAKER_BPS, "maker_bps": MAKER_BPS, "slip_bps": SLIP_BPS,
            "g0_hurdle_bps": G0_HURDLE_BPS,
            "no_lookahead": True, "leverage": "none_1x", "live": "off",
            "full_trades_absent": True,
        })
        param_hash = hashlib.sha256(
            json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
        result = {
            "construction": "cvd_rate_of_change_sign",
            "direction": e["direction"],
            "arm": e["arm"],
            "n_trades": r["n"],
            "n_indep": r["n_indep"],
            "mean_gross_bps": round(r["gross_bps"], 4),
            "mean_net_bps_realistic": round(r["net_bps"], 4),
            "t_stat_declustered": round(r["t_indep"], 4),
            "win_rate": round(r["win"] if np.isfinite(r["win"]) else 0.0, 6),
            "g0_clears_45bps": r["g0"],
            "sum_net_bps": round(r["sum_net_bps"], 4),
            "no_lookahead": True, "leverage": "none_1x", "live": "off",
            "full_trades_absent": True,
        }
        if not args.no_write:
            out = ledger.increment_trial("HYP-34", param_hash, universe_hash,
                                         e["period"][0], e["period"][1], result)
            print(f"  wrote {e['arm']}-{e['direction']}: "
                  f"param_hash={out['param_hash'][:16]}... "
                  f"chain_hash={out['chain_hash'][:16]}...")
        else:
            print(f"  [--no-write] {e['arm']}-{e['direction']}: "
                  f"param_hash={param_hash[:16]}...")

    ok, msg = ledger.verify_integrity()
    print(f"\nledger integrity: {ok} ({msg})")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())