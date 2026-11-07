"""revalidate_hyp23_rr_target_ratio.py — HYP-23 R:R target-ratio sensitivity.

Read-only research driver. THIS IS A METHODOLOGY TEST, NOT A STRATEGY CANDIDATE:
it isolates whether the TARGET ratio (1R vs 2R vs 3R) — with ENTRY + STOP +
SIGNAL held constant — changes NET expectancy. It does NOT test whether
cross-sectional momentum has edge (already known weak). The only free variable
is the target distance.

Pre-registered (HYP-23 frontmatter — FIXED, do NOT tune):
  * Signal: cross-sectional 7d price momentum, long top-decile / short
    bottom-decile (simple, well-defined, KNOWN weak edge).
  * Stop: fixed 2x ATR14 (= 1R).
  * Target: {1R, 2R, 3R} — THREE runs, entry + stop IDENTICAL, ONLY target moves.
  * Cost: realistic 4.5 bps/leg taker + hourly funding (longs pay positive
    funding) + adverse entry slippage (2.5 bps). NOT the 45 bps/leg error.

Prior (recorded in the hypothesis BEFORE the run): R:R selects the breakeven
win rate, not edge. For a FIXED signal + stop, net expectancy should be
~invariant; farther targets should HURT net (lower win rate amortizes fixed
fees worse, longer hold pays more funding, realized stop dilutes the intended
asymmetry more at far targets). So prior: net(3R) <= net(2R) <= net(1R).

Data: hl_oi_hf (hourly mark_price -> daily OHLC, native perps) + hl_funding_hf
(hourly funding_rate -> daily funding charge). 235 coins x ~1269 daily bars,
2023-05 -> 2026-10.

Mechanics (no look-ahead): signal at day-t close (7d momentum), fill at day-t+1
open (adverse entry slip), R = 2*ATR14[t]. Walk DAILY bars forward from t+1;
first touch of stop vs target wins (gap-through exits at the open; both-touched
in one bar resolves pessimistic to stop-first). Time-stop after TIMESTOP_BARS.
Funding = sum of hourly funding over the exact holding window (longs pay
positive funding: cost = -sign * sum_funding). No leverage beyond +-1x. LIVE
off. Cost charged once. Writes THREE trials-ledger entries (one per target,
fresh param_hash each). Path-scoped commit (never git add -A/.).

Usage: python3 revalidate_hyp23_rr_target_ratio.py [--no-write]
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

OI_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_oi_hf"
FUNDING_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_funding_hf"

# ── Pre-registered constants (FIXED — do not tune) ──────────────────────────
DECILE_FRAC = 0.10          # top/bottom decile per leg
MOMENTUM_LOOKBACK = 7       # 7d price momentum
ATR_WINDOW = 14             # ATR lookback (daily bars)
STOP_ATR_MULT = 2.0         # stop distance = 2x ATR = 1R
TARGETS_R = [1.0, 2.0, 3.0]  # THE TEST VARIABLE
TAKER_BPS = 4.5             # realistic taker, per leg (fill)
ENTRY_SLIP_BPS = 2.5        # adverse entry slippage (buy higher / sell lower)
TIMESTOP_BARS = 20          # time-stop horizon (daily bars)
MIN_COINS_DAY = 20          # require >= this many ranked coins to form a day
FUNDING_AS_CHARGE = True    # funding accrues as a cost, not a signal


# ────────────────────────────────────────────────────────────────────────────
def load_daily_ohlc() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                pd.DataFrame]:
    """Hourly mark_price -> daily open/high/low/close panels (native perps)."""
    files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no OI parquet under {OI_DIR}")
    parts = [pd.read_parquet(f, columns=["timestamp", "coin", "dex", "mark_price"])
             for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[df["dex"] == ""].dropna(subset=["mark_price"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()

    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(open=("mark_price", "first"), high=("mark_price", "max"),
                  low=("mark_price", "min"), close=("mark_price", "last"))
             .reset_index())

    start = daily["date"].min()
    end = daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    opens = daily.pivot(index="date", columns="coin", values="open").reindex(cal)
    highs = daily.pivot(index="date", columns="coin", values="high").reindex(cal)
    lows = daily.pivot(index="date", columns="coin", values="low").reindex(cal)
    closes = daily.pivot(index="date", columns="coin", values="close").reindex(cal)
    return opens, highs, lows, closes


def load_daily_funding() -> pd.DataFrame:
    """Hourly funding_rate -> daily SUM panel (native perps)."""
    files = sorted(glob.glob(str(FUNDING_DIR / "*.parquet")))
    if not files:
        raise SystemExit(f"no funding parquet under {FUNDING_DIR}")
    parts = [pd.read_parquet(f, columns=["timestamp", "coin", "dex", "funding_rate"])
             for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[df["dex"] == ""].dropna(subset=["funding_rate"])
    native["timestamp"] = native["timestamp"].dt.tz_convert("UTC")
    native["date"] = native["timestamp"].dt.normalize()

    daily = (native.sort_values("timestamp")
             .groupby(["coin", "date"], sort=False)
             .agg(fund_sum=("funding_rate", "sum"))
             .reset_index())

    start = daily["date"].min()
    end = daily["date"].max()
    cal = pd.date_range(start, end, freq="D", tz="UTC")
    return daily.pivot(index="date", columns="coin", values="fund_sum").reindex(cal)


def compute_indicator_arrays(
    opens: pd.DataFrame, highs: pd.DataFrame,
    lows: pd.DataFrame, closes: pd.DataFrame,
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray,
           np.ndarray, np.ndarray]:
    """Return aligned (n_coins x n_days) float arrays: O,H,L,C,ATR14,mom.

    ATR14 = simple mean of true range over ATR_WINDOW daily bars.
    mom7 = close / close.shift(7) - 1.
    """
    coins = list(closes.columns)
    n_days = len(closes)

    # ATR (simple moving average of true range)
    prev_close = closes.shift(1)
    tr = pd.DataFrame(np.maximum.reduce([
        (highs - lows).to_numpy(dtype=float),
        (highs - prev_close).abs().to_numpy(dtype=float),
        (lows - prev_close).abs().to_numpy(dtype=float),
    ]), index=closes.index, columns=closes.columns)
    atr = tr.rolling(ATR_WINDOW, min_periods=ATR_WINDOW).mean()

    mom = closes / closes.shift(MOMENTUM_LOOKBACK) - 1.0

    def arr(df: pd.DataFrame) -> np.ndarray:
        return df.to_numpy(dtype=float).T  # (n_coins, n_days)

    return (coins, arr(opens), arr(highs), arr(lows), arr(closes),
            arr(atr), arr(mom))


# ────────────────────────────────────────────────────────────────────────────
def load_hourly_marks(coins: list[str]) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Hourly mark_price -> (hours x coin) panel on a continuous hourly index.

    The hl_oi_hf data is sampled uniformly on the hour, so every listed coin has
    a mark each hour. Returns (panel, hourly_index).
    """
    files = sorted(glob.glob(str(OI_DIR / "*.parquet")))
    parts = [pd.read_parquet(f, columns=["timestamp", "coin", "dex", "mark_price"])
             for f in files]
    df = pd.concat(parts, ignore_index=True)
    native = df[(df["dex"] == "") & (df["coin"].isin(coins))].dropna(subset=["mark_price"])
    native["h"] = native["timestamp"].dt.tz_convert("UTC").dt.floor("h")
    keep = (native.sort_values("timestamp")
            .drop_duplicates(subset=["h", "coin"], keep="last"))
    panel = keep.pivot(index="h", columns="coin", values="mark_price")
    hr_idx = pd.date_range(panel.index.min(), panel.index.max(), freq="h", tz="UTC")
    panel = panel.reindex(hr_idx)
    return panel, hr_idx


