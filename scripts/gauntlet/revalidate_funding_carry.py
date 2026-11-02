"""revalidate_funding_carry.py — HermesForge US-185 re-validation driver.

Runs the reconstituted funding-carry strategy on REAL data and prints four
REAL sections (spec §5.3 item 6 + the VERIFY requirement):

  A. Full-universe dispatch     — live 235-coin metaAndAssetCtxs: how each non-
                                  delisted perp routes (directional_short /
                                  directional_long / skip) from its CURRENT
                                  funding sign.
  B. Directional gate + λ       — for the CRYPTO_UNIVERSE coins with real mark
                                  history, realized σ (5m-bar closes) × current
                                  funding → directional_risk_gate eligibility
                                  and the λ ∈ {0.25,0.5,1.0} sensitivity table.
  C. Directional hard-stop backtest — simulate_carry over the real 17-day mark
                                  window (5m bars) + deep funding history:
                                  episodes, exit reasons, directional loss-vs-
                                  funding ratio, g3_gate (carry_g3_record).
  D. Real-basis kill-stop       — REAL assetCtxs mark/oracle basis vs the
                                  compressed fundingHistory premium; proves the
                                  basis_widen kill-stop is re-sourced (§2.2).

Import direction (driver): funding_carry -> {hl_funding_store, hl_assetctx_store,
hl_bar_store, fee_source, g3_gate}. Read-only — writes NOTHING to any store.

Usage:
    python3 revalidate_funding_carry.py [--coins BTC ETH] [--no-live]
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

_THIS_DIR = pathlib.Path(__file__).resolve().parent          # scripts/gauntlet
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
_DATA_DIR = _THIS_DIR.parent / "data"                        # scripts/data
if str(_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(_DATA_DIR))
_SCRIPTS_DIR = _THIS_DIR.parent                                # scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import funding_carry as fc            # noqa: E402
import hl_funding_store                # noqa: E402
import hl_assetctx_store               # noqa: E402
import hl_bar_store                    # noqa: E402
from hermes_config.universe import CRYPTO_UNIVERSE  # noqa: E402


def hourly_mark_closes(coin: str) -> pd.DataFrame | None:
    """Real mark-price proxy: 5m bar closes resampled to hourly closes.
    Returns DataFrame[time(ms), mark_px]; None if the coin has no bars."""
    try:
        bars = hl_bar_store.read_bars(coin, "5m")
    except Exception:
        return None
    if bars is None or bars.empty:
        return None
    df = bars.copy()
    df["dt"] = pd.to_datetime(df["ts"], unit="ms")
    s = df.set_index("dt")["close"].resample("1h").last().dropna()
    if s.empty:
        return None
    # Explicit ms resolution (pandas 3.x defaults to datetime64[us], so a bare
    # .astype("int64") yields MICROseconds — always cast to [ms] first).
    times_ms = s.index.astype("datetime64[ms]").astype("int64").to_numpy()
    return pd.DataFrame({"time": times_ms, "mark_px": s.to_numpy(dtype=float)})


def mark_only_basis_real(mark: pd.DataFrame) -> pd.DataFrame:
    """Wrap hourly mark closes as the basis_real frame simulate_carry expects
    (mark_px present, basis_bps NaN -> basis kill disabled, directional active)."""
    return pd.DataFrame({"time": mark["time"], "mark_px": mark["mark_px"],
                         "oracle_px": np.nan, "basis_bps": np.nan})


def section_a(universe_ctxs: list[dict]):
    """Full-universe dispatch from CURRENT funding signs."""
    print("\n=== A. Full-universe execution-form dispatch (live library) ===")
    counts = {"directional_short": 0, "directional_long": 0, "skip": 0}
    for r in universe_ctxs:
        funding = r.get("funding")
        if funding is None:
            form = "skip"
        else:
            form = fc.dispatch_execution_form(float(funding))
        counts[form] = counts.get(form, 0) + 1
    total = sum(counts.values())
    print(f"non-delisted perps: {total}")
    for form, n in sorted(counts.items()):
        print(f"  {form:18s} {n:4d}  ({100 * n / total:.1f}%)")
    print("  (delta_neutral is GATED OFF by default -> funding>0 routes to "
          "directional_short)")


def section_b(coins: list[str]):
    """Directional gate + lambda sensitivity on real funding + realized vol."""
    print("\n=== B. Directional funding gate on REAL data (lambda x realized vol) ===")
    print(f"{'coin':8s} {'sigma':>7s} {'fundAPR':>8s} "
          f"{'hurdle(0.5)':>11s} {'eligible':>9s}")
    rows = []
    for coin in coins:
        funding = hl_funding_store.read_funding(coin)
        if funding is None or funding.empty:
            continue
        mark = hourly_mark_closes(coin)
        if mark is None:
            continue
        sig = fc.funding_window_signal(funding)
        mean_apr = sig["mean_mag_apr"]
        vol = fc.realized_annualized_vol(pd.Series(mark["mark_px"]))
        gate = fc.directional_risk_gate(mean_apr, vol)
        rows.append({"coin": coin, "sigma": vol, "fund_apr": mean_apr,
                     "hurdle": gate["hurdle_apr"], "eligible": gate["eligible"]})
        print(f"{coin:8s} {vol:7.3f} {mean_apr:8.4f} "
              f"{gate['hurdle_apr']:11.4f} {str(gate['eligible']):>9s}")

    print("\nLambda sensitivity table (eligible count over the same sample):")
    print(f"{'lambda':>8s} {'eligible':>9s} {'of'}")
    for lam in (0.25, 0.5, 1.0):
        n_el = 0
        for r in rows:
            hurdle = max(fc.FUNDING_SUSTAIN_FLOOR_APR, lam * r["sigma"])
            if r["fund_apr"] >= hurdle:
                n_el += 1
        print(f"{lam:8.2f} {n_el:9d} {len(rows)}")
    print("  (DIRECTIONAL_STOP_BPS=200 hard-stop sizes notional to "
          f"0.5x capital at {fc.DIRECTIONAL_STOP_BPS}bp stop -> risk_usd == 1% "
          "capital, exact 1R.)")


def section_c(coins: list[str]):
    """Directional hard-stop backtest over the real mark window + λ sensitivity."""
    print("\n=== C. Directional short/long backtest (real 17-day mark window) ===")
    # Pre-load funding + mark windows (mark bounds the directional stop).
    loaded = []
    for coin in coins:
        mark = hourly_mark_closes(coin)
        if mark is None:
            continue
        start_ts = int(mark["time"].min()) - 2 * 24 * 3600 * 1000
        funding = hl_funding_store.read_funding(coin, start_ts=start_ts)
        if funding is None or funding.empty:
            continue
        funding.attrs["coin"] = coin
        loaded.append((coin, funding, mark_only_basis_real(mark)))

    if not loaded:
        print("  No mark history available (no historical markPx yet; accumulates "
              "going forward — F3).")
        return

    print(f"{'lambda':>8s} {'episodes':>9s} {'fund_pnl':>10s} {'dir_pnl':>10s} "
          f"{'loss/fund':>10s} {'G3_realR':>9s} {'passed':>7s}")
    for lam in (0.25, 0.5, 1.0):
        all_eps = []
        for _, funding, basis_real in loaded:
            eps = fc.simulate_carry(funding, basis_real=basis_real,
                                    params={"capital": 1_000_000.0,
                                            "directional_lambda": lam})
            if eps is not None and not eps.empty:
                all_eps.append(eps)
        if not all_eps:
            print(f"{lam:8.2f} {0:9d} (no episodes)")
            continue
        combo = pd.concat(all_eps, ignore_index=True)
        n = len(combo)
        funding_sum = float(combo["funding_pnl"].sum())
        direction_loss = float(
            combo.loc[combo["direction_pnl"] < 0, "direction_pnl"].sum())
        ratio = abs(direction_loss) / funding_sum if funding_sum > 0 else float("nan")
        g3 = fc.carry_g3_record(combo)
        print(f"{lam:8.2f} {n:9d} {funding_sum:+10.1f} "
              f"{float(combo['direction_pnl'].sum()):+10.1f} {ratio:10.4f} "
              f"{g3['realistic_mean_r']:9.4f} {str(g3['passed']):>7s}")

    # Detail the λ=0.5 (default) episodes.
    print("\n  λ=0.5 exit reasons + forms:")
    all_eps = []
    for _, funding, basis_real in loaded:
        eps = fc.simulate_carry(funding, basis_real=basis_real,
                                params={"capital": 1_000_000.0})
        if eps is not None and not eps.empty:
            all_eps.append(eps)
    if all_eps:
        combo = pd.concat(all_eps, ignore_index=True)
        print(f"    exit reasons: {combo['exit_reason'].value_counts().to_dict()}")
        print(f"    forms: {combo['execution_form'].value_counts().to_dict()}")
        stopped = combo[combo["exit_reason"] == "directional_stop"]
        if not stopped.empty:
            print(f"    hard-stop episodes (-1R each, risk_usd=1% capital): "
                  f"{len(stopped)} -> direction_pnl "
                  f"{stopped['direction_pnl'].sum():+.2f}")


def section_d():
    """Real mark-oracle basis vs the compressed fundingHistory premium."""
    print("\n=== D. Real-basis kill-stop re-source (assetCtxs mark/oracle vs premium) ===")
    for coin in ("BTC", "ETH", "SOL"):
        basis = hl_assetctx_store.read_basis(coin)
        funding = hl_funding_store.read_funding(coin)
        if basis.empty or funding is None or funding.empty:
            print(f"  {coin}: no real basis/funding yet")
            continue
        real_basis = float(basis["basis_bps"].iloc[-1])
        mark = float(basis["mark_px"].iloc[-1])
        oracle = float(basis["oracle_px"].iloc[-1])
        if np.isfinite(real_basis):
            basis_via_helper = fc.basis_widen(mark, oracle)
            prem = float(funding["premium"].iloc[-1])
            print(f"  {coin}: mark={mark:.2f} oracle={oracle:.2f} "
                  f"real_basis={real_basis:+.2f}bp (basis_widen={basis_via_helper:+.2f}bp) "
                  f"vs fundingPremium={prem * 1e4:+.2f}bp")
        else:
            print(f"  {coin}: mark/oracle present but basis not computable (oracle missing)")
    print("  The basis_widen kill-stop now reads mark_px/oracle_px (the REAL "
          "mark-oracle spread), NOT the compressed premium. When basis_real is "
          "unavailable the kill is DISABLED (fallback never reverts to premium).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", nargs="*", default=None)
    ap.add_argument("--no-live", action="store_true",
                    help="skip the live universe probe (sections A)")
    args = ap.parse_args()
    coins = args.coins if args.coins else list(CRYPTO_UNIVERSE)

    section_d()

    if not args.no_live:
        try:
            from ingest_hl_assetctx import fetch_assetctxs, parse_snapshot
            meta, ctxs = fetch_assetctxs()
            rows = parse_snapshot(meta, ctxs)
            # parse_snapshot skips delisted; each row carries the live funding
            # sign for dispatch.
            section_a(rows)
        except Exception as e:
            print(f"  [live universe probe skipped: {e}]")

    section_b(coins)
    section_c(coins)
    return 0


if __name__ == "__main__":
    sys.exit(main())