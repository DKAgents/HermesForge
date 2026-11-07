"""backtest_hyp26_liquidation_flow.py — HYP-26 forced liquidation flow -> subsequent return.

Read-only research driver. First test of a genuinely NEW structural data class:
tick-level liquidation fills. A long-liquidation is CLOSED by sells (downward
pressure); a short-liquidation by buys (upward pressure). Per hypothesis,

    net liquidation flow = (forced-buy notional - forced-sell notional) per
    market per day, cross-sectionally ranked so large books (BTC/ETH) do not
    dominate by raw size.

Two PRE-REGISTERED arms (do NOT tune — the direction is READ, not assumed):
  * H1 continuation: rank of net flow predicts SAME-sign forward return
    (long top-decile flow, short bottom-decile flow).
  * H2 reversal:        rank of net flow predicts OPPOSITE-sign forward return
    (exact mirror of H1, by construction H2_gross == -H1_gross).

Pre-registered operationalization (FIXED):
  * Universe: native HL perps (dex == ''), liquidity floor = trailing 7d mean
    daily last open_interest_usd >= $250k (repo MIN_DAILY_NOTIONAL_USD
    convention; floor measured at signal time t, no look-ahead).
  * Flow: aggregate liquidation FILLS to daily per-market net = buy - sell
    notional. Days with no fills -> net flow = 0 (included in the rank).
  * Forward return: enter next-open (open[t+1]), exit open[t+1+hold].  Signal
    consumes only day-t fills/OI; entry is after midnight -> strictly no
    look-ahead (fills run to ~23:30Z, so a close-to-close return would leak the
    23:00-23:30 fill window).
  * Horizon: 1d and 5d, NON-OVERLAPPING (rebalance every `hold` days).
  * Traded arm: cross-sectional decile (10%), equal weight, long top / short
    bottom by net-flow rank. H1 = long top, H2 = long bottom.
  * Cost: realistic fee_source crypto round-trip (4.5bps/leg taker x2 + 2.5bps
    adverse slip + 0.5bps funding = 12bps per position) charged ONCE per
    rebalance to BOTH legs of the spread (24bps/rebalance).  A fail-closed 4x
    hurdle (45bps/leg x2 = 90bps/rebalance) is reported separately as the G0
    cross-check.  No leverage beyond the +/-1x spread. LIVE off.

Reports (1) raw rank-IC (Spearman) + Pearson IC of net flow vs fwd return at
1d/5d, (2) traded net multi-R per arm per horizon, (3) G0/harvestability verdict.

Writes ONE trials-ledger entry per (arm, horizon) with a FRESH param_hash.

Usage: python3 backtest_hyp26_liquidation_flow.py [--no-write]
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import trials_ledger as ledger                              # noqa: E402
from fee_source import get_round_trip_bps, get_taker_bps    # noqa: E402

FILLS_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_liquidations_hf" / "data" / "fills"
OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf_clean"

# ── Pre-registered constants (FIXED — no tuning) ─────────────────────────────
LIQ_FLOOR_USD = 250_000.0   # trailing 7d mean daily OI floor (repo convention)
LIQ_LOOKBACK = 7            # trailing window for the OI liquidity floor
DECILE_FRAC = 0.10          # top/bottom decile for the traded arm
MIN_COINS_DAY = 20          # require >= this many ranked coins to form a day
HOLD_HORIZONS = (1, 5)      # 1d and 5d forward, non-overlapping
COST_HURDLE_BPS_LEG = 45.0  # fail-closed 4x hurdle, per leg (both legs charged)


# ────────────────────────────────────────────────────────────────────────────
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate fills -> daily per-market net flow; OI native -> daily ohlc+oi.

    Returns (daily panel, netflow long-form):
      daily:   columns [market, date, open, close, oi] for native perps
      netflow: columns [market, date, netflow, buy_usd, sell_usd]
    """
    ocols = ["timestamp", "market", "coin", "dex", "mark_price", "open_interest_usd"]
    o_files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    if not o_files:
        raise SystemExit(f"no OI parquet under {OI_DIR}")
    o = pd.concat([pd.read_parquet(p, columns=ocols) for p in o_files],
                  ignore_index=True)
    native = o[o["dex"] == ""]
    native["date"] = native["timestamp"].dt.normalize()
    daily = (native.sort_values("timestamp")
             .groupby(["market", "date"], sort=False)
             .agg(open=("mark_price", "first"),
                  close=("mark_price", "last"),
                  oi=("open_interest_usd", "last"))
             .reset_index())

    f_files = sorted(glob.glob(str(FILLS_DIR / "*.parquet")))
    if not f_files:
        raise SystemExit(f"no liquidation fills under {FILLS_DIR}")
    fcols = ["timestamp", "market", "side", "notional_usd"]
    f = pd.concat([pd.read_parquet(p, columns=fcols) for p in f_files],
                  ignore_index=True)
    f = f[f["market"].isin(set(daily["market"].unique()))]   # native perps only
    f["date"] = f["timestamp"].dt.normalize()
    f["buy_usd"] = np.where(f["side"] == "buy", f["notional_usd"], 0.0)
    f["sell_usd"] = np.where(f["side"] == "sell", f["notional_usd"], 0.0)
    netflow = (f.groupby(["market", "date"], sort=False)
               .agg(buy_usd=("buy_usd", "sum"), sell_usd=("sell_usd", "sum"))
               .reset_index())
    netflow["netflow"] = netflow["buy_usd"] - netflow["sell_usd"]
    return daily, netflow


