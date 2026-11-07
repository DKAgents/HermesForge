"""revalidate_hyp25_short_continuation.py — HYP-25 short-side continuation, gated on shortability.

HYP-24's leg decomposition found the SHORT leg of cross-sectional 7d momentum
carries a REAL, control-beating edge (+0.201R above the zero-drift control):
"losers keep decaying". The caveat: shorting the bottom-decile means shorting
tiny/illiquid/dying coins. HYP-25 tests whether that edge SURVIVES a shortability
floor, or lives only on names you cannot actually borrow/fill/hold.

Pre-registered operationalization (FIXED — no tuning):
  * Signal: cross-sectional 7d price momentum; SHORT ONLY the bottom-decile.
  * SHORTABILITY FLOOR (the crux): restrict the short universe to LIQUID names —
    coins above a documented trailing open-interest floor (trailing 7d mean of
    daily last open_interest_usd, at signal time t — no look-ahead).
  * Two runs of the SHORT leg:
      (a) FULL bottom-decile (all names, no floor);
      (b) bottom-decile RESTRICTED to the floor (the tradeable names).
  * Stop: 2x ATR14 (=1R).  Target: 3R (FIXED).  Exit: HOURLY first-touch.
  * Cost: 4.5 bps/leg taker (2 legs, charged ONCE as round-trip) + 2.5 bps
    adverse entry slip + hourly funding (shorts PAY when funding < 0, receive
    when > 0). G3 fill-realism add-on on the POST-FLOOR names.
  * Zero-drift synthetic control runs ALONGSIDE on BOTH universes; the reported
    "alpha" = real - control (discounts log-normal geometric tilt).

Verdict: does the short-the-losers edge SURVIVE the floor + realistic fills +
funding (tradeable), or vanish once restricted to liquid/shortable names (a
geometry-of-dying-coins artifact)?

Driver writes ONE trials-ledger entry per universe (full, liquid) with a FRESH
param_hash. Read-only on live state; LIVE off.

Usage: python3 revalidate_hyp25_short_continuation.py [--no-write]
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
from g3_gate import MIN_TRADES, EDGE_DECAY_FLOOR             # noqa: E402 (G3 semantics only)

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"
FUNDING_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding_hf"

# ── Pre-registered constants (FIXED — do not tune) ──────────────────────────
DECILE_FRAC = 0.10
MOMENTUM_LOOKBACK = 7
ATR_WINDOW = 14
STOP_ATR_MULT = 2.0        # stop distance = 2x ATR = 1R
TARGET_R = 3.0             # FIXED — the HYP-23 wide target
TAKER_BPS = 4.5            # per leg
ENTRY_SLIP_BPS = 2.5       # adverse entry slip
TIMESTOP_BARS = 20
MIN_COINS_DAY = 20

# ── SHORTABILITY FLOOR (documented) ─────────────────────────────────────────
# Trailing 7d mean of daily last open_interest_usd. A coin is "shortable" only
# if this trailing OI exceeds the floor. Primary floor = $250k (matches the
# repo's MIN_DAILY_NOTIONAL_USD liquidity convention). $100k / $500k / $1m are
# reported as TRANSPARENT SENSITIVITY brackets, not the primary adjudication.
OI_TRAILING_WINDOW = 7
OI_FLOOR_USD = 250_000.0
OI_BRACKETS = [100_000.0, 500_000.0, 1_000_000.0]


def _load_mark_panel(directory: pathlib.Path, columns=None, dropna_col="mark_price"):
    files = sorted(glob.glob(str(directory / "*.parquet")))
    if not files:
        raise SystemExit(f"no parquet under {directory}")
    cols = columns or ["timestamp", "coin", "dex", "mark_price"]
    parts = [pd.read_parquet(f, columns=cols) for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[(df["dex"] == "")].dropna(subset=[dropna_col])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()
    return native


def load_daily_ohlc() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                pd.DataFrame]:
    native = _load_mark_panel(OI_DIR)
    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(open=("mark_price", "first"), high=("mark_price", "max"),
                  low=("mark_price", "min"), close=("mark_price", "last"))
             .reset_index())
    start, end = daily["date"].min(), daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    opens = daily.pivot(index="date", columns="coin", values="open").reindex(cal)
    highs = daily.pivot(index="date", columns="coin", values="high").reindex(cal)
    lows = daily.pivot(index="date", columns="coin", values="low").reindex(cal)
    closes = daily.pivot(index="date", columns="coin", values="close").reindex(cal)
    return opens, highs, lows, closes


def load_daily_oi_usd() -> pd.DataFrame:
    """Daily last open_interest_usd -> wide panel (native perps). Trailing OI
    floor source. open_interest_usd == open_interest * mark_price (verified)."""
    native = _load_mark_panel(
        OI_DIR, columns=["timestamp", "coin", "dex", "open_interest_usd"],
        dropna_col="open_interest_usd",
    )
    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(oi_usd=("open_interest_usd", "last"))
             .reset_index())
    start, end = daily["date"].min(), daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    return daily.pivot(index="date", columns="coin", values="oi_usd").reindex(cal)


def load_hourly_marks(coins, directory=OI_DIR) -> tuple[np.ndarray, list]:
    native = _load_mark_panel(directory)
    native = native[native["coin"].isin(coins)]
    native["h"] = native["timestamp"].dt.floor("h")
    keep = (native.sort_values("timestamp")
            .drop_duplicates(subset=["h", "coin"], keep="last"))
    panel = keep.pivot(index="h", columns="coin", values="mark_price")
    hr_idx = pd.date_range(panel.index.min(), panel.index.max(), freq="h", tz="UTC")
    panel = panel.reindex(hr_idx)
    return panel[coins].to_numpy(dtype=float).T, list(hr_idx.normalize())


def load_daily_funding() -> pd.DataFrame:
    files = sorted(glob.glob(str(FUNDING_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no funding parquet under {FUNDING_DIR}")
    parts = [pd.read_parquet(f, columns=["timestamp", "coin", "dex", "funding_rate"])
             for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[(df["dex"] == "")].dropna(subset=["funding_rate"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()
    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(fund_sum=("funding_rate", "sum")).reset_index())
    start, end = daily["date"].min(), daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    return daily.pivot(index="date", columns="coin", values="fund_sum").reindex(cal)


def indicators(opens, highs, lows, closes):
    coins = list(closes.columns)
    prev_close = closes.shift(1)
    tr = pd.DataFrame(np.maximum.reduce([
        (highs - lows).to_numpy(dtype=float),
        (highs - prev_close).abs().to_numpy(dtype=float),
        (lows - prev_close).abs().to_numpy(dtype=float),
    ]), index=closes.index, columns=closes.columns)
    atr = tr.rolling(ATR_WINDOW, min_periods=ATR_WINDOW).mean()
    mom = closes / closes.shift(MOMENTUM_LOOKBACK) - 1.0

    def arr(df):
        return df.to_numpy(dtype=float).T
    return coins, arr(opens), arr(highs), arr(lows), arr(closes), arr(atr), arr(mom)


def zero_drift_panel(Mh: np.ndarray) -> np.ndarray:
    """Per-coin ZERO-DRIFT hourly panel (cumsum-anchored). Identical to HYP-24."""
    out = np.full_like(Mh, np.nan)
    for c in range(Mh.shape[0]):
        p = Mh[c]
        finite = np.isfinite(p)
        if finite.sum() < 8:
            continue
        idx = np.where(finite)[0]
        pv = p[idx]
        lr = np.diff(np.log(np.maximum(pv, 1e-12)))
        lr = lr - lr.mean()
        cum = np.concatenate(([0.0], np.cumsum(lr)))
        out[c, idx] = pv[0] * np.exp(cum)
    return out


def trailing_oi_matrix(OI: np.ndarray, window: int) -> np.ndarray:
    """Trailing-`window`-day MEAN of daily OI_USD, ending at each day t
    (no look-ahead: uses days <= t). OI is (coins x days), aligned to closes."""
    n_coins, n_days = OI.shape
    out = np.full_like(OI, np.nan)
    for c in range(n_coins):
        row = OI[c]
        # row is daily last OI_USD, NaN where missing
        for t in range(n_days):
            lo = max(0, t - window + 1)
            w = row[lo:t + 1]
            w = w[np.isfinite(w)]
            if w.size:
                out[c, t] = w.mean()
    return out


def run_short_trades(Mh, C, F, ATR, M, OIt, dates, coins, day_to_first,
                     hour_to_day, floor_usd=None, syn_panel=None,
                     day_to_last=None):
    """Short-only backtest of the bottom-decile. Returns list of trade dicts.

    floor_usd=None  -> FULL bottom-decile (no shortability restriction).
    floor_usd=value -> restrict SHORT candidates to names with trailing OI
                       >= floor_usd at signal time t (the tradeable tail).
    syn_panel -> zero-drift control: identical entries/ATR/fees/funding, only
                 the forward price drift is removed.
    """
    n_coins, n_days = C.shape
    n_hours = Mh.shape[1]
    records = []
    fees_frac = (2.0 * TAKER_BPS + ENTRY_SLIP_BPS) / 1e4
    max_hours = TIMESTOP_BARS * 24

    def mark(c, h, base_h):
        if syn_panel is None:
            return Mh[c, h]
        b = syn_panel[c, base_h]
        s = syn_panel[c, h]
        if not (np.isfinite(b) and np.isfinite(s) and b > 0):
            return np.nan
        return Mh[c, base_h] * (s / b)

    for t in range(0, n_days - 1):
        mom_t = M[:, t]
        atr_t = ATR[:, t]
        close_t = C[:, t]
        valid = (np.isfinite(mom_t) & np.isfinite(atr_t) & np.isfinite(close_t)
                 & (atr_t > 0))
        if valid.sum() < MIN_COINS_DAY:
            continue
        start_h = day_to_first.get(dates[t + 1])
        if start_h is None:
            continue
        entry_col = Mh[:, start_h]
        valid &= np.isfinite(entry_col) & (entry_col > 0)
        if valid.sum() < MIN_COINS_DAY:
            continue

        idx = np.where(valid)[0]
        mvals = mom_t[idx]
        order = np.argsort(mvals)
        n = len(order)
        k = max(1, int(n * DECILE_FRAC))
        bot_idx = idx[order[:k]]          # bottom-decile losers -> SHORT ONLY

        # ── shortability floor (the crux) ──────────────────────────────────
        if floor_usd is not None:
            oi_t = OIt[:, t]
            liquid_mask = np.isfinite(oi_t) & (oi_t >= floor_usd)
            bot_idx = bot_idx[liquid_mask[bot_idx]]

        for c in bot_idx:
            entry = Mh[c, start_h]
            risk = 2.0 * atr_t[c]
            risk_pct = risk / entry
            if not (risk_pct > 0) or not np.isfinite(risk_pct):
                continue
            stop = entry + risk                    # short stop above entry
            target = entry - TARGET_R * risk       # short target below entry

            kind = None
            exit_h = None
            end_h = min(start_h + 1 + max_hours, n_hours)
            for h in range(start_h + 1, end_h):
                m = mark(c, h, start_h)
                if not np.isfinite(m):
                    continue
                if m >= stop:
                    kind, exit_h = "stop", h
                    break
                if m <= target:
                    kind, exit_h = "target", h
                    break

            if kind is None:
                kind = "time"
                exit_day = min(t + TIMESTOP_BARS, n_days - 1)
                if not np.isfinite(C[c, exit_day]):
                    continue
            else:
                exit_day = int(hour_to_day[exit_h])
                if exit_day < 0:
                    continue

            if kind == "target":
                gross_r = TARGET_R
            elif kind == "stop":
                gross_r = -1.0
            else:
                if syn_panel is not None and day_to_last is not None:
                    close_h = day_to_last.get(dates[exit_day])
                    epx = (mark(c, close_h, start_h) if close_h is not None
                           else np.nan)
                else:
                    epx = C[c, exit_day]
                if not np.isfinite(epx) or not (epx > 0):
                    continue
                # short: profit = (entry - exit)
                gross_r = (entry - epx) / entry / risk_pct

            fund_frac = 0.0
            for b in range(t + 1, exit_day + 1):
                fv = F[c, b]
                if np.isfinite(fv):
                    fund_frac += fv
            # short (direction=-1): funding_r = +fund_frac/risk_pct
            #   -> shorts RECEIVE when funding>0, PAY when funding<0.
            funding_r = fund_frac / risk_pct
            fee_r = fees_frac / risk_pct
            net_r = gross_r - fee_r + funding_r

            records.append({
                "strategy": "short_continuation_3R",
                "trade_date": dates[t],
                "coin": coins[c],
                "direction": -1,
                "kind": kind,
                "gross_r": float(gross_r),
                "fee_r": float(fee_r),
                "funding_r": float(funding_r),
                "net_r": float(net_r),
                "bars_held": exit_day - t,
                "risk_pct": float(risk_pct),
                "entry": float(entry),
                "stop": float(stop),
                "trailing_oi_usd": (float(OIt[c, t]) if np.isfinite(OIt[c, t])
                                    else None),
            })
    return records


def _pf(rs):
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def _stats(records):
    if not records:
        return {"n_trades": 0}
    net = np.array([r["net_r"] for r in records])
    gross = np.array([r["gross_r"] for r in records])
    fee = np.array([r["fee_r"] for r in records])
    fund = np.array([r["funding_r"] for r in records])
    wins = net > 0
    pos = float(net[wins].sum()) if wins.any() else 0.0
    neg = float(-net[~wins].sum()) if (~wins).any() else 0.0
    return {
        "n_trades": int(len(records)),
        "mean_net_r": float(net.mean()),
        "median_net_r": float(np.median(net)),
        "total_net_r": float(net.sum()),
        "win_rate": float(wins.mean()),
        "pf": pos / neg if neg > 0 else (float("inf") if pos > 0 else 0.0),
        "mean_gross_r": float(gross.mean()),
        "mean_fee_r": float(fee.mean()),
        "mean_funding_r": float(fund.mean()),
        "exit_breakdown": {k: int(sum(1 for r in records if r["kind"] == k))
                           for k in ("target", "stop", "time")},
    }


def _g3_fill_realism(records) -> dict:
    """G3 fill-realism semantics on the post-floor (liquid) short trades.

    optimistic = gross R (frictionless). realistic = gross - fee_r (taker
    round-trip + entry slip, the strategy's own cost). pessimistic = realistic
    - one extra adverse exit leg (one more 4.5bp taker / risk_pct), the
    worst-print-stand-in. Mirrors g3_gate._bar_level_metrics without
    double-counting the strategy's built-in cost.
    """
    opt_rs, real_rs, pess_rs = [], [], []
    for r in records:
        risk_pct = r["risk_pct"]
        if not (risk_pct > 0):
            continue
        extra_r = (TAKER_BPS / 1e4) / risk_pct
        opt_rs.append(r["gross_r"])
        real_rs.append(r["gross_r"] - r["fee_r"])
        pess_rs.append(r["gross_r"] - r["fee_r"] - extra_r)
    if not opt_rs:
        return {"n": 0, "passed": False, "reasons": ["no trades"]}
    opt = float(np.mean(opt_rs))
    real = float(np.mean(real_rs))
    pess_pf = _pf(pess_rs)
    decay = (real / opt) if opt > 0 else float("inf")
    reasons = []
    if len(opt_rs) < MIN_TRADES:
        reasons.append(f"INSUFFICIENT DATA: n={len(opt_rs)} < {MIN_TRADES}")
    if real <= 0:
        reasons.append(f"realistic mean R = {real:.4f} <= 0")
    if pess_pf <= 1.0:
        reasons.append(f"pessimistic PF = {pess_pf:.4f} <= 1.0")
    if opt > 0 and real < EDGE_DECAY_FLOOR * opt:
        reasons.append(f"edge decay: realistic {real:.4f} < "
                       f"{EDGE_DECAY_FLOOR}*opt {opt:.4f}")
    return {
        "n": len(opt_rs),
        "optimistic_mean_r": round(opt, 4),
        "realistic_mean_r": round(real, 4),
        "pessimistic_pf": round(pess_pf, 4),
        "edge_decay_ratio": round(decay, 4) if np.isfinite(decay) else None,
        "passed": len(reasons) == 0,
        "reasons": reasons,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-25 — short-side continuation, gated on shortability ===\n")

    print("loading daily OHLC + funding + OI (real) ...")
    opens, highs, lows, closes = load_daily_ohlc()
    fundsum = load_daily_funding()
    oi_usd = load_daily_oi_usd()
    common = [c for c in closes.columns if c in fundsum.columns and c in oi_usd.columns]
    closes = closes[common]; opens = opens[common]
    highs = highs[common]; lows = lows[common]
    fundsum = fundsum[common]; oi_usd = oi_usd[common]
    print(f"  {len(common)} coins, {closes.shape[0]} days "
          f"({closes.index.min().date()} -> {closes.index.max().date()})")

    coins, O, H, L, C, ATR, M = indicators(opens, highs, lows, closes)
    F = fundsum.to_numpy(dtype=float).T
    OI = oi_usd.to_numpy(dtype=float).T
    dates = [pd.Timestamp(d) for d in closes.index]

    print("computing trailing OI floor matrix (7d mean daily OI_USD) ...")
    OIt = trailing_oi_matrix(OI, OI_TRAILING_WINDOW)

    print("loading hourly marks (real) ...")
    Mh, hr_days = load_hourly_marks(common, OI_DIR)
    uniq_days, first_idx = np.unique(np.asarray(hr_days, dtype=object),
                                     return_index=True)
    day_to_first = {uniq_days[i]: int(first_idx[i])
                    for i in range(len(uniq_days))}
    day_to_last = {}
    for i in range(len(uniq_days)):
        d = uniq_days[i]
        matches = np.where(np.asarray(hr_days, dtype=object) == d)[0]
        if matches.size:
            day_to_last[d] = int(matches[-1])
    date_to_didx = {d: i for i, d in enumerate(dates)}
    hour_to_day = np.array([date_to_didx.get(d, -1) for d in hr_days],
                           dtype=np.int64)
    print(f"  hourly marks: {Mh.shape[0]} coins x {Mh.shape[1]} hours\n")

    # ── zero-drift control panel ────────────────────────────────────────────
    print("building zero-drift control panel ...")
    syn = zero_drift_panel(Mh)

    def run_universe(floor, label):
        if label:
            print(f"-- {label} --")
        real = run_short_trades(Mh, C, F, ATR, M, OIt, dates, coins,
                                day_to_first, hour_to_day, floor_usd=floor)
        ctrl = run_short_trades(Mh, C, F, ATR, M, OIt, dates, coins,
                                day_to_first, hour_to_day, floor_usd=floor,
                                syn_panel=syn, day_to_last=day_to_last)
        return real, ctrl

    # (a) FULL bottom-decile
    full_real, full_ctrl = run_universe(None, "(a) FULL bottom-decile (no floor)")
    # (b) LIQUID bottom-decile (primary floor)
    liq_real, liq_ctrl = run_universe(OI_FLOOR_USD,
                                      f"(b) LIQUID bottom-decile (OI>={OI_FLOOR_USD:,.0f})")

    def fmt(s):
        if not s.get("n_trades"):
            return "(no trades)"
        return (f"n={s['n_trades']} net={s['mean_net_r']:+.4f}R "
                f"win={s['win_rate']:.3f} PF={s['pf']:.3f} "
                f"gross={s['mean_gross_r']:+.4f}R "
                f"fee={s['mean_fee_r']:.4f}R fund={s['mean_funding_r']:+.4f}R "
                f"exits={s['exit_breakdown']}")

    rs_f = _stats(full_real); cs_f = _stats(full_ctrl)
    rs_l = _stats(liq_real); cs_l = _stats(liq_ctrl)

    print("\n  FULL   REAL :", fmt(rs_f))
    print("  FULL   CTRL :", fmt(cs_f))
    print("  LIQ    REAL :", fmt(rs_l))
    print("  LIQ    CTRL :", fmt(cs_l))

    def alpha(rs, cs, key):
        if not rs.get("n_trades") or not cs.get("n_trades"):
            return float("nan")
        return rs[key] - cs[key]

    print("\n  alpha (real - control) mean net R:")
    print(f"    FULL bottom-decile : {alpha(rs_f, cs_f, 'mean_net_r'):+.4f}R")
    print(f"    LIQUID bottom-decile: {alpha(rs_l, cs_l, 'mean_net_r'):+.4f}R")

    # ── sensitivity brackets ────────────────────────────────────────────────
    print(f"\n  sensitivity brackets (trailing OI floor, mean net R real/ctrl/alpha):")
    for fl in OI_BRACKETS:
        r, c = run_universe(fl, "")
        s_r, s_c = _stats(r), _stats(c)
        a = (s_r["mean_net_r"] - s_c["mean_net_r"]) if (
            s_r.get("n_trades") and s_c.get("n_trades")) else float("nan")
        print(f"    floor ${fl:>9,.0f}: n={s_r.get('n_trades',0):>6}  "
              f"real={s_r.get('mean_net_r', float('nan')):+.4f}R  "
              f"ctrl={s_c.get('mean_net_r', float('nan')):+.4f}R  "
              f"alpha={a:+.4f}R")

    # ── G3 fill-realism on the POST-FLOOR (liquid/tradeable) names ──────────
    g3 = _g3_fill_realism(liq_real)
    print("\n  G3 fill-realism (post-floor liquid short leg):")
    print(f"    n={g3['n']}  optimistic={g3['optimistic_mean_r']:+.4f}R  "
          f"realistic={g3['realistic_mean_r']:+.4f}R  "
          f"pessimistic_pf={g3['pessimistic_pf']:.3f}  "
          f"edge_decay={g3['edge_decay_ratio']}  passed={g3['passed']}")
    if g3["reasons"]:
        print("    reasons:", "; ".join(g3["reasons"]))

    # trailing OI distribution of the SELECTED short names (documentation)
    def oi_quantiles(records):
        ois = np.array([r["trailing_oi_usd"] for r in records
                        if r["trailing_oi_usd"] is not None])
        if not ois.size:
            return {}
        return {q: float(np.percentile(ois, q * 100))
                for q in (0.25, 0.5, 0.75)}

    print("\n  trailing OI of selected short names (USD):")
    print(f"    FULL : {oi_quantiles(full_real)}")
    print(f"    LIQUID: {oi_quantiles(liq_real)}")

    # ── write trials ────────────────────────────────────────────────────────
    universe = sorted(common)
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()
    period_start = str(closes.index.min().date())
    period_end = str(closes.index.max().date())

    def _write(label, floor_usd, rs, cs):
        param_dict = {
            "construction": "short_side_continuation_shortability_gated",
            "signal": "cross_sectional_7d_price_momentum",
            "direction": "short_only_bottom_decile",
            "decile_frac": DECILE_FRAC,
            "stop_atr_mult": STOP_ATR_MULT,
            "atr_window": ATR_WINDOW,
            "momentum_lookback": MOMENTUM_LOOKBACK,
            "target_r": TARGET_R,
            "taker_bps": TAKER_BPS,
            "entry_slip_bps": ENTRY_SLIP_BPS,
            "timestop_bars": TIMESTOP_BARS,
            "min_coins_day": MIN_COINS_DAY,
            "exit_resolution": "hourly_first_touch",
            "funding": "shorts_pay_negative_receive_positive",
            "shortability_floor_usd": floor_usd,
            "oi_trailing_window_days": OI_TRAILING_WINDOW,
            "zero_drift_control": "per_coin_hourly_log_return_demeaned",
            "no_lookahead": True,
            "leverage": "none_-1x_max",
            "live": "off",
        }
        param_hash = hashlib.sha256(
            json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
        result = {
            "construction": param_dict["construction"],
            "shortability_floor_usd": floor_usd,
            "n_coins_universe": len(universe),
            "n_trades": rs["n_trades"],
            "mean_net_r": round(rs["mean_net_r"], 6) if rs.get("n_trades") else None,
            "median_net_r": round(rs["median_net_r"], 6) if rs.get("n_trades") else None,
            "total_net_r": round(rs["total_net_r"], 6) if rs.get("n_trades") else None,
            "win_rate": round(rs["win_rate"], 6) if rs.get("n_trades") else None,
            "profit_factor": round(rs["pf"], 6) if rs.get("n_trades") else None,
            "mean_gross_r": round(rs["mean_gross_r"], 6) if rs.get("n_trades") else None,
            "mean_fee_r": round(rs["mean_fee_r"], 6) if rs.get("n_trades") else None,
            "mean_funding_r": round(rs["mean_funding_r"], 6) if rs.get("n_trades") else None,
            "exit_breakdown": rs["exit_breakdown"],
            "control_mean_net_r": round(cs["mean_net_r"], 6) if cs.get("n_trades") else None,
            "alpha_mean_net_r": (round(rs["mean_net_r"] - cs["mean_net_r"], 6)
                                 if rs.get("n_trades") and cs.get("n_trades") else None),
            "exit_resolution": "hourly_first_touch",
            "no_lookahead": True,
            "leverage": "none_-1x_max",
            "live": "off",
            "data_source": "hl_oi_hf + hl_funding_hf parquet (native perps, 3.5y)",
        }
        if label == "LIQUID":
            result["g3_fill_realism"] = g3
        if not args.no_write:
            e = ledger.increment_trial("HYP-25", param_hash, universe_hash,
                                       period_start, period_end, result)
            print(f"\n  wrote HYP-25 {label}: param_hash={param_hash[:16]}...  "
                  f"chain_hash={e['chain_hash'][:16]}...")
        else:
            print(f"\n  [--no-write] HYP-25 {label}: param_hash={param_hash[:16]}...")

    _write("FULL", None, rs_f, cs_f)
    _write("LIQUID", OI_FLOOR_USD, rs_l, cs_l)

    # scratch JSON for the report
    out = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "hyp25_result.json"
    payload = {
        "full": {"real": _stats(full_real), "control": _stats(full_ctrl)},
        "liquid": {"real": rs_l, "control": cs_l},
        "alpha_full": alpha(rs_f, cs_f, "mean_net_r"),
        "alpha_liquid": alpha(rs_l, cs_l, "mean_net_r"),
        "g3_liquid": g3,
        "oi_floor_usd": OI_FLOOR_USD,
        "oi_brackets": OI_BRACKETS,
    }
    with open(out, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"  result saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())