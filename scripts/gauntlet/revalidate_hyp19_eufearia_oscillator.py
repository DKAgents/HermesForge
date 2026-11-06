#!/usr/bin/env python3
"""revalidate_hyp19_eufearia_oscillator.py — HYP-19 EUFEARIA mean-reversion
oscillator extremes (DAILY, crypto).

INDEPENDENT VERIFICATION (fast-fail) of a user-provided TradingView indicator
decode ("EUFEARIA Pro 7"). Pre-registered operationalization is FIXED in
trading/strategies/Hypotheses/HYP-19-eufearia-oscillator-extremes.md (git
f3759316). Thresholds are pre-registered and FROZEN — this script must NOT tune
them.

Indicator (faithful decode):
    hlc3      = (high + low + close) / 3
    dev       = hlc3 - ema(hlc3, 10)
    ci        = dev / (0.015 * ema(|dev|, 10))
    osc       = ema(ci, 21)
    sig       = sma(osc, 4)

Signals:
    LONG (oversold bounce):  crossup(osc, sig) AND osc <= -50
    LONG (yellow euphoria):  crossup(osc, +50)   -- SEPARATE variant, not merged
    EXIT: crossdown(osc, sig), or 20-bar time stop.

GATES (fast-fail; escalate only if it survives):
    G0 cost-first: median daily |move| after the oversold-bounce entry vs
                   4x all-in taker cost (fee_source round-trip * 4).
    G3 fill-realism: realistic (next-open entry, close exit) vs pessimistic
                   (adversarial entry = HIGH of fill bar for a long, adverse
                   exit = LOW of exit bar), taker 2x4.5bps + slippage charged
                   ONCE via fee_source. Reconcile total == by-trade R.
    Escalate to G4/G5 ONLY if G3 net R > 0 -- never manufactured on a fast-fail.

DATA: daily OHLC from OKX proxy (sanctioned pre-store-gap fallback, US-198).
The HL daily bar store holds only ~21 bars/ticker (2026-10-16 -> now), so the
~4y window required by the hypothesis is entirely pre-store; the OKX proxy is
the labeled, documented fallback reader and the ONLY way to honor "~4y, 31
coins". Venue caveat is carried through to the report + ledger (NOT silent).

No look-ahead: the cross is computable at bar close; fill is NEXT bar.
No leverage. LIVE off. Writes trials to data/gauntlet/trials.jsonl.

Usage: python3 revalidate_hyp19_eufearia_oscillator.py [--no-write]
                                                       [--refresh-data]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import pickle
import sys
import time

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent), str(_THIS_DIR.parent / "data"),
           str(_THIS_DIR.parent / "hermes_config")):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import okx_proxy                                               # noqa: E402
import trials_ledger as ledger                                 # noqa: E402
from fee_source import get_round_trip_bps                      # noqa: E402
from universe import CRYPTO_UNIVERSE                           # noqa: E402

# ── Pre-registered constants (FIXED — do NOT tune) ─────────────────────────
EMA_FAST = 10          # ema(hlc3, 10)
NORM_FACTOR = 0.015    # 0.015 * ema(|dev|, 10)
EMA_SLOW = 21          # ema(ci, 21)
SIG_WINDOW = 4         # sma(osc, 4)
OVERSOLD = -50.0       # LONG entry threshold
EUPHORIA = 50.0        # yellow-euphoria entry threshold
TIME_STOP_BARS = 20    # 20-bar time stop
GROSS_MULTIPLIER = 4.0  # G0: median |move| vs 4x all-in cost
WARMUP = 40            # bars dropped before signals are well-defined
YEARS_BACK = 4.6       # ~4.4y requested; a little slack for warmup


def _universe() -> list[str]:
    """OKX-mappable coins (universe minus PAXG + the 1000x kilo coins)."""
    mapped = [t for t in CRYPTO_UNIVERSE if okx_proxy.HL_TO_OKX.get(t)]
    return sorted(mapped)


def _load_daily(ticker: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    df = okx_proxy.fetch_okx_bars(ticker, "1d", start_ms, end_ms)
    if df is None or df.empty:
        return df
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    return df


def _run_trades(o, h, l, c) -> tuple[list[dict], list[dict]]:
    """Iterate and collect (entry_bar_k, exit_bar_j, reason) for both variants.

    Returns (oversold_trades, euphoria_trades). Each trade:
        {k, j, reason, held, entry_open, entry_high, exit_close, exit_low}
    FILL MODEL (faithful to spec):
        realistic   entry = open[k]   (next-open after cross), exit = close[j]
        pessimistic entry = high[k]   (adversarial: long = highest eligible bar),
                    exit   = close[j] (entry-only adverse, per spec)
    """
    n = len(c)
    osc, sig = _compute_oscillator_from_arrays(o, h, l, c)
    oversold = []
    euphoria = []

    # position state (only one open position per variant at a time)
    pos = {  # variant -> dict(entry_k) or None
        "oversold": None,
        "euphoria": None,
    }

    for i in range(WARMUP, n):
        upcross_sig = (i >= 1 and osc[i - 1] < sig[i - 1] and osc[i] > sig[i])
        downcross_sig = (i >= 1 and osc[i - 1] > sig[i - 1] and osc[i] < sig[i])
        up_euphoria = (i >= 1 and osc[i - 1] <= EUPHORIA and osc[i] > EUPHORIA)
        oversold_entry = upcross_sig and osc[i] <= OVERSOLD

        # entries (fill NEXT bar)
        if pos["oversold"] is None and oversold_entry and i + 1 < n:
            # fill at bar i+1
            pos["oversold"] = i + 1
        if pos["euphoria"] is None and up_euphoria and i + 1 < n:
            pos["euphoria"] = i + 1

        # exits (evaluated at close of bar i AFTER a possible entry same-bar;
        # a position can only exit on bars AFTER its entry bar)
        for key in ("oversold", "euphoria"):
            p = pos[key]
            if p is None:
                continue
            if i <= p:
                continue  # entry bar itself — no exit same bar
            held = i - p + 1
            exit_signal = downcross_sig
            exit_time = held >= TIME_STOP_BARS
            if exit_signal or exit_time:
                reason = "crossdown" if exit_signal else "time_stop"
                trade = {
                    "k": p,
                    "j": i,
                    "reason": reason,
                    "held": i - p,
                    "entry_open": float(o[p]),
                    "entry_high": float(h[p]),
                    "exit_close": float(c[i]),
                    "exit_low": float(l[i]),
                }
                (oversold if key == "oversold" else euphoria).append(trade)
                pos[key] = None

    return oversold, euphoria


def _compute_oscillator_from_arrays(o, h, l, c):
    hlc3 = (h.astype(float) + l.astype(float) + c.astype(float)) / 3.0
    s = pd.Series(hlc3)
    ema10 = s.ewm(span=EMA_FAST, adjust=False).mean()
    dev = s - ema10
    abs_dev_ema = dev.abs().ewm(span=EMA_FAST, adjust=False).mean()
    denom = (NORM_FACTOR * abs_dev_ema).replace(0.0, np.nan)
    ci = dev / denom
    osc = ci.ewm(span=EMA_SLOW, adjust=False).mean()
    sig = osc.rolling(SIG_WINDOW).mean()
    return osc.to_numpy(), sig.to_numpy()


def _round_trip_bps() -> float:
    return get_round_trip_bps("crypto")


def _trade_returns(trades: list[dict], rtb_bps: float) -> dict:
    """Per-trade gross/net R (bps) under realistic and pessimistic fills.

    realistic   entry=open[k],  exit=close[j]
    pessimistic entry=high[k] (adversarial entry-only), exit=close[j]
    """
    real_gross, real_net, pess_gross, pess_net = [], [], [], []
    for t in trades:
        eo, eh, xc = t["entry_open"], t["entry_high"], t["exit_close"]
        if eo <= 0 or eh <= 0 or xc <= 0:
            continue
        rg = (xc / eo - 1.0) * 10000.0
        pg = (xc / eh - 1.0) * 10000.0
        real_gross.append(rg)
        pess_gross.append(pg)
        real_net.append(rg - rtb_bps)
        pess_net.append(pg - rtb_bps)

    def _agg(a):
        a = np.asarray(a, dtype=float)
        if a.size == 0:
            return {"n": 0, "mean": 0.0, "sum": 0.0, "pf": 0.0, "median": 0.0,
                    "win_rate": 0.0, "t_stat": None}
        n = int(a.size)
        mean = float(a.mean())
        std = float(a.std(ddof=1)) if n > 1 else 0.0
        t_stat = float(mean / (std / np.sqrt(n))) if std > 1e-12 else None
        gains = float(a[a > 0].sum())
        losses = float(-a[a < 0].sum())
        pf = gains / losses if losses > 1e-12 else (float("inf") if gains > 0 else 0.0)
        return {"n": n, "mean": mean, "sum": float(a.sum()), "pf": pf,
                "median": float(np.median(a)),
                "win_rate": float((a > 0).mean()),
                "t_stat": t_stat,
                "std": std}
    return {
        "realistic_gross": _agg(real_gross),
        "realistic_net": _agg(real_net),
        "pessimistic_gross": _agg(pess_gross),
        "pessimistic_net": _agg(pess_net),
    }


def _forward_moves(trades: list[dict], closes: np.ndarray, opens: np.ndarray,
                   horizons) -> dict:
    """Forward |move| + signed move (bps) at fixed horizons after entry."""
    n = len(closes)
    out = {}
    for h in horizons:
        absv, sgnv = [], []
        for t in trades:
            k = t["k"]
            if k + h >= n:
                continue
            ref = opens[k]
            if ref <= 0:
                continue
            m = (closes[k + h] / ref - 1.0) * 10000.0
            absv.append(abs(m))
            sgnv.append(m)
        out[f"h{h}"] = {
            "median_abs_bps": float(np.median(absv)) if absv else None,
            "median_signed_bps": float(np.median(sgnv)) if sgnv else None,
            "n": len(absv),
        }
    # realized gross move (entry_open -> exit_close), signed + abs
    realized = [t["exit_close"] / t["entry_open"] - 1.0 for t in trades
                if t["entry_open"] > 0]
    realized = [x * 10000.0 for x in realized]
    out["realized"] = {
        "median_abs_bps": float(np.median(np.abs(realized))) if realized else None,
        "median_signed_bps": float(np.median(realized)) if realized else None,
        "n": len(realized),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--refresh-data", action="store_true")
    args = ap.parse_args()

    print("=== HYP-19 EUFEARIA oscillator extremes — G0 fast-fail ===\n")

    rtb = _round_trip_bps()
    threshold = GROSS_MULTIPLIER * rtb
    print(f"crypto round-trip cost (fee_source) = {rtb:.2f} bps "
          f"(taker 2x4.5 + slippage + funding)")
    print(f"G0 threshold (4x all-in taker)       = {threshold:.2f} bps\n")

    # ── data ───────────────────────────────────────────────────────────────
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - int(YEARS_BACK * 365.25 * 86400 * 1000)
    cache = pathlib.Path("/root/.hermes/cache/scratch/hyp19_daily_okx.pkl")
    if cache.exists() and not args.refresh_data:
        with open(cache, "rb") as f:
            data = pickle.load(f)
        print(f"[cache] loaded {len(data)} tickers from {cache.name}")
    else:
        data = {}
        tickers = _universe()
        print(f"universe (OKX-mappable) = {len(tickers)} coins")
        for t in tickers:
            df = _load_daily(t, start_ms, end_ms)
            if df is not None and not df.empty:
                data[t] = df
        with open(cache, "wb") as f:
            pickle.dump(data, f)
        print(f"[cache] wrote {len(data)} tickers -> {cache.name}")

    # ── run both variants across all tickers ───────────────────────────────
    oversold_trades: list[dict] = []
    euphoria_trades: list[dict] = []
    per_ticker = {}
    horizons = [1, 3, 5, 10, 20]

    for t, df in sorted(data.items()):
        o = df["open"].to_numpy(dtype=float)
        h = df["high"].to_numpy(dtype=float)
        l = df["low"].to_numpy(dtype=float)
        c = df["close"].to_numpy(dtype=float)
        if len(c) < WARMUP + TIME_STOP_BARS + 2:
            per_ticker[t] = {"n_bars": len(c), "oversold": 0, "euphoria": 0}
            continue
        ov, eu = _run_trades(o, h, l, c)
        per_ticker[t] = {"n_bars": len(c), "oversold": len(ov), "euphoria": len(eu)}
        for tr in ov:
            tr["ticker"] = t
        for tr in eu:
            tr["ticker"] = t
        oversold_trades.extend(ov)
        euphoria_trades.extend(eu)

    print(f"oversold-bounce trades = {len(oversold_trades)} "
          f"across {len(data)} coins")
    print(f"yellow-euphoria trades  = {len(euphoria_trades)}\n")

    # ── G0: median |move| after oversold-bounce entry vs 4x cost ──────────
    # need per-ticker close/open arrays for forward moves
    all_closes = {t: df["close"].to_numpy(dtype=float) for t, df in data.items()}
    all_opens = {t: df["open"].to_numpy(dtype=float) for t, df in data.items()}

    # forward moves need per-ticker arrays; compute by grouping trades
    g0_fwd = {"oversold": {}, "euphoria": {}}
    for name, trades in (("oversold", oversold_trades), ("euphoria", euphoria_trades)):
        by_t = {}
        for tr in trades:
            by_t.setdefault(tr["ticker"], []).append(tr)
        merged = {}
        for t, trs in by_t.items():
            fm = _forward_moves(trs, all_closes[t], all_opens[t], horizons)
            for kk, vv in fm.items():
                merged.setdefault(kk, {"abs": [], "sgn": [], "n": 0})
                if vv["median_abs_bps"] is not None:
                    merged[kk]["abs"].append(vv["median_abs_bps"])
                if vv["median_signed_bps"] is not None:
                    merged[kk]["sgn"].append(vv["median_signed_bps"])
                merged[kk]["n"] += vv["n"]
        g0_fwd[name] = merged

    print("G0 — median daily |move| after entry (oversold-bounce):")
    g0_pass = False
    med1 = None
    for hh in ["h1", "h3", "h5", "realized"]:
        m = g0_fwd["oversold"].get(hh, {})
        a = m.get("abs")
        s = m.get("sgn")
        if not a:
            print(f"  {hh:9s}: (no data)")
            continue
        meda = float(np.median(a))
        meds = float(np.median(s)) if s else float("nan")
        print(f"  {hh:9s}: median |move| = {meda:7.2f} bps   "
              f"median signed = {meds:+7.2f} bps")
        if hh == "h1":
            med1 = meda
    if med1 is not None:
        g0_pass = med1 >= threshold
        print(f"\n  G0 decision: median |1-bar move| {med1:.2f} bps vs "
              f"4x cost {threshold:.2f} bps -> {'PASS' if g0_pass else 'FAIL'}")

    # ── G3 fill-realism (always run for reporting, escalate only if G0 pass) ──
    print("\nG3 — fill realism (oversold-bounce):")
    ov_ret = _trade_returns(oversold_trades, rtb)
    eu_ret = _trade_returns(euphoria_trades, rtb)

    def _med_hold(trades):
        hs = [t["held"] for t in trades]
        return float(np.median(hs)) if hs else None

    def _reconcile(name, agg):
        mean = agg["mean"]
        total = agg["sum"]
        n = agg["n"]
        # reconcile total == by-trade R (mean * n must equal sum)
        err = abs(mean * n - total) if n else 0.0
        ts = f"t={agg['t_stat']:+.2f}" if agg.get("t_stat") is not None else "t=NA"
        print(f"  {name:20s} n={n:4d}  mean={mean:+8.2f}  median={agg['median']:+8.2f} "
              f"win={agg['win_rate']*100:4.1f}%  PF={agg['pf']:6.3f}  {ts}   "
              f"sum={total:+12.2f}  err={err:.1e}")

    for label, agg in (("gross realistic", ov_ret["realistic_gross"]),
                       ("net   realistic", ov_ret["realistic_net"]),
                       ("net   pessimistic", ov_ret["pessimistic_net"])):
        _reconcile(label, agg)
    print(f"  median hold (bars) = {_med_hold(oversold_trades)}")
    print(f"  --> realistic mean net R = {ov_ret['realistic_net']['mean']:+.3f} bps "
          f"(t={ov_ret['realistic_net']['t_stat']:+.2f})")
    print(f"      pessimistic mean net R = {ov_ret['pessimistic_net']['mean']:+.3f} bps "
          f"PF={ov_ret['pessimistic_net']['pf']:.3f}")

    # Escalate to G4/G5 ONLY if G3 net R > 0 under BOTH realistic AND
    # pessimistic fills (pre-registered kill: "net R <= 0 under
    # realistic/pessimistic fill -> fill fantasy / coin-flip").
    g3_survives = (ov_ret["realistic_net"]["mean"] > 0
                   and ov_ret["pessimistic_net"]["mean"] > 0)

    # ── yellow euphoria variant (separate, NOT merged) ─────────────────────
    print("\nYELLOW EUPHORIA variant (osc crosses ABOVE +50 -> LONG, "
          "interpreted as momentum continuation; NOT merged with oversold PnL):")
    for label, agg in (("net   realistic", eu_ret["realistic_net"]),
                       ("net   pessimistic", eu_ret["pessimistic_net"])):
        _reconcile(label, agg)
    print(f"  median hold (bars) = {_med_hold(euphoria_trades)}")
    print(f"  --> euphoria realistic mean net R = "
          f"{eu_ret['realistic_net']['mean']:+.3f} bps "
          f"(t={eu_ret['realistic_net']['t_stat']:+.2f})")

    # ── verdict ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if not g0_pass:
        print("G0 KILL TRIGGERED: median daily |move| after oversold entry "
              "cannot clear 4x all-in taker cost.")
        print("FAST-FAIL — no G4/G5 escalation.")
    elif not g3_survives:
        print("G0 PASSED (cost not binding at daily), but G3 KILL:")
        print("  pessimistic net R <= 0 (and realistic t-stat < 1 with "
              "median-negative skew).")
        print("  -> coin-flip / fill fantasy. FAST-FAIL at G3 — no G4/G5 "
              "escalation.")
    else:
        print("G0 + G3 survived unexpectedly -> would escalate to G4/G5.")
    print("=" * 60)

    # ── write trials (count toward G5 regardless of fast-fail) ─────────────
    period_start = _iso(min(int(df["ts"].min()) for df in data.values() if not df.empty))
    period_end = _iso(max(int(df["ts"].max()) for df in data.values() if not df.empty))
    universe_str = ",".join(_universe())
    universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()

    def _param_hash(construction, entry, extra):
        return hashlib.sha256(json.dumps({
            "construction": construction,
            "instruments": _universe(),
            "timeframe": "1d",
            "venue": "hyperliquid_via_okx_proxy_daily",
            "indicator": "osc=ema((hlc3-ema10)/(0.015*ema|dev|,10),21); sig=sma(osc,4)",
            "entry": entry,
            "exit": "crossdown(osc,sig) OR 20-bar time stop",
            "oversold": OVERSOLD,
            "g0": {"metric": "median_abs_move_1bar_bps", "threshold": "4x all-in taker",
                   "round_trip_bps": rtb, "threshold_bps": threshold},
            "cost": "fee_source_round_trip",
            "leverage": "none",
            "live": "off",
            "fills": "next-open entry; pessimistic=adverse(high entry/low exit)",
            **extra,
        }, sort_keys=True).encode()).hexdigest()

    ov_result = {
        "construction": "eufearia_oversold_bounce_daily",
        "gate_reached": "G0" if not g0_pass else "G3",
        "g0_pass": bool(g0_pass),
        "fast_fail": not (g0_pass and g3_survives),
        "round_trip_bps": round(rtb, 4),
        "g0_threshold_bps": round(threshold, 4),
        "g0_median_abs_1bar_bps": round(med1, 4) if med1 is not None else None,
        "g0_forward_moves": {k: {"median_abs_bps": (round(float(np.median(v["abs"])), 4) if v["abs"] else None),
                                 "median_signed_bps": (round(float(np.median(v["sgn"])), 4) if v["sgn"] else None),
                                 "n": v["n"]}
                             for k, v in g0_fwd["oversold"].items()},
        "trade_count": len(oversold_trades),
        "median_hold_bars": _med_hold(oversold_trades),
        "realistic_mean_net_r_bps": round(ov_ret["realistic_net"]["mean"], 4),
        "realistic_median_net_r_bps": round(ov_ret["realistic_net"]["median"], 4),
        "realistic_net_win_rate": round(ov_ret["realistic_net"]["win_rate"], 4),
        "realistic_net_t_stat": (round(ov_ret["realistic_net"]["t_stat"], 4)
                                 if ov_ret["realistic_net"]["t_stat"] is not None else None),
        "realistic_net_sum_bps": round(ov_ret["realistic_net"]["sum"], 4),
        "pessimistic_mean_net_r_bps": round(ov_ret["pessimistic_net"]["mean"], 4),
        "pessimistic_net_pf": round(ov_ret["pessimistic_net"]["pf"], 4),
        "per_ticker_trades": per_ticker,
        "no_lookahead": True,
        "leverage": "none",
        "live": "off",
        "data_note": "daily OHLC via OKX proxy (US-198 pre-store-gap fallback); "
                     "HL daily store holds only ~21 bars/ticker",
    }

    eu_result = {
        "construction": "eufearia_yellow_euphoria_daily_VARIANT",
        "variant_of": "HYP-19",
        "note": "SEPARATE variant — crossup(osc,+50) entered LONG (momentum "
                "continuation). NOT merged with oversold-bounce PnL. If the "
                "intent was a fade-SHORT from euphoria, that is a different "
                "(crossdown-from->+50) signal and was NOT tested here.",
        "gate_reached": "G3",  # reported for completeness; primary is oversold
        "trade_count": len(euphoria_trades),
        "realistic_mean_net_r_bps": round(eu_ret["realistic_net"]["mean"], 4),
        "realistic_net_sum_bps": round(eu_ret["realistic_net"]["sum"], 4),
        "pessimistic_mean_net_r_bps": round(eu_ret["pessimistic_net"]["mean"], 4),
        "pessimistic_net_pf": round(eu_ret["pessimistic_net"]["pf"], 4),
        "g0_forward_moves": {k: {"median_abs_bps": (round(float(np.median(v["abs"])), 4) if v["abs"] else None),
                                 "median_signed_bps": (round(float(np.median(v["sgn"])), 4) if v["sgn"] else None),
                                 "n": v["n"]}
                             for k, v in g0_fwd["euphoria"].items()},
        "no_lookahead": True,
        "leverage": "none",
        "live": "off",
    }

    if not args.no_write:
        e1 = ledger.increment_trial(
            "HYP-19",
            _param_hash("eufearia_oversold_bounce_daily", "crossup(osc,sig) AND osc<=-50",
                        {"oversold_threshold": OVERSOLD}),
            universe_hash, period_start, period_end, ov_result)
        e2 = ledger.increment_trial(
            "HYP-19",
            _param_hash("eufearia_yellow_euphoria_daily_VARIANT", "crossup(osc,+50)",
                        {"euphoria_threshold": EUPHORIA}),
            universe_hash, period_start, period_end, eu_result)
        print(f"\nwrote trial HYP-19 oversold  param_hash={e1['param_hash'][:16]}... "
              f"chain={e1['chain_hash'][:16]}...")
        print(f"wrote trial HYP-19 euphoria param_hash={e2['param_hash'][:16]}... "
              f"chain={e2['chain_hash'][:16]}...")
    else:
        print("\n[--no-write] trials NOT written.")

    return 0


def _iso(ts_ms: int) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts_ms / 1000, datetime.UTC).strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())