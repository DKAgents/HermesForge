"""
_phase1b_g_sweep.py — Phase 1B parameter sensitivity sweep for STR-G
(Relative-Strength / Sector-Rotation). Standalone script, does NOT touch
scanner_g_relative_strength.py or run_phase1a.py's 'g' registration.

Reuses the identical RS/SMA/crossover entry logic from the baseline scanner,
but parametrizes: RR_MULT (target), STOP_LOOKBACK (stop window), MAX_HOLD
(time stop), and an optional stronger momentum filter (RS_ROC_MIN) or a
"RS near top of its own N-bar range" quality filter.

Run directly: python3 scripts/validation/scanners/_phase1b_g_sweep.py
"""

import datetime
import pathlib
import sys

import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"

SUBPERIODS = [
    ("period1_bull",    "2019-04-01", "2021-12-31"),
    ("period2_bear",    "2022-01-01", "2023-12-31"),
    ("period3_current", "2024-01-01", "2099-12-31"),
]


def label_subperiod(date) -> str:
    d = pd.Timestamp(date).date()
    for name, start, end in SUBPERIODS:
        if datetime.date.fromisoformat(start) <= d <= datetime.date.fromisoformat(end):
            return name
    return "pre_warmup"


RS_SMA_LEN = 20
RS_ROC_LEN = 20
SMA50_LEN = 50
MIN_BARS = SMA50_LEN
MIN_ALIGNED = RS_SMA_LEN + RS_ROC_LEN

_SPY_CACHE_PATH = CACHE_DIR / "SPY.parquet"
_SPY_DF = None


def _load_spy() -> pd.DataFrame:
    global _SPY_DF
    if _SPY_DF is None:
        spy = pd.read_parquet(_SPY_CACHE_PATH)
        spy.columns = spy.columns.str.lower()
        spy = spy.sort_index()
        _SPY_DF = spy
    return _SPY_DF


def _simulate_exit(df, entry_idx, entry_price, stop_price, target_price, max_hold):
    risk = entry_price - stop_price
    n = len(df)
    for offset in range(1, max_hold + 1):
        bar_idx = entry_idx + offset
        if bar_idx >= n:
            last_close = df["close"].iloc[bar_idx - 1] if bar_idx > 0 else entry_price
            r_mult = (last_close - entry_price) / risk
            return dict(exit_price=round(last_close, 4), exit_reason="time",
                        bars_held=offset, r_multiple=round(r_mult, 3))
        close = df["close"].iloc[bar_idx]
        if close <= stop_price:
            r_mult = (close - entry_price) / risk
            return dict(exit_price=round(close, 4), exit_reason="stop",
                        bars_held=offset, r_multiple=round(r_mult, 3))
        if close >= target_price:
            r_mult = (close - entry_price) / risk
            return dict(exit_price=round(close, 4), exit_reason="target",
                        bars_held=offset, r_multiple=round(r_mult, 3))
    last_close = df["close"].iloc[entry_idx + max_hold]
    r_mult = (last_close - entry_price) / risk
    return dict(exit_price=round(last_close, 4), exit_reason="time",
                bars_held=max_hold, r_multiple=round(r_mult, 3))


