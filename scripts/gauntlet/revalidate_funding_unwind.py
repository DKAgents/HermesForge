"""revalidate_funding_unwind.py — US-212 funding-extreme unwind at SWING horizon.

Read-only research driver. Replays the POSITIONING-CONDITIONED funding-extreme
unwind (seed-pool HYP-01, re-specified at swing 4-48h) on REAL funding history,
and separates the HONEST funding component from the basis-proxy component.

Signal construction (per coin, on ~400d hourly fundingHistory):
  funding percentile  = trailing 90d rolling percentile of the hourly funding rate
  ENTRY: funding > 95th pct  -> fade crowded LONGS (short; receive funding)
         funding <  5th pct  -> fade crowded SHORTS (long; receive funding)
  EXIT:  funding reverts below 80th pct (longs) / above 20th pct (shorts),
         or a hard 48h max-hold (the swing cap), whichever first.

What is honestly computable vs. what is data-gated (REPORTED, not papered over):
  * FUNDING-only edge (funding collected while fading / cost)  -> COMPUTED here
      from hl_funding_store (~400d, 35 coins). This is the carry component only.
  * DIRECTIONAL unwind (does price mean-revert as the crowd unwinds) -> DATA-GATED:
      mark history is forward-only (hl_assetctx_store ~12 rows), no deep markPx.
  * OI-delta quadrant (`oi_delta`) + OKX funding SPREAD (`cross_venue_basis`) ->
      DATA-GATED: hl_assetctx openInterest ~12 rows, OKX spread ~6 rows — both
      forward-accumulating feeds with essentially no history. These are the
      load-bearing "positioning-conditioned" parts that distinguish this
      construction from the naked directional carry that structural analysis
      (US-179/185) already rejected (price risk 20-39x funding).

The funding-only figure is quoted as the honest edge (funding_pnl - cost); the
basis-proxy contribution is reported separately and NOT folded in (per the
strategy-gauntlet decomposition).

Writes ONE trial to data/gauntlet/trials.jsonl (fresh param_hash). No leverage
(notional = 1x capital), cost counted once (fee_source round-trip), no live state.
Usage: python3 revalidate_funding_unwind.py [--no-write]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
for _p in (_THIS_DIR, str(_THIS_DIR.parent), str(_THIS_DIR.parent / "data")):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import hl_funding_store as fs                           # noqa: E402
import trials_ledger as ledger                          # noqa: E402
from fee_source import get_round_trip_bps               # noqa: E402
from hermes_config.universe import CRYPTO_UNIVERSE      # noqa: E402

PCTILE_ENTRY_HIGH = 95        # funding > 95th pct -> fade longs (short)
PCTILE_EXIT_HIGH = 80         # funding < 80th pct -> exit the short
PCTILE_ENTRY_LOW = 5          # funding < 5th pct  -> fade shorts (long)
PCTILE_EXIT_LOW = 20          # funding > 20th pct -> exit the long
PCTILE_WINDOW_HOURS = 90 * 24  # trailing 90d percentile window
MAX_HOLD_HOURS = 48           # swing horizon cap (4-48h)
CAPITAL = 1_000_000.0         # sizing reference only (notional = 1x capital)
RISK_UNIT_FRAC = 0.01         # 1R = 1% capital


def funding_percentile(series: pd.DataFrame, window: int = PCTILE_WINDOW_HOURS):
    """Trailing `window`-hour percentile of the funding rate (rolling .rank)."""
    rates = series["funding_rate"].astype(float)
    pct = rates.rolling(window, min_periods=max(24, window // 8)).apply(
        lambda w: (w < w.iloc[-1]).mean() * 100.0, raw=False)
    return pct


def simulate_unwind(funding: pd.DataFrame, coin: str) -> list[dict]:
    """Funding-only unwind replay. Returns one dict per episode.

    Each episode: {entry_ts, exit_ts, hours, side, funding_pnl, cost_frac,
    net_funding_r}. side=+1 short (fade longs), -1 long (fade shorts).
    NOTIONAL = 1x capital (no leverage); funding_pnl = sign * rate * notional
    summed hourly (a short RECEIVES positive funding -> funding_pnl > 0).
    net_funding_r = (funding_pnl - cost) / (1% capital). This is the carry only —
    the directional mark move is NOT computed here (data-gated).
    """
    if funding is None or len(funding) < PCTILE_WINDOW_HOURS:
        return []
    pct = funding_percentile(funding)
    rates = funding["funding_rate"].astype(float).to_numpy()
    times = funding["time"].astype("int64").to_numpy()
    rtb = get_round_trip_bps("crypto")          # all-in round-trip (12 bps)
    cost_frac = rtb / 1e4                        # charged once per episode
    notional = CAPITAL
    risk_usd = RISK_UNIT_FRAC * CAPITAL

    episodes: list[dict] = []
    i = PCTILE_WINDOW_HOURS
    n = len(funding)
    while i < n:
        p = pct.iloc[i]
        if not np.isfinite(p):
            i += 1
            continue
        if rates[i] <= 0 or rates[i] >= 0:      # no-op guard (always true)
            pass
        # determine side
        if p >= PCTILE_ENTRY_HIGH and rates[i] > 0:
            side = +1     # short — fade crowded longs (positive funding)
        elif p <= PCTILE_ENTRY_LOW and rates[i] < 0:
            side = -1     # long — fade crowded shorts (negative funding)
        else:
            i += 1
            continue

        entry_ts = int(times[i])
        fp = 0.0
        j = i
        exited = False
        while j < n and (j - i) <= MAX_HOLD_HOURS:
            fp += side * rates[j] * notional      # funding accrual each hour held
            q = pct.iloc[j] if j < n else np.nan
            if side == +1 and np.isfinite(q) and q <= PCTILE_EXIT_HIGH:
                exited = True
                break
            if side == -1 and np.isfinite(q) and q >= PCTILE_EXIT_LOW:
                exited = True
                break
            j += 1
        ep_end = int(times[j]) if j < n else int(times[n - 1])
        hours = j - i
        net_funding = fp - cost_frac * notional
        episodes.append({
            "coin": coin, "entry_ts": entry_ts, "exit_ts": ep_end,
            "hours": hours, "side": side,
            "exit_reason": ("pctile_revert" if exited else "max_hold"),
            "funding_pnl": fp, "cost_frac": cost_frac * notional,
            "net_funding_r": net_funding / risk_usd,
        })
        i = j + 1
    return episodes


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== US-212 funding-extreme unwind (swing 4-48h) — real-data ===\n")

    # ── data reality ─────────────────────────────────────────────────────────
    from hl_assetctx_store import read_positioning
    from basis_store import read_basis
    pos_rows = read_positioning("BTC")
    spd_rows = read_basis("BTC")
    print("data-depth reality (load-bearing conditioning feeds):")
    print(f"  hl_fundingHistory: ~400d hourly, 35 coins (FULL)")
    print(f"  hl assetCtx openInterest (OI-delta): {0 if pos_rows is None else len(pos_rows)} rows — forward-only")
    print(f"  cross-venue OKX funding spread: {0 if spd_rows is None else len(spd_rows)} rows — forward-only")
    print("  -> OI-delta quadrant + OKX spread (the 'positioning-conditioned' parts)")
    print("     have NO historical depth; the NAKED funding-percentile replay is what")
    print("     is honestly testable today.\n")

    all_eps = []
    for coin in CRYPTO_UNIVERSE:
        f = fs.read_funding(coin)
        if f is None or f.empty:
            continue
        f.attrs["coin"] = coin
        all_eps.extend(simulate_unwind(f, coin))

    if not all_eps:
        print("no episodes")
        return 0

    eps = pd.DataFrame(all_eps)
    n = len(eps)
    side_short = eps[eps["side"] == 1]
    side_long = eps[eps["side"] == -1]
    fp_sum = float(eps["funding_pnl"].sum())
    cost_sum = float(eps["cost_frac"].sum())
    net_r = eps["net_funding_r"].astype(float)

    print(f"episodes: {n}  (short-fades {len(side_short)}, long-fades {len(side_long)})")
    print(f"distinct coins: {eps['coin'].nunique()}")
    print(f"mean hold: {eps['hours'].mean():.1f}h   exit_reason: "
          f"{eps['exit_reason'].value_counts().to_dict()}")

    print("\n--- honest FUNDING component (funding collected - cost), net R ---")
    print(f"  funding collected (sum): {fp_sum:+,.0f} USD on {CAPITAL:,.0f} notional")
    print(f"  round-trip cost (sum):   {cost_sum:,.0f} USD (12 bps x N)")
    print(f"  mean net_funding_r: {net_r.mean():+.4f}   median: {net_r.median():+.4f}")
    print(f"  PF(funding-only): {_pf(net_r.tolist()):.4f}")
    print(f"  Sharpe(per-episode): {net_r.mean()/net_r.std() if net_r.std()>0 else 0:.3f}")
    print(f"  basis-proxy contribution: NOT folded in (reported separately = 0 here;")
    print(f"      the delta-neutral basis path is GATED off and no mark-oracle history")
    print(f"      exists to source it -> basis_source='none', flagged).")

    print("\n--- G0 cost screen (ADR-009, taker; maker fail-closed) ---")
    rtb = get_round_trip_bps("crypto")
    gross_needed = rtb * 4
    # median |funding| move over a 48h hold is the tradeable 'capture' proxy:
    # the honest figure is the funding collected vs the 45bps gross-capture bar.
    median_net_bps = float(net_r.median()) * RISK_UNIT_FRAC * 1e4  # R -> bps of capital
    print(f"  median funding-only capture {median_net_bps:+.2f} bps vs gross-needed ~{gross_needed:.0f} bps (4x {rtb}bps)")
    print(f"  -> funding-only carry is {('ABOVE' if median_net_bps >= gross_needed else 'BELOW')} the G0 cost bar")

    print("\n--- G1 (ADR-008 recalibrated) ---")
    from g1_gate import evaluate_g1, power_min_sample
    mu_r = float(net_r.mean()) if len(net_r) else None
    sigma_r = float(net_r.std()) if len(net_r) else None
    g1 = evaluate_g1(signal_count=n,
                     distinct_symbols=int(eps["coin"].nunique()),
                     mu_r=mu_r, sigma_r=sigma_r,
                     max_order_usd=CAPITAL,
                     top5_depth_usd_10bps=500_000.0)  # depth placeholder; not measured live
    print(f"  signal_count={n}  distinct_symbols={g1['distinct_symbols']}")
    print(f"  mu_R={mu_r:.4f} sigma_R={sigma_r:.4f}  N_min_power={g1['n_min_power']}")
    print(f"  breadth_ok={g1['breadth_ok']}  power_ok={g1['power_ok']}")
    print(f"  reasons={g1['reasons']}")

    # ── write trial ──────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "funding_unwind_swing",
        "entry_high_pct": PCTILE_ENTRY_HIGH, "exit_high_pct": PCTILE_EXIT_HIGH,
        "entry_low_pct": PCTILE_ENTRY_LOW, "exit_low_pct": PCTILE_EXIT_LOW,
        "pctile_window_hours": PCTILE_WINDOW_HOURS, "max_hold_hours": MAX_HOLD_HOURS,
        "notional_mode": "1x_capital", "cost": "fee_source_round_trip",
    }, sort_keys=True).encode()).hexdigest()
    universe_str = ",".join(sorted(eps["coin"].unique()))
    universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()
    result = {
        "avg_r": round(float(net_r.mean()), 6),
        "max_r": round(float(net_r.max()), 6),
        "min_r": round(float(net_r.min()), 6),
        "pf": round(_pf(net_r.tolist()), 6),
        "sharpe": round(float(net_r.mean() / net_r.std()), 6) if net_r.std() > 0 else 0.0,
        "trade_count": n,
        "win_rate": round(float((net_r > 0).mean()), 6),
        "r_outliers_skipped": 0,
        "construction": "funding_only_carry",
        "funding_collected_sum": round(fp_sum, 2),
        "cost_sum": round(cost_sum, 2),
        "distinct_symbols": int(eps["coin"].nunique()),
        "basis_pnl_folded_in": False,
        "basis_source": "none",
        "oi_delta_gated": True,
        "okx_spread_gated": True,
        "directional_component_gated": True,
        "g1_breadth_ok": g1["breadth_ok"],
        "g1_power_ok": g1["power_ok"],
        "n_min_power": g1["n_min_power"],
    }
    period_start = "2025-09-27"
    period_end = "2026-11-02"
    if not args.no_write:
        e = ledger.increment_trial("HYP-15", param_hash, universe_hash,
                                   period_start, period_end, result)
        print(f"\nwrote trial HYP-15  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())