#!/usr/bin/env python3
"""hyp38_wallet_cohort.py — HYP-38 PRELIMINARY run: on-chain Commitment of Traders.

Proves the LABELING MACHINERY end-to-end + a first-look directional sniff on the
~30-day free-key window. NOT the 90-day Explorer test.

Pipeline (leak-free):
  1. PULL hl.wallet_daily for BTC/ETH/SOL over the reachable window (Ironflow,
     free key) — cached to a local parquet so re-runs don't re-hit the API.
  2. LABEL wallets on the EX-ANTE labeling window (10-10..10-24) only, per the
     pre-registered rubric (realized PnL / win rate / maker ratio / consistency).
     Holding period is DATA-GATED and does not enter the label.
  3. COHORT SIGNAL: for each coin/day after the labeling window, sum net_size_signed
     over skilled vs unskilled wallets; signals = follow-skilled / fade-unskilled / combined.
  4. FIRST-LOOK: next-day close->close forward return vs the signal; report IC
     (Pearson + Spearman), net P&L at maker cost (3 bps round-trip), and the M-5
     MDE floor (mde.mde_sharpe_dsr / mde.mde_ic). Nulls phrased "not detected above MDE X".

Usage:
    python3 hyp38_wallet_cohort.py            # pull (if needed) + run + write trial
    python3 hyp38_wallet_cohort.py --no-write # skip trials-ledger write
    python3 hyp38_wallet_cohort.py --no-pull  # reuse cached parquet

LIVE off. No leverage. Maker-only cost (conservative at maker; taker is worse).
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

_HERE = pathlib.Path(__file__).resolve().parent          # scripts/research/
_GNT = _HERE.parent / "gauntlet"                          # scripts/gauntlet/
_DATA = _HERE.parent / "data"                             # scripts/data/
for _p in (_GNT, _DATA, str(_HERE)):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mde                      # noqa: E402
import trials_ledger as ledger  # noqa: E402
from ingest_hl_fills import query  # noqa: E402  (Ironflow client, free key)

# ---------------------------------------------------------------------------
# Frozen configuration (pre-registered — no tuning)
# ---------------------------------------------------------------------------

MARKETS = ["BTC-PERP", "ETH-PERP", "SOL-PERP"]
COINS = ["BTC", "ETH", "SOL"]

LABEL_START = "2026-10-10"
LABEL_END = "2026-10-24"        # skill assignment window (EX-ANTE)
SIGNAL_START = "2026-10-25"     # first signal day (labels already frozen)

MIN_FILLS = 10                  # min fills in labeling window to be labelable
MIN_DAYS = 3                    # min distinct active days
MIN_CLOSING_FILLS = 5           # min closing fills for a meaningful win_rate

SKILLED_COND = ("realized_pnl_usd > 0 AND win_rate >= 0.5 AND maker_ratio >= 0.5")
UNSKILLED_COND = ("realized_pnl_usd < 0 AND win_rate < 0.5 AND maker_ratio < 0.5")

MAKER_RT_BPS = 3.0              # 2 * 1.5 bps maker round-trip (daily rebalance)

CACHE_PATH = pathlib.Path.home() / ".hermes" / "market_data" / "hl_fills" / \
    "wallet_daily_cache.parquet"

WALLET_COLS = [
    "day", "address", "market", "fills", "realized_pnl_usd",
    "maker_fills", "taker_fills", "net_size_signed",
    "winning_fills", "closing_fills",
]


# ---------------------------------------------------------------------------
# 1. Pull (paginated, budget-paced, cached)
# ---------------------------------------------------------------------------

def pull_wallet_daily(force: bool = False) -> pd.DataFrame:
    """Pull hl.wallet_daily for the 3 markets over the reachable window.

    Paginates by (day, address, market) keyset in 1000-row pages, honoring the
    free-key budget via the shared ``query`` client. Caches to parquet.
    """
    if CACHE_PATH.exists() and not force:
        df = pd.read_parquet(CACHE_PATH)
        print(f"[pull] cached {len(df)} rows from {CACHE_PATH}")
        return df

    cols_sql = ", ".join(WALLET_COLS)
    in_clause = ", ".join(f"'{m}'" for m in MARKETS)
    rows: list[dict] = []
    # day range: pull the full reachable window (label + signal days).
    day = LABEL_START
    last_day = "2026-11-09"
    cursor = (LABEL_START, "", "")   # (day, address, market)
    pages = 0
    while day <= last_day:
        # rediscover per-day cursor: (day, address, market) keyset asc
        d, addr, mkt = cursor
        cond = (
            f"WHERE market IN ({in_clause}) AND day >= '{LABEL_START}' "
            f"AND day <= '{last_day}' "
            f"AND (day > '{d}' OR (day = '{d}' AND address > '{addr}') "
            f"OR (day = '{d}' AND address = '{addr}' AND market > '{mkt}'))"
        )
        sql = (f"SELECT {cols_sql} FROM hl.wallet_daily {cond} "
               f"ORDER BY day, address, market LIMIT 1000")
        r = query(sql)
        batch = r.get("rows", [])
        pages += 1
        if not batch:
            break
        for rec in batch:
            rows.append(dict(zip(WALLET_COLS, rec)))
        last = batch[-1]
        day = last[0]
        cursor = (last[0], last[1], last[2])
        if pages % 100 == 0:
            print(f"[pull] ... {len(rows)} rows ({pages} pages)")

    df = pd.DataFrame(rows)
    for c in ("fills", "maker_fills", "taker_fills",
              "winning_fills", "closing_fills"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("realized_pnl_usd", "net_size_signed"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["day"] = df["day"].astype(str)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".parquet.tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(CACHE_PATH)
    print(f"[pull] pulled+cached {len(df)} rows over {pages} pages")
    return df


# ---------------------------------------------------------------------------
# 2. Labeling machinery (frozen rubric)
# ---------------------------------------------------------------------------

def label_wallets(df: pd.DataFrame) -> pd.DataFrame:
    """Classify wallets on the EX-ANTE labeling window only. Returns per-wallet
    label table with `skill` in {skilled, unskilled, neutral, unlabeled}."""
    lab = df[(df["day"] >= LABEL_START) & (df["day"] <= LABEL_END)]
    g = lab.groupby("address").agg(
        fills=("fills", "sum"),
        n_days=("day", "nunique"),
        closing_fills=("closing_fills", "sum"),
        winning_fills=("winning_fills", "sum"),
        realized_pnl_usd=("realized_pnl_usd", "sum"),
        maker_fills=("maker_fills", "sum"),
        taker_fills=("taker_fills", "sum"),
    ).reset_index()

    # consistency: Sharpe of the wallet's daily realized_pnl_usd series
    daily = lab.groupby(["address", "day"])["realized_pnl_usd"].sum().reset_index()
    consistency = daily.groupby("address")["realized_pnl_usd"].apply(
        lambda s: (s.mean() / s.std(ddof=0)) if (s.std(ddof=0) > 0 and len(s) > 1)
        else 0.0).rename("consistency")
    g = g.merge(consistency.reset_index(), on="address", how="left")
    g["consistency"] = g["consistency"].fillna(0.0)

    g["win_rate"] = np.where(g["closing_fills"] > 0,
                             g["winning_fills"] / g["closing_fills"], 0.0)
    denom = g["maker_fills"] + g["taker_fills"]
    g["maker_ratio"] = np.where(denom > 0, g["maker_fills"] / denom, 0.0)

    def _rule(r):
        if r["fills"] < MIN_FILLS or r["n_days"] < MIN_DAYS or \
                r["closing_fills"] < MIN_CLOSING_FILLS:
            return "unlabeled"
        if r["realized_pnl_usd"] > 0 and r["win_rate"] >= 0.5 and \
                r["maker_ratio"] >= 0.5:
            return "skilled"
        if r["realized_pnl_usd"] < 0 and r["win_rate"] < 0.5 and \
                r["maker_ratio"] < 0.5:
            return "unskilled"
        return "neutral"

    g["skill"] = g.apply(_rule, axis=1)
    return g


# ---------------------------------------------------------------------------
# 3 + 4. Cohort signal + first-look test
# ---------------------------------------------------------------------------

def _load_bars() -> pd.DataFrame:
    import sqlite3
    db = pathlib.Path.home() / ".hermes" / "market_data" / "hl_bars" / "bars_1d.db"
    con = sqlite3.connect(db)
    frames = []
    for t in COINS:
        d = pd.read_sql_query(
            "SELECT ts, close FROM bars WHERE ticker=? AND timeframe='1d'",
            con, params=(t,))
        d["coin"] = t
        frames.append(d)
    con.close()
    bars = pd.concat(frames, ignore_index=True)
    bars["ts"] = pd.to_datetime(bars["ts"], unit="ms", utc=True)
    bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
    bars = bars.sort_values(["coin", "ts"])
    bars["fwd_ret"] = bars.groupby("coin")["close"].pct_change().shift(-1)
    return bars


def run_first_look(df: pd.DataFrame, labels: pd.DataFrame) -> dict:
    labels_by_addr = labels.set_index("address")["skill"].to_dict()
    skilled = set(labels[labels["skill"] == "skilled"]["address"])
    unskilled = set(labels[labels["skill"] == "unskilled"]["address"])

    # cohort net positioning per coin/day over the SIGNAL window
    sig = df[(df["day"] >= SIGNAL_START)].copy()
    sig["coin"] = sig["market"].str.replace("-PERP", "", regex=False)

    def _mark(row):
        a = row["address"]
        if a in skilled:
            return "skilled"
        if a in unskilled:
            return "unskilled"
        return "other"

    sig["cohort"] = sig["address"].map(_mark)

    cohort_net = (sig.groupby(["coin", "day", "cohort"])["net_size_signed"]
                  .sum().unstack(fill_value=0.0).reset_index())
    for c in ("skilled", "unskilled"):
        if c not in cohort_net.columns:
            cohort_net[c] = 0.0

    bars = _load_bars()
    bars = bars[bars["day"] >= SIGNAL_START]
    cn = cohort_net.merge(
        bars[["coin", "day", "fwd_ret"]].rename(columns={"day": "day"}),
        on=["coin", "day"], how="left")

    cn["follow_skilled"] = np.sign(cn["skilled"])
    cn["fade_unskilled"] = np.sign(-cn["unskilled"])
    cn["combined"] = np.sign(cn["skilled"] - cn["unskilled"])

    out = {}
    for name, sigcol in (("follow_skilled", "follow_skilled"),
                         ("fade_unskilled", "fade_unskilled"),
                         ("combined", "combined")):
        valid = cn[(cn["fwd_ret"].notna()) & (cn[sigcol] != 0)].copy()
        if len(valid) < 2:
            out[name] = {"n": len(valid), "ic_pearson": None,
                         "ic_spearman": None, "n_long": 0, "n_short": 0,
                         "net_pnl_bps": None, "mde_ic": None, "mde_sharpe_dsr": None}
            continue
        x = valid[sigcol].astype(float)
        y = valid["fwd_ret"].astype(float)
        pearson = float(np.corrcoef(x, y)[0, 1]) if y.std() > 0 else None
        spearman = float(pd.Series(x).corr(pd.Series(y), method="spearman"))
        # net P&L at maker cost: sign*return, charged 3bps per held day
        pnl = (x * y) - (MAKER_RT_BPS / 10000.0)
        n_long = int((x > 0).sum())
        n_short = int((x < 0).sum())
        out[name] = {
            "n": int(len(valid)),
            "n_long": n_long, "n_short": n_short,
            "ic_pearson": None if pearson is None else round(pearson, 4),
            "ic_spearman": round(spearman, 4),
            "mean_fwd_ret_bps_signpos": round(float((x * y).mean()) * 1e4, 2),
            "net_pnl_bps": round(float(pnl.sum()) * 1e4, 2),
            "net_pnl_per_obs_bps": round(float(pnl.mean()) * 1e4, 2),
        }
    out["meta"] = {
        "n_labeled_wallets": int(len(labels)),
        "n_skilled": int(len(skilled)),
        "n_unskilled": int(len(unskilled)),
        "n_neutral": int((labels["skill"] == "neutral").sum()),
        "n_unlabeled": int((labels["skill"] == "unlabeled").sum()),
        "signal_days": sorted(cn["day"].unique().tolist()),
        "n_signal_obs_total": int(len(cn[cn["fwd_ret"].notna()])),
    }
    return out


# ---------------------------------------------------------------------------
# MDE framing + trial write
# ---------------------------------------------------------------------------

def attach_mde(res: dict, n_trials: int) -> dict:
    for name in ("follow_skilled", "fade_unskilled", "combined"):
        n = res[name]["n"]
        if n >= 2:
            res[name]["mde_sharpe_dsr"] = round(mde.mde_sharpe_dsr(n, n_trials), 4)
            res[name]["mde_ic"] = round(mde.mde_ic(n, n_trials, breadth=1.0), 4)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="HYP-38 wallet-cohort first look")
    ap.add_argument("--no-write", action="store_true",
                    help="skip trials-ledger write")
    ap.add_argument("--no-pull", action="store_true",
                    help="reuse cached wallet_daily parquet")
    ap.add_argument("--force-pull", action="store_true")
    args = ap.parse_args()

    df = pull_wallet_daily() if not args.no_pull else \
        pd.read_parquet(CACHE_PATH)

    labels = label_wallets(df)
    res = run_first_look(df, labels)
    n_trials = ledger.count()
    res = attach_mde(res, n_trials)

    print("\n=== HYP-38 wallet-cohort — labels ===")
    print(f"labelable wallets: {res['meta']['n_labeled_wallets']}")
    print(f"  skilled  : {res['meta']['n_skilled']}")
    print(f"  unskilled: {res['meta']['n_unskilled']}")
    print(f"  neutral  : {res['meta']['n_neutral']}")
    print(f"  unlabeled: {res['meta']['n_unlabeled']}")
    print(f"signal days: {len(res['meta']['signal_days'])} "
          f"({res['meta']['signal_days'][0]} .. {res['meta']['signal_days'][-1]})")

    print("\n=== first-look (maker cost) ===")
    for name in ("follow_skilled", "fade_unskilled", "combined"):
        r = res[name]
        ic = f"{r['ic_spearman']:+.3f}" if r["ic_spearman"] is not None else "n/a"
        pnl = f"{r['net_pnl_bps']:+.1f} bps" if r["net_pnl_bps"] is not None else "n/a"
        mde_ic = f"{r['mde_ic']:.3f}" if r.get("mde_ic") else "n/a"
        print(f"  {name:16s} n={r['n']:3d} (L{r['n_long']}/S{r['n_short']}) "
              f"IC_spearman={ic}  netPnL={pnl}  MDE_IC={mde_ic}")
        if r["ic_spearman"] is not None and r.get("mde_ic"):
            if abs(r["ic_spearman"]) < r["mde_ic"]:
                print(f"    -> {mde.format_null_verdict(r['ic_spearman'], r['mde_ic'], 'IC')}")

    # ---- trial write ----
    param_hash = hashlib.sha256(json.dumps({
        "hypothesis": "HYP-38", "construction": "wallet_cohort_cot_first_look",
        "venue": "hyperliquid", "universe": COINS,
        "label_window": [LABEL_START, LABEL_END],
        "signal_start": SIGNAL_START,
        "rubric": {"min_fills": MIN_FILLS, "min_days": MIN_DAYS,
                   "min_closing_fills": MIN_CLOSING_FILLS,
                   "skilled": SKILLED_COND, "unskilled": UNSKILLED_COND,
                   "holding_period": "DATA_GATED_deferred"},
        "cost": {"maker_rt_bps": MAKER_RT_BPS, "leverage": "none"},
        "live": "off", "no_lookahead": True,
    }, sort_keys=True).encode()).hexdigest()
    universe_hash = hashlib.sha256(",".join(sorted(COINS)).encode()).hexdigest()

    result = {
        "construction": "wallet_cohort_cot_first_look",
        "venue": "hyperliquid", "universe": COINS,
        "leverage": "none", "live": "off", "no_lookahead": True,
        "label_window": [LABEL_START, LABEL_END],
        "signal_start": SIGNAL_START,
        "label_counts": res["meta"],
        "first_look": {k: res[k] for k in
                       ("follow_skilled", "fade_unskilled", "combined")},
        "verdict": (
            f"PRELIMINARY machinery validation on {len(res['meta']['signal_days'])} "
            f"signal days (free key ~30d window). Skill persistence + cohort-stable "
            f"signal CANNOT be established this short; see the 90-day Explorer run."
        ),
    }

    if not args.no_write:
        e = ledger.increment_trial("HYP-38", param_hash, universe_hash,
                                   LABEL_START, "2026-11-09", result)
        print(f"\nwrote trial HYP-38  param_hash={e['param_hash'][:16]}...  "
              f"chain_hash={e['chain_hash'][:16]}...")
        ok, msg = ledger.verify_integrity()
        print(f"ledger chain verify: {ok} ({msg})")
    else:
        print(f"\n[--no-write] trial NOT written. param_hash={param_hash[:16]}...")

    # dump result JSON for the report
    out_path = _HERE.parent.parent / "reports" / "backtester" / \
        "HYP-38_wallet_cohort_first_look.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"result JSON -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())