def scan_variant(df, ticker, *, rr_mult=2.5, stop_lookback=10, max_hold=10,
                  rs_roc_min=0.0, require_range_high=False, range_len=60,
                  range_pct=0.8, strategy_id="STR-G-variant"):
    """
    Parametrized clone of scanner_g_relative_strength.scan().

    require_range_high: if True, additionally requires RS_today to be within
    the top `range_pct` fraction of its own trailing `range_len`-bar range
    (RS_today >= range_low + range_pct*(range_high-range_low)) -- a
    "quality of momentum" filter selecting stronger relative-strength setups.
    """
    if ticker == "SPY":
        return []
    df = df.copy()
    df.columns = df.columns.str.lower()
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(df.columns):
        return []
    df = df.sort_index()
    if len(df) < MIN_BARS:
        return []

    spy_df = _load_spy()
    aligned = pd.DataFrame({
        "ticker_close": df["close"],
        "spy_close": spy_df["close"],
    }).dropna()

    min_aligned = MIN_ALIGNED if not require_range_high else max(MIN_ALIGNED, range_len)
    if len(aligned) < min_aligned:
        return []

    rs = aligned["ticker_close"] / aligned["spy_close"]
    rs_sma20 = rs.rolling(RS_SMA_LEN).mean()
    rs_roc = rs / rs.shift(RS_ROC_LEN) - 1.0
    rs_roll_min = rs.rolling(range_len).min()
    rs_roll_max = rs.rolling(range_len).max()

    sma50 = df["close"].rolling(SMA50_LEN).mean()

    signals = []
    aligned_dates = aligned.index

    for j in range(min_aligned, len(aligned_dates)):
        date = aligned_dates[j]
        rs_today = rs.iloc[j]
        rs_yesterday = rs.iloc[j - 1]
        sma_today = rs_sma20.iloc[j]
        sma_yesterday = rs_sma20.iloc[j - 1]
        roc_today = rs_roc.iloc[j]

        if pd.isna(sma_today) or pd.isna(sma_yesterday) or pd.isna(roc_today):
            continue

        crossed_up = (rs_yesterday < sma_yesterday) and (rs_today >= sma_today)
        if not crossed_up:
            continue

        if not (roc_today > rs_roc_min):
            continue

        if require_range_high:
            rlo, rhi = rs_roll_min.iloc[j], rs_roll_max.iloc[j]
            if pd.isna(rlo) or pd.isna(rhi) or rhi <= rlo:
                continue
            threshold = rlo + range_pct * (rhi - rlo)
            if not (rs_today >= threshold):
                continue

        if date not in df.index:
            continue
        i = df.index.get_loc(date)
        if isinstance(i, slice) or not isinstance(i, int):
            continue

        sma50_today = sma50.iloc[i]
        if pd.isna(sma50_today):
            continue
        today_close = df["close"].iloc[i]
        if not (today_close > sma50_today):
            continue

        if i < stop_lookback:
            continue

        entry_price = today_close
        stop_price = df["low"].iloc[i - stop_lookback:i].min()
        if stop_price >= entry_price:
            continue

        risk = entry_price - stop_price
        target_price = entry_price + rr_mult * risk

        exit_info = _simulate_exit(df, i, entry_price, stop_price, target_price, max_hold)

        ts = pd.Timestamp(str(df.index[i]))
        date_val = ts.date()

        signals.append(dict(
            ticker=ticker,
            date=date_val,
            entry_price=round(entry_price, 4),
            stop_price=round(stop_price, 4),
            target_price=round(target_price, 4),
            direction="long",
            subperiod=label_subperiod(ts),
            strategy_id=strategy_id,
            **exit_info,
        ))

    return signals


def load_all_cached():
    data = {}
    for p in sorted(CACHE_DIR.glob("*.parquet")):
        ticker = p.stem
        try:
            df = pd.read_parquet(p)
            df.columns = df.columns.str.lower()
            df = df.sort_index()
            data[ticker] = df
        except Exception as e:
            print(f"  skip {ticker}: {e}", file=sys.stderr)
    return data


def summarize(results: pd.DataFrame) -> dict:
    if results.empty:
        return dict(total_signals=0, signals_per_year=0.0, avg_r=0.0, median_r=0.0,
                    win_rate=0.0, sub_positive=0, sub_detail={}, classification="KILL",
                    friction_flag=False)
    results = results.copy()
    results["date"] = pd.to_datetime(results["date"])
    years = max((results["date"].max() - results["date"].min()).days / 365.25, 0.1)
    signals_per_year = len(results) / years
    avg_r = float(results["r_multiple"].mean())
    median_r = float(results["r_multiple"].median())
    win_rate = float((results["r_multiple"] > 0).mean())

    sub_positive = 0
    sub_detail = {}
    for sp, _, _ in SUBPERIODS:
        sub = results[results["subperiod"] == sp]
        n = len(sub)
        avg = float(sub["r_multiple"].mean()) if n else float("nan")
        positive = n >= 3 and avg > 0
        sub_detail[sp] = (n, avg, positive)
        if positive:
            sub_positive += 1

    if signals_per_year < 12 or avg_r < 0.2:
        classification = "KILL"
    elif signals_per_year >= 25 and avg_r >= 0.6 and sub_positive >= 2:
        classification = "PASS"
    else:
        classification = "WATCH"
    friction_flag = avg_r < 0.5

    return dict(
        total_signals=len(results), signals_per_year=round(signals_per_year, 1),
        avg_r=round(avg_r, 3), median_r=round(median_r, 3), win_rate=round(win_rate, 3),
        sub_positive=sub_positive, sub_detail=sub_detail, classification=classification,
        friction_flag=friction_flag,
    )


