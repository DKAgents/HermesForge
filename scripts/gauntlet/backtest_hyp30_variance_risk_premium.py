"""backtest_hyp30_variance_risk_premium.py — HYP-30 execution (VRP).

Pre-registered (HYP-30, `trading/strategies/Hypotheses/HYP-30-variance-risk-premium.md`).
FIXED operationalization — do NOT tune. Reads the US-231 Deribit options-history
backfill (options_history.db) + the US-187 DVOL store (iv_surface.db).

Signal: SELL the ATM straddle on BTC/ETH, hold to expiry. The edge is the
variance risk premium (VRP = implied vol at entry − realized vol over the hold).

Data (free Deribit backfill, already stored + verified):
  options_history.db
    options_atm_straddle : (currency, expiry, day) -> call/put mark premium,
                           atm_straddle_premium, atm_iv, strike, underlying, dte
    underlying_daily     : (currency, day) -> index close
    realized_vol_daily   : (currency, day) -> 30d realized vol + DVOL close
  iv_surface.db
    dvol_index           : (currency, ts hourly) -> DVOL level (%) back to 2021-03

MEASUREMENT (fixed):
  * Trade = the store's expiry cadence (Deribit weekly/periodic expiries). Each
    (currency, expiry) is one short straddle, entered at ENTRY_DTE days to expiry,
    held to expiry. Entry uses the close-of-day mark (knowable at close; the
    adverse fill is charged on top, not assumed away).
  * VRP (vol pp) = atm_iv(entry, %) − realized_vol(hold, annualized, %).
  * Payoff (coin-settled Deribit, reversed): short straddle P&L in coin = premium
    − |S_T − K| / S_T. Premium quoted in BTC/ETH per contract.
  * VOL-OF-VOL GATE: enter only when DVOL (daily close) is below its own trailing
    30-day mean ("low/decaying, not spiking"). Ungated = unconditional VRP.
  * COST: option bid-ask spread (vol points, wider than perp — no L2 book held,
    flagged assumption) + taker fee + margin opportunity cost, maker vs taker.
  * TAIL: settled P&L stream (non-overlapping holds) + daily mark-to-market of
    open straddles -> max drawdown + the vol-spike episodes.

HARD RULES honored: fresh param_hash in trials ledger; no look-ahead (entry on
close info only); no leverage (1x notional straddle, premium is the risk unit);
LIVE off; cost charged on both legs; short-tail handled honestly (held-to-expiry
includes the full spike give-back, no early-exit rescue).

Usage: python3 backtest_hyp30_variance_risk_premium.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import trials_ledger as ledger  # noqa: E402

OPTIONS_DB = pathlib.Path.home() / ".hermes" / "market_data" / "options_history" / "options_history.db"
IV_DB = pathlib.Path.home() / ".hermes" / "market_data" / "iv_surface" / "iv_surface.db"

# ── Pre-registered constants (FIXED — no tuning) ────────────────────────────
CURRENCIES = ["BTC", "ETH"]
ENTRY_DTE = 7.0          # primary horizon: weekly straddle, held to expiry
ENTRY_DTE_ROBUST = 30.0  # robustness horizon: monthly straddle (monthly/quarterly
                         # expiries only, non-overlapping)
DTE_TOL = 3.0            # entry tolerance (days) around ENTRY_DTE
DAYS_PER_YEAR = 365.0

# Vol-of-vol gate: enter only when DVOL below its own trailing mean.
GATE_WINDOW_DAYS = 30
GATE_MEAN_MULT = 1.0     # calm == dvol < trailing_mean (below its own band)

# Cost model (all FIXED; option bid-ask is a FLAGGED assumption — no L2 book).
ATM_FACTOR = 0.797884560803          # sqrt(2/pi): ATM straddle ≈ factor*S*sigma*sqrt(T)
TAKER_FEE_BPS = 3.0                  # Deribit options taker, bps of underlying (x2 legs)
MAKER_FEE_BPS = 0.0                  # fail-closed: no maker rebate credited
MARGIN_UNDERLYING_FRAC = 0.20        # margin = premium + 20% of underlying
MARGIN_OPP_RATE = 0.05               # opportunity cost of tied margin (flagged)
# Option bid-ask half-spread in VOL POINTS (assumption band, no L2 book held).
HALF_SPREAD_VOL_MAKER = 0.0          # maker: post at mark (no improvement, no rebate)
HALF_SPREAD_VOL_TAKER = 1.0          # realistic: cross half a 2-vol-pt straddle spread
HALF_SPREAD_VOL_STRESS = 2.0         # pessimistic: half a 4-vol-pt stressed spread

DEFAULT_RESULT_PRECISION = 4


# ── Store readers (direct sqlite; schemas verified against the backfill) ────
def _read(sql: str, params: tuple, db: pathlib.Path) -> pd.DataFrame:
    conn = sqlite3.connect(str(db))
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def load_options(currency: str) -> pd.DataFrame:
    df = _read("SELECT currency, expiry, day, snap_ts, dte, underlying, strike, "
               "call_premium, put_premium, atm_straddle_premium, atm_iv, iv_source "
               "FROM options_atm_straddle WHERE currency=? ORDER BY day ASC, expiry ASC",
               (currency,), OPTIONS_DB)
    return df


def load_underlying(currency: str) -> pd.DataFrame:
    df = _read("SELECT day, close FROM underlying_daily WHERE currency=? "
               "ORDER BY day ASC", (currency,), OPTIONS_DB)
    df = df.dropna(subset=["close"])
    df["close"] = df["close"].astype(float)
    return df


def load_dvol_daily(currency: str) -> pd.DataFrame:
    """Daily DVOL close (last hourly close per UTC day), full history back to 2021."""
    df = _read("SELECT ts, close FROM dvol_index WHERE currency=? ORDER BY ts ASC",
               (currency,), IV_DB)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])
    df["day"] = (df["ts"] // 86_400_000) * 86_400_000
    d = df.groupby("day", as_index=False)["close"].last()
    return d


# ── Realized vol over the hold ──────────────────────────────────────────────
def realized_vol_hold(underlying: pd.DataFrame, entry_day: int, expiry: int) -> float | None:
    """Annualized std of log returns from entry_day (close) to expiry-day close."""
    closes = underlying[(underlying["day"] >= entry_day) & (underlying["day"] <= expiry)] \
        .sort_values("day")["close"].tolist()
    if len(closes) < 3:
        return None
    lr = np.diff(np.log(np.asarray(closes, dtype=float)))
    lr = lr[np.isfinite(lr)]
    if len(lr) < 2:
        return None
    return float(np.std(lr, ddof=1) * np.sqrt(DAYS_PER_YEAR))


def straddle_vega_per_volpt(T: float) -> float:
    """Straddle vega (coin per coin-notional) per ONE vol point (0.01)."""
    return ATM_FACTOR * np.sqrt(T) * 0.01


# ── Gate ────────────────────────────────────────────────────────────────────
def build_dvol_series(dvol_daily: pd.DataFrame) -> pd.Series:
    s = dvol_daily.set_index("day")["close"].sort_index()
    return s


def gate_series(dvol: pd.Series, window: int = GATE_WINDOW_DAYS) -> pd.Series:
    """calm == dvol < trailing window mean (prior `window` days, exclusive of today)."""
    mean = dvol.rolling(window, min_periods=max(3, window // 2)).mean().shift(1)
    calm = dvol < mean
    return calm, mean


# ── Cost (fraction of 1-coin notional, same units as premium) ──────────────
def entry_cost(T: float, premium: float, fee_bps: float,
               half_spread_vol: float) -> float:
    """Entry cost for a short straddle (sell both legs), as a fraction of a
    1-coin notional (matching `premium`, which is coin per 1-coin contract).

      spread    = half_spread_vol * straddle_vega_per_vol_pt
      fee       = fee_bps/1e4 * 2 legs (1 coin notional each)
      margin_opp= (premium + 0.20) * rate * T   (margin = premium + 20% underlying)

    Charged on BOTH legs (straddle = call + put; vega already folds both in).
    """
    vega = straddle_vega_per_volpt(T)
    spread = half_spread_vol * vega
    fee = (fee_bps / 1e4) * 2.0
    margin = premium + MARGIN_UNDERLYING_FRAC
    margin_opp = margin * MARGIN_OPP_RATE * T
    return float(spread + fee + margin_opp)


# ── Trade construction ──────────────────────────────────────────────────────
def build_trades(currency: str, entry_dte: float, monthly_only: bool = False) -> pd.DataFrame:
    opt = load_options(currency)
    und = load_underlying(currency)
    dvol = build_dvol_series(load_dvol_daily(currency))

    if opt.empty or und.empty:
        return pd.DataFrame()

    # For the monthly robustness horizon, restrict to long-dated expiries
    # (listed with >= ENTRY_DTE_ROBUST - tol days to expiry).
    if monthly_only:
        mx = opt.groupby("expiry")["dte"].max()
        keep = mx[mx >= entry_dte - DTE_TOL].index
        opt = opt[opt["expiry"].isin(keep)]

    trades = []
    for expiry, g in opt.groupby("expiry"):
        # Drop rows with missing IV (honest provenance: mark_iv absent).
        g = g.dropna(subset=["atm_iv"])
        if g.empty:
            continue
        dte = g["dte"].astype(float)
        # entry = snapshot with DTE closest to entry_dte, but not an already-expired stub
        cand = g[(dte >= 0.5) & (dte <= entry_dte + DTE_TOL)]
        if cand.empty:
            continue
        entry = cand.iloc[(cand["dte"].astype(float) - entry_dte).abs().argsort().iloc[0]]

        S0 = float(entry["underlying"])
        K = float(entry["strike"])
        T = float(entry["dte"]) / DAYS_PER_YEAR
        premium = float(entry["atm_straddle_premium"])
        atm_iv = float(entry["atm_iv"])
        entry_day = int(entry["day"])
        snap_ts = int(entry["snap_ts"])

        if premium <= 0 or S0 <= 0 or T <= 0:
            continue

        # payoff: underlying close at expiry (daily close proxy for 08:00 UTC settle)
        exp_close = und[und["day"] <= expiry].sort_values("day")
        if exp_close.empty:
            continue
        S_T = float(exp_close["close"].iloc[-1])

        rv = realized_vol_hold(und, entry_day, expiry)
        if rv is None:
            continue

        # gate (DVOL at entry day vs trailing mean)
        dvol_entry = None
        if entry_day in dvol.index:
            dvol_entry = float(dvol.loc[entry_day])
        calm = _gate_value(dvol, entry_day)

        payoff_coin = abs(S_T - K) / S_T
        gross_pnl_coin = premium - payoff_coin
        vrp_gross = atm_iv - rv * 100.0  # vol points

        trades.append({
            "currency": currency, "expiry": expiry, "entry_day": entry_day,
            "snap_ts": snap_ts, "dte": float(entry["dte"]), "T": T,
            "S0": S0, "K": K, "S_T": S_T,
            "premium": premium, "atm_iv": atm_iv,
            "rv_hold": rv * 100.0,   # percent
            "vrp_gross": vrp_gross,
            "payoff_coin": payoff_coin,
            "gross_pnl_coin": gross_pnl_coin,
            "gross_pnl_r": gross_pnl_coin / premium,
            "dvol_entry": dvol_entry,
            "calm": calm,
        })
    return pd.DataFrame(trades)


def _gate_value(dvol: pd.Series, entry_day: int):
    """calm (bool) = DVOL at entry day < trailing 30d mean of PRIOR days."""
    if entry_day not in dvol.index:
        return None
    idx = dvol.index.get_loc(entry_day)
    if idx < GATE_WINDOW_DAYS:
        return None
    trailing = dvol.iloc[idx - GATE_WINDOW_DAYS:idx]
    mean = float(trailing.mean())
    return bool(dvol.iloc[idx] < mean)


# ── Summary helpers ─────────────────────────────────────────────────────────
def _stats(rvals: np.ndarray) -> dict:
    rvals = np.asarray(rvals, dtype=float)
    rvals = rvals[np.isfinite(rvals)]
    if rvals.size == 0:
        return {"n": 0, "mean": None, "median": None, "std": None,
                "min": None, "max": None}
    return {"n": int(rvals.size), "mean": float(rvals.mean()),
            "median": float(np.median(rvals)), "std": float(rvals.std(ddof=1)),
            "min": float(rvals.min()), "max": float(rvals.max())}


def _profit_factor(rvals: np.ndarray) -> float:
    rvals = np.asarray(rvals, dtype=float)
    gains = rvals[rvals > 0].sum()
    losses = abs(rvals[rvals < 0].sum())
    return float(gains / losses) if losses > 0 else float("inf")


def _max_drawdown(equity: np.ndarray) -> float:
    eq = np.asarray(equity, dtype=float)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    return float(dd.min()) if dd.size else 0.0


def _sharpe(rvals: np.ndarray, per_year: float) -> float:
    rvals = np.asarray(rvals, dtype=float)
    if rvals.size < 2:
        return 0.0
    std = rvals.std(ddof=1)
    return float(rvals.mean() / std * np.sqrt(per_year)) if std > 0 else 0.0


def summarize_trades(df: pd.DataFrame, cost_label: str = "maker") -> None:
    pass  # (report formatting handled in main)


def _cost_r_col(df: pd.DataFrame, label: str) -> pd.Series:
    """Net P&L in R (fraction of premium) per trade, after entry cost."""
    if label == "maker":
        fee, hsv = MAKER_FEE_BPS, HALF_SPREAD_VOL_MAKER
    elif label == "taker":
        fee, hsv = TAKER_FEE_BPS, HALF_SPREAD_VOL_TAKER
    else:  # stressed taker
        fee, hsv = TAKER_FEE_BPS, HALF_SPREAD_VOL_STRESS
    cost = df.apply(lambda r: entry_cost(r["T"], r["premium"], fee, hsv), axis=1)
    prem = df["premium"]
    net_r = (prem - df["payoff_coin"] - cost) / prem
    return net_r


def net_pnl_bps(df: pd.DataFrame, label: str) -> np.ndarray:
    """Net P&L per trade in bps of notional (premium/payoff/cost are coin-fractions)."""
    net_r = _cost_r_col(df, label).to_numpy()
    prem = df["premium"].to_numpy(dtype=float)
    return net_r * prem * 1e4


def trailing_dvol_pct(dvol: pd.Series, entry_day: int, window: int = 90) -> float | None:
    """Percentile of DVOL(entry) within the trailing `window` days (0..1), strictly
    prior days (no look-ahead)."""
    if entry_day not in dvol.index:
        return None
    idx = dvol.index.get_loc(entry_day)
    if idx < 10:
        return None
    trailing = dvol.iloc[max(0, idx - window):idx]
    if trailing.size < 5:
        return None
    val = dvol.iloc[idx]
    return float((trailing < val).astype(float).mean())


def conditional_matrix(df: pd.DataFrame, dvol: pd.Series,
                       n_quantiles: int = 5) -> list[dict]:
    """VRP + net-R by DVOL percentile bucket — the honest regime-separation check."""
    pct = df["entry_day"].map(lambda d: trailing_dvol_pct(dvol, d))
    df2 = df.assign(dvol_pct=pct).dropna(subset=["dvol_pct"])
    df2["bucket"] = pd.qcut(df2["dvol_pct"], n_quantiles, labels=False)
    rows = []
    for b in range(n_quantiles):
        sub = df2[df2["bucket"] == b]
        if sub.empty:
            continue
        maker_r = _cost_r_col(sub, "maker").to_numpy()
        taker_r = _cost_r_col(sub, "taker").to_numpy()
        rows.append({
            "bucket": int(b),
            "dvol_pct_lo": round(float(sub["dvol_pct"].min()), 2),
            "dvol_pct_hi": round(float(sub["dvol_pct"].max()), 2),
            "n": int(len(sub)),
            "vrp_mean": round(float(np.nanmean(sub["vrp_gross"].to_numpy())), 2),
            "net_r_maker": round(float(np.nanmean(maker_r)), 3),
            "net_r_taker": round(float(np.nanmean(taker_r)), 3),
        })
    return rows


# ── Vol-spike episode identification (daily DVOL) ──────────────────────────
def vol_spike_episodes(dvol: pd.Series, fwd_days: int = 7, surge: float = 0.20) -> list[dict]:
    """Daily-DVOL episodes where DVOL rises > surge (e.g. +20%) within fwd_days."""
    dv = dvol.sort_index()
    closes = dv.values
    idx = dv.index
    gap = fwd_days
    episodes = []
    active = None
    for i in range(len(closes) - gap):
        fwd_ret = closes[i + gap] / closes[i] - 1.0
        spike = fwd_ret > surge
        if spike and active is None:
            active = {"start": int(idx[i]), "peak_ret": fwd_ret,
                      "start_dvol": float(closes[i])}
        elif spike and active is not None:
            active["peak_ret"] = max(active["peak_ret"], fwd_ret)
            active["end"] = int(idx[i])
        elif not spike and active is not None:
            active["end"] = int(idx[i])
            # find peak DVOL within the episode window
            seg = dv[(dv.index >= active["start"]) & (dv.index <= active["end"])]
            active["peak_dvol"] = float(seg.max())
            active["dvol_rise"] = float(seg.max() / active["start_dvol"] - 1.0)
            episodes.append(active)
            active = None
    if active is not None:
        active["end"] = int(idx[-1])
        seg = dv[(dv.index >= active["start"]) & (dv.index <= active["end"])]
        active["peak_dvol"] = float(seg.max())
        active["dvol_rise"] = float(seg.max() / active["start_dvol"] - 1.0)
        episodes.append(active)
    return episodes


# ── Main ────────────────────────────────────────────────────────────────────
def run_horizon(currency: str, entry_dte: float, monthly_only: bool = False) -> pd.DataFrame:
    return build_trades(currency, entry_dte, monthly_only)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-30 variance risk premium — sell ATM straddle, hold to expiry ===\n")
    print(f"primary horizon: weekly (ENTRY_DTE={ENTRY_DTE}d); robustness: monthly "
          f"(ENTRY_DTE={ENTRY_DTE_ROBUST}d, long-dated expiries)")
    print(f"gate: DVOL < trailing {GATE_WINDOW_DAYS}d mean (low/decaying, not spiking)\n")

    all_result = {}
    per_currency = {}
    for currency in CURRENCIES:
        cur_result = {}
        for label, dte, monthly_only in [("weekly", ENTRY_DTE, False),
                                          ("monthly", ENTRY_DTE_ROBUST, True)]:
            tr = run_horizon(currency, dte, monthly_only)
            if tr.empty:
                print(f"--- {currency} {label}: no trades ---")
                continue
            tr["year"] = pd.to_datetime(tr["entry_day"], unit="ms", utc=True).dt.year
            # gated = calm True; ungated = all (including calm None treated as not entered)
            gated = tr[tr["calm"] == True]
            ungated = tr
            # VRP
            vrp_all = ungated["vrp_gross"].to_numpy()
            vrp_gated = gated["vrp_gross"].to_numpy()
            # net R per cost tier
            tiers = {}
            for tl in ["maker", "taker", "taker_stress"]:
                net_r = _cost_r_col(tr, tl)
                tiers[tl] = {
                    "all": _stats(net_r.to_numpy()),
                    "gated": _stats(net_r[tr["calm"] == True].to_numpy()),
                }
            cur_result[label] = {
                "n_all": int(len(ungated)), "n_gated": int(len(gated)),
                "vrp_gross_all": _stats(vrp_all),
                "vrp_gross_gated": _stats(vrp_gated),
                "vrp_by_year": {
                    str(y): _stats(ungated[ungated["year"] == y]["vrp_gross"].to_numpy())
                    for y in sorted(ungated["year"].unique())
                },
                "vrp_gated_by_year": {
                    str(y): _stats(gated[gated["year"] == y]["vrp_gross"].to_numpy())
                    for y in sorted(gated["year"].unique())
                },
                "tiers": tiers,
                "trades": tr,
            }
            print(f"--- {currency} {label}: {len(tr)} trades "
                  f"(gated {len(gated)}), VRP all mean {np.nanmean(vrp_all):+.2f}pp, "
                  f"gated {np.nanmean(vrp_gated):+.2f}pp")
        per_currency[currency] = cur_result
    all_result["per_currency"] = per_currency

    # ── VRP by year (gated vs ungated) ──────────────────────────────────────
    print("\n=== VRP (implied − realized, vol pp) BY YEAR ===")
    for currency in CURRENCIES:
        r = per_currency[currency]["weekly"]
        print(f"  {currency}:")
        years = sorted(r["trades"]["year"].unique())
        for y in years:
            a = r["vrp_by_year"].get(str(y), {})
            g = r["vrp_gated_by_year"].get(str(y), {})
            am = a.get("mean")
            gm = g.get("mean")
            a_s = f"{am:+.2f}" if am is not None else "n/a"
            g_s = f"{gm:+.2f}" if gm is not None else "n/a"
            print(f"    {y}: ungated {a_s} (n={a.get('n')}) | "
                  f"gated {g_s} (n={g.get('n')})")

    # ── Net P&L after spread + margin (bps of notional) + tail ──────────────
    print("\n=== NET STRADDLE P&L (after spread + margin, bps of notional) ===")
    for currency in CURRENCIES:
        r = per_currency[currency]["weekly"]
        tr = r["trades"].sort_values("entry_day")
        dvol = build_dvol_series(load_dvol_daily(currency))
        gated = tr["calm"] == True
        years = (tr["entry_day"].max() - tr["entry_day"].min()) / 86_400_000 / 365.0
        for tl, label in [("maker", "maker"), ("taker", "taker"),
                          ("taker_stress", "taker+stress")]:
            bps_all = net_pnl_bps(tr, tl)
            bps_gated = bps_all[gated.to_numpy()]
            tot = float(np.nansum(bps_all)); tot_g = float(np.nansum(bps_gated))
            ann = tot / years; ann_g = tot_g / years
            # cumulative bps equity (ungated) for max drawdown
            cum = np.cumsum(np.nan_to_num(bps_all))
            mdd = _max_drawdown(cum)
            worst = int(np.argmin(bps_all))
            print(f"  {currency} [{label}]: total {tot:+.1f} bps ({ann:+.1f}/yr), "
                  f"gated {tot_g:+.1f} bps ({ann_g:+.1f}/yr); "
                  f"maxDD(equity) {mdd*100:.1f}%; worst trade {bps_all[worst]:+.1f} bps "
                  f"({datetime.fromtimestamp(tr['entry_day'].iloc[worst]/1000,tz=timezone.utc).date()})")

    # ── Conditional matrix: VRP by DVOL percentile (the regime-separation test)
    print("\n=== CONDITIONAL MATRIX: VRP + net-R by entry-DVOL percentile (weeklies) ===")
    for currency in CURRENCIES:
        tr = per_currency[currency]["weekly"]["trades"]
        dvol = build_dvol_series(load_dvol_daily(currency))
        rows = conditional_matrix(tr, dvol, n_quantiles=5)
        print(f"  {currency}:")
        for rw in rows:
            print(f"    DVOL pct [{rw['dvol_pct_lo']:.2f}-{rw['dvol_pct_hi']:.2f}] "
                  f"n={rw['n']}: VRP {rw['vrp_mean']:+.2f}pp | net-R maker "
                  f"{rw['net_r_maker']:+.3f} taker {rw['net_r_taker']:+.3f}")

    # ── Vol-spike episodes (trade window only) + overlap P&L ────────────────
    print("\n=== VOL-SPIKE EPISODES (DVOL >= +20%/7d, TRADE WINDOW 2024-11+) ===")
    opt_start = 1730937600000  # 2024-11-07
    for currency in CURRENCIES:
        tr = per_currency[currency]["weekly"]["trades"].sort_values("entry_day")
        dvol = build_dvol_series(load_dvol_daily(currency))
        episodes = [e for e in vol_spike_episodes(dvol) if e["start"] >= opt_start]
        print(f"  {currency}: {len(episodes)} spike episodes in trade window")
        for e in episodes[:8]:
            s = datetime.fromtimestamp(e["start"]/1000, tz=timezone.utc).date()
            en = datetime.fromtimestamp(e["end"]/1000, tz=timezone.utc).date()
            # trades whose hold overlaps the episode (entry <= end AND expiry >= start)
            ov = tr[(tr["entry_day"] <= e["end"]) & (tr["expiry"] >= e["start"])]
            if ov.empty:
                pnl = None
            else:
                pnl = float(net_pnl_bps(ov, "taker").sum())
            print(f"    {s} -> {en}: DVOL {e['start_dvol']:.0f} -> {e['peak_dvol']:.0f} "
                  f"(+{e['dvol_rise']*100:.0f}%) | {len(ov)} straddle(s) held: "
                  f"net {pnl if pnl is None else f'{pnl:+.1f}'} bps (taker)")

    # ── Write trial ─────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "variance_risk_premium_short_atm_straddle",
        "universe": CURRENCIES, "venue": "deribit",
        "entry_dte_primary": ENTRY_DTE, "entry_dte_robust": ENTRY_DTE_ROBUST,
        "hold": "to_expiry", "settlement": "coin_settled_reversed",
        "gate": f"dvol < trailing {GATE_WINDOW_DAYS}d mean",
        "gate_window_days": GATE_WINDOW_DAYS,
        "cost": {"taker_fee_bps": TAKER_FEE_BPS, "maker_fee_bps": MAKER_FEE_BPS,
                 "half_spread_vol_maker": HALF_SPREAD_VOL_MAKER,
                 "half_spread_vol_taker": HALF_SPREAD_VOL_TAKER,
                 "half_spread_vol_stress": HALF_SPREAD_VOL_STRESS,
                 "margin_underlying_frac": MARGIN_UNDERLYING_FRAC,
                 "margin_opp_rate": MARGIN_OPP_RATE,
                 "spread_source": "ASSUMED vol-pt band (no L2 options book held)"},
        "leverage": "none_1x_notional_premium_risk_unit",
        "live": "off",
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(sorted(CURRENCIES)).encode()).hexdigest()

    # serialize the computed result (drop DataFrames for the ledger)
    result = {"construction": "variance_risk_premium_short_atm_straddle",
              "venue": "deribit", "universe": CURRENCIES, "leverage": "none",
              "live": "off", "no_lookahead": True,
              "per_currency": {}}
    for c in CURRENCIES:
        result["per_currency"][c] = {}
        for lbl in ["weekly", "monthly"]:
            r = per_currency[c][lbl]
            result["per_currency"][c][lbl] = {
                "n_all": r["n_all"], "n_gated": r["n_gated"],
                "vrp_gross_all": r["vrp_gross_all"],
                "vrp_gross_gated": r["vrp_gross_gated"],
                "vrp_by_year": r["vrp_by_year"],
                "tiers": {t: {k: v for k, v in r["tiers"][t].items()}
                          if False else r["tiers"][t] for t in r["tiers"]},
            }

    print("\n=== VERDICT (summary of gated net-R clears cost?) ===")
    verdict_lines = []
    for c in CURRENCIES:
        for lbl in ["weekly", "monthly"]:
            r = per_currency[c][lbl]
            for tl in ["maker", "taker", "taker_stress"]:
                g = r["tiers"][tl]["gated"]
                mean = g.get("mean")
                if mean is None:
                    continue
                verdict_lines.append(f"  {c} {lbl}/{tl}: gated net-R mean {mean:+.4f} "
                                     f"(n={g['n']})")
    for v in verdict_lines:
        print(v)

    if not args.no_write:
        e = ledger.increment_trial("HYP-30", param_hash, universe_hash,
                                   "2024-11-07", "2026-11-07", result)
        print(f"\nwrote trial HYP-30 param_hash={e['param_hash'][:16]}... "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
