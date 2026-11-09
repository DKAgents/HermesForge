"""backtest_hyp37_trend_sleeve.py — HYP-37 execution (time-series trend on majors).

Directive §8 "HYP-33" (renumbered HYP-37 — see the pre-registration note). FIXED
operationalization — do NOT tune.

Tests whether a vol-targeted time-series trend on BTC/ETH/SOL, executed as a
MAKER (M-2 cost symmetry), with M-3 no-trade buffering and HAR-RV vol targeting,
survives the amended gates. Evaluated as a SLEEVE alongside the delta-neutral
funding carry (correlation + combined drawdown).

GATES / amendments applied:
  M-2 maker-cost symmetry   — maker AND taker variants, maker must clear.
  M-3 no-trade band         — sign hysteresis at round-trip cost.
  M-5 MDE                   — nulls reported "not detected above MDE X".
  M-6 trial accounting      — DSR deflated by hypothesis-family count, not all rows.
  M-7 IC-by-horizon         — 1..20d non-overlapping forward IC.
  G4 CPCV                   — 10th-pct fold PF (non-overlapping weekly blocks).
  G5 DSR                    — DSR >= 0.95 under M-6 accounting.

FALSIFICATION (pre-registered): at MAKER cost, 10th-pct fold PF < 1.0, OR DSR below
threshold under M-6 accounting -> NOT promoted.

Usage: python3 backtest_hyp37_trend_sleeve.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sqlite3
import sys
import math

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import trials_ledger as ledger  # noqa: E402
import cpcv_harness as cpcv  # noqa: E402
import mde  # noqa: E402

MD = pathlib.Path.home() / ".hermes" / "market_data"
PRICE_DIR = MD / "crypto"
FUNDING_DB = MD / "hl_funding" / "funding.db"

# ── Pre-registered constants (FIXED — no tuning) ────────────────────────────
CURRENCIES = ["BTC", "ETH", "SOL"]
LOOKBACKS = [20, 60, 120]
BLEND_W = [0.5, 0.3, 0.2]            # 20/60/120-day momentum blend weights
HAR_WIN = {"d": 1, "w": 5, "m": 21}  # daily/weekly/monthly realized-vol windows
HAR_W = [0.25, 0.35, 0.40]           # HAR-RV weights (d, w, m)
VOL_TARGET_ANN = 0.20                # 20% annualized vol target
DAYS_PER_YEAR = 365
SIGMA_DAILY_TARGET = VOL_TARGET_ANN / math.sqrt(DAYS_PER_YEAR)
POS_CAP = 1.0                        # no leverage

# Cost model (fee_source crypto base tier): maker 1.5 / taker 4.5 bps, slip 2.5.
MAKER_BPS = 1.5
TAKER_BPS = 4.5
SLIP_BPS = 2.5
FUNDING_BPS = 0.5                    # fee_source's ~1-settlement accrual (round-trip ref only)
MAKER_RT_BPS = 2 * MAKER_BPS + SLIP_BPS + FUNDING_BPS   # 6.0
TAKER_RT_BPS = 2 * TAKER_BPS + SLIP_BPS + FUNDING_BPS   # 12.0
MAKER_ONE_WAY = MAKER_BPS + SLIP_BPS / 2.0              # 2.75
TAKER_ONE_WAY = TAKER_BPS + SLIP_BPS / 2.0              # 5.75

IC_HORIZONS = [1, 2, 3, 5, 10, 20]   # M-7 IC-by-horizon
BLOCK_DAYS = 5                        # non-overlapping weekly blocks for CPCV/DSR


# ── Loaders ─────────────────────────────────────────────────────────────────
def load_prices() -> dict[str, pd.Series]:
    out = {}
    for c in CURRENCIES:
        df = pd.read_parquet(PRICE_DIR / f"{c}.parquet")
        s = df["close"].astype(float)
        s.index = pd.to_datetime(s.index).normalize()
        s = s[~s.index.duplicated(keep="last")].sort_index()
        out[c] = s
    return out


def load_funding() -> dict[str, pd.DataFrame]:
    """Hourly HL funding per coin (real, for carry sleeve + funding sensitivity)."""
    con = sqlite3.connect(FUNDING_DB)
    out = {}
    for c in CURRENCIES:
        df = pd.read_sql_query(
            "SELECT time, funding_rate, premium FROM funding WHERE coin=? ORDER BY time",
            con, params=(c,),
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        df = df.set_index("time")
        df.index = df.index.tz_convert(None)  # naive UTC to align with price index
        out[c] = df
    con.close()
    return out


# ── Feature build (causal: uses info <= t) ──────────────────────────────────
def trend_score(close: pd.Series) -> pd.Series:
    s = 0.0
    for lb, w in zip(LOOKBACKS, BLEND_W):
        s = s + w * np.log(close / close.shift(lb))
    return s


def har_vol_forecast(close: pd.Series) -> pd.Series:
    r = np.log(close / close.shift(1))
    rv = r ** 2
    rv_d = rv
    rv_w = rv.rolling(HAR_WIN["w"]).mean()
    rv_m = rv.rolling(HAR_WIN["m"]).mean()
    fvar = (HAR_W[0] * rv_d + HAR_W[1] * rv_w + HAR_W[2] * rv_m)
    return np.sqrt(fvar)


# ── Strategy engine (returns daily gross + net return series) ───────────────
def run_strategy(close: pd.Series, long_short: bool, maker: bool) -> dict:
    score = trend_score(close)
    vol = har_vol_forecast(close)
    r = np.log(close / close.shift(1))

    one_way = MAKER_ONE_WAY if maker else TAKER_ONE_WAY
    band = (MAKER_RT_BPS if maker else TAKER_RT_BPS) / 1e4

    # aligned arrays (drop warmup NaNs from score/vol)
    df = pd.DataFrame({"score": score, "vol": vol, "r": r}).dropna()
    score_v = df["score"].to_numpy()
    vol_v = df["vol"].to_numpy()
    r_v = df["r"].to_numpy()
    n = len(df)

    scale = np.minimum(POS_CAP, SIGMA_DAILY_TARGET / np.maximum(vol_v, 1e-12))
    sign = np.where(score_v > 0, 1.0, -1.0) if long_short else np.where(score_v > 0, 1.0, 0.0)
    raw_target = sign * scale

    # M-3 sign hysteresis + full vol-target sizing within the chosen direction.
    w = np.zeros(n)
    cur = 0.0
    for t in range(n):
        target = raw_target[t]
        tsign = 1.0 if target > 0 else (-1.0 if target < 0 else 0.0)
        csign = 1.0 if cur > 0 else (-1.0 if cur < 0 else 0.0)
        if tsign == csign:
            # same direction: update size only (vol-target), keep sign
            new = tsign * scale[t]
            w[t] = new
        else:
            # direction change requested: require |score| >= band (M-3)
            if abs(score_v[t]) >= band:
                w[t] = tsign * scale[t]
            else:
                w[t] = cur
        cur = w[t]

    # PnL: gross[t] = w[t-1]*r[t]; txn[t] = |w[t]-w[t-1]| * one_way/1e4
    w_prev = np.concatenate([[0.0], w[:-1]])
    gross = w_prev * r_v
    txn = np.abs(w - w_prev) * (one_way / 1e4)
    net = gross - txn

    return {
        "net": net, "gross": gross, "w": w, "score": score_v, "vol": vol_v,
        "index": df.index, "turnover": float(np.abs(np.diff(w)).sum()),
        "n_days": int(n), "n_flips": int(np.sum(np.sign(w[1:]) != np.sign(w[:-1]))),
        "scale_turnover": float(np.abs(np.diff(scale)).sum()),
        "avg_abs_w": float(np.abs(w).mean()),
    }


# ── Stats ───────────────────────────────────────────────────────────────────
def annualized_sharpe(daily: np.ndarray) -> float:
    d = daily[np.isfinite(daily)]
    if d.size < 2 or d.std(ddof=1) <= 0:
        return 0.0
    return float(d.mean() / d.std(ddof=1) * math.sqrt(DAYS_PER_YEAR))


def max_drawdown(daily: np.ndarray) -> float:
    eq = np.cumprod(1.0 + daily)
    peak = np.maximum.accumulate(eq)
    return float((eq / peak - 1.0).min())


def cagr(daily: np.ndarray) -> float:
    eq = np.cumprod(1.0 + daily)
    n = len(eq)
    if n < 2:
        return 0.0
    return float(eq[-1] ** (DAYS_PER_YEAR / n) - 1.0)


def block_returns(daily: np.ndarray, index, block_days: int) -> tuple[np.ndarray, list]:
    """Non-overlapping block returns + trade dicts for CPCV (pnl in bps)."""
    s = pd.Series(daily, index=index)
    blocks = []
    rets = []
    g = (s.index - s.index[0]).days // block_days
    for _, grp in s.groupby(g):
        if len(grp) < 1:
            continue
        r = (1.0 + grp).prod() - 1.0
        rets.append(r)
        blocks.append({
            "entry_time": int(grp.index[0].value // 1e9),
            "exit_time": int(grp.index[-1].value // 1e9),
            "pnl_bps": float(r * 1e4),
        })
    return np.array(rets), blocks


def ic_by_horizon(score: np.ndarray, close: pd.Series, horizons, index) -> list[dict]:
    """M-7: corr(score_t, forward h-day log-return), NON-OVERLAPPING (stride h)."""
    c = close.reindex(index)
    out = []
    for h in horizons:
        fwd = np.log(c.shift(-h) / c)
        valid = np.isfinite(score) & np.isfinite(fwd.to_numpy())
        s = score[valid]
        f = fwd.to_numpy()[valid]
        # non-overlapping stride-h
        s = s[::h]
        f = f[::h]
        n = len(s)
        if n < 8:
            out.append({"h": h, "ic": None, "n": n, "t": None, "p": None})
            continue
        ic = float(np.corrcoef(s, f)[0, 1])
        if not np.isfinite(ic) or abs(ic) >= 1.0:
            t = p = float("nan")
        else:
            t = ic * math.sqrt(n - 2) / math.sqrt(1 - ic * ic)
            p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
        out.append({"h": h, "ic": round(ic, 4), "n": int(n),
                    "t": round(float(t), 3), "p": round(float(p), 4)})
    return out


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ── M-6 family counting ─────────────────────────────────────────────────────
def m6_family_counts() -> dict:
    """Count distinct signal families in the trials ledger (cluster variants)."""
    ids = set()
    for e in ledger.read_all():
        h = e.get("hypothesis_id", "")
        if h:
            ids.add(h)
    suffixes = ["-phase1a", "-phase1b", "-phase2", "-phase3", "-phase4",
                "-robustness-sweep", "-robustness", "-g3-capacity", "-g4g5",
                "-correct-cost", "-data-gate", "-revalidation", "-walkforward",
                "-v2", "-v3", "-sweep", "_g3_capacity", "_correct_cost",
                "_robustness", "-correct-cost-robustness"]
    def family_of(hid: str) -> str:
        base = hid
        for suf in suffixes:
            base = base.replace(suf, "")
        # collapse STR-YYYYMMDD-name -> name root (rough)
        import re
        base = re.sub(r"STR-\d{8}-", "", base)
        base = re.sub(r"STR-\d{6,8}", "STR", base)
        return base
    families = {family_of(h) for h in ids}
    # trend/momentum family subset (prior search pressure for THIS family)
    trend_kw = ["momentum", "trend", "xsmom", "continuation", "HYP-16",
                "HYP-18", "HYP-24", "HYP-25", "HYP-22"]
    trend_fam = {f for f in families if any(k in f for k in trend_kw)}
    return {
        "n_rows": ledger.count(),
        "n_distinct_ids": len(ids),
        "n_families": len(families),
        "n_trend_family": len(trend_fam),
    }


# ── Carry sleeve (real funding) ─────────────────────────────────────────────
def carry_daily_returns(funding: dict[str, pd.DataFrame], start, end) -> pd.Series:
    """Delta-neutral carry daily return = short-perp receives funding (gross,
    pre-churn, pre-basis-drift). Equal-weight BTC/ETH/SOL."""
    series = {}
    for c in CURRENCIES:
        f = funding[c]["funding_rate"].astype(float)
        daily = f.resample("1D").sum()  # short receives +funding each hour
        series[c] = daily
    carry = pd.DataFrame(series).mean(axis=1)
    return carry[(carry.index >= start) & (carry.index <= end)]


def funding_pnl_signed(w: np.ndarray, index, funding, coin) -> float:
    """Funding P&L on the trend sleeve: long pays +funding, short receives.
    Sum over overlap window; returns total in return-units."""
    f = funding[coin]["funding_rate"].astype(float)
    daily_f = f.resample("1D").sum()
    # align w (daily position) to funding days
    w_s = pd.Series(w, index=index)
    j = pd.concat([w_s.rename("w"), daily_f.rename("f")], axis=1, join="inner").dropna()
    # long (w>0) pays funding: pnl = -w * f
    return float((-j["w"] * j["f"]).sum())


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-37 time-series trend on majors (vol-targeted, buffered) ===\n")
    prices = load_prices()
    funding = load_funding()

    print(f"universe {CURRENCIES}; trend 20/60/120 blend; HAR-RV vol-target "
          f"{VOL_TARGET_ANN*100:.0f}% ann; M-3 band maker {MAKER_RT_BPS:.1f}bps / "
          f"taker {TAKER_RT_BPS:.1f}bps\n")

    # ── per-coin + portfolio strategy (4 variants) ──────────────────────────
    variants = [("long/flat", "maker"), ("long/flat", "taker"),
                ("long/short", "maker"), ("long/short", "taker")]
    strat = {}
    for coin in CURRENCIES:
        close = prices[coin]
        for ls, mk in variants:
            key = (coin, ls, mk)
            strat[key] = run_strategy(close, long_short=(ls == "long/short"),
                                      maker=(mk == "maker"))

    # portfolio = equal-weight across coins (align common index)
    common_idx = strat[(CURRENCIES[0], "long/flat", "maker")]["index"]
    for c in CURRENCIES[1:]:
        common_idx = common_idx.intersection(strat[(c, "long/flat", "maker")]["index"])

    results = {}
    print("=== STRATEGY (portfolio, equal-weight BTC/ETH/SOL) ===\n")
    for ls, mk in variants:
        nets = []
        for c in CURRENCIES:
            net = pd.Series(strat[(c, ls, mk)]["net"], index=strat[(c, ls, mk)]["index"])
            nets.append(net.reindex(common_idx))
        port = pd.concat(nets, axis=1).mean(axis=1).to_numpy()
        sharpe = annualized_sharpe(port)
        dd = max_drawdown(port)
        cg = cagr(port)
        # turnover (sum across coins)
        to = sum(strat[(c, ls, mk)]["turnover"] for c in CURRENCIES) / len(CURRENCIES)
        results[(ls, mk)] = {"port": port, "idx": common_idx, "sharpe": sharpe,
                             "dd": dd, "cagr": cg, "turnover": to}
        print(f"  {ls:10s} {mk:5s}: CAGR {cg*100:+7.2f}%/yr | Sharpe {sharpe:+5.2f} "
              f"| maxDD {dd*100:+6.1f}% | ann.turnover {to:.1f}x")

    # turnover diagnostics (maker long/flat)
    d = strat[(CURRENCIES[0], "long/flat", "maker")]
    print(f"\n  [diag] BTC maker long/flat: n_flips={d['n_flips']} "
          f"scale_turnover={d['scale_turnover']:.1f}x over {d['n_days']}d "
          f"({d['scale_turnover']/d['n_days']*365:.1f}x/yr scale-churn) | "
          f"avg|w|={d['avg_abs_w']:.2f}")

    print()

    # ── M-7 IC by horizon (portfolio-level, using BTC signal as proxy) ──────
    print("=== M-7 IC-BY-HORIZON (non-overlapping, portfolio trend score) ===\n")
    # portfolio-level score = mean of per-coin scores (equal weight), and
    # portfolio forward return = mean of per-coin forward returns
    score_df = pd.DataFrame({c: pd.Series(strat[(c, "long/flat", "maker")]["score"],
                                          index=strat[(c, "long/flat", "maker")]["index"])
                             for c in CURRENCIES}).reindex(common_idx)
    port_score = score_df.mean(axis=1).to_numpy()
    # forward return on the portfolio close = equal-weight of closes
    port_close = pd.DataFrame({c: prices[c].reindex(common_idx) for c in CURRENCIES}).mean(axis=1)
    ic = ic_by_horizon(port_score, port_close, IC_HORIZONS, common_idx)
    for row in ic:
        if row["ic"] is None:
            print(f"  h={row['h']:>2}d: n={row['n']} (insufficient)")
        else:
            print(f"  h={row['h']:>2}d: IC={row['ic']:+.4f} (t={row['t']:+.2f}, "
                  f"p={row['p']:.3f}, n={row['n']})")
    print()

    # ── G4 CPCV + G5 DSR (maker long/short, the strongest candidate) ────────
    print("=== G4 CPCV + G5 DSR (maker variants; non-overlapping weekly blocks) ===\n")
    m6 = m6_family_counts()
    print(f"  M-6 trial accounting: {m6['n_rows']} ledger rows | "
          f"{m6['n_distinct_ids']} distinct IDs | {m6['n_families']} families | "
          f"{m6['n_trend_family']} trend/momentum-family")
    n_trials_m6 = max(1, m6["n_trend_family"])

    cpcv_out = {}
    for ls in ["long/flat", "long/short"]:
        for mk in ["maker", "taker"]:
            port = results[(ls, mk)]["port"]
            idx = results[(ls, mk)]["idx"]
            weekly, trades = block_returns(port, idx, BLOCK_DAYS)
            cp = cpcv.run_cpcv(trades, n_groups=12, k_test=2,
                               n_trials_from_ledger=n_trials_m6,
                               holding_horizon_bars=2, embargo_bars=2)
            pfs = sorted(m["pf"] for m in cp["split_metrics"])
            pct10 = pfs[max(0, int(0.10 * len(pfs)) - 1)] if pfs else 0.0
            # DSR on non-overlapping weekly returns
            wk = weekly[np.isfinite(weekly)]
            sw = float(wk.mean() / wk.std(ddof=1)) if wk.size > 2 and wk.std(ddof=1) > 0 else 0.0
            sk = float(pd.Series(wk).skew()) if wk.size > 3 else 0.0
            ku = float(pd.Series(wk).kurt()) if wk.size > 4 else 0.0
            dsr_m6 = cpcv.compute_dsr(sw, sk, ku, n_trials_m6, len(wk))
            dsr_168 = cpcv.compute_dsr(sw, sk, ku, 168, len(wk))
            dsr_137 = cpcv.compute_dsr(sw, sk, ku, m6["n_distinct_ids"], len(wk))
            mde_dsr = mde.mde_sharpe_dsr(len(wk), n_trials_m6)
            cpcv_out[(ls, mk)] = {
                "n_blocks": len(wk), "pbo": cp["pbo"], "dsr_m6": dsr_m6,
                "dsr_137": dsr_137, "dsr_168": dsr_168, "sharpe_weekly": sw,
                "pct10_pf": pct10, "median_pf": float(np.median(pfs)) if pfs else 0.0,
                "mde_dsr": mde_dsr,
            }
            print(f"  {ls:10s} {mk:5s}: n={len(wk)} blocks | 10th-pct PF {pct10:.3f} "
                  f"| median PF {cpcv_out[(ls, mk)]['median_pf']:.3f} | "
                  f"PBO {cp['pbo']:.2f} | DSR(m6={n_trials_m6}) {dsr_m6:.3f} "
                  f"| DSR(137) {dsr_137:.3f} | DSR(168) {dsr_168:.3f}")
    print()

    # ── Sleeve correlation + combined drawdown vs carry ─────────────────────
    print("=== SLEEVE vs CARRY (real HL funding, overlap window) ===\n")
    fstart = max(min(funding[c].index.min() for c in CURRENCIES),
                 common_idx.min())
    fend = min(max(funding[c].index.max() for c in CURRENCIES),
               common_idx.max())
    carry = carry_daily_returns(funding, fstart, fend)
    carry_ann = float(carry.mean() * DAYS_PER_YEAR)

    sleeve = results[("long/short", "maker")]["port"]
    sleeve_s = pd.Series(sleeve, index=common_idx)
    sleeve_win = sleeve_s[(sleeve_s.index >= fstart) & (sleeve_s.index <= fend)]
    j = pd.concat([sleeve_win.rename("sleeve"), carry.rename("carry")],
                  axis=1, join="inner").dropna()
    corr = float(j["sleeve"].corr(j["carry"])) if len(j) > 2 else float("nan")

    # combined 50/50
    comb = (0.5 * j["sleeve"] + 0.5 * j["carry"]).to_numpy()
    comb_sharpe = annualized_sharpe(comb)
    comb_dd = max_drawdown(comb)
    comb_cagr = cagr(comb)
    sleeve_win_arr = j["sleeve"].to_numpy()
    print(f"  carry daily mean (gross funding) = {carry.mean()*1e4:.2f} bps/day "
          f"= {carry_ann*100:.1f}% APR")
    print(f"  overlap window {fstart.date()} -> {fend.date()} ({len(j)} days)")
    print(f"  correlation(sleeve, carry) = {corr:+.3f}")
    print(f"  sleeve Sharpe {annualized_sharpe(sleeve_win_arr):+.2f} | "
          f"carry Sharpe {annualized_sharpe(j['carry'].to_numpy()):+.2f}")
    print(f"  COMBINED 50/50: CAGR {comb_cagr*100:+.2f}%/yr | Sharpe {comb_sharpe:+.2f} "
          f"| maxDD {comb_dd*100:+.1f}%")
    print(f"  sleeve-alone maxDD {max_drawdown(sleeve_win_arr)*100:+.1f}% | "
          f"carry-alone maxDD {max_drawdown(j['carry'].to_numpy())*100:+.1f}%")

    # funding interaction: long-trend sleeve PAYS funding
    print("\n  Funding interaction (sleeve vs carry):")
    fp = {}
    for c in CURRENCIES:
        w = strat[(c, "long/short", "maker")]["w"]
        idx = strat[(c, "long/short", "maker")]["index"]
        fp[c] = funding_pnl_signed(w, idx, funding, c)
        print(f"    {c}: trend-sleeve funding P&L {fp[c]*1e4:+.2f} bps over overlap "
              f"(signed: long pays / short receives)")
    tot_fp = sum(fp.values()) / len(CURRENCIES)
    print(f"    sleeve mean funding P&L {tot_fp*1e4:+.2f} bps vs carry gross "
          f"{carry.sum()*1e4:+.2f} bps -> sleeve funding is "
          f"{tot_fp/carry.sum()*100:+.1f}% of carry gross (offset)")
    print()

    # ── Verdict ─────────────────────────────────────────────────────────────
    print("=== FALSIFICATION VERDICT (maker cost) ===\n")
    promote = {}
    for ls in ["long/flat", "long/short"]:
        mk = cpcv_out[(ls, "maker")]
        tk = cpcv_out[(ls, "taker")]
        g4_pass = mk["pct10_pf"] >= 1.0
        g5_pass = mk["dsr_m6"] >= 0.95
        maker_better = mk["sharpe_weekly"] >= tk["sharpe_weekly"]
        promote[ls] = bool(g4_pass and g5_pass)
        print(f"  {ls:10s}: 10th-pct PF {mk['pct10_pf']:.3f} (>=1.0: {g4_pass}) | "
              f"DSR(m6) {mk['dsr_m6']:.3f} (>=0.95: {g5_pass}) | "
              f"maker>=taker Sharpe {maker_better} | -> "
              f"{'PROMOTE' if promote[ls] else 'NOT PROMOTED'}")
        if not g5_pass:
            print(f"      " + mde.format_null_verdict(mk["sharpe_weekly"],
                  mk["mde_dsr"], "Sharpe"))

    any_promote = any(promote.values())
    print(f"\n  ANY PROMOTABLE at maker cost: {any_promote}")

    # ── Write trial ─────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "time_series_trend_vol_targeted_sleeve",
        "universe": CURRENCIES, "venue": "hyperliquid_daily",
        "lookbacks": LOOKBACKS, "blend_weights": BLEND_W,
        "har_rv_weights": HAR_W, "har_windows": list(HAR_WIN.values()),
        "vol_target_ann": VOL_TARGET_ANN, "pos_cap": POS_CAP,
        "m3_buffer_bps": {"maker": MAKER_RT_BPS, "taker": TAKER_RT_BPS},
        "cost": {"maker_one_way": MAKER_ONE_WAY, "taker_one_way": TAKER_ONE_WAY,
                 "slip_bps": SLIP_BPS, "funding_separate": True},
        "leverage": "none", "live": "off", "non_overlapping": True,
        "gates": "M2/M3/M5/M6/M7 + G4/G5",
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(sorted(CURRENCIES)).encode()).hexdigest()

    result = {
        "construction": "time_series_trend_vol_targeted_sleeve",
        "venue": "hyperliquid_daily",
        "universe": CURRENCIES,
        "leverage": "none", "live": "off", "no_lookahead": True,
        "variants": {
            f"{ls}_{mk}": {"cagr": results[(ls, mk)]["cagr"],
                           "sharpe_ann": results[(ls, mk)]["sharpe"],
                           "max_dd": results[(ls, mk)]["dd"],
                           "turnover": results[(ls, mk)]["turnover"]}
            for (ls, mk) in variants
        },
        "ic_by_horizon": ic,
        "cpcv_dsr": {f"{ls}_{mk}": cpcv_out[(ls, mk)] for (ls, mk) in variants},
        "m6_family_counts": m6,
        "sleeve_vs_carry": {"correlation": corr, "carry_apr_gross": carry_ann,
                            "combined_50_50": {"cagr": comb_cagr,
                                               "sharpe": comb_sharpe,
                                               "max_dd": comb_dd},
                            "funding_pnl_per_coin_bps": {c: fp[c] * 1e4 for c in CURRENCIES},
                            "sleeve_funding_offset_pct_of_carry": tot_fp / carry.sum() * 100
                            if carry.sum() != 0 else None},
        "promote": promote,
        "verdict": (
            f"Time-series trend on majors ({CURRENCIES}), 20/60/120 blend, HAR-RV "
            f"vol-target {VOL_TARGET_ANN*100:.0f}%, M-3 buffered, maker+taker. "
            f"See report for the gate-by-gate verdict; ANY_PROMOTABLE={any_promote}."
        ),
    }

    if not args.no_write:
        e = ledger.increment_trial("HYP-37", param_hash, universe_hash,
                                   "2020-08-19", "2026-11-08", result)
        print(f"\nwrote trial HYP-37 param_hash={e['param_hash'][:16]}... "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
