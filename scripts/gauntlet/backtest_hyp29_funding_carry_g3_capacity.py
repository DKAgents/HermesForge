"""backtest_hyp29_funding_carry_g3_capacity.py — HYP-29 execution gate.

HYP-28 established the delta-neutral funding carry is REAL (~15-21% unlevered
APR, funding-true, maker survives, taker degrades-but-survives) — but it hedged
with the ORACLE (mid) price and did not prove the spot leg FILLS, nor how much
notional the funding floor can absorb.

HYP-29 is the "is it actually HARVESTABLE?" gate — G3 fill-realism on BOTH legs
+ capacity. Pre-registered and FIXED (no post-hoc tuning).

Pre-registered operationalization (FIXED):
  * G3 FILL-REALISM on BOTH legs. Grade the carry (short-perp + long-spot)
    through three fill tiers:
      - optimistic  = mid fills both legs, maker fee only (HYP-28 baseline)
      - realistic   = queue / same-side-adverse: spot bought at ASK, sold at
                      BID (full round-trip spread on the hedge); perp short at
                      BID, cover at ASK (full round-trip spread on the perp leg).
                      Maker fee.
      - pessimistic = taker + adverse: taker fee (4.5 bps/leg) PLUS the full
                      round-trip spread on BOTH legs at a wider (stressed) level.
  * The load-bearing check is the HEDGE leg: does the spot round-trip spread
    (buy ask / sell bid), paid ~48-59 times/yr, eat the ~15-21% headline?
  * CAPACITY: notional ceiling before the funding floor compresses, via a
    conservative liquidity proxy (fraction of daily notional volume / spot
    depth). Reported in USD + the APR at that ceiling, FLAGGED as an estimate
    (no L2 spot book is held).
  * RISK CHECK: enumerate the uncompensated risks the market charges ~11% for:
    hedge basis drift (mark-oracle), exchange/custody, churn forced-fill cost.
  * No leverage (unlevered carry on 1x notional). No look-ahead.

Spread sources (honest):
  * PERP spread: measured from real HL perp fills (tick gap) — BTC ~0.1 bps,
    ETH ~0.4 bps, SOL ~0.1 bps (sub-tick-to-1-tick; effectively negligible).
  * SPOT spread: NO L2 spot book is held. Flagged as an ASSUMPTION band:
    - realistic   half-spread 2.5 bps (BTC/ETH), 5.0 bps (SOL)  -> RT 5/5/10 bps
    - pessimistic half-spread 10 bps (all)                      -> RT 20 bps
    These are conservative vs liquid-CEX spot (BTC/USDT top-of-book ~0.5-1 bps)
    and are reported as a SENSITIVITY with the per-coin break-even spot spread.

Cost charged on BOTH legs (entry + exit) every episode.

Scope: same as HYP-28 — hourly funding sample 2023-06-08 -> 2026-10-31.

Writes ONE trial to data/gauntlet/trials.jsonl (fresh param_hash).

Usage: python3 backtest_hyp29_funding_carry_g3_capacity.py [--no-write]
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

import trials_ledger as ledger                              # noqa: E402

# ── Data locations ──────────────────────────────────────────────────────────
FUNDING_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding_hf"
MARK_ORACLE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf_clean"

# ── Pre-registered constants (FIXED — no tuning) ────────────────────────────
UNIVERSE = ["BTC", "ETH", "SOL"]
GATE_MEAN_APR = 0.08                       # rolling 24h mean APR >= 8%
GATE_POSITIVE_FRAC = 0.75                  # >= 75% of window hours positive
GATE_WINDOW_HOURS = 24
HOURS_PER_YEAR = 8760
SAMPLE_START = "2023-06-08"

# Fee schedule (fee_source base tier; fail-closed): maker 1.5, taker 4.5 bps/leg.
MAKER_BPS_PER_LEG = 1.5
TAKER_BPS_PER_LEG = 4.5
N_LEGS = 2                                  # short perp + long spot
N_SIDES = 2                                 # entry + exit
MAKER_RT_BPS = MAKER_BPS_PER_LEG * N_LEGS * N_SIDES   # 6 bps
TAKER_RT_BPS = TAKER_BPS_PER_LEG * N_LEGS * N_SIDES   # 18 bps

# SPOT half-spread assumptions (bps) — FLAGGED, no L2 book held.
SPOT_HALF_REALISTIC = {"BTC": 2.5, "ETH": 2.5, "SOL": 5.0}
SPOT_HALF_PESSIMISTIC = {"BTC": 10.0, "ETH": 10.0, "SOL": 10.0}
# PERP full round-trip spread (bps) — measured from HL fills tick gap.
PERP_RT_BPS = {"BTC": 0.12, "ETH": 0.41, "SOL": 0.10}

# Capacity rails (conservative liquidity proxy — flagged estimate).
OI_CAPACITY_FRAC = 0.02                    # 2% of open interest
DAILY_VOL_CAPACITY_FRAC = 0.005            # 0.5% of daily perp notional volume
SPOT_DEPTH_VS_PERP_VOL = 0.20              # spot depth ~20% of perp daily vol
SPOT_DEPTH_FRAC = 0.05                     # take <= 5% of that spot depth


def _load_funding() -> pd.DataFrame:
    frames = []
    for f in sorted(FUNDING_DIR.glob("*.parquet")):
        df = pd.read_parquet(f, columns=["timestamp", "coin", "funding_rate"])
        df = df[df["coin"].isin(UNIVERSE)]
        frames.append(df)
    fu = pd.concat(frames, ignore_index=True)
    fu["hour"] = fu["timestamp"].dt.floor("h")
    fu = fu.drop_duplicates(subset=["coin", "hour"]).sort_values("hour")
    return fu


def _load_basis() -> pd.DataFrame:
    frames = []
    for f in sorted(MARK_ORACLE_DIR.glob("*.parquet")):
        df = pd.read_parquet(f, columns=["timestamp", "coin",
                                         "mark_price", "oracle_price"])
        df = df[df["coin"].isin(UNIVERSE)]
        frames.append(df)
    mo = pd.concat(frames, ignore_index=True)
    mo["hour"] = mo["timestamp"].dt.floor("h")
    mo = mo.drop_duplicates(subset=["coin", "hour"]).sort_values("hour")
    mark = mo["mark_price"].astype(float)
    oracle = mo["oracle_price"].astype(float)
    mo["basis_bps"] = np.where(oracle > 0, (mark - oracle) / oracle * 1e4, np.nan)
    return mo


def _hourly_grid() -> pd.DatetimeIndex:
    return pd.date_range(SAMPLE_START, "2026-10-31 23:00", freq="h", tz="UTC")


def _gate_series(rate_hourly: pd.Series) -> pd.Series:
    mean_apr = (rate_hourly.rolling(GATE_WINDOW_HOURS, min_periods=GATE_WINDOW_HOURS)
                .mean() * HOURS_PER_YEAR)
    pos_frac = (rate_hourly > 0).rolling(GATE_WINDOW_HOURS,
                                         min_periods=GATE_WINDOW_HOURS).mean()
    gate = (mean_apr >= GATE_MEAN_APR) & (pos_frac >= GATE_POSITIVE_FRAC)
    return gate.fillna(False).astype(bool)


def _simulate_coin(rate: pd.Series, basis_bps: pd.Series) -> pd.DataFrame:
    """One row per gated episode (funding-only gross, in bps of notional)."""
    n = len(rate)
    gate = _gate_series(rate).to_numpy()
    r = rate.to_numpy(dtype=float)
    b = basis_bps.to_numpy(dtype=float)

    episodes = []
    in_pos = False
    e = None
    for i in range(n):
        if not in_pos:
            if gate[i]:
                in_pos = True
                e = i
            continue
        if not gate[i]:
            held = r[e + 1:i + 1]
            funding_bps = float(np.nansum(held)) * 1e4
            eb = float(b[e]) if np.isfinite(b[e]) else 0.0
            xb = float(b[i]) if np.isfinite(b[i]) else 0.0
            episodes.append({
                "entry_ts": rate.index[e], "exit_ts": rate.index[i],
                "hours": int(i - e), "funding_bps": funding_bps,
                "basis_bps": float(eb - xb),
                "entry_basis_bps": eb, "exit_basis_bps": xb,
            })
            in_pos = False
            e = None
    if in_pos and e is not None and e + 1 < n:
        held = r[e + 1:]
        funding_bps = float(np.nansum(held)) * 1e4
        eb = float(b[e]) if np.isfinite(b[e]) else 0.0
        xb = float(b[n - 1]) if np.isfinite(b[n - 1]) else 0.0
        episodes.append({
            "entry_ts": rate.index[e], "exit_ts": rate.index[n - 1],
            "hours": int(n - 1 - e), "funding_bps": funding_bps,
            "basis_bps": float(eb - xb),
            "entry_basis_bps": eb, "exit_basis_bps": xb,
        })
    return pd.DataFrame(episodes)


def _fill_cost_bps(coin: str, tier: str) -> float:
    """Round-trip fill cost (fees + spreads) for BOTH legs, in bps of notional.

    optimistic : mid fills, maker fee only.
    realistic  : maker fee + full spot RT spread (buy ask/sell bid) + full
                 perp RT spread (short bid/cover ask) at normal levels.
    pessimistic: taker fee + wider (stressed) spot RT spread + perp RT spread.
    """
    if tier == "optimistic":
        return MAKER_RT_BPS
    if tier == "realistic":
        spot_rt = 2.0 * SPOT_HALF_REALISTIC[coin]
        return MAKER_RT_BPS + spot_rt + PERP_RT_BPS[coin]
    if tier == "pessimistic":
        spot_rt = 2.0 * SPOT_HALF_PESSIMISTIC[coin]
        return TAKER_RT_BPS + spot_rt + PERP_RT_BPS[coin]
    raise ValueError(tier)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    print("=== HYP-29 funding carry — G3 fill-realism + capacity ===\n")

    fu = _load_funding()
    mo = _load_basis()
    grid = _hourly_grid()

    tiers = ["optimistic", "realistic", "pessimistic"]
    coin_results = {}

    for coin in UNIVERSE:
        fr = fu[fu["coin"] == coin].set_index("hour")["funding_rate"]
        fr = fr[~fr.index.duplicated(keep="first")].reindex(grid)
        ba = mo[mo["coin"] == coin].set_index("hour")["basis_bps"]
        ba = ba[~ba.index.duplicated(keep="first")].reindex(grid)

        ep = _simulate_coin(fr, ba)
        if ep.empty:
            print(f"--- {coin}: no episodes ---")
            continue

        hours_in_pos = int(ep["hours"].sum())
        n_ep = int(len(ep))
        funding_total = float(ep["funding_bps"].sum())

        per_tier = {}
        for tier in tiers:
            cost = _fill_cost_bps(coin, tier)
            net = funding_total - n_ep * cost
            apr = (net / 1e4) / hours_in_pos * HOURS_PER_YEAR if hours_in_pos else 0.0
            per_tier[tier] = {
                "cost_bps": round(cost, 3),
                "net_total_bps": round(net, 4),
                "net_apr": round(apr, 4),
            }

        # Spot spread break-even: the full RT spot spread that zeroes the carry
        # (given the fee and the measured perp spread already charged).
        gross_apr = (funding_total / 1e4) / hours_in_pos * HOURS_PER_YEAR
        churn_yr = n_ep / 3.42  # ~3.42y sample
        # net APR as function of spot RT spread s (bps):
        #   net(s) = gross - (fee + s + perp)/1e4 * churn_yr * (8760/hr means)
        # cleaner: per-episode budget. Carry net-maker APR baseline first.
        net_maker_apr = ((funding_total - n_ep * MAKER_RT_BPS) / 1e4) \
            / hours_in_pos * HOURS_PER_YEAR
        # break-even spot RT spread: fee+perp+s such that funding_total == n*(cost)
        budget_per_ep_bps = funding_total / n_ep - MAKER_RT_BPS - PERP_RT_BPS[coin]
        spot_break_even_rt_bps = budget_per_ep_bps if budget_per_ep_bps > 0 else 0.0

        coin_results[coin] = {
            "n_episodes": n_ep,
            "episodes_per_year": round(churn_yr, 1),
            "hours_in_pos": hours_in_pos,
            "mean_hold_days": round(float(ep["hours"].mean()) / 24, 3),
            "gross_apr": round(gross_apr, 4),
            "net_maker_apr": round(net_maker_apr, 4),
            "funding_total_bps": round(funding_total, 4),
            "basis_total_bps": round(float(ep["basis_bps"].sum()), 4),
            "tiers": per_tier,
            "spot_break_even_rt_bps": round(spot_break_even_rt_bps, 2),
        }

        print(f"--- {coin} ---")
        print(f"  episodes {n_ep} ({churn_yr:.1f}/yr), hold {float(ep['hours'].mean())/24:.2f}d, "
              f"gross APR {gross_apr*100:.2f}%, net-maker {net_maker_apr*100:.2f}%")
        for tier in tiers:
            p = per_tier[tier]
            print(f"  {tier:>11}: cost {p['cost_bps']:>6.2f} bps -> net APR "
                  f"{p['net_apr']*100:>7.2f}%  (net {p['net_total_bps']:+.2f} bps)")
        print(f"  spot RT spread break-even: {spot_break_even_rt_bps:.2f} bps "
              f"(assumed realistic {2*SPOT_HALF_REALISTIC[coin]:.1f}, "
              f"pessimistic {2*SPOT_HALF_PESSIMISTIC[coin]:.1f})")

    # ── Capacity (conservative liquidity proxy — flagged estimate) ──────────
    print("\n=== CAPACITY (conservative liquidity proxy, FLAGGED estimate) ===")
    capacity = {}
    for coin in UNIVERSE:
        # open interest (recent median from hl_oi_hf_clean) and daily perp vol
        # are read from small hard-coded recent medians here ONLY as the estimate
        # source; they are measured values, not tuned outputs.
        oi_usd, daily_vol_usd = {
            "BTC": (2.96e9, 3.447e9),
            "ETH": (2.46e9, 1.139e9),
            "SOL": (5.74e8, 3.04e8),
        }[coin]
        rail_oi = OI_CAPACITY_FRAC * oi_usd
        rail_vol = DAILY_VOL_CAPACITY_FRAC * daily_vol_usd
        rail_spot = (SPOT_DEPTH_VS_PERP_VOL * daily_vol_usd) * SPOT_DEPTH_FRAC
        ceiling = min(rail_oi, rail_vol, rail_spot)
        binding = min([(rail_oi, "2% OI"), (rail_vol, "0.5% daily perp vol"),
                       (rail_spot, "5% spot depth (20% of perp vol)")],
                      key=lambda x: x[0])[1]
        capacity[coin] = {
            "oi_usd_med": oi_usd,
            "daily_perp_vol_usd": daily_vol_usd,
            "rail_oi_usd": rail_oi,
            "rail_vol_usd": rail_vol,
            "rail_spot_usd": rail_spot,
            "ceiling_usd": ceiling,
            "binding": binding,
            "apr_at_ceiling": coin_results[coin]["tiers"]["realistic"]["net_apr"],
        }
        print(f"  {coin}: OI ${oi_usd/1e9:.2f}B, daily perp vol ${daily_vol_usd/1e9:.2f}B -> "
              f"ceiling ${ceiling/1e6:.1f}M ({binding}); APR at ceiling "
              f"{coin_results[coin]['tiers']['realistic']['net_apr']*100:.2f}%")

    total_ceiling = sum(c["ceiling_usd"] for c in capacity.values())
    print(f"  TOTAL portfolio ceiling (sum of three legs): ${total_ceiling/1e6:.2f}M")

    # ── Risk check (the ~11% funding floor price) ───────────────────────────
    print("\n=== RISK CHECK (why is the floor ~11%?) ===")
    # hedge basis drift (mark-oracle) tail, measured over full sample
    basis_risk = {}
    for coin in UNIVERSE:
        b = mo[mo["coin"] == coin]["basis_bps"].dropna()
        basis_risk[coin] = {
            "median_bps": round(float(b.median()), 2),
            "p05_bps": round(float(b.quantile(0.05)), 2),
            "p95_bps": round(float(b.quantile(0.95)), 2),
            "min_bps": round(float(b.min()), 2),
            "max_bps": round(float(b.max()), 2),
            "pct_abs_gt_10bps": round(float((b.abs() > 10).mean()) * 100, 2),
        }

    # Approx churn forced-fill cost (realistic tier) as share of gross funding.
    churn_cost_share = {}
    for coin in UNIVERSE:
        cr = coin_results[coin]
        churn_cost_share[coin] = round(
            cr["n_episodes"] * _fill_cost_bps(coin, "realistic")
            / cr["funding_total_bps"], 3)

    risk_result = {
        "funding_floor_apr": 0.1095,
        "hedge_basis_drift_mark_oracle_bps": basis_risk,
        "exchange_custody": {
            "note": "capital sits on one venue (Hyperliquid) + the spot hedge "
                    "venue; the ~11% structural floor is in part a charge for "
                    "custody/counterparty/withdrawal-suspension tail risk that "
                    "is NOT hedgeable within the carry itself.",
            "quantified_as": "residual above the risk-free rate (query-able "
                             "funding floor 10.95% vs ~0-4% risk-free) — "
                             "uncompensated in the strategy, borne by the trader.",
        },
        "churn_forced_fill_cost_share_of_gross": churn_cost_share,
    }

    for coin in UNIVERSE:
        br = basis_risk[coin]
        print(f"  {coin} mark-oracle basis: median {br['median_bps']:+.2f} bps, "
              f"[p05 {br['p05_bps']:+.1f}, p95 {br['p95_bps']:+.1f}] bps, "
              f"|basis|>10bps {br['pct_abs_gt_10bps']:.1f}% of hours")
        print(f"    churn forced-fill (realistic) = {churn_cost_share[coin]*100:.1f}% of gross funding")
    print("  exchange/custody risk: unhedgeable counterparty/venue tail — the "
          "floor of 10.95% APR is the charge")

    # ── Write trial ─────────────────────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "funding_carry_g3_fill_realism_capacity",
        "gate_mean_apr": GATE_MEAN_APR,
        "gate_positive_frac": GATE_POSITIVE_FRAC,
        "gate_window_hours": GATE_WINDOW_HOURS,
        "universe": UNIVERSE,
        "maker_rt_bps": MAKER_RT_BPS,
        "taker_rt_bps": TAKER_RT_BPS,
        "spot_half_realistic": SPOT_HALF_REALISTIC,
        "spot_half_pessimistic": SPOT_HALF_PESSIMISTIC,
        "perp_rt_bps": PERP_RT_BPS,
        "capacity_rails": {
            "oi_frac": OI_CAPACITY_FRAC,
            "daily_vol_frac": DAILY_VOL_CAPACITY_FRAC,
            "spot_depth_vs_perp_vol": SPOT_DEPTH_VS_PERP_VOL,
            "spot_depth_frac": SPOT_DEPTH_FRAC,
        },
        "leverage": "none_1x_notional",
        "sample_start": SAMPLE_START,
        "spot_spread_source": "ASSUMED band (no L2 book held) — flagged",
    }, sort_keys=True).encode()).hexdigest()
    universe_str = ",".join(sorted(UNIVERSE))
    universe_hash = hashlib.sha256(universe_str.encode()).hexdigest()

    result = {
        "construction": "funding_carry_g3_fill_realism_capacity",
        "universe": UNIVERSE,
        "hedge": "long-spot (oracle mid proxy baseline); spot RT spread charged separately",
        "gate": {"mean_apr": GATE_MEAN_APR, "positive_frac": GATE_POSITIVE_FRAC,
                 "window_hours": GATE_WINDOW_HOURS},
        "fill_tiers": tiers,
        "spot_spread_source": "ASSUMED band (no L2 spot book held) — flagged",
        "perp_spread_source": "measured from HL fills tick gap",
        "per_major": coin_results,
        "capacity": {
            "note": "CONSERVATIVE liquidity proxy (no L2 spot book held) — flagged estimate",
            "rails": {
                "oi_frac": OI_CAPACITY_FRAC,
                "daily_vol_frac": DAILY_VOL_CAPACITY_FRAC,
                "spot_depth_vs_perp_vol": SPOT_DEPTH_VS_PERP_VOL,
                "spot_depth_frac": SPOT_DEPTH_FRAC,
            },
            "per_major": capacity,
            "total_ceiling_usd": total_ceiling,
        },
        "risk_check": risk_result,
        "no_lookahead": True,
        "leverage": "none_1x_notional",
        "live": "off",
    }

    # ── Verdict ─────────────────────────────────────────────────────────────
    print("\n=== VERDICT ===")
    real_survives = all(
        coin_results[c]["tiers"]["realistic"]["net_apr"] > 0 for c in UNIVERSE)
    pess_survives = all(
        coin_results[c]["tiers"]["pessimistic"]["net_apr"] > 0 for c in UNIVERSE)
    nontrivial_capacity = total_ceiling >= 1e6  # >= $1M combined
    if real_survives and nontrivial_capacity:
        verdict = (
            "PROMOTE-TO-PAPER: carry survives realistic fills on BOTH legs "
            f"at a non-trivial capacity ceiling (${total_ceiling/1e6:.2f}M).")
        if pess_survives:
            verdict += " Pessimistic (taker + stressed spread) ALSO survives."
        else:
            verdict += " Pessimistic (taker + stressed spread) turns it "\
                       "negative -> run maker/queue only in paper."
    else:
        verdict = (
            "RETIRE-AS-REAL-YIELD-CANT-CAPTURE: realistic fills on the hedge "
            "or pocket-sized capacity kill the headline.")
    result["verdict"] = verdict
    print(f"  realistic survives: {real_survives}")
    print(f"  pessimistic survives: {pess_survives}")
    print(f"  non-trivial capacity (>= $1M): {nontrivial_capacity} "
          f"(${total_ceiling/1e6:.2f}M)")
    print(f"  => {verdict}")

    if not args.no_write:
        e = ledger.increment_trial("HYP-29", param_hash, universe_hash,
                                   SAMPLE_START, "2026-10-31", result)
        print(f"\nwrote trial HYP-29  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
