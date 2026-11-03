"""revalidate_funding_crowding.py — HYP-17 funding-crowding volatility proxy.

Read-only research driver. Tests the coach's "crowded positioning -> big move"
thesis PROXIED by extreme funding (|funding| >= 90th pct of the coin's trailing
90d), since exact OI history is AWS-gated (HYP-16). Funding is directional
crowding (long/short imbalance); OI is total positioning — related, not identical.

Pre-registered operationalization (FIXED — no post-hoc tuning):
  * Crowding trigger: |funding| >= 90th percentile of the coin's trailing 90d
    |funding| distribution (extreme in EITHER direction).
  * H1 (expansion): mean |forward return| over next 1-5 daily bars in the
    extreme-funding regime vs the unconditional full-sample mean.
  * H2 (directional unwind, exploratory): extreme +funding -> short (expect
    negative forward return); extreme -funding -> long (expect positive forward
    return), NET of taker+fees. Expected net <= 0 (HYP-01 already showed the
    fade fails on friction).

Data: hl_funding_store (~400d hourly, 35 coins) + HL 1d bars (~4y, fetched live
via candleSnapshot, cached to scratch). The binding window is the ~400d funding
history (roughly ONE regime — a stated limitation).

No look-ahead: percentile window is trailing-only; forward returns strictly-after.
Cost charged once via fee_source (round-trip). No leverage. LIVE off.
Writes ONE trial to data/gauntlet/trials.jsonl (fresh param_hash).

Usage: python3 revalidate_funding_crowding.py [--no-write] [--no-fetch-cache]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent), str(_THIS_DIR.parent / "data")):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import requests  # noqa: E402

import hl_funding_store as fs                           # noqa: E402
import trials_ledger as ledger                          # noqa: E402
from fee_source import get_round_trip_bps               # noqa: E402
from hermes_config.universe import CRYPTO_UNIVERSE      # noqa: E402

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"

# ── Pre-registered constants (FIXED) ────────────────────────────────────────
PCTILE = 90.0                    # 90th percentile
PCTILE_WINDOW_DAYS = 90          # trailing 90d
PCTILE_WINDOW_HOURS = PCTILE_WINDOW_DAYS * 24
FORWARD_BARS = 5                 # forward return 1-5 bars
DAY_MS = 86400000
LOOKBACK_DAYS = 4 * 365          # ~4y daily bars

_CACHE = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "hyp17_1d_bars.json"


def fetch_hl_daily_bars(coin: str, lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """One candleSnapshot call returns HL's retained 1d floor (~1461 bars)."""
    now = int(time.time() * 1000)
    start = now - lookback_days * DAY_MS
    r = requests.post(HYPERLIQUID_INFO_URL,
                      json={"type": "candleSnapshot",
                            "req": {"coin": coin, "interval": "1d",
                                    "startTime": start, "endTime": now}},
                      timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not data:
        return []
    bars = [{"ts": int(c["t"]), "close": float(c["c"])} for c in data]
    return sorted(bars, key=lambda b: b["ts"])


def load_daily(universe: list[str], use_cache: bool = True) -> dict[str, pd.DataFrame]:
    if use_cache and _CACHE.exists():
        with open(_CACHE) as f:
            raw = json.load(f)
        return {c: pd.DataFrame(rows) for c, rows in raw.items()}
    out: dict[str, pd.DataFrame] = {}
    for i, coin in enumerate(universe):
        try:
            bars = fetch_hl_daily_bars(coin)
        except Exception as e:  # noqa: BLE001
            print(f"  fetch {coin:10s} FAILED: {e}", file=sys.stderr)
            bars = []
        if bars:
            out[coin] = pd.DataFrame(bars)
        print(f"  fetch {coin:10s} {len(bars)} bars", file=sys.stderr)
        if i < len(universe) - 1:
            time.sleep(0.15)
    if use_cache:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE, "w") as f:
            json.dump({c: df.to_dict("records") for c, df in out.items()}, f)
    return out


