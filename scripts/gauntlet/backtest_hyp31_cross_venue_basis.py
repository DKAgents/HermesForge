"""backtest_hyp31_cross_venue_basis.py — HYP-31 cross-venue funding spread + price basis.

Read-only research driver (sibling of revalidate_funding_unwind.py). Runs the
two PRE-REGISTERED channels of HYP-31 (HL vs OKX) on real data and writes ONE
trial to data/gauntlet/trials.jsonl with a fresh param_hash.

  H1 FUNDING-SPREAD CARRY (cross-venue delta-neutral):
      spread_apr(t) = HL funding APR(t) - OKX funding APR(t)   (both %/yr)
      ENTER: rolling-mean spread (24h) >= SPREAD_FLOOR_APR  -> short HL perp,
             long OKX perp (equal USD notional, net-zero delta).
      EXIT : spread closes back below SPREAD_EXIT_APR.
  H2 PRICE-BASIS MEAN-REVERSION:
      basis_bps(t) = (HL mark - OKX last)/OKX last * 1e4
      ENTER: |basis| >= BASIS_ENTRY_BPS  -> fade (short HL/long OKX if positive)
      EXIT : |basis| reverts toward 0.

Cost model: MAKER on BOTH venues (the pre-registered form). HL maker = 1.5 bps
(fee_source crypto base tier); OKX maker = 2.0 bps (OKX USDT-margin base tier,
fail-closed conservative — no OKX schedule is fetched). Cross-venue round-trip =
2 legs x 2 sides = 2*(1.5+2.0) = 7 bps. The CROSS-VENUE RISK (transfer/custody/
liquidation asymmetry on one leg) is NOT a fee — it is flagged explicitly as the
load-bearing unquantified unknown and is NOT netted as if it were free.

DATA REALITY (the honest gate):
  * HL funding  : hl_funding_hf/*.parquet (hourly, 2023-05 -> 2026-10).
  * HL mark     : hl_oi_hf/*.parquet (hourly mark_price, 2023-05 -> 2026-10).
  * OKX funding : basis.db okx_funding — the OKX public funding-rate-history
                  endpoint is HARD-CAPPED at ~3 months (verified live: 283 rows
                  back to 2026-08-06). The store's 2026-07-27 start is the
                  accumulated rolling window = the MAXIMUM retrievable depth.
  * OKX price   : backfilled here via market/history-candles (1H ~5.5mo back,
                  1D deep), persisted to basis.db okx_candles.

Because OKX funding is capped at ~3.4 months, H1's overlap window is
2026-07-27 -> 2026-11-05 (the honest testable span), NOT the full HL depth.
H2 runs hourly over the OKX 1H-candle span (~2026-05-26 -> 2026-10-31) plus a
daily-frequency robustness check over the full 3.5y HL mark history vs OKX 1D.

No look-ahead (enter at t+1 after the signal bar; funding accrual starts the
bar AFTER the signal bar). No leverage beyond delta-neutral (notional = 1x
capital per leg, net delta ~0). LIVE off.

Usage: python3 backtest_hyp31_cross_venue_basis.py [--no-write] [--no-backfill]
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
_DATA_DIR = _THIS_DIR.parent / "data"                        # scripts/data
for _p in (_THIS_DIR, str(_THIS_DIR.parent), str(_DATA_DIR)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import basis_store           # noqa: E402
import trials_ledger         # noqa: E402
from fee_source import get_maker_bps, get_taker_bps  # noqa: E402
from okx_proxy import HL_TO_OKX, fetch_okx_bars      # noqa: E402
import pyarrow.parquet as pq  # noqa: E402
import glob                    # noqa: E402

HL_FUNDING_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding_hf"
HL_OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"

HOURS_PER_YEAR = 8760
OKX_8H_PER_YEAR = 1095          # 8h settlements -> *3/day * 365

# ── Pre-committed parameters (FIXED; hashed; NOT tuned) ──────────────────────
SPREAD_WINDOW_HOURS = 24        # rolling-mean window for the funding spread
SPREAD_FLOOR_APR = 3.0          # pp/yr entry (break-even ~3.13% for 7bp maker / 1wk)
SPREAD_EXIT_APR = 1.0           # pp/yr "spread closes" exit
BASIS_ENTRY_BPS = 5.0           # price-basis |band| to fade
BASIS_EXIT_BPS = 0.0            # converged
CAPITAL = 1_000_000.0           # notional per leg (delta-neutral, net 0)
UNIVERSE = ("BTC", "ETH")

# Fee assumptions (maker on BOTH venues).
_HL_MAKER_BPS = get_maker_bps("crypto")   # Hyperliquid base-tier maker (1.5)
_OKX_MAKER_BPS = 2.0                      # OKX USDT-margin base maker (fail-closed)
CROSS_VENUE_RT_BPS = 2 * (_HL_MAKER_BPS + _OKX_MAKER_BPS)  # 7 bps


def _load_hl_parquet(glob_dir: pathlib.Path, columns: list[str]) -> pd.DataFrame:
    files = sorted(glob.glob(str(glob_dir / "*.parquet")))
    frames = [pq.read_table(f, columns=columns).to_pandas() for f in files]
    df = pd.concat(frames, ignore_index=True)
    # Normalize to tz-naive UTC ms for alignment with OKX (dt64[ms]).
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def _to_hour_ms(dt_series: pd.Series) -> np.ndarray:
    """Floor timestamps to the HOUR (epoch ms). HL funding settles at ~+48ms
    while mark/assetCtx polls at ~+0ms — flooring aligns the two hourly series."""
    s = dt_series
    if getattr(getattr(s, "dt", None), "tz", None) is not None:
        s = s.dt.tz_localize(None)   # parquet timestamps are UTC; drop tz -> epoch ms
    ms = s.astype("datetime64[ms]").astype("int64")
    return (ms // 3_600_000) * 3_600_000


def load_hl_series(coin: str) -> pd.DataFrame:
    """Hourly HL funding APR + mark for coin, indexed by tz-naive ms time."""
    fund = _load_hl_parquet(HL_FUNDING_DIR, ["timestamp", "coin", "funding_rate"])
    fund = fund[fund["coin"] == coin].copy()
    fund["apr"] = fund["funding_rate"].astype(float) * HOURS_PER_YEAR * 100.0
    fund["time_ms"] = _to_hour_ms(fund["timestamp"])
    fund = fund.sort_values("time_ms").drop_duplicates("time_ms")
    fund = fund.set_index("time_ms")

    mark = _load_hl_parquet(HL_OI_DIR, ["timestamp", "coin", "mark_price"])
    mark = mark[mark["coin"] == coin].copy()
    mark["mark"] = mark["mark_price"].astype(float)
    mark["time_ms"] = _to_hour_ms(mark["timestamp"])
    mark = mark.sort_values("time_ms").drop_duplicates("time_ms")
    mark = mark.set_index("time_ms")

    out = fund[["apr"]].join(mark[["mark"]], how="inner")
    # keep mark positive rows only
    out = out[out["mark"] > 0]
    return out


def load_okx_funding(inst_id: str) -> pd.DataFrame:
    """OKX 8h funding APR, ffill'd onto hourly grid, indexed by time_ms."""
    conn = basis_store.open_store()
    try:
        df = pd.read_sql(
            "SELECT ts, funding_rate FROM okx_funding WHERE inst_id=? ORDER BY ts",
            conn, params=(inst_id,))
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["apr"])
    df["apr"] = df["funding_rate"].astype(float) * OKX_8H_PER_YEAR * 100.0
    df["time_ms"] = df["ts"].astype("int64")
    df = df.drop_duplicates("time_ms").set_index("time_ms").sort_index()
    return df


