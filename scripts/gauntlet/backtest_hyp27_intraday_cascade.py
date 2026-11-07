"""backtest_hyp27_intraday_cascade.py — HYP-27 intraday liquidation cascade.

Read-only research driver. Measures the SUB-DAILY aftermath of a liquidation
CLUSTER that HYP-26's daily operationalization could not see.

Pre-registered operationalization (FIXED — do NOT tune):
  * Universe: BTC only. The 5m bar store is near-full for BTC from ~2026-06-15;
    ETH/SOL 5m bars begin 2026-10-15, leaving a ~16-day overlap with the
    liquidation window (ends 2026-10-30) — INSUFFICIENT for a trailing
    distribution. Flagged as a DATA-CONSTRAINED first look (~4.5 months BTC).
  * Net flow: aggregate liquidation FILLS (market == "BTC-PERP") to 5m buckets,
      net = buy_notional - sell_notional.  A long-liquidation is closed by
      SELLS -> net sell = forced (downward) pressure.
  * Cluster: a 5m bucket whose |net| is in the TOP-DECILE (>= 90th percentile)
      of the market's own TRAILING distribution OF FLOW-BEARING BUCKETS (net !=
      0). Trailing window = 30 days (8640 5m bars, min MIN_FLOW_EVENTS events),
      EXCLUDING the current bar (the 90th percentile is evaluated on bars
      strictly BEFORE the cluster bar -> no look-ahead). Flow-bearing-only is
      NOT a tuning choice: only ~11% of BTC 5m buckets carry any forced flow, so
      a literal "top-decile over ALL buckets (incl. empty)" would give a ~$0
      threshold and degenerate to "any liquidation at all", defeating
      "unusually large". The 30d window + flow-bearing scope is the fixed
      operationalization of the hypothesis's "trailing distribution"
      (pre-registered gap, committed here, hashed with the trial).
  * Forward return over h in {1, 6, 12, 24} bars (5m/30m/1h/2h), entry = close
      of the cluster bar (== first-bar open after close; 5m bars contiguous).
  * Arms (both reports): H1 continuation (forced-sell -> short; forced-buy ->
      long); H2 exhaustion (opposite). pnl_H1 = sign(net)*ret; pnl_H2 = -that.
  * Cost: 11.5bps round-trip (2 x 4.5bps taker + 2.5bps adverse slip; funding
      ~0 intraday) charged ONCE per trade. G0 hurdle = 45bps gross/leg (the
      fail-closed 4x anchor used across the gauntlet). No leverage. LIVE off.

Writes ONE trials-ledger entry per (arm, horizon) with a FRESH param_hash.

Usage: python3 backtest_hyp27_intraday_cascade.py [--no-write]
"""

from __future__ import annotations

import argparse
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

FILLS_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_liquidations_hf" / "data" / "fills"
BARS_DB = pathlib.Path.home() / ".hermes" / "market_data" / "hl_bars" / "bars_5m.db"

# ── Pre-registered constants (FIXED — no tuning) ─────────────────────────────
MARKET = "BTC-PERP"
TICKER = "BTC"
TRAIL_DAYS = 30                 # trailing window for the market's own distribution
TRAIL_BARS = TRAIL_DAYS * 288   # 8640 bars
DECILE_Q = 0.90                 # top-decile => 90th percentile of |net|
MIN_FLOW_EVENTS = 100           # min flow-bearing buckets needed in the trailing
                                # window for a stable 90th percentile
HORIZONS = (1, 6, 12, 24)       # 5m / 30m / 1h / 2h
TAKER_BPS = 4.5                 # per leg
SLIP_BPS = 2.5                  # adverse slip, charged once per round trip
COST_RT_BPS = 2 * TAKER_BPS + SLIP_BPS   # 11.5bps, funding ~0 intraday
G0_HURDLE_BPS = 45.0            # fail-closed 4x anchor