def build_panels(daily: pd.DataFrame, netflow: pd.DataFrame
                 ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Wide panels: opens, closes, netflow (date x market), full daily calendar."""
    m = daily.merge(netflow[["market", "date", "netflow"]],
                    on=["market", "date"], how="left")
    m["netflow"] = m["netflow"].fillna(0.0)
    m = m.sort_values(["market", "date"]).reset_index(drop=True)
    start, end = m["date"].min(), m["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    opens = m.pivot(index="date", columns="market", values="open").reindex(cal)
    closes = m.pivot(index="date", columns="market", values="close").reindex(cal)
    ois = m.pivot(index="date", columns="market", values="oi").reindex(cal)
    flows = m.pivot(index="date", columns="market", values="netflow").reindex(cal)
    return opens, ois, flows


def liquidity_mask(ois: pd.DataFrame) -> pd.DataFrame:
    """Trailing LIQ_LOOKBACK-day mean OI >= floor (signal-time, no look-ahead)."""
    return ois.rolling(LIQ_LOOKBACK, min_periods=1).mean() >= LIQ_FLOOR_USD


def forward_returns(opens: pd.DataFrame, hold: int) -> pd.DataFrame:
    """fwd[t] = open[t+1+hold]/open[t+1] - 1  (next-open entry, no look-ahead)."""
    entry = opens.shift(-1)
    exitp = opens.shift(-(1 + hold))
    return exitp / entry - 1.0


# ────────────────────────────────────────────────────────────────────────────
def _rank_series(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Rank within the masked cross-section; NaN elsewhere. Average ties."""
    out = np.full(x.shape, np.nan)
    xv = x[mask]
    if len(xv) == 0:
        return out
    ranks = pd.Series(xv).rank(method="average").to_numpy(dtype=float)
    out[mask] = ranks
    return out


def compute_rank_ic(flows: pd.DataFrame, ois: pd.DataFrame, opens: pd.DataFrame,
                    hold: int) -> dict:
    """Cross-sectional Spearman (rank) IC + Pearson IC of netflow vs fwd return.

    Restricts the cross-section to the LIQUID universe (trailing OI floor) to
    match the traded arm and the pre-registered universe definition.
    """
    fwd = forward_returns(opens, hold)
    liq = liquidity_mask(ois)
    cols = [c for c in flows.columns if c in opens.columns and c in ois.columns]
    flows = flows[cols]; fwd = fwd[cols]; liq = liq[cols]
    common = flows.index.intersection(fwd.index).intersection(liq.index)
    flows = flows.loc[common]; fwd = fwd.loc[common]; liq = liq.loc[common]

    spearman_ics, pearson_ics, n_per_day = [], [], []
    dates = list(flows.index)
    for t in range(len(dates) - (1 + hold)):
        signal = flows.iloc[t].to_numpy(dtype=float)
        ret = fwd.iloc[t].to_numpy(dtype=float)
        lmask = liq.iloc[t].to_numpy(dtype=bool)
        mask = np.isfinite(signal) & np.isfinite(ret) & lmask
        if mask.sum() < MIN_COINS_DAY:
            continue
        r_sig = _rank_series(signal, mask)
        r_ret = _rank_series(ret, mask)
        # Spearman = Pearson on ranks
        spearman_ics.append(_pearson(r_sig, r_ret, mask))
        pearson_ics.append(_pearson(signal, ret, mask))
        n_per_day.append(int(mask.sum()))

    if not spearman_ics:
        return {"hold": hold, "n_days": 0, "mean_spearman_ic": float("nan"),
                "mean_pearson_ic": float("nan")}

    def _summ(arr):
        a = np.array(arr)
        return {
            "mean": float(a.mean()),
            "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
            "t_stat": float(a.mean() / (a.std(ddof=1) / np.sqrt(len(a))))
                      if (len(a) > 1 and a.std(ddof=1) > 0) else 0.0,
            "frac_pos": float((a > 0).mean()),
            "n": int(len(a)),
        }

    # non-overlapping t-stat: subsample step=hold to avoid autocorrelated IC
    step = hold
    sub_s = np.array(spearman_ics)[::step]
    sub_p = np.array(pearson_ics)[::step]

    return {
        "hold": hold,
        "n_days": int(len(spearman_ics)),
        "mean_n_coins": float(np.mean(n_per_day)),
        "spearman_ic": _summ(spearman_ics),
        "pearson_ic": _summ(pearson_ics),
        "spearman_ic_nonoverlap_t": float(
            sub_s.mean() / (sub_s.std(ddof=1) / np.sqrt(len(sub_s))))
            if (len(sub_s) > 1 and sub_s.std(ddof=1) > 0) else 0.0,
        "pearson_ic_nonoverlap_t": float(
            sub_p.mean() / (sub_p.std(ddof=1) / np.sqrt(len(sub_p))))
            if (len(sub_p) > 1 and sub_p.std(ddof=1) > 0) else 0.0,
    }


def _pearson(x: np.ndarray, y: np.ndarray, mask: np.ndarray) -> float:
    xv = x[mask]; yv = y[mask]
    if len(xv) < 2:
        return float("nan")
    xv = xv - xv.mean(); yv = yv - yv.mean()
    denom = np.sqrt((xv ** 2).sum() * (yv ** 2).sum())
    if denom == 0:
        return float("nan")
    return float((xv * yv).sum() / denom)


# ────────────────────────────────────────────────────────────────────────────
def run_traded_arm(flows: pd.DataFrame, ois: pd.DataFrame, opens: pd.DataFrame,
                   hold: int, direction: str, cost_per_rebalance: float
                   ) -> dict:
    """Cross-sectional decile spread, `direction` in {'continuation','reversal'}.

    continuation (H1): long top-decile netflow, short bottom-decile.
    reversal     (H2): mirror (long bottom, short top).
    """
    fwd = forward_returns(opens, hold)
    liq = liquidity_mask(ois)
    cols = [c for c in flows.columns if c in opens.columns and c in ois.columns]
    flows = flows[cols]; fwd = fwd[cols]; liq = liq[cols]; ois = ois[cols]
    common = flows.index.intersection(fwd.index).intersection(liq.index)
    flows = flows.loc[common]; fwd = fwd.loc[common]; liq = liq.loc[common]

    records, top_leg, bottom_leg, n_coins_list = [], [], [], []
    dates = list(flows.index)
    step = hold                      # non-overlapping
    t = 0
    while t < len(dates) - (1 + hold):
        signal = flows.iloc[t].to_numpy(dtype=float)
        ret = fwd.iloc[t].to_numpy(dtype=float)
        lmask = liq.iloc[t].to_numpy(dtype=bool)
        mask = np.isfinite(signal) & np.isfinite(ret) & lmask
        if mask.sum() < MIN_COINS_DAY:
            t += step
            continue
        s_v = signal[mask]; f_v = ret[mask]
        order = np.argsort(s_v)                      # ascending netflow
        n = len(s_v)
        k = max(1, int(round(n * DECILE_FRAC)))
        bot_idx = order[:k]                          # lowest flow
        top_idx = order[-k:]                         # highest flow
        top_ret = float(np.mean(f_v[top_idx]))       # high-flow coins
        bot_ret = float(np.mean(f_v[bot_idx]))       # low-flow coins
        if direction == "continuation":
            spread_gross = top_ret - bot_ret         # buy high-flow, short low-flow
        else:  # reversal
            spread_gross = bot_ret - top_ret         # buy low-flow, short high-flow
        net = spread_gross - cost_per_rebalance
        records.append({"date": str(dates[t].date()), "n": n, "k": k,
                        "gross": spread_gross, "net": net,
                        "top_ret": top_ret, "bot_ret": bot_ret})
        top_leg.append(top_ret)
        bottom_leg.append(bot_ret)
        n_coins_list.append(n)
        t += step

    if not records:
        return {"direction": direction, "hold": hold, "n_rebalances": 0,
                "reconciled": False, "records": []}

    gross_arr = np.array([r["gross"] for r in records])
    net_arr = np.array([r["net"] for r in records])

    total_net_series = float(net_arr.sum())
    total_gross_series = float(gross_arr.sum())
    # Direction-aware by-trade reconstruction (mirror legs for reversal).
    if direction == "continuation":
        by_trade_gross = float(np.sum(top_leg) - np.sum(bottom_leg))
    else:
        by_trade_gross = float(np.sum(bottom_leg) - np.sum(top_leg))
    by_trade_net = by_trade_gross - cost_per_rebalance * len(records)
    reconciled = abs(total_net_series - by_trade_net) < 1e-9 and \
                 abs(total_gross_series - by_trade_gross) < 1e-9

    mean_gross = float(gross_arr.mean())
    mean_net = float(net_arr.mean())
    sharpe = float(mean_net / net_arr.std(ddof=1)) if net_arr.std(ddof=1) > 0 else 0.0
    wins = float((net_arr > 0).mean())

    # Annualized gross: per-rebalance mean x rebalances/year (no compounding).
    ann_gross_bps = mean_gross * 1e4 * (365.0 / hold)

    return {
        "direction": direction, "hold": hold,
        "n_rebalances": len(records),
        "mean_n_coins": float(np.mean(n_coins_list)),
        "mean_k_per_leg": float(np.mean([r["k"] for r in records])),
        "mean_gross_r": mean_gross, "mean_gross_bps": mean_gross * 1e4,
        "mean_net_r": mean_net, "mean_net_bps": mean_net * 1e4,
        "total_net_r": total_net_series,           # "multi-R": summed net spread
        "total_gross_r": total_gross_series,
        "by_trade_net": by_trade_net, "by_trade_gross": by_trade_gross,
        "reconciled": bool(reconciled),
        "sharpe": sharpe, "win_rate": wins,
        "top_decile_mean_gross_bps": float(np.mean(top_leg)) * 1e4,
        "bottom_decile_mean_gross_bps": float(np.mean(bottom_leg)) * 1e4,
        "annualized_gross_bps": ann_gross_bps,
        "cost_per_rebalance_bps": cost_per_rebalance * 1e4,
        "records": records,
    }


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    taker_bps = get_taker_bps("crypto")
    rtb_bps = get_round_trip_bps("crypto")
    cost_real = 2.0 * rtb_bps / 1e4               # 24bps both legs (12bps/position)
    cost_hurdle = 2.0 * COST_HURDLE_BPS_LEG / 1e4  # 90bps both legs (fail-closed 4x)

    print("=== HYP-26 forced liquidation flow -> subsequent return ===\n")
    print(f"cost model: realistic {rtb_bps:.1f}bps/position rt x2 = "
          f"{cost_real*1e4:.0f}bps/rebalance; fail-closed hurdle "
          f"{cost_hurdle*1e4:.0f}bps/rebalance (taker {taker_bps:.1f}bps/leg)")
    print(f"liquidity floor: trailing {LIQ_LOOKBACK}d mean OI >= "
          f"${LIQ_FLOOR_USD:,.0f}; decile {DECILE_FRAC:.0%}; "
          f"min {MIN_COINS_DAY} coins/day")

    print("\nloading fills + OI ...")
    daily, netflow = load_data()
    opens, ois, flows = build_panels(daily, netflow)
    n_markets = opens.shape[1]
    print(f"  panel (OI span): {opens.shape[0]} days x {n_markets} native perp "
          f"markets ({opens.index.min().date()} -> {opens.index.max().date()})")
    print(f"  fills span: {netflow.date.min().date()} -> {netflow.date.max().date()}")

    # Restrict to the liquidation-data span: before the first fill, net flow is
    # STRUCTURALLY zero (no data), not "measured zero" — so the signal is only
    # measurable 2025-05-25 -> 2026-10-31.  This is a data-availability boundary,
    # not a tuning choice.
    fill_start = netflow["date"].min().normalize()
    fill_end = netflow["date"].max().normalize()
    opens = opens.loc[(opens.index >= fill_start) & (opens.index <= fill_end)]
    ois = ois.loc[(ois.index >= fill_start) & (ois.index <= fill_end)]
    flows = flows.loc[(flows.index >= fill_start) & (flows.index <= fill_end)]
    print(f"  analysis window (signal-measurable): {opens.index.min().date()} "
          f"-> {opens.index.max().date()}  ({opens.shape[0]} days)")

    # ── 1. raw rank-IC (honest sign + magnitude) ─────────────────────────────
    print("\n===== 1. Raw predictive relationship (rank-IC) =====")
    rank_ic = {}
    for hold in HOLD_HORIZONS:
        ic = compute_rank_ic(flows, ois, opens, hold)
        rank_ic[hold] = ic
        s = ic["spearman_ic"]; p = ic["pearson_ic"]
        print(f"  hold={hold}d: n_days={ic['n_days']}  mean n_coins={ic['mean_n_coins']:.0f}")
        print(f"    Spearman rank-IC: mean {s['mean']:+.4f}  std {s['std']:.4f}  "
              f"t {s['t_stat']:+.2f} (non-overlap t {ic['spearman_ic_nonoverlap_t']:+.2f})  "
              f"frac+ {s['frac_pos']:.3f}")
        print(f"    Pearson      IC : mean {p['mean']:+.4f}  std {p['std']:.4f}  "
              f"t {p['t_stat']:+.2f} (non-overlap t {ic['pearson_ic_nonoverlap_t']:+.2f})  "
              f"frac+ {p['frac_pos']:.3f}")
        sign = "CONTINUATION (H1)" if s["mean"] > 0 else "REVERSAL (H2)"
        print(f"    => raw sign: {sign}")

    # ── 2. traded arms (both directions, both horizons) ──────────────────────
    print("\n===== 2. Traded arms (H1 continuation / H2 reversal) =====")
    traded = {}
    for hold in HOLD_HORIZONS:
        for direction, dlabel in [("continuation", "H1"), ("reversal", "H2")]:
            for cost_name, cost in [("realistic", cost_real),
                                    ("hurdle", cost_hurdle)]:
                r = run_traded_arm(flows, ois, opens, hold, direction, cost)
                key = f"{dlabel}_hold{hold}_{cost_name}"
                traded[key] = r
                if cost_name == "realistic":
                    print(f"  {dlabel} hold={hold}d: n_rebal={r['n_rebalances']}  "
                          f"n/coins={r['mean_n_coins']:.0f}  k/leg={r['mean_k_per_leg']:.1f}")
                    print(f"    gross {r['mean_gross_bps']:+.3f} bps/reb "
                          f"(ann {r['annualized_gross_bps']:+.1f}bps)  "
                          f"high-flow {r['top_decile_mean_gross_bps']:+.3f}  "
                          f"low-flow {r['bottom_decile_mean_gross_bps']:+.3f}")
                    print(f"    net@realistic {r['mean_net_bps']:+.3f} bps/reb  "
                          f"multi-R {r['total_net_r']:+.4f}  sharpe {r['sharpe']:+.3f}  "
                          f"win {r['win_rate']:.3f}  recon={r['reconciled']}")
            # hurdle net for this arm+hold (only need the net figure)
            hr = traded[f"{dlabel}_hold{hold}_hurdle"]
            rr = traded[f"{dlabel}_hold{hold}_realistic"]
            print(f"       net@hurdle {hr['mean_net_bps']:+.3f} bps/reb  "
                  f"(multi-R {hr['total_net_r']:+.4f})")

    # ── 3. write trials (fresh param_hash per arm/horizon) ───────────────────
    period_start = str(opens.index.min().date())
    period_end = str(opens.index.max().date())
    # universe = native perps that ever cleared the $250k floor (deterministic)
    liq_any = liquidity_mask(ois)
    universe_markets = sorted([c for c in liq_any.columns
                               if bool(liq_any[c].any())])
    universe_hash = hashlib.sha256(",".join(universe_markets).encode()).hexdigest()

    print("\n===== 3. Trials ledger writes =====")
    for hold in HOLD_HORIZONS:
        for direction, dlabel in [("continuation", "H1"), ("reversal", "H2")]:
            r_real = traded[f"{dlabel}_hold{hold}_realistic"]
            r_hurdle = traded[f"{dlabel}_hold{hold}_hurdle"]
            param_dict = {
                "signal": "daily_net_liquidation_flow_rank",
                "signal_def": "buy_notional - sell_notional per native perp per day",
                "direction": direction,
                "hold_days": hold,
                "entry": "next_open",
                "decile_frac": DECILE_FRAC,
                "liquidity_floor_usd": LIQ_FLOOR_USD,
                "liquidity_lookback_days": LIQ_LOOKBACK,
                "min_coins_day": MIN_COINS_DAY,
                "cost_bps_realistic_per_rebalance": cost_real * 1e4,
                "cost_bps_hurdle_per_rebalance": cost_hurdle * 1e4,
                "non_overlapping": True,
            }
            param_hash = hashlib.sha256(
                json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
            ic = rank_ic[hold]
            result = {
                "construction": "cross_sectional_liquidation_flow_rank",
                "direction": direction,
                "hold_days": hold,
                "n_rebalances": r_real["n_rebalances"],
                "mean_n_coins": round(r_real["mean_n_coins"], 2),
                "mean_k_per_leg": round(r_real["mean_k_per_leg"], 2),
                "mean_gross_bps": round(r_real["mean_gross_bps"], 4),
                "annualized_gross_bps": round(r_real["annualized_gross_bps"], 2),
                "mean_net_bps_realistic": round(r_real["mean_net_bps"], 4),
                "mean_net_bps_hurdle": round(r_hurdle["mean_net_bps"], 4),
                "total_net_r_realistic": round(r_real["total_net_r"], 8),
                "total_net_r_hurdle": round(r_hurdle["total_net_r"], 8),
                "top_decile_mean_gross_bps": round(r_real["top_decile_mean_gross_bps"], 4),
                "bottom_decile_mean_gross_bps": round(r_real["bottom_decile_mean_gross_bps"], 4),
                "sharpe": round(r_real["sharpe"], 6),
                "win_rate": round(r_real["win_rate"], 6),
                "reconciled": r_real["reconciled"],
                "spearman_ic_mean": round(ic["spearman_ic"]["mean"], 6),
                "spearman_ic_t": round(ic["spearman_ic"]["t_stat"], 4),
                "pearson_ic_mean": round(ic["pearson_ic"]["mean"], 6),
                "pearson_ic_t": round(ic["pearson_ic"]["t_stat"], 4),
                "no_lookahead": True,
                "leverage": "none_+/-1x_spread",
                "live": "off",
                "data_source": "hl_liquidations_hf fills + hl_oi_hf_clean marks/OI",
                "n_markets_total": n_markets,
                "n_markets_liquid_universe": len(universe_markets),
            }
            if not args.no_write:
                e = ledger.increment_trial("HYP-26", param_hash, universe_hash,
                                           period_start, period_end, result)
                print(f"  wrote {dlabel}-{hold}d: param_hash={e['param_hash'][:16]}... "
                      f"chain_hash={e['chain_hash'][:16]}...")
            else:
                print(f"  [--no-write] {dlabel}-{hold}d: param_hash={param_hash[:16]}...")

    # integrity check
    ok, msg = ledger.verify_integrity()
    print(f"\nledger integrity: {ok} ({msg})")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())