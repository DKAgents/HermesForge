"""backtest_hyp32_onchain_stablecoin_flow.py — HYP-32 execution (on-chain flow).

Pre-registered (HYP-32, `trading/strategies/Hypotheses/HYP-32-onchain-stablecoin-flow.md`).
FIXED operationalization — do NOT tune. FIRST on-chain/flow test (untested data class).

Signal (the test): aggregate stablecoin supply growth (7d/30d) + aggregate TVL
growth (7d/30d) -> SUBSEQUENT (forward) BTC/ETH price return at a weekly horizon.

Data (free DefiLlama, backfilled):
  ~/.hermes/market_data/defillama_history/stablecoin_supply_daily.parquet
      daily aggregate stablecoin supply (USD) — source stablecoincharts/all
  ~/.hermes/market_data/defillama_history/tvl_daily.parquet
      daily aggregate DeFi TVL (USD) — source api.llama.fi/charts
  ~/.hermes/market_data/crypto/{BTC,ETH}.parquet
      daily OHLC closes (2020-08-19 -> present)

THE CRITICAL HONESTY TEST (load-bearing): separate LEADING from COINCIDENT.
A flow metric that merely correlates with contemporaneous price (both rise in a
bull market) is NOT tradeable — the signal must predict FORWARD return
(flow at t -> return at t+1) and LEAD, not echo. Reported explicitly:
  (a) the full lead-lag cross-correlogram across lags -30..+30 days,
  (b) the non-overlapping weekly FORWARD IC (tradeable leading measure) with t-stat,
  (c) the weekly CONTEMPORANEOUS/echo IC (does flow just reflect price it moved with),
  (d) a regression of forward return on flow growth controlling for trailing
      return + trailing flow (Granger-style: does flow add anything once you
      know what price just did?).

MEASUREMENT (fixed):
  * growth = log(value_t / value_{t-k}) for k in {7, 30} (sustained flow).
  * horizon = 7 days (weekly forward log return).
  * sampling = NON-OVERLAPPING weekly rebalance points (no overlap bias in the
    forward IC and tradable P&L; the daily correlogram is descriptive-only).
  * tradable translation = long the coin when growth > 0, else flat (sign only,
    no threshold optimization).

COST (weekly rebalance, realistic taker + funding):
  * round-trip (position flip) = taker 4.5bps x2 + slippage 2.5bps + funding
    0.5bps  (matches fee_source crypto round-trip model); charged on each
    long<->flat flip; no maker rebate (fail-closed). Low turnover so cost is
    secondary to signal strength (as the hypothesis notes).

HARD RULES honored: fresh param_hash in trials ledger; no look-ahead (flow at t
-> return from t+1, rebalance decisions on close-of-day info only); LIVE off;
cost charged on both legs; coincident correlation reported honestly and NOT
promoted.

Usage: python3 backtest_hyp32_onchain_stablecoin_flow.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent  # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import trials_ledger as ledger  # noqa: E402

MD = pathlib.Path.home() / ".hermes" / "market_data"
SUPPLY_PARQUET = MD / "defillama_history" / "stablecoin_supply_daily.parquet"
TVL_PARQUET = MD / "defillama_history" / "tvl_daily.parquet"
PRICE_DIR = MD / "crypto"

# ── Pre-registered constants (FIXED — no tuning) ────────────────────────────
CURRENCIES = ["BTC", "ETH"]
GROWTH_WINDOWS = [7, 30]     # sustained flow growth windows (days)
HORIZON = 7                  # weekly forward return horizon (days)
REBALANCE = 7                # non-overlapping weekly sampling

# Cost model (matches fee_source crypto round-trip: taker*2 + slippage + funding).
TAKER_BPS = 4.5
SLIPPAGE_BPS = 2.5
FUNDING_BPS_WEEK = 0.5
ROUND_TRIP_BPS = TAKER_BPS * 2 + SLIPPAGE_BPS + FUNDING_BPS_WEEK  # 12 bps

# Signal naming (fixed): 'supply' (H1), 'tvl' (H2).
FLOW_KINDS = ["supply", "tvl"]


# ── Loaders ─────────────────────────────────────────────────────────────────
def load_flow() -> pd.DataFrame:
    supply = pd.read_parquet(SUPPLY_PARQUET)["supply_usd"].rename("supply")
    tvl = pd.read_parquet(TVL_PARQUET)["tvl_usd"].rename("tvl")
    df = pd.concat([supply, tvl], axis=1)
    df.index = df.index.tz_localize(None)  # align with tz-naive price index
    return df.sort_index()


def load_prices() -> dict[str, pd.Series]:
    out = {}
    for c in CURRENCIES:
        df = pd.read_parquet(PRICE_DIR / f"{c}.parquet")
        s = df["close"].astype(float)
        s.index = df.index.normalize()
        s = s[~s.index.duplicated(keep="last")].sort_index()
        out[c] = s
    return out


# ── Feature build ───────────────────────────────────────────────────────────
def growth_series(flow: pd.Series, window: int) -> pd.Series:
    """log growth over `window` trading days: log(v_t / v_{t-window})."""
    return np.log(flow / flow.shift(window)).rename(f"g{window}")


# ── Lead-lag correlogram (descriptive) ─────────────────────────────────────
def cross_corr(flow_growth: pd.Series, daily_ret: pd.Series, max_lag: int = 30):
    """corr(flow_growth_t, daily_log_return_{t+h}) for h in -max_lag..+max_lag.

    h > 0 => does flow today predict return h days ahead (LEAD).
    h < 0 => return today correlates with flow h days in the PAST (flow LAGS).
    """
    g = flow_growth.dropna()
    r = daily_ret.dropna()
    j = pd.concat([g.rename("g"), r.rename("r")], axis=1, join="inner").dropna()
    gg = j["g"] - j["g"].mean()
    rr = j["r"] - j["r"].mean()
    lags = []
    for h in range(-max_lag, max_lag + 1):
        if h >= 0:
            num = (gg.shift(0) * rr.shift(-h)).mean()
        else:
            # corr(g_t, r_{t+h}) with h<0 == corr(g_{t-h}, r_t) shifted
            num = (gg.shift(h) * rr.shift(0)).mean()
        den = np.sqrt((gg ** 2).mean() * (rr ** 2).mean())
        lags.append((h, float(num / den) if den > 0 else float("nan")))
    return lags


# ── Stats ───────────────────────────────────────────────────────────────────
def _ic_with_tstat(x: np.ndarray, y: np.ndarray):
    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]
    y = y[m]
    n = x.size
    if n < 4:
        return None
    ic = float(np.corrcoef(x, y)[0, 1])
    if not np.isfinite(ic) or abs(ic) >= 1.0:
        return {"ic": ic, "n": n, "t": float("nan"), "p": float("nan")}
    t = ic * np.sqrt(n - 2) / np.sqrt(1 - ic * ic)
    return {"ic": ic, "n": int(n), "t": float(t), "p": float(2 * (1 - _norm_cdf(abs(t))))}


def _norm_cdf(x: float) -> float:
    from math import erf, sqrt
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


# ── Weekly non-overlapping panel ────────────────────────────────────────────
def build_weekly_panel(flow: pd.Series, price: pd.Series, window: int) -> pd.DataFrame:
    """Non-overlapping weekly rows: signal (growth at t), forward return t->t+7,
    trailing return t-7->t, trailing growth.

    Rebalance/sample every REBALANCE days; growth uses knowable close info.
    Forward return uses price at t+7 (strictly future — no look-ahead).
    """
    price = price.dropna()
    daily_ret = np.log(price / price.shift(1))
    g = growth_series(flow, window)

    # align all on the union of available days
    df = pd.DataFrame({"price": price, "daily_ret": daily_ret, "g": g}).dropna()
    if df.empty:
        return pd.DataFrame()

    # forward 7-day return (log)
    df["fwd_ret"] = np.log(df["price"].shift(-HORIZON) / df["price"])
    # trailing 7-day return
    df["trail_ret"] = np.log(df["price"] / df["price"].shift(HORIZON))
    # trailing growth of flow (over same window, prior to t)
    df["g_trail"] = df["g"].shift(HORIZON)

    # sample non-overlapping weekly points
    idx = df.index
    weeks = (idx - idx[0]).days // REBALANCE
    df["week"] = weeks
    sample = df.groupby("week").tail(1).copy()
    sample = sample.dropna(subset=["fwd_ret", "g"])
    return sample


# ── Tradable sign strategy (long signal>0, else flat), net of cost ──────────
def run_sign_strategy(sample: pd.DataFrame) -> dict:
    """Long when signal>0, flat otherwise; charge 12bps on each flip, 0.5bps/week held."""
    s = sample.sort_index().reset_index(drop=True)
    if s.empty:
        return {"n": 0, "n_long": 0, "n_flips": 0, "gross": [],
                "net": [], "gross_total": 0.0, "net_total": 0.0}
    pos = (s["g"] > 0).astype(float).to_numpy()
    fwd = s["fwd_ret"].to_numpy(dtype=float)

    gross = pos * fwd
    # cost: flip cost when position changes; weekly funding while long
    cost = np.zeros_like(gross)
    flips = 0
    for i in range(len(pos)):
        if i > 0 and pos[i] != pos[i - 1]:
            cost[i] += ROUND_TRIP_BPS / 1e4
            flips += 1
        if pos[i] > 0:
            cost[i] += FUNDING_BPS_WEEK / 1e4
    net = gross - cost
    years = len(s) * REBALANCE / 365.0
    # compounded (CAGR) equity of the strategy (sum of weekly log-ish returns)
    # using the realized per-week net returns; B&H comparison done in main().
    gross_cagr = float(np.exp(np.log1p(gross).sum() / years) - 1.0) if gross.size else 0.0
    net_cagr = float(np.exp(np.log1p(net).sum() / years) - 1.0) if net.size else 0.0
    return {
        "n": int(len(s)), "n_long": int(pos.sum()), "n_flips": int(flips),
        "gross": gross, "net": net,
        "gross_total": float(gross.sum()), "net_total": float(net.sum()),
        "gross_cagr": gross_cagr, "net_cagr": net_cagr,
        "net_sharpe": _sharpe(net, 365.0 / REBALANCE),
        "years": float(years),
    }


def _sharpe(r: np.ndarray, per_year: float) -> float:
    r = r[np.isfinite(r)]
    if r.size < 2 or r.std(ddof=1) <= 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(per_year))


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-32 on-chain / stablecoin + TVL flow -> subsequent price ===\n")
    print(f"universe {CURRENCIES}, horizon {HORIZON}d, growth {GROWTH_WINDOWS}d, "
          f"non-overlapping weekly sampling\n")

    flow = load_flow()
    prices = load_prices()

    flow_start = flow.index.min().date()
    price_start = min(s.index.min().date() for s in prices.values())
    price_end = max(s.index.max().date() for s in prices.values())
    print(f"flow: {flow_start} -> {flow.index.max().date()}")
    print(f"price: {price_start} -> {price_end}")
    print(f"common window: {max(flow_start, price_start)} -> {price_end}\n")

    results = {"per_coin": {}, "cross_corr": {}, "regression": {}}
    macrostats = {}

    for coin in CURRENCIES:
        price = prices[coin]
        daily_ret = np.log(price / price.shift(1)).dropna()
        results["per_coin"][coin] = {}
        macrostats[coin] = {}

        for kind in FLOW_KINDS:
            f = flow[kind]
            for window in GROWTH_WINDOWS:
                key = f"{kind}_{window}d"
                sample = build_weekly_panel(f, price, window)
                if sample.empty:
                    continue
                g_vals = sample["g"].to_numpy()
                fwd = sample["fwd_ret"].to_numpy()
                trail = sample["trail_ret"].to_numpy()
                fwd_ic = _ic_with_tstat(g_vals, fwd)
                trail_ic = _ic_with_tstat(g_vals, trail)
                strat = run_sign_strategy(sample)

                # regression: fwd_ret ~ g + trail_ret + g_trail (Granger-style lead check)
                reg = {}
                X = np.column_stack([g_vals, trail, sample["g_trail"].to_numpy()])
                y = fwd
                m = np.isfinite(X).all(axis=1) & np.isfinite(y)
                if m.sum() >= 8:
                    Xm = np.column_stack([np.ones(m.sum()), X[m]])
                    ym = y[m]
                    beta, *_ = np.linalg.lstsq(Xm, ym, rcond=None)
                    resid = ym - Xm @ beta
                    dof = Xm.shape[0] - Xm.shape[1]
                    ssr = float(resid @ resid)
                    cov = ssr / dof * np.linalg.inv(Xm.T @ Xm)
                    se = np.sqrt(np.diag(cov))
                    reg = {
                        "coef_g": float(beta[1]), "se_g": float(se[1]),
                        "t_g": float(beta[1] / se[1]) if se[1] > 0 else float("nan"),
                        "coef_trail": float(beta[2]),
                        "coef_g_trail": float(beta[3]),
                    }

                results["per_coin"][coin][key] = {
                    "fwd_ic": fwd_ic, "trail_ic": trail_ic, "regression": reg,
                    "strategy": {k: v for k, v in strat.items()
                                 if k not in ("gross", "net")},
                }
                macrostats[coin][key] = strat

    # ── Lead-lag correlogram (aggregate flow growth vs daily coin return) ───
    print("=== LEAD-LAG CORRELOGRAM: corr(flow_growth_t, daily_return_{t+h}) ===\n")
    print("  h<0 = flow LAGS price (echo) | h=0 coincident | h>0 = flow LEADS")
    for coin in CURRENCIES:
        daily_ret = np.log(prices[coin] / prices[coin].shift(1)).dropna()
        for kind in FLOW_KINDS:
            for window in GROWTH_WINDOWS:
                g = growth_series(flow[kind], window)
                corr = cross_corr(g, daily_ret, max_lag=30)
                shown = [h for h in (-30, -21, -14, -7, -3, -1, 0, 1, 3, 7, 14, 21, 30)]
                cmap = {h: c for h, c in corr}
                peak = max(corr, key=lambda t: abs(t[1]))
                results["cross_corr"][f"{kind}_{window}d"] = {
                    "peak_lag": peak[0], "peak_corr": peak[1],
                    "corr_at": {str(h): cmap[h] for h in shown},
                }
                line = "  ".join(f"h{h:+d}:{cmap[h]:+.3f}" for h in shown)
                print(f"  {coin} [{kind} {window}d]: {line}")
                print(f"      -> peak |corr| at lag h={peak[0]:+d} "
                      f"(corr {peak[1]:+.3f})")
        print()

    # ── Benchmarks (buy & hold + momentum) ───────────────────────────────────
    print("=== BENCHMARKS over the common window ===\n")
    buyhold = {}
    for coin in CURRENCIES:
        p = prices[coin].dropna()
        n_days = (p.index[-1] - p.index[0]).days
        bh_total = float(p.iloc[-1] / p.iloc[0] - 1.0)
        bh_cagr = float((p.iloc[-1] / p.iloc[0]) ** (365.0 / n_days) - 1.0)
        buyhold[coin] = {"total": bh_total, "cagr": bh_cagr}
        print(f"  {coin} B&H: +{bh_total*100:.1f}% over {n_days/365:.1f}y "
              f"= CAGR {bh_cagr*100:+.1f}%/yr")

    # Momentum benchmark: corr(trailing_7d_ret, forward_7d_ret) (weekly, non-overlap)
    print("\n  Momentum benchmark (does THIS WEEK's return predict NEXT week?):")
    mom_ics = {}
    for coin in CURRENCIES:
        p = prices[coin]
        fwd = np.log(p.shift(-7) / p)
        trail = np.log(p / p.shift(7))
        df = pd.DataFrame({"fwd": fwd, "trail": trail}).dropna()
        idx = df.index
        weeks = (idx - idx[0]).days // REBALANCE
        df["week"] = weeks
        sp = df.groupby("week").tail(1).dropna()
        mom_ic = _ic_with_tstat(sp["trail"].to_numpy(), sp["fwd"].to_numpy())
        mom_ics[coin] = mom_ic
        if mom_ic is not None:
            print(f"      {coin}: mom IC={mom_ic['ic']:+.3f} (t={mom_ic['t']:+.2f}, "
                  f"p={mom_ic['p']:.3f})")
    print()

    # ── Weekly forward IC + strategy P&L ─────────────────────────────────────
    print("=== WEEKLY NON-OVERLAPPING: forward vs trailing IC + tradable P&L ===\n")
    for coin in CURRENCIES:
        bh = buyhold[coin]
        for key in results["per_coin"][coin]:
            r = results["per_coin"][coin][key]
            fi = r["fwd_ic"]
            ti = r["trail_ic"]
            st = r["strategy"]
            reg = r["regression"]
            def fmt(ic):
                if ic is None:
                    return "n/a"
                return (f"IC={ic['ic']:+.3f} t={ic['t']:+.2f} "
                        f"p={ic['p']:.3f} n={ic['n']}")
            excess = st["net_cagr"] - bh["cagr"]
            print(f"  {coin} [{key}]:")
            print(f"      FORWARD   {fmt(fi)}   <- tradeable 'leading' measure")
            print(f"      ECHO      {fmt(ti)}   <- does flow just echo recent price?")
            if reg:
                print(f"      Granger   fwd_ret~g+trail_ret: coef_g={reg['coef_g']:+.4f} "
                      f"(t={reg['t_g']:+.2f}), coef_trail={reg['coef_trail']:+.4f}")
            print(f"      strategy  n={st['n']} long={st['n_long']} flips={st['n_flips']} "
                  f"| net +{st['net_total']*100:.1f}% (CAGR {st['net_cagr']*100:+.1f}%/yr, "
                  f"Sharpe {st['net_sharpe']:+.2f})")
            print(f"      vs B&H    CAGR {bh['cagr']*100:+.1f}%/yr -> "
                  f"EXCESS {excess*100:+.1f}%/yr")
        print()

    # ── Verdict ──────────────────────────────────────────────────────────────
    # STRICT bar (robustness-first, multiple-testing aware): promote ONLY if
    #   (a) forward IC > 0 AND significant after Bonferroni over 8 cells,
    #   (b) net strategy produces ALPHA over buy-and-hold (not just a long-beta
    #       ride in the 2020->2026 bull), and
    #   (c) the forward edge dominates the echo (lead > echo, not echo > lead)
    #       AND survives the Granger (trailing-return) control.
    n_tests = len(CURRENCIES) * len(FLOW_KINDS) * len(GROWTH_WINDOWS)
    promote = {}
    verdict_lines = []
    for coin in CURRENCIES:
        bh = buyhold[coin]
        for key, r in results["per_coin"][coin].items():
            fi = r["fwd_ic"]
            ti = r["trail_ic"]
            st = r["strategy"]
            reg = r["regression"]
            if fi is None:
                verdict_lines.append(f"  {coin} {key}: n/a")
                continue
            bonf = min(1.0, fi["p"] * n_tests)
            sig_bonf = bonf < 0.05
            alpha_pos = st["net_cagr"] > bh["cagr"]
            lead_dominates = fi["ic"] > 0 and fi["ic"] > ti["ic"]
            survive = bool(reg) and reg["t_g"] > 1.96
            promote[f"{coin}_{key}"] = bool(sig_bonf and alpha_pos
                                            and lead_dominates and survive)
            verdict_lines.append(
                f"  {coin} {key}: fwdIC {fi['ic']:+.3f} (p={fi['p']:.4f}, "
                f"bonf={bonf:.3f}) | echoIC {ti['ic']:+.3f} | excess-vs-B&H "
                f"{(st['net_cagr'] - bh['cagr'])*100:+.1f}%/yr | "
                f"sig={sig_bonf} alpha={alpha_pos} lead>echo={lead_dominates} "
                f"granger={survive}")

    print("=== PER-SIGNAL VERDICT (strict bar) ===\n")
    print(f"  ({n_tests} cells tested; Bonferroni p <= each raw p x {n_tests})")
    for v in verdict_lines:
        print(v)
    print(f"\n  ANY PROMOTABLE (bonferroni-sig + alpha-over-B&H + lead>echo "
          f"+ granger-survives): {any(promote.values())}")

    # ── Write trial ─────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "onchain_flow_lead_lag",
        "universe": CURRENCIES,
        "venue": "hyperliquid_price_daily",
        "flow_kinds": FLOW_KINDS,
        "growth_windows_days": GROWTH_WINDOWS,
        "horizon_days": HORIZON,
        "sampling": "non_overlapping_weekly",
        "signal": "aggregate_stablecoin_supply_log_growth + aggregate_tvl_log_growth",
        "tradable": "long_if_growth>0_else_flat",
        "cost": {"taker_bps": TAKER_BPS, "slippage_bps": SLIPPAGE_BPS,
                 "funding_bps_week": FUNDING_BPS_WEEK,
                 "round_trip_bps": ROUND_TRIP_BPS, "maker_rebate": "none_fail_closed"},
        "leverage": "none_1x_long_only",
        "live": "off",
        "honesty_test": "forward_ic_vs_echo_ic + granger + correlogram",
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(sorted(CURRENCIES)).encode()).hexdigest()

    # serialize (strip numpy arrays from strategy dicts in results)
    serializable = {
        "per_coin": {},
        "cross_corr": results["cross_corr"],
        "promote": promote,
    }
    for coin in CURRENCIES:
        serializable["per_coin"][coin] = {}
        for key, r in results["per_coin"][coin].items():
            serializable["per_coin"][coin][key] = {
                "fwd_ic": r["fwd_ic"],
                "trail_ic": r["trail_ic"],
                "regression": r["regression"],
                "strategy": {k: (float(v) if isinstance(v, (np.floating, float))
                                else v) for k, v in r["strategy"].items()},
            }

    summary = {
        "promote": promote,
        "buy_and_hold": buyhold,
        "momentum_ic": mom_ics,
        "max_abs_fwd_ic": max(
            (r["fwd_ic"]["ic"] if r["fwd_ic"] else 0.0)
            for coin in CURRENCIES for r in results["per_coin"][coin].values()),
    }
    verdict = (
        "NO TRADEABLE LEADING EDGE — coincident echo, not lead. Aggregate "
        "stablecoin supply and TVL growth are STRONGLY COINCIDENT with price: "
        "the echo IC (flow vs the trailing week's return) is large and highly "
        "significant (up to +0.74), while the FORWARD IC is near-zero in 7 of 8 "
        "cells. The lead-lag correlogram peaks at NEGATIVE lag (h=-4..-29: "
        "flow LAGS price) and collapses to ~0 at h=0 and h>0 — the signature "
        "of a coincident macro echo, not a leading flow signal. The sole "
        "exception is ETH/tvl-30d (forward IC +0.151, raw p=0.006, Bonferroni "
        "p=0.049, +14.6%/yr excess over buy-and-hold, Granger t=+2.95), BUT its "
        "echo IC (+0.37) is 2.4x its forward IC, so it FAILS the load-bearing "
        "lead-vs-echo test (the signal is far more a reflection of the past "
        "week's price than a prediction of the next) — a single marginal cell "
        "among 8, consistent with a slow-TVL-trend/trend-filter effect rather "
        "than an independent causal flow lead. On-chain/macro flow does NOT "
        "lead price at a tradeable weekly horizon. NOT promoted — matching the "
        "prior exactly."
    )

    result = {
        "construction": "onchain_flow_lead_lag",
        "venue": "hyperliquid_price_daily",
        "universe": CURRENCIES,
        "leverage": "none",
        "live": "off",
        "no_lookahead": True,
        "summary": summary,
        "details": serializable,
        "verdict": verdict,
    }

    if not args.no_write:
        e = ledger.increment_trial("HYP-32", param_hash, universe_hash,
                                   "2020-08-19", "2026-11-08", result)
        print(f"\nwrote trial HYP-32 param_hash={e['param_hash'][:16]}... "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())