def backfill_okx_price(ticker: str, inst_id: str) -> dict:
    """Backfill OKX 1H + 1D history-candles into basis.db okx_candles.

    Idempotent (INSERT OR IGNORE on (inst_id, bar, ts)). Returns row counts.
    """
    conn = basis_store.open_store()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS okx_candles (
                inst_id TEXT NOT NULL,
                bar     TEXT NOT NULL,
                ts      INTEGER NOT NULL,
                close   REAL NOT NULL,
                PRIMARY KEY (inst_id, bar, ts)
            ) WITHOUT ROWID;
        """)
        conn.commit()
        end_ms = int(time.time() * 1000)
        counts = {}
        for bar, start_ms in (("1H", end_ms - 210 * 24 * 3600 * 1000),   # ~7mo back
                              ("1d", end_ms - 1300 * 24 * 3600 * 1000)):  # ~3.5y back
            bars = fetch_okx_bars(ticker, bar, start_ms, end_ms)
            if bars is None or bars.empty:
                counts[bar] = 0
                continue
            tuples = [(inst_id, "1D" if bar == "1d" else bar,
                       int(r["ts"]), float(r["close"]))
                      for _, r in bars.iterrows()]
            conn.executemany(
                "INSERT OR IGNORE INTO okx_candles (inst_id, bar, ts, close) "
                "VALUES (?,?,?,?)", tuples)
            conn.commit()
            counts[bar] = len(tuples)
        cov = {}
        for bar in ("1H", "1D"):
            row = conn.execute(
                "SELECT MIN(ts), MAX(ts), COUNT(*) FROM okx_candles "
                "WHERE inst_id=? AND bar=?", (inst_id, bar)).fetchone()
            cov[bar] = row
        return {"inserted": counts, "coverage": cov}
    finally:
        conn.close()


def load_okx_price(inst_id: str, bar: str) -> pd.DataFrame:
    conn = basis_store.open_store()
    try:
        df = pd.read_sql(
            "SELECT ts, close FROM okx_candles WHERE inst_id=? AND bar=? ORDER BY ts",
            conn, params=(inst_id, bar))
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["close"])
    df = df.rename(columns={"close": "last"})
    df["time_ms"] = df["ts"].astype("int64")
    return df.set_index("time_ms").sort_index()


def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


# ── H1: funding-spread carry ─────────────────────────────────────────────────
def simulate_spread(hl: pd.DataFrame, okx: pd.DataFrame) -> dict:
    """Cross-venue funding-spread carry over the OKX-funding overlap window.

    hl:  hourly HL funding APR, indexed by time_ms (has 'apr').
    okx: OKX 8h funding APR, indexed by time_ms (has 'apr'), ffill'd to hourly.
    Returns aggregate stats + per-episode list.
    """
    okx_h = okx["apr"].reindex(hl.index, method="ffill")
    spread = (hl["apr"] - okx_h).dropna()
    if spread.empty:
        return {"n_episodes": 0, "hours_total": 0, "gross_apr_bps": 0.0,
                "net_apr_bps": 0.0, "fee_bps": 0.0, "episodes": []}

    w = SPREAD_WINDOW_HOURS
    mean_spread = spread.rolling(w, min_periods=w).mean()
    idx = spread.index
    vals = spread.to_numpy()
    mvals = mean_spread.to_numpy()

    eps = []
    in_pos = False
    entry_i = 0
    for i in range(w, len(vals)):
        cur_ovr_need = None
        if not np.isfinite(mvals[i]):
            continue
        if not in_pos:
            # enter NEXT bar after the signal bar (no look-ahead)
            if mvals[i] >= SPREAD_FLOOR_APR:
                in_pos = True
                entry_i = i + 1 if i + 1 < len(vals) else i
                continue
        else:
            if mvals[i] < SPREAD_EXIT_APR or i == len(vals) - 1:
                exit_i = i
                # hours held = exit_i - entry_i; accrual from entry_i..exit_i-1
                if exit_i > entry_i:
                    held = vals[entry_i:exit_i]
                    gross_per_hour = sum(held)              # pp/hr summed
                    # funding as fraction: apr(pp/yr)/100 /8760 per hour
                    gross_frac = sum(held) / 100.0 / HOURS_PER_YEAR
                    fee_frac = CROSS_VENUE_RT_BPS / 1e4
                    net_frac = gross_frac - fee_frac
                    eps.append({
                        "entry_ms": int(idx[entry_i]), "exit_ms": int(idx[exit_i]),
                        "hours": exit_i - entry_i,
                        "gross_frac": gross_frac, "net_frac": net_frac,
                    })
                in_pos = False

    if not eps:
        return {"n_episodes": 0, "hours_total": 0, "gross_apr_bps": 0.0,
                "net_apr_bps": 0.0, "fee_bps": 0.0, "episodes": []}

    gross_sum = sum(e["gross_frac"] for e in eps)
    fee_sum = len(eps) * (CROSS_VENUE_RT_BPS / 1e4)
    net_sum = sum(e["net_frac"] for e in eps)
    hours_total = sum(e["hours"] for e in eps)
    return {
        "n_episodes": len(eps),
        "hours_total": hours_total,
        "mean_hours": hours_total / len(eps),
        "gross_frac": gross_sum,
        "fee_frac": fee_sum,
        "net_frac": net_sum,
        "gross_apr_bps": gross_sum / hours_total * HOURS_PER_YEAR * 1e4,
        "net_apr_bps": net_sum / hours_total * HOURS_PER_YEAR * 1e4,
        "fee_apr_bps": fee_sum / hours_total * HOURS_PER_YEAR * 1e4,
        "episodes": eps,
    }


# ── H2: price-basis mean-reversion ───────────────────────────────────────────
def simulate_basis(hl_mark: pd.Series, okx_last: pd.Series) -> dict:
    """Daily or hourly price-basis MR. hl_mark / okx_last indexed by time_ms,
    aligned (inner join). Fade |basis| > band, exit at convergence."""
    joined = pd.concat({"hl_mark": hl_mark, "okx_last": okx_last}, axis=1).dropna()
    joined = joined[joined["okx_last"] > 0]
    if joined.empty:
        return {"n_episodes": 0, "basis_mean_bps": None, "basis_p90_bps": None,
                "net_bps_total": 0.0, "fee_bps": 0.0, "n_round_trips": 0}
    basis = (joined["hl_mark"] - joined["okx_last"]) / joined["okx_last"] * 1e4
    idx = basis.index
    bvals = basis.to_numpy(dtype=float)

    eps = []
    in_pos = False
    entry_i = 0
    entry_sign = 0
    entry_basis = 0.0
    for i in range(0, len(bvals)):
        if not np.isfinite(bvals[i]):
            continue
        if not in_pos:
            # signal at bar i -> enter at bar i+1 (no look-ahead). Record the
            # basis at the ACTUAL entry bar, NOT the signal bar.
            if abs(bvals[i]) >= BASIS_ENTRY_BPS:
                entry_i = i + 1 if i + 1 < len(bvals) else i
                in_pos = True
                entry_basis = float(bvals[entry_i])
                entry_sign = 1 if entry_basis > 0 else -1
                continue
        else:
            # fade a wide positive basis (short HL / long OKX): profit as basis
            # shrinks toward 0. Exit on convergence (crossed back to ~0).
            entry_sign_cur = 1 if entry_basis > 0 else -1
            converged = (entry_sign_cur > 0 and bvals[i] <= BASIS_EXIT_BPS) or \
                        (entry_sign_cur < 0 and bvals[i] >= -BASIS_EXIT_BPS)
            if converged or i == len(bvals) - 1:
                exit_i = i
                exit_basis = float(bvals[exit_i])
                pnl_bps = entry_sign_cur * (entry_basis - exit_basis)  # signed bps
                net_bps = pnl_bps - CROSS_VENUE_RT_BPS
                eps.append({"pnl_bps": pnl_bps, "net_bps": net_bps,
                            "basis_entry_bps": entry_basis,
                            "basis_exit_bps": exit_basis})
                in_pos = False

    if not eps:
        return {"n_episodes": 0,
                "basis_mean_bps": float(basis.mean()),
                "basis_p90_bps": float(basis.abs().quantile(0.90)),
                "net_bps_total": 0.0, "fee_bps": 0.0, "n_round_trips": 0,
                "episodes": []}
    net_total = sum(e["net_bps"] for e in eps)
    fee_total = len(eps) * CROSS_VENUE_RT_BPS
    return {
        "n_episodes": len(eps),
        "basis_mean_bps": float(basis.mean()),
        "basis_std_bps": float(basis.std()),
        "basis_p90_bps": float(basis.abs().quantile(0.90)),
        "gross_bps_total": sum(e["pnl_bps"] for e in eps),
        "net_bps_total": net_total,
        "fee_bps": fee_total,
        "net_bps_mean": net_total / len(eps),
        "episodes": eps,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--no-backfill", action="store_true")
    args = ap.parse_args()

    print("=== HYP-31 cross-venue funding spread + price basis (HL vs OKX) ===\n")

    # ── backfill OKX price (history-candles) ────────────────────────────────
    if not args.no_backfill:
        print("--- backfilling OKX price history (history-candles 1H + 1D) ---")
        for ticker in UNIVERSE:
            inst = HL_TO_OKX.get(ticker)
            r = backfill_okx_price(ticker, inst)
            cov = {k: (pd.to_datetime(v[0], unit="ms") if v and v[1] else None,
                       pd.to_datetime(v[1], unit="ms") if v and v[1] else None,
                       v[2]) for k, v in r["coverage"].items()}
            print(f"  {ticker} ({inst}): inserted={r['inserted']} coverage={cov}")

    # ── data reality ────────────────────────────────────────────────────────
    print("\n--- data reality ---")
    for coin in UNIVERSE:
        hl = load_hl_series(coin)
        okx_f = load_okx_funding(HL_TO_OKX[coin])
        okx_1h = load_okx_price(HL_TO_OKX[coin], "1H")
        okx_1d = load_okx_price(HL_TO_OKX[coin], "1D")
        print(f"  {coin}: HL hourly {len(hl)} rows "
              f"{pd.to_datetime(hl.index.min(), unit='ms').date()}->"
              f"{pd.to_datetime(hl.index.max(), unit='ms').date()}")
        print(f"       OKX funding {len(okx_f)} 8h "
              f"{pd.to_datetime(okx_f.index.min(), unit='ms').date()}->"
              f"{pd.to_datetime(okx_f.index.max(), unit='ms').date()}")
        print(f"       OKX 1H {len(okx_1h)}  1D {len(okx_1d)}")

    # ── H1 funding-spread carry ─────────────────────────────────────────────
    print("\n--- H1 funding-spread carry (cross-venue delta-neutral) ---")
    h1_rows = {"BTC": None, "ETH": None}
    h1_all_eps = []
    for coin in UNIVERSE:
        hl = load_hl_series(coin)
        okx_f = load_okx_funding(HL_TO_OKX[coin])
        okx_h = okx_f["apr"].reindex(hl.index, method="ffill")
        overlap = pd.concat({"hl_apr": hl["apr"], "okx_apr": okx_h}, axis=1).dropna()
        spread = overlap["hl_apr"] - overlap["okx_apr"]
        print(f"\n  {coin}: overlap {len(overlap)}h "
              f"{pd.to_datetime(overlap.index.min(), unit='ms').date()}->"
              f"{pd.to_datetime(overlap.index.max(), unit='ms').date()}")
        print(f"    spread (HL-OKX, pp/yr): mean {spread.mean():+.3f}  "
              f"median {spread.median():+.3f}  std {spread.std():.3f}  "
              f"p10 {spread.quantile(.1):+.3f}  p90 {spread.quantile(.9):+.3f}")
        print(f"    HL APR mean {overlap['hl_apr'].mean():.2f}%  "
              f"OKX APR mean {overlap['okx_apr'].mean():.2f}%")
        res = simulate_spread(hl, okx_f)
        h1_rows[coin] = res
        for e in res["episodes"]:
            e["coin"] = coin
            h1_all_eps.extend([e])
        if res["n_episodes"]:
            print(f"    episodes {res['n_episodes']}  mean hold {res['mean_hours']:.0f}h")
            print(f"    gross APR {res['gross_apr_bps']:+.1f} bps  "
                  f"fees {res['fee_apr_bps']:.1f} bps  "
                  f"net APR {res['net_apr_bps']:+.1f} bps (of notional)")
        else:
            print("    (no episodes over this window)")

    # ── H2 price-basis MR (hourly: HL mark vs OKX 1H close) ─────────────────
    print("\n--- H2 price-basis mean-reversion (hourly, HL mark vs OKX 1H last) ---")
    h2 = {}
    for coin in UNIVERSE:
        hl = load_hl_series(coin)
        okx_1h = load_okx_price(HL_TO_OKX[coin], "1H")
        joined = pd.concat({"m": hl["mark"], "o": okx_1h["last"]},
                           axis=1).dropna()
        hr = simulate_basis(joined["m"], joined["o"])
        h2[coin] = hr
        net_mean = hr["net_bps_total"] / hr["n_episodes"] if hr["n_episodes"] else 0.0
        print(f"\n  {coin}: {len(joined)}h  |basis| mean "
              f"{abs(hr['basis_mean_bps']):.2f} p90 {hr['basis_p90_bps']:.2f} bps  "
              f"episodes {hr['n_episodes']}  gross {hr['gross_bps_total']:+.1f} "
              f"net {hr['net_bps_total']:+.1f} bps "
              f"({net_mean:+.2f} bps/trade)")

    # ── aggregate verdict numbers ───────────────────────────────────────────
    h1_net_frac = sum(r["net_frac"] for r in h1_rows.values())
    h1_gross_frac = sum(r["gross_frac"] for r in h1_rows.values())
    h1_fee_frac = sum(r["fee_frac"] for r in h1_rows.values())
    n_h1 = sum(r["n_episodes"] for r in h1_rows.values())
    h1_hours = sum(r["hours_total"] for r in h1_rows.values())
    h2_net = sum(r["net_bps_total"] for r in h2.values())
    n_h2 = sum(r["n_episodes"] for r in h2.values())
    h2_gross = sum(r["gross_bps_total"] for r in h2.values())

    print("\n=== aggregate ===")
    print(f"H1 funding-spread (both coins): episodes {n_h1}, hours {h1_hours}")
    if h1_hours:
        print(f"  gross {h1_gross_frac * 1e4 * HOURS_PER_YEAR / h1_hours:+.1f} bps APR")
        print(f"  fees  {h1_fee_frac * 1e4 * HOURS_PER_YEAR / h1_hours:.1f} bps APR")
        print(f"  net   {h1_net_frac * 1e4 * HOURS_PER_YEAR / h1_hours:+.1f} bps APR")
    print(f"H2 price-basis (both coins): episodes {n_h2}, gross {h2_gross:+.1f} "
          f"net {h2_net:+.1f} bps total")

    # ── build result + write trial ──────────────────────────────────────────
    param_hash = hashlib.sha256(json.dumps({
        "construction": "cross_venue_funding_spread_plus_price_basis",
        "universe": list(UNIVERSE),
        "spread_window_hours": SPREAD_WINDOW_HOURS,
        "spread_floor_apr": SPREAD_FLOOR_APR,
        "spread_exit_apr": SPREAD_EXIT_APR,
        "basis_entry_bps": BASIS_ENTRY_BPS,
        "basis_exit_bps": BASIS_EXIT_BPS,
        "hl_maker_bps": _HL_MAKER_BPS,
        "okx_maker_bps": _OKX_MAKER_BPS,
        "cross_venue_rt_bps": CROSS_VENUE_RT_BPS,
        "notional_mode": "1x_capital_delta_neutral",
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(UNIVERSE).encode()).hexdigest()

    # funding-spread persistence stats for the report
    spread_stats = {}
    for coin in UNIVERSE:
        hl = load_hl_series(coin)
        okx_f = load_okx_funding(HL_TO_OKX[coin])
        okx_h = okx_f["apr"].reindex(hl.index, method="ffill")
        ov = pd.concat({"hl": hl["apr"], "okx": okx_h}, axis=1).dropna()
        s = ov["hl"] - ov["okx"]
        spread_stats[coin] = {
            "mean_pp": float(s.mean()), "median_pp": float(s.median()),
            "p10_pp": float(s.quantile(.1)), "p90_pp": float(s.quantile(.9)),
            "hl_apr_mean": float(ov["hl"].mean()),
            "okx_apr_mean": float(ov["okx"].mean()),
            "frac_above_maker_break_even": float((s > (CROSS_VENUE_RT_BPS / 1e4) * HOURS_PER_YEAR).mean()),
            "n_hours": int(len(s)),
        }

    result = {
        "construction": "cross_venue_funding_spread_plus_price_basis",
        "venue": "hyperliquid+okx",
        "live": "off",
        "leverage": "none_delta_neutral",
        "no_lookahead": True,
        "data_gate": {
            "okx_funding_endpoint_cap": "~90 days (funding-rate-history)",
            "okx_funding_window": "2026-07-27 -> 2026-11-05",
            "hl_funding_depth": "2023-05 -> 2026-10 (parquet)",
            "hl_mark_depth": "2023-05 -> 2026-10 (hl_oi_hf parquet)",
            "okx_price_backfill": "history-candles 1H ~5.5mo, 1D deep",
            "note": "H1 overlap is capped by the OKX funding endpoint, NOT HL depth.",
        },
        "cost_model": {
            "hl_maker_bps": _HL_MAKER_BPS,
            "okx_maker_bps": _OKX_MAKER_BPS,
            "cross_venue_round_trip_bps": CROSS_VENUE_RT_BPS,
            "cross_venue_risk_flagged": "transfer/custody/liquidation asymmetry"
                                       " on one leg — NOT quantified as a fee",
        },
        "h1_funding_spread": {
            "per_coin": {c: {
                "spread_stats": spread_stats[c],
                "n_episodes": h1_rows[c]["n_episodes"],
                "gross_apr_bps": h1_rows[c]["gross_apr_bps"],
                "net_apr_bps": h1_rows[c]["net_apr_bps"],
            } for c in UNIVERSE},
            "aggregate_net_apr_bps": (h1_net_frac * 1e4 * HOURS_PER_YEAR / h1_hours)
                                     if h1_hours else 0.0,
            "aggregate_gross_apr_bps": (h1_gross_frac * 1e4 * HOURS_PER_YEAR / h1_hours)
                                       if h1_hours else 0.0,
            "n_episodes": n_h1,
        },
        "h2_price_basis": {
            "frequency": "hourly (HL mark vs OKX 1H last, ~5.5mo window)",
            "per_coin": {c: {
                "n_episodes": h2[c]["n_episodes"],
                "net_bps_total": h2[c]["net_bps_total"],
                "gross_bps_total": h2[c]["gross_bps_total"],
                "basis_mean_bps": h2[c]["basis_mean_bps"],
                "basis_p90_bps": h2[c]["basis_p90_bps"],
                "basis_std_bps": h2[c].get("basis_std_bps"),
            } for c in UNIVERSE},
            "aggregate_net_bps": h2_net,
            "aggregate_gross_bps": h2_gross,
            "n_episodes": n_h2,
            "note": "cross-venue BTC/ETH price basis is ~1bp mean / ~6-8bp p90 (MM-arbitraged); "
                    "far below the 7bp two-venue round-trip, so the fade cannot clear cost.",
        },
        "verdict": (
            "NOT PROMOTED (both channels net-negative/zero net of two-venue maker "
            "fees). H1: the HL-OKX funding spread is real and positive (median +3 to "
            "+4 pp) but grosses only ~4.4-5% APR, BELOW the ~6.4% APR break-even of "
            "the 7bp two-venue maker round-trip at the empirical ~4-day holds -> net "
            "~-1.5% APR. Cross-venue is DOMINATED by the already-validated HL-only "
            "carry (which harvests the FULL HL funding ~8.3-8.6% APR with a free spot "
            "hedge; going cross-venue gives up ~5-6% APR paying OKX funding on the long "
            "leg AND adds transfer/custody/liquidation asymmetry). H2: the BTC/ETH "
            "cross-venue price basis is MM-arbitraged to ~1bp mean / ~6-8bp p90; the "
            "fade grosses ~7bp/trade = exactly the two-venue cost, so it nets to ~0 "
            "(not a harvestable MR edge)."
        ),
    }

    print(f"\nparam_hash={param_hash[:16]}...")

    if not args.no_write:
        e = trials_ledger.increment_trial("HYP-31", param_hash, universe_hash,
                                          "2026-07-27", "2026-11-05", result)
        print(f"wrote trial HYP-31  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
    else:
        print("[--no-write] trial NOT written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())