def load_data() -> pd.DataFrame:
    """Align BTC-PERP net liquidation flow onto the BTC 5m bar grid.

    Returns a DataFrame indexed by bar start ts (ms) with:
      open, close, net (buy-sell notional; 0 where no fills), buy, sell, n_trades
    """
    # liquidation fills -> 5m bucket of net notional
    fcols = ["timestamp", "market", "side", "notional_usd"]
    files = sorted(pathlib.Path(FILLS_DIR).glob("*.parquet"))
    if not files:
        raise SystemExit(f"no liquidation fills under {FILLS_DIR}")
    f = pd.concat([pd.read_parquet(p, columns=fcols) for p in files],
                  ignore_index=True)
    btc = f[f["market"] == MARKET].copy()
    # timestamps arrive as datetime64[ms, UTC] -> .astype(int64) yields epoch ms
    btc["ts_ms"] = btc["timestamp"].astype("int64")
    btc["bucket"] = (btc["ts_ms"] // 300_000) * 300_000
    btc["buy"] = np.where(btc["side"] == "buy", btc["notional_usd"], 0.0)
    btc["sell"] = np.where(btc["side"] == "sell", btc["notional_usd"], 0.0)
    grp = (btc.groupby("bucket", sort=False)
           .agg(buy=("buy", "sum"), sell=("sell", "sum"), n_trades=("ts_ms", "size"))
           .reset_index())
    grp["net"] = grp["buy"] - grp["sell"]

    # 5m bars on the tradable grid
    con = sqlite3.connect(BARS_DB)
    bars = pd.read_sql_query(
        f"SELECT ts, open, close FROM bars WHERE ticker='{TICKER}' ORDER BY ts", con)
    con.close()

    df = bars.merge(grp[["bucket", "buy", "sell", "net", "n_trades"]],
                    left_on="ts", right_on="bucket", how="left").drop(columns="bucket")
    for c in ("buy", "sell", "net", "n_trades"):
        df[c] = df[c].fillna(0.0)
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def detect_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """Top-decile |net| vs the market's own TRAILING (30d) flow distribution.

    The trailing distribution is the |net notional| of FLOW-BEARING buckets only
    (net != 0). Including empty buckets (no liquidation) makes "top-decile"
    degenerate to "any liquidation at all" — only ~11% of BTC 5m buckets carry
    any forced flow, so the 90th percentile over ALL buckets is ~$0 and the
    cluster rule would lose all meaning.  threshold[t] = 90th percentile of
    flow-bearing |net| over bars [t-8640, t-1] (min MIN_FLOW_EVENTS events,
    evaluated strictly BEFORE the bar -> no look-ahead).  A bar is a cluster iff
    |net| >= threshold AND net != 0.
    """
    # NaN where no flow; pandas rolling.quantile skips NaN (verified on 3.1.0)
    flow_abs = df["net"].abs().where(df["net"] != 0.0)
    rq = flow_abs.rolling(TRAIL_BARS, min_periods=MIN_FLOW_EVENTS).quantile(DECILE_Q)
    thr = rq.shift(1)                     # eval strictly BEFORE the bar - no look-ahead
    df["abs_net"] = df["net"].abs()
    df["flow_count"] = (df["net"] != 0.0).astype(int).rolling(
        TRAIL_BARS, min_periods=1).sum().shift(1)
    df["threshold"] = thr
    df["cluster"] = (df["abs_net"] >= thr) & (df["net"] != 0.0) & thr.notna()
    df["sign"] = np.sign(df["net"])
    return df


def forward_return(df: pd.DataFrame, h: int) -> np.ndarray:
    """ret[h] = close[t+h]/close[t] - 1."""
    return df["close"].shift(-h).to_numpy() / df["close"].to_numpy() - 1.0


def _tstat(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return 0.0
    sd = x.std(ddof=1)
    return float(x.mean() / (sd / np.sqrt(len(x)))) if sd > 0 else 0.0


def decluster_idx(cluster_idx: np.ndarray, h: int) -> np.ndarray:
    """Keeps cluster bars separated by >= h bars so forward windows don't overlap
    (conservative effective-N for overlapping-horizon t-stats)."""
    kept = []
    last = -10 ** 12
    for i in cluster_idx:
        if int(i) - last >= h:
            kept.append(int(i))
            last = int(i)
    return np.array(kept, dtype=int)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-27 intraday liquidation cascade (sub-daily continuation) ===\n")
    print(f"universe: {MARKET}/{TICKER} ONLY (5m bars near-full from 2026-06-15).")
    print("ETH/SOL INELIGIBLE: 5m bars begin 2026-10-15 -> ~16d overlap with "
          "liquidation window < 30d trailing window. Flagged, not run.")
    print(f"cluster: |net| >= {DECILE_Q:.0%} pct of trailing {TRAIL_DAYS}d "
          f"({TRAIL_BARS} bar) FLOW-BEARING distribution (min {MIN_FLOW_EVENTS} "
          f"events; excl. current bar).")
    print(f"cost: {COST_RT_BPS:.1f}bps round-trip ({2*TAKER_BPS:.0f}bps taker + "
          f"{SLIP_BPS:.1f}bps slip); G0 hurdle {G0_HURDLE_BPS:.0f}bps gross/leg; "
          f"no leverage; LIVE off.\n")

    print("loading fills + bars ...")
    df = load_data()
    df = detect_clusters(df)
    # restrict to analysis window: starts when BTC bars begin, ends at last fill
    # (liquidation data ends 2026-10-31).  Bars run to present but forward-return
    # beyond the fill window is untestable signal.
    fill_bucket_max = int(df.loc[df["net"] != 0, "ts"].max())
    df = df[df["ts"] <= fill_bucket_max].reset_index(drop=True)
    clusters = df[df["cluster"]].copy()
    n_clusters = len(clusters)
    n_sell = int((clusters["net"] < 0).sum())
    n_buy = int((clusters["net"] > 0).sum())
    first_ts = int(df.loc[df["cluster"] & df["threshold"].notna(), "ts"].min())
    import datetime as _dt
    first_cluster = _dt.datetime.fromtimestamp(first_ts / 1000, _dt.UTC).date()
    print(f"  bars loaded: {len(df)}  (span {_dt.datetime.fromtimestamp(int(df.ts.min())/1000, _dt.UTC).date()} "
          f"-> {_dt.datetime.fromtimestamp(int(df.ts.max())/1000, _dt.UTC).date()})")
    print(f"  clusters detected: {n_clusters}  (forced-sell {n_sell}, forced-buy {n_buy})")
    print(f"  first cluster (post-warmup): {first_cluster}")
    med_thr = clusters["threshold"].median()
    print(f"  median cluster threshold: |net| >= ${med_thr:,.0f} notional")
    print(f"  DATA-CONSTRAINED: ~5-month look ({first_cluster} -> "
          f"{_dt.datetime.fromtimestamp(int(df.ts.max())/1000, _dt.UTC).date()})\n")

    # ── 1. raw relationship: forced-sell / forced-buy cluster -> fwd return ──
    print("===== 1. Raw directional relationship =====\n")
    print(f"{'horizon':>8} {'bars':>5} | {'sell->ret':>11} {'sell_t':>7} {'n':>6} "
          f"| {'buy->ret':>11} {'buy_t':>7} {'n':>6}")
    raw = {}
    for h in HORIZONS:
        ret = forward_return(df, h)
        idx = clusters.index.to_numpy()
        valid = idx[(idx + h) < len(df)]
        retv = ret[valid]
        netv = clusters.loc[valid, "net"].to_numpy()
        sell_m = netv < 0
        buy_m = netv > 0
        sell_r = retv[sell_m]; buy_r = retv[buy_m]
        raw[h] = {
            "sell_mean_bps": float(np.mean(sell_r)) * 1e4 if len(sell_r) else np.nan,
            "sell_t": _tstat(sell_r), "sell_n": int(len(sell_r)),
            "buy_mean_bps": float(np.mean(buy_r)) * 1e4 if len(buy_r) else np.nan,
            "buy_t": _tstat(buy_r), "buy_n": int(len(buy_r)),
        }
        print(f"{h*5:>7}m {h:>4} | {raw[h]['sell_mean_bps']:>+10.3f} "
              f"{raw[h]['sell_t']:>+7.2f} {raw[h]['sell_n']:>6} "
              f"| {raw[h]['buy_mean_bps']:>+10.3f} {raw[h]['buy_t']:>+7.2f} "
              f"{raw[h]['buy_n']:>6}")
    print("\n  sign guide: sell->ret <0 = continuation down (H1); >0 = reversal up (H2).")
    # unconditional drift control (all bars, same horizons)
    print("\n  market-drift control (unconditional fwd return, all bars):")
    drift = {}
    for h in HORIZONS:
        r = forward_return(df, h)
        r = r[~np.isnan(r)]
        drift[h] = {"mean_bps": float(np.mean(r)) * 1e4, "t": _tstat(r)}
        print(f"    {h*5:>6}m: {drift[h]['mean_bps']:+.3f} bps  (t {drift[h]['t']:+.2f})")

    # ── 2. traded arms (H1 continuation / H2 exhaustion) ─────────────────────
    print("\n===== 2. Traded arms (net of 11.5bps cost, charged once) =====\n")
    print(f"{'arm':>3} {'horizon':>7} {'bars':>4} | {'gross_bps':>10} {'net_bps':>10} "
          f"{'t_stat':>7} {'t_indep':>7} {'win':>6} {'n':>6} {'n_indep':>7} {'G0?':>4}")
    traded = {}
    for h in HORIZONS:
        ret = forward_return(df, h)
        idx = clusters.index.to_numpy()
        valid = idx[(idx + h) < len(df)]
        retv = ret[valid]
        netv = clusters.loc[valid, "net"].to_numpy()
        signv = np.sign(netv)
        for direction, dlabel in [("continuation", "H1"), ("reversal", "H2")]:
            if direction == "continuation":
                pnl = signv * retv           # forced-sell -> short -> same sign
            else:
                pnl = -signv * retv          # exhaustion
            gross_bps = float(np.mean(pnl)) * 1e4
            net_bps = float(np.mean(pnl - COST_RT_BPS / 1e4)) * 1e4
            t = _tstat(pnl)
            win = float((pnl > 0).mean())
            # declustered effective-N (windows separated by >= h bars)
            indep = decluster_idx(valid, h)
            t_indep = _tstat(pnl[np.isin(valid, indep)])
            n_indep = len(indep)
            gos = gross_bps >= G0_HURDLE_BPS
            traded[f"{dlabel}_{h}"] = {
                "direction": direction, "horizon_bars": h, "n": int(len(pnl)),
                "gross_bps": gross_bps, "net_bps": net_bps, "t_stat": t,
                "t_stat_declustered": t_indep, "n_indep": n_indep,
                "win_rate": win, "g0_clears": bool(gos),
                "median_net_bps": float(np.median(pnl - COST_RT_BPS / 1e4)) * 1e4,
            }
            print(f"{dlabel:>3} {h*5:>6}m {h:>4} | {gross_bps:>+10.3f} "
                  f"{net_bps:>+10.3f} {t:>+7.2f} {t_indep:>+7.2f} {win:>6.3f} "
                  f"{len(pnl):>6} {n_indep:>7} {'Y' if gos else 'N':>4}")

    # ── 3. write trials (fresh param_hash per arm/horizon) ───────────────────
    period_start = str(_dt.datetime.fromtimestamp(int(df.ts.min()) / 1000, _dt.UTC).date())
    period_end = str(_dt.datetime.fromtimestamp(int(df.ts.max()) / 1000, _dt.UTC).date())
    universe_hash = hashlib.sha256(f"{MARKET}/{TICKER}".encode()).hexdigest()

    print("\n===== 3. Trials ledger writes =====")
    for h in HORIZONS:
        for direction, dlabel in [("continuation", "H1"), ("reversal", "H2")]:
            r = traded[f"{dlabel}_{h}"]
            param_dict = {
                "signal": "intraday_liquidation_cluster_continuation",
                "signal_def": "5m |net liquidation notional| >= top-decile of trailing 30d distribution",
                "market": MARKET,
                "direction": direction,
                "horizon_bars": h,
                "horizon_min": h * 5,
                "entry": "cluster_bar_close",
                "trail_days": TRAIL_DAYS,
                "trail_bars": TRAIL_BARS,
                "decile_quantile": DECILE_Q,
                "flow_bearing_only": True,
                "min_flow_events": MIN_FLOW_EVENTS,
                "cost_bps_roundtrip": COST_RT_BPS,
                "taker_bps": TAKER_BPS,
                "slip_bps": SLIP_BPS,
                "g0_hurdle_bps": G0_HURDLE_BPS,
                "no_lookahead": True,
            }
            param_hash = hashlib.sha256(
                json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
            result = {
                "construction": "event_study_liquidation_cluster",
                "direction": direction,
                "horizon_bars": h,
                "horizon_min": h * 5,
                "n_events": r["n"],
                "n_events_declustered": r["n_indep"],
                "mean_gross_bps": round(r["gross_bps"], 4),
                "mean_net_bps_realistic": round(r["net_bps"], 4),
                "median_net_bps_realistic": round(r["median_net_bps"], 4),
                "t_stat": round(r["t_stat"], 4),
                "t_stat_declustered": round(r["t_stat_declustered"], 4),
                "win_rate": round(r["win_rate"], 6),
                "g0_clears_45bps": r["g0_clears"],
                "cost_bps_roundtrip": COST_RT_BPS,
                "no_lookahead": True,
                "leverage": "none_1x",
                "live": "off",
                "data_source": "hl_liquidations_hf fills (BTC-PERP) + hl_bars 5m (BTC)",
                "data_constrained": True,
                "universe": "BTC only (ETH/SOL ineligible: ~16d 5m overlap)",
                "n_clusters": n_clusters,
                "n_clusters_forced_sell": n_sell,
                "n_clusters_forced_buy": n_buy,
                "market_drift_bps": round(drift[h]["mean_bps"], 4),
            }
            if not args.no_write:
                e = ledger.increment_trial("HYP-27", param_hash, universe_hash,
                                           period_start, period_end, result)
                print(f"  wrote {dlabel}-{h*5}m: param_hash={e['param_hash'][:16]}... "
                      f"chain_hash={e['chain_hash'][:16]}...")
            else:
                print(f"  [--no-write] {dlabel}-{h*5}m: param_hash={param_hash[:16]}...")

    ok, msg = ledger.verify_integrity()
    print(f"\nledger integrity: {ok} ({msg})")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())