def compute_coin(coin: str, funding: pd.DataFrame, bars: pd.DataFrame) -> tuple[list, list]:
    """Return (events, baseline) for one coin.

    events: one dict per extreme-funding daily bar (with >=5 forward bars).
    baseline: one dict per daily bar (with >=5 forward bars), unconditional.
    """
    if funding is None or funding.empty or bars is None or bars.empty:
        return [], []

    f = funding.sort_values("time").reset_index(drop=True)
    f["abs_f"] = f["funding_rate"].astype(float).abs()
    # trailing 90d percentile of |funding| (full 90d window required)
    f["p90"] = (f["abs_f"]
                .rolling(PCTILE_WINDOW_HOURS, min_periods=PCTILE_WINDOW_HOURS)
                .quantile(PCTILE / 100.0))

    b = bars.sort_values("ts").reset_index(drop=True)
    b["close_time"] = b["ts"] + DAY_MS
    closes = b["close"].astype(float).to_numpy()
    n = len(b)

    # asof-map funding (rate + p90) onto each daily bar's close time
    fsrc = f[["time", "funding_rate", "abs_f", "p90"]].rename(columns={"time": "close_time"})
    tgt = pd.DataFrame({"close_time": b["close_time"].to_numpy()})
    merged = pd.merge_asof(tgt, fsrc, on="close_time", direction="backward")
    cur_rate = merged["funding_rate"].to_numpy(dtype=float)
    cur_abs = merged["abs_f"].to_numpy(dtype=float)
    cur_p90 = merged["p90"].to_numpy(dtype=float)

    # forward returns over h=1..5 (strictly-after)
    fwd_abs = np.full(n, np.nan)
    fwd_signed = np.full(n, np.nan)
    fwd_abs_h = {h: np.full(n, np.nan) for h in range(1, FORWARD_BARS + 1)}
    fwd_signed_h = {h: np.full(n, np.nan) for h in range(1, FORWARD_BARS + 1)}
    for t in range(n - FORWARD_BARS):
        rets = []
        for h in range(1, FORWARD_BARS + 1):
            r = closes[t + h] / closes[t] - 1.0
            rets.append(r)
            fwd_abs_h[h][t] = abs(r)
            fwd_signed_h[h][t] = r
        fwd_abs[t] = float(np.mean([abs(r) for r in rets]))
        fwd_signed[t] = float(np.mean(rets))

    events: list[dict] = []
    baseline: list[dict] = []
    for t in range(n - FORWARD_BARS):
        if not np.isfinite(fwd_abs[t]):
            continue
        rec = {
            "coin": coin, "ts": int(b["ts"].iloc[t]),
            "fwd_abs": float(fwd_abs[t]), "fwd_signed": float(fwd_signed[t]),
        }
        for h in range(1, FORWARD_BARS + 1):
            rec[f"fwd_abs_h{h}"] = float(fwd_abs_h[h][t])
            rec[f"fwd_signed_h{h}"] = float(fwd_signed_h[h][t])
        baseline.append(rec)

        p90 = cur_p90[t]
        if not np.isfinite(p90) or p90 <= 0:
            continue
        if cur_abs[t] >= p90:
            rec2 = dict(rec)
            rec2["funding_rate"] = float(cur_rate[t])
            rec2["abs_funding"] = float(cur_abs[t])
            rec2["p90"] = float(p90)
            rec2["sign"] = 1 if cur_rate[t] > 0 else (-1 if cur_rate[t] < 0 else 0)
            events.append(rec2)

    return events, baseline