# ────────────────────────────────────────────────────────────────────────────
def run_target(Mh, C, F, ATR, M, dates, day_to_first, hour_to_day,
               target_r: float) -> dict:
    """Run the full backtest for ONE target ratio. Returns stats dict.

    Signal at day-t close (7d momentum), fill at day-t+1 open (= first hourly
    mark). Walk HOURLY marks forward; first touch of stop vs target resolved in
    true chronological order (no daily-bar ambiguity). Exit fills AT the level
    (stop = -1R, target = +target_r R); time-stop exits at the close.
    """
    n_coins, n_days = C.shape
    n_hours = Mh.shape[1]
    records: list[dict] = []

    # per-trade cost fractions (taker 2 legs + adverse entry slip)
    fees_frac = (2.0 * TAKER_BPS + ENTRY_SLIP_BPS) / 1e4
    max_hours = TIMESTOP_BARS * 24

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
        bot_idx = idx[order[:k]]       # short bottom-decile
        top_idx = idx[order[-k:]]      # long top-decile
        cands = [(c, +1) for c in top_idx] + [(c, -1) for c in bot_idx]

        for c, direction in cands:
            entry = Mh[c, start_h]
            risk = 2.0 * atr_t[c]          # stop distance = 2x ATR = 1R
            risk_pct = risk / entry
            if not (risk_pct > 0) or not np.isfinite(risk_pct):
                continue
            if direction > 0:
                stop = entry - risk
                target = entry + target_r * risk
            else:
                stop = entry + risk
                target = entry - target_r * risk

            kind = None
            exit_h = None
            end_h = min(start_h + 1 + max_hours, n_hours)
            for h in range(start_h + 1, end_h):
                m = Mh[c, h]
                if not np.isfinite(m):
                    continue
                if direction > 0:
                    if m <= stop:
                        kind, exit_h = "stop", h
                        break
                    if m >= target:
                        kind, exit_h = "target", h
                        break
                else:
                    if m >= stop:
                        kind, exit_h = "stop", h
                        break
                    if m <= target:
                        kind, exit_h = "target", h
                        break

            if kind is None:
                # time-stop: exit at close of day t+TIMESTOP_BARS (or last day)
                exit_day = min(t + TIMESTOP_BARS, n_days - 1)
                if not np.isfinite(C[c, exit_day]):
                    continue
            else:
                exit_day = int(hour_to_day[exit_h])
                if exit_day < 0:
                    continue

            # ── gross price R (exit at level) ───────────────────────────────
            if kind == "target":
                gross_r = target_r                 # +target_r R
            elif kind == "stop":
                gross_r = -1.0                     # -1R
            else:                                   # time-stop: close drift
                epx = C[c, exit_day]
                gross_r = ((epx - entry) / entry / risk_pct if direction > 0
                           else (entry - epx) / entry / risk_pct)

            # ── funding over holding window t+1 .. exit_day (daily sums) ────
            fund_frac = 0.0
            for b in range(t + 1, exit_day + 1):
                fv = F[c, b]
                if np.isfinite(fv):
                    fund_frac += fv
            funding_r = -direction * fund_frac / risk_pct  # longs pay +funding

            fee_r = fees_frac / risk_pct
            net_r = gross_r - fee_r + funding_r
            bars_held = exit_day - t  # entry day = t+1 -> 1 bar if exits on entry

            records.append({
                "date": dates[t], "coin": c, "direction": direction,
                "kind": kind, "gross_r": gross_r, "fee_r": fee_r,
                "funding_r": funding_r, "net_r": net_r, "bars_held": bars_held,
                "risk_pct": risk_pct,
            })

    return _stats(records)