VARIANTS = [
    dict(name="baseline (repro check)", rr_mult=2.5, stop_lookback=10, max_hold=10, rs_roc_min=0.0, require_range_high=False),
    dict(name="V1: rr_mult=1.5", rr_mult=1.5, stop_lookback=10, max_hold=10, rs_roc_min=0.0, require_range_high=False),
    dict(name="V2: V1 + stop_lookback=15", rr_mult=1.5, stop_lookback=15, max_hold=10, rs_roc_min=0.0, require_range_high=False),
    dict(name="V3: V1+V2 + max_hold=15", rr_mult=1.5, stop_lookback=15, max_hold=15, rs_roc_min=0.0, require_range_high=False),
    dict(name="V4a: V1+V2+V3 + rs_roc_min=0.02", rr_mult=1.5, stop_lookback=15, max_hold=15, rs_roc_min=0.02, require_range_high=False),
    dict(name="V4b: V1+V2+V3 + RS top-of-60bar-range(0.8)", rr_mult=1.5, stop_lookback=15, max_hold=15, rs_roc_min=0.0, require_range_high=True, range_len=60, range_pct=0.8),
    # -- exploratory extras (isolate which single tweak helps most / stress harder filter) --
    dict(name="X1: V1 only (rr=1.5, stop=10, hold=10) + range-filter(0.8)", rr_mult=1.5, stop_lookback=10, max_hold=10, rs_roc_min=0.0, require_range_high=True, range_len=60, range_pct=0.8),
    dict(name="X2: baseline stop/hold + range-filter(0.9, tighter)", rr_mult=1.5, stop_lookback=10, max_hold=10, rs_roc_min=0.0, require_range_high=True, range_len=60, range_pct=0.9),
    dict(name="X3: rr=1.5 + range-filter(0.9) + rs_roc_min=0.02", rr_mult=1.5, stop_lookback=10, max_hold=10, rs_roc_min=0.02, require_range_high=True, range_len=60, range_pct=0.9),
]


def main():
    print("Loading cached data...")
    data = load_all_cached()
    print(f"Loaded {len(data)} tickers.")

    rows = []
    for v in VARIANTS:
        name = v["name"]
        kwargs = {k: val for k, val in v.items() if k != "name"}
        all_signals = []
        for ticker, df in data.items():
            try:
                sigs = scan_variant(df, ticker, strategy_id=f"STR-G-variant-{name}", **kwargs)
                all_signals.extend(sigs)
            except Exception as e:
                print(f"  ERROR {name} on {ticker}: {e}", file=sys.stderr)
        results = pd.DataFrame(all_signals)
        summary = summarize(results)
        summary["name"] = name
        summary["params"] = kwargs
        rows.append(summary)
        print(f"\n{'='*90}\n{name}\n{'='*90}")
        print(f"  params: {kwargs}")
        print(f"  signals={summary['total_signals']}  sig/yr={summary['signals_per_year']}  "
              f"avg_r={summary['avg_r']}  median_r={summary['median_r']}  win_rate={summary['win_rate']:.1%}  "
              f"sub_positive={summary['sub_positive']}/3  friction_flag={summary['friction_flag']}  "
              f"=> {summary['classification']}")
        for sp, _, _ in SUBPERIODS:
            n, avg, pos = summary["sub_detail"].get(sp, (0, float('nan'), False))
            print(f"    {sp:20s} n={n:5d}  avg_r={avg if n else float('nan'):+.3f}  positive={pos}")

    print(f"\n\n{'#'*100}\nSENSITIVITY SWEEP SUMMARY TABLE\n{'#'*100}")
    header = f"{'Variant':<45}{'Sig/Yr':>8}{'AvgR':>8}{'MedR':>8}{'WinR':>8}{'SubPos':>8}{'Friction':>10}{'Class':>8}"
    print(header)
    print("-" * len(header))
    for r in rows:
        friction = "FLAG" if r["friction_flag"] else "ok"
        print(f"{r['name']:<45}{r['signals_per_year']:>8.1f}{r['avg_r']:>8.3f}{r['median_r']:>8.3f}"
              f"{r['win_rate']:>8.1%}{r['sub_positive']:>7}/3{friction:>10}{r['classification']:>8}")

    return rows


if __name__ == "__main__":
    main()