def bootstrap_diff(regime: np.ndarray, baseline: np.ndarray, B: int = 10000,
                   seed: int = 17) -> dict:
    """Bootstrap the difference (regime_mean - baseline_mean) and the ratio.

    Returns {diff, diff_ci_lo, diff_ci_hi, p_value, ratio, ratio_ci_lo, ratio_ci_hi}.
    p_value = one-sided P(regime_mean <= baseline_mean) under bootstrap.
    """
    rng = np.random.default_rng(seed)
    nr, nb = len(regime), len(baseline)
    diffs = np.empty(B)
    ratios = np.empty(B)
    for i in range(B):
        rb = rng.choice(regime, size=nr, replace=True)
        bb = rng.choice(baseline, size=nb, replace=True)
        mr, mb = rb.mean(), bb.mean()
        diffs[i] = mr - mb
        ratios[i] = mr / mb if mb > 0 else np.nan
    diffs = diffs[np.isfinite(diffs)]
    ratios = ratios[np.isfinite(ratios)]
    return {
        "diff": float(regime.mean() - baseline.mean()),
        "diff_ci_lo": float(np.percentile(diffs, 2.5)),
        "diff_ci_hi": float(np.percentile(diffs, 97.5)),
        "p_value": float((diffs <= 0).mean()),
        "ratio": float(regime.mean() / baseline.mean()) if baseline.mean() > 0 else float("nan"),
        "ratio_ci_lo": float(np.percentile(ratios, 2.5)),
        "ratio_ci_hi": float(np.percentile(ratios, 97.5)),
    }


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--no-fetch-cache", action="store_true")
    args = ap.parse_args()

    print("=== HYP-17 funding-crowding volatility proxy — real-data ===\n")

    # ── data ─────────────────────────────────────────────────────────────────
    print("loading HL 1d bars (live candleSnapshot, cached)...")
    daily = load_daily(CRYPTO_UNIVERSE, use_cache=not args.no_fetch_cache)
    print(f"  1d bars: {len(daily)} coins fetched")

    all_events: list[dict] = []
    all_baseline: list[dict] = []
    coin_meta: dict = {}
    for coin in CRYPTO_UNIVERSE:
        f = fs.read_funding(coin)
        b = daily.get(coin)
        if f is None or f.empty or b is None or b.empty:
            continue
        ev, bl = compute_coin(coin, f, b)
        coin_meta[coin] = {"n_funding": len(f), "n_bars": len(b),
                           "n_events": len(ev), "n_baseline": len(bl)}
        all_events.extend(ev)
        all_baseline.extend(bl)

    if not all_events or not all_baseline:
        print("no events — aborting")
        return 1

    ev = pd.DataFrame(all_events)
    bl = pd.DataFrame(all_baseline)

    # ── data window ──────────────────────────────────────────────────────────
    fmin = min(m["n_funding"] for m in coin_meta.values())
    print(f"\ncoins with both funding+bars: {len(coin_meta)}")
    print(f"funding rows/coin: {fmin} hourly (~{fmin/24:.0f}d)")
    print(f"extreme-funding events: {len(ev)}   unconditional bars: {len(bl)}")
    print(f"event ts range: {pd.to_datetime(ev['ts'], unit='ms').min().date()} -> "
          f"{pd.to_datetime(ev['ts'], unit='ms').max().date()}")
    print(f"baseline ts range: {pd.to_datetime(bl['ts'], unit='ms').min().date()} -> "
          f"{pd.to_datetime(bl['ts'], unit='ms').max().date()}")

    # ── H1 expansion ─────────────────────────────────────────────────────────
    regime_abs = ev["fwd_abs"].astype(float).to_numpy()
    base_abs = bl["fwd_abs"].astype(float).to_numpy()
    regime_mean = float(regime_abs.mean())
    base_mean = float(base_abs.mean())
    bs = bootstrap_diff(regime_abs, base_abs)

    # same-window baseline (funding overlap) — fair regime comparison, since the
    # ~400d funding window is roughly ONE regime and the 4y baseline spans
    # multiple vol regimes (2022-23 winter etc.).
    ev_min_ts = int(ev["ts"].min())
    ev_max_ts = int(ev["ts"].max())
    bl_overlap = bl[(bl["ts"] >= ev_min_ts) & (bl["ts"] <= ev_max_ts)]
    base_overlap_abs = bl_overlap["fwd_abs"].astype(float).to_numpy()
    base_overlap_mean = float(base_overlap_abs.mean())
    bs_overlap = bootstrap_diff(regime_abs, base_overlap_abs)

    print("\n--- H1 (expansion): does extreme funding predict BIGGER moves? ---")
    print(f"  regime mean |move| (1-5 bars): {regime_mean*100:.4f}%  (n={len(regime_abs)})")
    print(f"  baseline mean |move| (full 4y): {base_mean*100:.4f}%  (n={len(base_abs)})")
    print(f"  baseline mean |move| (same ~310d window): {base_overlap_mean*100:.4f}%  "
          f"(n={len(base_overlap_abs)})")
    print(f"  ratio (regime/full):           {bs['ratio']:.4f}")
    print(f"  ratio (regime/same-window):    {bs_overlap['ratio']:.4f}")
    print(f"  diff vs full (regime - base):  {bs['diff']*100:.4f}%  "
          f"95% CI [{bs['diff_ci_lo']*100:.4f}%, {bs['diff_ci_hi']*100:.4f}%]")
    print(f"  diff vs same-window:           {bs_overlap['diff']*100:.4f}%  "
          f"95% CI [{bs_overlap['diff_ci_lo']*100:.4f}%, {bs_overlap['diff_ci_hi']*100:.4f}%]")
    print(f"  bootstrap p (regime<=full):    {bs['p_value']:.4f}")
    print(f"  bootstrap p (regime<=same-win): {bs_overlap['p_value']:.4f}")

    # per-horizon breakdown
    print("  per-horizon mean |move| (regime vs baseline):")
    for h in range(1, FORWARD_BARS + 1):
        rh = ev[f"fwd_abs_h{h}"].astype(float).mean()
        bh = bl[f"fwd_abs_h{h}"].astype(float).mean()
        print(f"    h={h}: regime {rh*100:.4f}%  baseline {bh*100:.4f}%  ratio {rh/bh:.4f}")

    # ── H2 directional unwind ────────────────────────────────────────────────
    rtb = get_round_trip_bps("crypto")
    cost_frac = rtb / 1e4
    # directional P&L = -sign(funding) * forward return (fade the crowd)
    ev2 = ev[ev["sign"] != 0].copy()
    ev2["dir_ret"] = -ev2["sign"] * ev2["fwd_signed"]
    gross_bps = float(ev2["dir_ret"].mean()) * 1e4
    net_bps = gross_bps - rtb
    net_ret = ev2["dir_ret"] - cost_frac
    win_rate = float((net_ret > 0).mean())

    print("\n--- H2 (directional unwind, exploratory) ---")
    print(f"  n directional events: {len(ev2)}  (+funding {int((ev2['sign']==1).sum())}, "
          f"-funding {int((ev2['sign']==-1).sum())})")
    print(f"  gross directional return (mean): {gross_bps:+.3f} bps")
    print(f"  round-trip cost (fee_source):    {rtb:.1f} bps")
    print(f"  NET directional return:          {net_bps:+.3f} bps")
    print(f"  win rate (net): {win_rate:.4f}   PF(net): {_pf(net_ret.tolist()):.4f}")
    print(f"  -> net {'<= 0 (HYP-01 confirmed)' if net_bps <= 0 else '> 0 (unexpected)'}")

    # ── write trial ──────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "funding_crowding_expansion",
        "pctile": PCTILE, "pctile_window_days": PCTILE_WINDOW_DAYS,
        "forward_bars": FORWARD_BARS,
        "trigger": "abs_funding >= trailing_90d_p90",
        "cost": "fee_source_round_trip", "leverage": "none",
    }, sort_keys=True).encode()).hexdigest()
    universe_str = ",".join(sorted(coin_meta.keys()))
    universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()

    result = {
        "construction": "funding_crowding_expansion",
        "n_coins": len(coin_meta),
        "n_extreme_events": int(len(ev)),
        "n_baseline_bars": int(len(bl)),
        "h1_regime_mean_abs_move": round(regime_mean, 8),
        "h1_baseline_mean_abs_move": round(base_mean, 8),
        "h1_baseline_overlap_mean_abs_move": round(base_overlap_mean, 8),
        "h1_ratio": round(bs["ratio"], 6),
        "h1_ratio_overlap": round(bs_overlap["ratio"], 6),
        "h1_diff": round(bs["diff"], 8),
        "h1_diff_ci_lo": round(bs["diff_ci_lo"], 8),
        "h1_diff_ci_hi": round(bs["diff_ci_hi"], 8),
        "h1_bootstrap_p_value": round(bs["p_value"], 6),
        "h1_bootstrap_p_value_overlap": round(bs_overlap["p_value"], 6),
        "h1_ratio_ci_lo": round(bs["ratio_ci_lo"], 6),
        "h1_ratio_ci_hi": round(bs["ratio_ci_hi"], 6),
        "h2_n_directional": int(len(ev2)),
        "h2_gross_bps": round(gross_bps, 4),
        "h2_round_trip_bps": round(rtb, 4),
        "h2_net_bps": round(net_bps, 4),
        "h2_win_rate": round(win_rate, 6),
        "h2_pf": round(_pf(net_ret.tolist()), 6),
        "h2_net_le_zero": bool(net_bps <= 0),
        "trade_count": int(len(ev2)),
        "avg_r": round(float(net_ret.mean()), 6),
        "sharpe": round(float(net_ret.mean() / net_ret.std()), 6) if net_ret.std() > 0 else 0.0,
        "r_outliers_skipped": 0,
        "data_window_note": "funding ~400d (one regime); bars ~4y; binding window = funding",
        "no_lookahead": True,
        "leverage": "none",
        "live": "off",
    }

    period_start = "2025-09-27"
    period_end = "2026-11-02"
    if not args.no_write:
        e = ledger.increment_trial("HYP-17", param_hash, universe_hash,
                                   period_start, period_end, result)
        print(f"\nwrote trial HYP-17  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