# ────────────────────────────────────────────────────────────────────────────
def _pf(rs) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    return gains / losses if losses > 0 else (float("inf") if gains > 0 else 0.0)


def _stats(records: list[dict]) -> dict:
    if not records:
        return {"n_trades": 0}
    net = np.array([r["net_r"] for r in records], dtype=float)
    gross = np.array([r["gross_r"] for r in records], dtype=float)
    fee = np.array([r["fee_r"] for r in records], dtype=float)
    fund = np.array([r["funding_r"] for r in records], dtype=float)
    bars = np.array([r["bars_held"] for r in records], dtype=float)
    wins = net > 0
    pos = float(net[wins].sum()) if wins.any() else 0.0
    neg = float(-net[~wins].sum()) if (~wins).any() else 0.0
    return {
        "n_trades": int(len(records)),
        "mean_net_r": float(net.mean()),
        "median_net_r": float(np.median(net)),
        "std_net_r": float(net.std(ddof=1)) if len(net) > 1 else 0.0,
        "total_net_r": float(net.sum()),
        "win_rate": float(wins.mean()),
        "pf": pos / neg if neg > 0 else (float("inf") if pos > 0 else 0.0),
        "mean_gross_r": float(gross.mean()),
        "mean_fee_r": float(fee.mean()),
        "mean_funding_r": float(fund.mean()),
        "mean_bars_held": float(bars.mean()),
        "median_bars_held": float(np.median(bars)),
        "exit_breakdown": {k: int(sum(1 for r in records if r["kind"] == k))
                           for k in ("target", "stop", "time")},
    }


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    global TIMESTOP_BARS
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--timestop", type=int, default=TIMESTOP_BARS,
                    help="time-stop horizon in daily bars (diagnostic; "
                         "default is the pre-registered %d)" % TIMESTOP_BARS)
    args = ap.parse_args()
    TIMESTOP_BARS = args.timestop

    print("=== HYP-23 — R:R target-ratio sensitivity (methodology test) ===\n")

    print("loading hourly mark -> daily OHLC panels ...")
    opens, highs, lows, closes = load_daily_ohlc()
    print(f"  OI panel: {opens.shape[0]} days x {opens.shape[1]} coins "
          f"({opens.index.min().date()} -> {opens.index.max().date()})")

    print("loading hourly funding -> daily sum panel ...")
    fundsum = load_daily_funding()
    # align funding columns to OHLC columns
    common = [c for c in closes.columns if c in fundsum.columns]
    closes = closes[common]
    opens = opens[common]
    highs = highs[common]
    lows = lows[common]
    fundsum = fundsum[common]
    print(f"  intersection coins (price + funding): {len(common)}")

    coins, O, H, L, C, ATR, M = compute_indicator_arrays(
        opens, highs, lows, closes)
    F = fundsum.to_numpy(dtype=float).T
    dates = list(closes.index)

    # pre-compute median risk_pct and ATR magnitude for diagnostics
    atr_pct = np.where(C > 0, ATR / C, np.nan)
    valid_pct = atr_pct[np.isfinite(atr_pct) & (atr_pct > 0)]
    print(f"  median ATR14/price: {np.median(valid_pct)*100:.2f}%  "
          f"-> median 1R (2xATR): {np.median(valid_pct)*200:.2f}% of price")

    # hourly marks for unbiased stop/target first-touch ordering
    print("loading hourly marks for first-touch resolution ...")
    marks_panel, hr_idx = load_hourly_marks(common)
    Mh = marks_panel[common].to_numpy(dtype=float).T    # (n_coins, n_hours)
    hr_days = marks_panel.index.normalize()
    uniq_days, first_idx = np.unique(hr_days.to_numpy(), return_index=True)
    day_to_first = {pd.Timestamp(uniq_days[i]): int(first_idx[i])
                    for i in range(len(uniq_days))}
    # hour -> daily-calendar index
    date_to_didx = {d: i for i, d in enumerate(dates)}
    hour_to_day = np.array([date_to_didx.get(hr_days[i], -1)
                            for i in range(len(hr_days))], dtype=np.int64)
    print(f"  hourly marks: {Mh.shape[1]} hours x {Mh.shape[0]} coins\n")

    # --- run THREE targets ---
    results = {}
    for tr in TARGETS_R:
        r = run_target(Mh, C, F, ATR, M, dates, day_to_first, hour_to_day, tr)
        results[tr] = r
        s = r
        print(f"--- target {tr:g}R ---")
        print(f"  n_trades={s['n_trades']}  "
              f"net={s['mean_net_r']:+.4f}R  "
              f"win={s['win_rate']:.3f}  PF={s['pf']:.3f}  "
              f"bars={s['mean_bars_held']:.2f}")
        print(f"    gross={s['mean_gross_r']:+.4f}R  fee={s['mean_fee_r']:.4f}R  "
              f"funding={s['mean_funding_r']:+.4f}R")
        print(f"    exits: target={s['exit_breakdown']['target']}  "
              f"stop={s['exit_breakdown']['stop']}  "
              f"time={s['exit_breakdown']['time']}")

    # --- ledger writes (one fresh param_hash per target) ---
    universe = sorted(common)
    universe_hash = hashlib.sha256(",".join(universe).encode()).hexdigest()
    period_start = str(closes.index.min().date())
    period_end = str(closes.index.max().date())
    ledger_n = ledger.count()

    print("\n  summary table (target | net multi-R | win rate | PF | bars held):")
    print(f"  {'target':>6s} {'netR':>9s} {'win':>7s} {'PF':>7s} {'bars':>7s}")
    for tr in TARGETS_R:
        s = results[tr]
        print(f"  {tr:>6g} {s['mean_net_r']:>+9.4f} {s['win_rate']:>7.3f} "
              f"{s['pf']:>7.3f} {s['mean_bars_held']:>7.2f}")

    if not args.no_write:
        for tr in TARGETS_R:
            param_dict = {
                "construction": "rr_target_ratio_sensitivity",
                "signal": "cross_sectional_7d_price_momentum",
                "decile_frac": DECILE_FRAC,
                "stop_atr_mult": STOP_ATR_MULT,
                "atr_window": ATR_WINDOW,
                "momentum_lookback": MOMENTUM_LOOKBACK,
                "target_r": tr,
                "taker_bps": TAKER_BPS,
                "entry_slip_bps": ENTRY_SLIP_BPS,
                "timestop_bars": TIMESTOP_BARS,
                "min_coins_day": MIN_COINS_DAY,
                "exit_resolution": "hourly_first_touch",
                "funding": "hourly_sum_as_charge_longs_pay_positive",
                "no_lookahead": True,
                "leverage": "none_+/-1x",
                "live": "off",
            }
            param_hash = hashlib.sha256(
                json.dumps(param_dict, sort_keys=True).encode()).hexdigest()
            s = results[tr]
            result = {
                "construction": "rr_target_ratio_sensitivity",
                "target_r": tr,
                "n_coins_universe": len(universe),
                "stop_atr_mult": STOP_ATR_MULT,
                "taker_bps": TAKER_BPS,
                "entry_slip_bps": ENTRY_SLIP_BPS,
                "n_trades": s["n_trades"],
                "mean_net_r": round(s["mean_net_r"], 6),
                "median_net_r": round(s["median_net_r"], 6),
                "std_net_r": round(s["std_net_r"], 6),
                "total_net_r": round(s["total_net_r"], 6),
                "win_rate": round(s["win_rate"], 6),
                "profit_factor": round(s["pf"], 6),
                "mean_gross_r": round(s["mean_gross_r"], 6),
                "mean_fee_r": round(s["mean_fee_r"], 6),
                "mean_funding_r": round(s["mean_funding_r"], 6),
                "mean_bars_held": round(s["mean_bars_held"], 4),
                "median_bars_held": round(s["median_bars_held"], 4),
                "exit_resolution": "hourly_first_touch",
                "exit_breakdown": s["exit_breakdown"],
                "no_lookahead": True,
                "leverage": "none_+/-1x",
                "live": "off",
                "data_source": "hl_oi_hf + hl_funding_hf parquet (native perps, 3.5y)",
            }
            e = ledger.increment_trial("HYP-23", param_hash, universe_hash,
                                       period_start, period_end, result)
            print(f"  wrote trial HYP-23 target={tr:g}R  "
                  f"param_hash={e['param_hash'][:16]}...")
        print(f"  ledger_N before={ledger_n} after={ledger.count()}")
    else:
        print("  [--no-write] trials NOT written.")

    # dump combined results JSON for the report
    out = pathlib.Path.home() / ".hermes" / "cache" / "scratch" / "hyp23_result.json"
    payload = {str(tr): results[tr] for tr in TARGETS_R}
    with open(out, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\nresult saved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())