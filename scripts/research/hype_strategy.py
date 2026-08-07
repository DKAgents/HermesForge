#!/usr/bin/env python3
"""
hype_strategy.py — HermesForge Strategy H: Hype / Momentum Ignition (STR-H)
============================================================================

A long-only crypto "hype" strategy that proxies social-media attention spikes with
on-chart *volume acceleration*. Because we have no social-volume data (Twitter/X
mentions, Reddit, LunarCrush) under the free-data constraint, we substitute a
structurally similar proxy: a 3x volume spike over the 7-bar baseline combined
with a strong-close momentum-ignition candle. This is an honest limitation
documented in the validation report.

CRYPTO-ONLY. Hype is a crypto-native phenomenon. Stocks were tested and
discarded (negative out-of-sample edge). This strategy runs on the Hyperliquid
perpetual markets universe only.

Signal (ignition candle, bar i):
  - volume[i] > 3.0 x mean(volume[i-7 .. i-1])         # 7-bar baseline spike
  - (close[i] - low[i]) / (high[i] - low[i]) >= 0.75  # close in top 25% of range
  - volume[i] >= 2.0 x mean(volume[i-20 .. i-1])      # 20-bar volume expansion
  - Regime filter passes (BTC > SMA50)

Entry (scale-in, 2 tranches):
  - 50% at ignition close (bar i close).
  - 50% on first pullback to 8-EMA within the next 3 bars (fill at EMA8).
    If no pullback occurs, the remaining 50% is entered at market on bar i+3.
  - If the stop is hit before the 2nd tranche fills, the deployed 1st tranche is
    stopped out and the trade records R = -0.5 (dollar-accurate: half position,
    full stop on that half = 0.5R of the 0.5%-account risk budget).

Stop (long): swing low of the 5 bars preceding the ignition candle.

Exits (scanned bar-by-bar after entry completion):
  1. Stop loss (intrabar, gap-aware): low <= stop -> exit at stop (or open if gap).
  2. Hard exit: daily close < 21-EMA.
  3. Trailing exit: daily close < 8-EMA.
  4. Time stop: after 3 bars if the trade has NOT moved >= 2R in favor
     -> exit at that bar's close. Trades that have moved 2R keep trailing.
  5. Max-hold cap: 40 bars (backtest boundedness; exit at close).

Risk: 0.5% account risk per trade. Position size = (account * 0.005) / risk.
R-multiple = (exit - blended_entry) / (blended_entry - stop) for full trades.

Transaction costs: Crypto 5bp round-trip (2bp spread + 0.5bp commission x 2).

NOTE on timeframes: the spec calls for 4h crypto bars, but the project's cached
crypto data and Hyperliquid fetcher use daily bars. To stay within the free-data
+ existing-infra constraints, this version runs on daily bars. The strategy logic
is timeframe-agnostic.

USAGE:
    python3 hype_strategy.py            # run full walk-forward, write report+json
    python3 hype_strategy.py --json     # also dump JSON summary to stdout
    python3 hype_strategy.py --no-write # compute only, do not write files
"""

import sys
import json
import argparse
import pathlib
import datetime
import numpy as np
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

STRATEGY_ID = "STR-H-HYPE-IGNITION"

# ── Strategy parameters ──────────────────────────────────────────────────────
VOL_SPIKE_LOOKBACK  = 7      # baseline window for the 3x volume spike
VOL_SPIKE_MULT      = 3.0    # volume must exceed this multiple of 7-bar mean
VOL_20_MULT         = 2.0    # volume must exceed this multiple of 20-bar mean
VOL_20_LOOKBACK     = 20
CLOSE_RANGE_PCT     = 0.75   # close must be in top 25% of candle range
EMA_FAST            = 8      # trailing exit + pullback target
EMA_SLOW            = 21     # hard exit
SWING_LOOKBACK      = 5      # bars before ignition for swing-low stop
PULLBACK_WINDOW     = 3      # bars to wait for a pullback to EMA8
TIME_STOP_BARS_CRYPTO = 3
TIME_STOP_R         = 2.0    # if not +2R by time-stop, exit
MAX_HOLD_BARS       = 40
REGIME_SMA_CRYPTO   = 50     # BTC SMA(50)
RISK_PER_TRADE      = 0.005  # 0.5% account risk

# baseline health: require this many non-zero bars in the 7-bar window to
# avoid false spikes from Hyperliquid zero-volume daily bars (~42% are 0).
MIN_NONZERO_BASELINE = 4

# Transaction costs (match walk_forward.py)
COST_CRYPTO = (2.0 + 0.5) * 2 / 10000  # 5bp round trip


# ═════════════════════════════════════════════════════════════════════════════
# Strategy core
# ═════════════════════════════════════════════════════════════════════════════

def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def scan_ticker(df: pd.DataFrame, ticker: str, regime: pd.Series = None,
                asset_class: str = "crypto") -> list[dict]:
    """
    Scan one ticker's OHLCV for STR-H ignition signals. Returns a list of
    signal dicts in the HermesForge scanner convention (ticker, date,
    direction, entry_price, stop_price, target_price, exit_price,
    exit_reason, r_multiple, bars_held, strategy_id, ...).

    `regime` is an optional boolean pd.Series indexed by date (True = regime
    ON, trades allowed). When provided, signals are only emitted on dates
    where regime is True (aligned by YYYY-MM-DD).
    """
    df = df.copy().sort_index()
    if len(df) < max(EMA_SLOW, VOL_20_LOOKBACK) + 5:
        return []

    close = df["close"]; high = df["high"]; low = df["low"]
    vol  = df["volume"]; op   = df["open"]

    vol_mean_7  = vol.rolling(VOL_SPIKE_LOOKBACK).mean().shift(1)
    vol_mean_20 = vol.rolling(VOL_20_LOOKBACK).mean().shift(1)
    nonzero_7   = (vol > 0).rolling(VOL_SPIKE_LOOKBACK).sum().shift(1)
    ema8  = _ema(close, EMA_FAST)
    ema21 = _ema(close, EMA_SLOW)

    time_stop = TIME_STOP_BARS_CRYPTO
    cost_pct  = COST_CRYPTO

    a_c  = close.values.astype(float)
    a_h  = high.values.astype(float)
    a_l  = low.values.astype(float)
    a_v  = vol.values.astype(float)
    a_o  = op.values.astype(float)
    a_vm7  = vol_mean_7.values.astype(float)
    a_vm20 = vol_mean_20.values.astype(float)
    a_nz7  = nonzero_7.values.astype(float)
    a_e8   = ema8.values.astype(float)
    a_e21  = ema21.values.astype(float)
    dates = df.index
    n = len(df)

    # regime lookup set (dates where trading is allowed)
    regime_ok = None
    if regime is not None:
        regime_ok = set(regime.index[regime.values].strftime("%Y-%m-%d"))

    signals = []
    blocked_until = -1  # no new signals until this index (one trade per ticker)
    min_start = max(EMA_SLOW, VOL_20_LOOKBACK, SWING_LOOKBACK) + 2

    for i in range(min_start, n - 1):
        if i < blocked_until:
            continue
        # indicator warm-up / NaN guard
        if (np.isnan(a_vm7[i]) or np.isnan(a_vm20[i]) or np.isnan(a_e8[i])
                or np.isnan(a_e21[i]) or np.isnan(a_nz7[i])):
            continue
        # baseline health guard (skip degenerate zero-volume baselines)
        if a_nz7[i] < MIN_NONZERO_BASELINE:
            continue
        if a_vm7[i] <= 0 or a_vm20[i] <= 0:
            continue
        # regime filter
        if regime_ok is not None:
            if dates[i].strftime("%Y-%m-%d") not in regime_ok:
                continue
        # volume spike: > 3x 7-bar baseline
        if not (a_v[i] > VOL_SPIKE_MULT * a_vm7[i]):
            continue
        # strong close in top 25% of range
        rng = a_h[i] - a_l[i]
        if rng <= 0:
            continue
        if (a_c[i] - a_l[i]) / rng < CLOSE_RANGE_PCT:
            continue
        # volume expansion: >= 2x 20-bar average
        if not (a_v[i] >= VOL_20_MULT * a_vm20[i]):
            continue

        # ── Ignition confirmed at bar i ──
        first_entry = a_c[i]
        stop_price = float(np.min(a_l[i - SWING_LOOKBACK: i]))
        if stop_price >= first_entry:
            continue
        ref_risk = first_entry - stop_price  # for the 2R time-stop check

        # ── Scale-in: 2nd tranche (pullback to EMA8 within 3 bars) ──
        second_entry = None
        scale_done_idx = None
        early_stopped = False
        for k in range(1, PULLBACK_WINDOW + 1):
            j = i + k
            if j >= n:
                break
            # stop hit before 2nd tranche fills? (gap-aware)
            if a_l[j] <= stop_price:
                exit_px = stop_price if a_o[j] > stop_price else a_o[j]
                signals.append(_make_signal(
                    ticker, dates[i], "long",
                    entry_price=first_entry, stop_price=stop_price,
                    target_price=first_entry + 2.0 * ref_risk,
                    exit_price=exit_px, exit_reason="stop_pre_scalein",
                    r_multiple=-0.5, bars_held=k, asset_class=asset_class,
                    subperiod=_subperiod(dates[i], asset_class),
                ))
                blocked_until = j + 1
                early_stopped = True
                break
            # pullback to EMA8?
            if a_l[j] <= a_e8[j]:
                second_entry = a_e8[j]
                scale_done_idx = j
                break
        if early_stopped:
            continue
        # no pullback within window → market entry on bar i+PULLBACK_WINDOW
        if second_entry is None:
            j = min(i + PULLBACK_WINDOW, n - 1)
            # ensure j is a valid bar after i
            if j <= i:
                continue
            second_entry = a_c[j]
            scale_done_idx = j

        blended_entry = 0.5 * first_entry + 0.5 * second_entry
        risk = blended_entry - stop_price
        if risk <= 0:
            continue

        # ── Exits from bar after entry completion ──
        entry_complete = scale_done_idx
        max_high = float(a_h[entry_complete])
        exit_idx = None
        exit_price = None
        exit_reason = None
        for b in range(entry_complete + 1, n):
            if a_h[b] > max_high:
                max_high = float(a_h[b])
            lo, c = a_l[b], a_c[b]
            # 1) stop loss (intrabar, gap-aware)
            if lo <= stop_price:
                exit_price = stop_price if a_o[b] > stop_price else a_o[b]
                exit_idx, exit_reason = b, "stop"
                break
            # 2) hard exit: close below 21-EMA
            if c < a_e21[b]:
                exit_price, exit_idx, exit_reason = c, b, "hard_ema21"
                break
            # 3) trailing exit: close below 8-EMA
            if c < a_e8[b]:
                exit_price, exit_idx, exit_reason = c, b, "trail_ema8"
                break
            # 4) time stop
            bars_since = b - entry_complete
            moved_2r = max_high >= blended_entry + TIME_STOP_R * risk
            if bars_since >= time_stop and not moved_2r:
                exit_price, exit_idx, exit_reason = c, b, "time_stop"
                break
            # 5) max-hold cap
            if bars_since >= MAX_HOLD_BARS:
                exit_price, exit_idx, exit_reason = c, b, "max_hold"
                break

        if exit_idx is None:
            # still open at end of data → close at last close
            b = n - 1
            exit_price, exit_idx, exit_reason = float(a_c[b]), b, "eod"

        bars_held = exit_idx - entry_complete
        r = (exit_price - blended_entry) / risk
        # transaction cost in R (entry+exit ~ blended_entry level)
        cost_r = (blended_entry * cost_pct) / risk
        r -= cost_r

        signals.append(_make_signal(
            ticker, dates[i], "long",
            entry_price=blended_entry, stop_price=stop_price,
            target_price=blended_entry + 2.0 * risk,
            exit_price=exit_price, exit_reason=exit_reason,
            r_multiple=round(r, 4), bars_held=bars_held,
            asset_class=asset_class,
            subperiod=_subperiod(dates[i], asset_class),
            extra={
                "ignition_close": round(first_entry, 4),
                "second_entry": round(second_entry, 4),
                "cost_r": round(cost_r, 4),
                "scale_bars": scale_done_idx - i,
                "volume_spike_mult": round(a_v[i] / a_vm7[i], 2),
            },
        ))
        blocked_until = exit_idx + 1

    return signals


def _make_signal(ticker, date, direction, entry_price, stop_price,
                 target_price, exit_price, exit_reason, r_multiple,
                 bars_held, asset_class, subperiod="unknown", extra=None):
    sig = {
        "ticker": ticker,
        "date": date,
        "direction": direction,
        "entry_price": round(float(entry_price), 6),
        "stop_price": round(float(stop_price), 6),
        "target_price": round(float(target_price), 6),
        "exit_price": round(float(exit_price), 6),
        "exit_reason": exit_reason,
        "r_multiple": round(float(r_multiple), 4),
        "bars_held": int(bars_held),
        "strategy_id": STRATEGY_ID,
        "asset_class": asset_class,
        "confirmation_level": "Level 1",
        "subperiod": subperiod,
        "position_size_pct": RISK_PER_TRADE * 100,  # 0.5%
        "entry_status": "entered",
    }
    if extra:
        sig.update(extra)
    return sig


def _subperiod(date, asset_class):
    """Label the ADR-004 sub-period for a signal date."""
    if asset_class == "crypto":
        return "crypto_unlabeled"
    d = pd.Timestamp(date)
    if d >= pd.Timestamp("2024-01-01"):
        return "period3_current"
    if d >= pd.Timestamp("2022-01-01"):
        return "period2_bear"
    return "period1_bull"


# ═════════════════════════════════════════════════════════════════════════════
# Regime filters
# ═════════════════════════════════════════════════════════════════════════════

def crypto_regime(btc_df: pd.DataFrame) -> pd.Series:
    """BTC close > SMA(50) -> regime ON (bool, indexed by date)."""
    s = btc_df["close"].sort_index()
    sma = s.rolling(REGIME_SMA_CRYPTO).mean()
    return (s > sma).fillna(False)


# ═════════════════════════════════════════════════════════════════════════════
# Data loading
# ═════════════════════════════════════════════════════════════════════════════

def load_crypto_universe():
    """Load cached daily crypto data (+ BTC for regime)."""
    from fetch_crypto_data import load_all, load_symbol
    data = load_all()  # filters stale tickers
    try:
        btc = load_symbol("BTC")
    except FileNotFoundError:
        btc = None
    return data, btc


# ═════════════════════════════════════════════════════════════════════════════
# Statistics
# ═════════════════════════════════════════════════════════════════════════════

def compute_stats(signals: list[dict]) -> dict:
    """Compute trade-level statistics from a list of signal dicts."""
    if not signals:
        return {
            "n_trades": 0, "win_rate": 0.0, "mean_r": 0.0, "total_r": 0.0,
            "sharpe_per_trade": 0.0, "max_drawdown_r": 0.0,
            "avg_hold_bars": 0.0, "winners": 0, "losers": 0,
        }
    rs = np.array([s["r_multiple"] for s in signals], dtype=float)
    holds = np.array([s["bars_held"] for s in signals], dtype=float)
    n = len(rs)
    mean_r = float(np.mean(rs))
    total_r = float(np.sum(rs))
    wins = int(np.sum(rs > 0))
    win_rate = wins / n
    std_r = float(np.std(rs, ddof=1)) if n > 1 else 0.0
    sharpe = mean_r / std_r if std_r > 0 else 0.0  # per-trade, R-based

    # max drawdown on cumulative-R equity curve
    cum = np.cumsum(rs)
    running_max = np.maximum.accumulate(cum)
    dd = running_max - cum
    max_dd = float(np.max(dd)) if len(dd) else 0.0

    # exit-reason breakdown
    reasons = {}
    for s in signals:
        reasons[s["exit_reason"]] = reasons.get(s["exit_reason"], 0) + 1

    return {
        "n_trades": int(n),
        "winners": wins,
        "losers": int(n - wins),
        "win_rate": round(win_rate, 4),
        "mean_r": round(mean_r, 4),
        "total_r": round(total_r, 4),
        "std_r": round(std_r, 4),
        "sharpe_per_trade": round(sharpe, 4),
        "max_drawdown_r": round(max_dd, 4),
        "avg_hold_bars": round(float(np.mean(holds)), 2),
        "exit_reasons": reasons,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Walk-forward runner
# ═════════════════════════════════════════════════════════════════════════════

def _date_split_index(data: dict):
    """Return the cutoff date at the 70th percentile of the union of dates."""
    all_idx = pd.Index(sorted(set().union(*[set(df.index) for df in data.values()])))
    pos = int(0.70 * (len(all_idx) - 1))
    return all_idx[pos]


def run_walk_forward():
    """
    Load crypto data, build regime filter, scan every symbol, split
    signals 70/30 by date (train/test), and compute per-period stats.

    Returns a results dict ready to serialize.
    """
    print("=" * 72, file=sys.stderr)
    print("STR-H Hype / Momentum Ignition (Crypto-Only) - Walk-Forward Validation", file=sys.stderr)
    print("=" * 72, file=sys.stderr)

    # ── Load data ──
    print("\n[1] Loading crypto data...", file=sys.stderr)
    crypto_data, btc = load_crypto_universe()
    print(f"    Crypto: {len(crypto_data)} symbols", file=sys.stderr)

    # ── Regime filter ──
    print("\n[2] Building regime filter...", file=sys.stderr)
    c_reg = crypto_regime(btc) if btc is not None and len(btc) > REGIME_SMA_CRYPTO else None
    if c_reg is not None:
        print(f"    BTC regime ON: {int(c_reg.sum())}/{len(c_reg)} days "
              f"({c_reg.mean()*100:.1f}%)", file=sys.stderr)

    # ── Scan ──
    print("\n[3] Scanning crypto for ignition signals...", file=sys.stderr)
    crypto_signals = []
    for tkr, df in crypto_data.items():
        try:
            crypto_signals.extend(
                scan_ticker(df, tkr, regime=c_reg, asset_class="crypto"))
        except Exception as e:
            print(f"    [warn] {tkr}: {e}", file=sys.stderr)
    print(f"    Crypto signals: {len(crypto_signals)}", file=sys.stderr)

    # ── 70/30 train/test split by date ──
    print("\n[4] Splitting train/test (70/30 by date)...", file=sys.stderr)
    c_cut = _date_split_index(crypto_data) if crypto_data else None

    def split(sig, cut):
        if cut is None:
            return sig, []
        tr = [x for x in sig if pd.Timestamp(x["date"]) <= cut]
        te = [x for x in sig if pd.Timestamp(x["date"]) > cut]
        return tr, te

    c_train, c_test = split(crypto_signals, c_cut)

    print(f"    Crypto cutoff: {c_cut.date() if c_cut else 'n/a'}  "
          f"train={len(c_train)} test={len(c_test)}", file=sys.stderr)

    # ── Stats ──
    print("\n[5] Computing statistics...", file=sys.stderr)
    results = {
        "strategy_id": STRATEGY_ID,
        "strategy_name": "Hype / Momentum Ignition (crypto-only, long)",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "config": {
            "vol_spike_lookback": VOL_SPIKE_LOOKBACK,
            "vol_spike_mult": VOL_SPIKE_MULT,
            "vol_20_mult": VOL_20_MULT,
            "close_range_pct": CLOSE_RANGE_PCT,
            "ema_fast": EMA_FAST,
            "ema_slow": EMA_SLOW,
            "swing_lookback": SWING_LOOKBACK,
            "pullback_window": PULLBACK_WINDOW,
            "time_stop_bars_crypto": TIME_STOP_BARS_CRYPTO,
            "time_stop_r": TIME_STOP_R,
            "max_hold_bars": MAX_HOLD_BARS,
            "regime_sma_crypto": REGIME_SMA_CRYPTO,
            "risk_per_trade": RISK_PER_TRADE,
            "cost_crypto_bp": COST_CRYPTO * 10000,
            "direction": "long_only",
            "asset_class": "crypto_only",
            "timeframe_note": ("Daily bars used. Crypto spec called for 4h; "
                               "daily used due to cached free-data infra. "
                               "Logic is timeframe-agnostic."),
        },
        "universe": {
            "crypto_symbols": sorted(crypto_data.keys()),
            "n_crypto": len(crypto_data),
            "crypto_cutoff": str(c_cut.date()) if c_cut else None,
        },
        "crypto": {
            "train": compute_stats(c_train),
            "test":  compute_stats(c_test),
            "all":   compute_stats(crypto_signals),
        },
        "sample_trades": crypto_signals[:25],
    }

    _print_summary(results)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# Reporting
# ═════════════════════════════════════════════════════════════════════════════

def _fmt_stats(s: dict, label: str) -> str:
    if s["n_trades"] == 0:
        return (f"  {label:<14} n=0  (no trades)")
    return (f"  {label:<14} n={s['n_trades']:<4} win={s['win_rate']*100:5.1f}%  "
            f"meanR={s['mean_r']:+.3f}  totR={s['total_r']:+.2f}  "
            f"Sharpe={s['sharpe_per_trade']:+.2f}  maxDD={s['max_drawdown_r']:.2f}R  "
            f"hold={s['avg_hold_bars']:.1f}b")


def _print_summary(results: dict):
    print("\n" + "=" * 72, file=sys.stderr)
    print("STR-H WALK-FORWARD SUMMARY (CRYPTO-ONLY)", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print("\nCRYPTO (daily, BTC>SMA50 regime):", file=sys.stderr)
    print(_fmt_stats(results["crypto"]["train"], "train(70%)"), file=sys.stderr)
    print(_fmt_stats(results["crypto"]["test"],  "test(30%)"),  file=sys.stderr)
    print(_fmt_stats(results["crypto"]["all"],   "all(100%)"),  file=sys.stderr)
    print("\n" + "=" * 72, file=sys.stderr)


def build_markdown_report(results: dict) -> str:
    c_tr = results["crypto"]["train"]; c_te = results["crypto"]["test"]
    c_all = results["crypto"]["all"]
    cfg = results["config"]; uni = results["universe"]

    def row(d, label):
        if d["n_trades"] == 0:
            return f"| {label} | 0 | - | - | - | - | - | - |"
        return (f"| {label} | {d['n_trades']} | {d['win_rate']*100:.1f}% | "
                f"{d['mean_r']:+.3f} | {d['total_r']:+.2f} | "
                f"{d['sharpe_per_trade']:+.2f} | {d['max_drawdown_r']:.2f} | "
                f"{d['avg_hold_bars']:.1f} |")

    L = []
    L.append("# STR-H - Hype / Momentum Ignition - Walk-Forward Validation")
    L.append("")
    L.append(f"**Strategy ID:** `{results['strategy_id']}`  ")
    L.append(f"**Generated:** {results['generated_at']}  ")
    L.append(f"**Direction:** Long-only  ")
    L.append(f"**Asset class:** Crypto only  ")
    L.append(f"**Risk per trade:** {cfg['risk_per_trade']*100:.1f}% account  ")
    L.append(f"**Timeframe:** Daily bars (see note below)")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 1. Thesis")
    L.append("")
    L.append("Retail \"hype\" episodes (social-media-driven momentum) tend to ")
    L.append("leave a footprint in on-chart volume *before* the move is obvious. ")
    L.append("This strategy detects that footprint with a **volume acceleration** ")
    L.append("proxy and enters on the first pullback to the 8-EMA, trailing out ")
    L.append("behind the same EMA while a structural swing-low stop protects capital.")
    L.append("")
    L.append("## 2. Honest Limitations")
    L.append("")
    L.append("- **Social-volume proxy.** We have no social-media data (Twitter/X, ")
    L.append("  Reddit, LunarCrush) under the free-data constraint. The 3x 7-bar ")
    L.append("  volume spike is a structural proxy for attention-driven flow, but ")
    L.append("  it cannot distinguish organic hype from institutional rebalancing, ")
    L.append("  exchange listings, or news-driven volume. Treat results as ")
    L.append("  a *volume-momentum* strategy, not a confirmed social-sentiment strategy.")
    L.append("- **Timeframe deviation.** The spec calls for 4h crypto bars; the ")
    L.append("  project's cached free-data infrastructure (Hyperliquid fetcher + ")
    L.append("  parquet cache) uses daily bars. This run uses daily bars. ")
    L.append("  The strategy logic is timeframe-agnostic, so the daily results are a ")
    L.append("  lower-frequency (and more conservative) proxy for the 4h version.")
    L.append("- **Survivorship bias.** The crypto universe is the current set of ")
    L.append("  liquid Hyperliquid perpetual markets; previously delisted coins ")
    L.append("  (e.g. FTM, MATIC, RNDR, LUNA-class) were already excluded from the ")
    L.append("  cache. This is survivorship bias against failed projects, which is ")
    L.append("  *most acute for a hype strategy* since many hype-driven coins ")
    L.append("  subsequently went to zero.")
    L.append("- **Crypto volume quality.** ~42% of Hyperliquid daily bars report ")
    L.append("  zero volume. A baseline-health guard requires >=4 of the prior 7 bars ")
    L.append("  to have non-zero volume before a spike is counted, preventing false ")
    L.append("  spikes from degenerate zero-baselines.")
    L.append("- **Look-ahead-free.** All rolling means use `.shift(1)` so the ")
    L.append("  ignition bar never contaminates its own baseline. Entries/exits are ")
    L.append("  simulated on subsequent bars only.")
    L.append("")
    L.append("## 3. Signal Rules")
    L.append("")
    L.append(f"- **Volume spike:** `volume > {cfg['vol_spike_mult']}x mean(prior {cfg['vol_spike_lookback']} bars)`")
    L.append(f"- **Momentum ignition:** `(close-low)/(high-low) >= {cfg['close_range_pct']}` "
             f"(close in top 25% of range)")
    L.append(f"- **Volume expansion:** `volume >= {cfg['vol_20_mult']}x mean(prior 20 bars)`")
    L.append(f"- **Regime filter:** BTC > SMA({cfg['regime_sma_crypto']})")
    L.append("")
    L.append("## 4. Entry / Stop / Exit")
    L.append("")
    L.append("- **Scale-in:** 50% at ignition close; 50% on first pullback to 8-EMA "
             "within 3 bars (fill at EMA), else market on bar 3.")
    L.append(f"- **Stop:** swing low of the {cfg['swing_lookback']} bars preceding the "
             "ignition candle (structural, long-side).")
    L.append(f"- **Trailing exit:** daily close < 8-EMA.")
    L.append(f"- **Hard exit:** daily close < 21-EMA.")
    L.append(f"- **Time stop:** {cfg['time_stop_bars_crypto']} bars if the trade has not moved "
             f">= {cfg['time_stop_r']}R in favor.")
    L.append(f"- **Max-hold cap:** {cfg['max_hold_bars']} bars (backtest boundedness).")
    L.append(f"- **Costs:** crypto {cfg['cost_crypto_bp']:.0f}bp round-trip.")
    L.append("")
    L.append("## 5. Walk-Forward Results")
    L.append("")
    L.append("Split: train = first 70% of bars by date. test = last 30%.")
    L.append("")
    L.append("### Performance Table")
    L.append("")
    L.append("| Period | Trades | Win Rate | Mean R | Total R | Sharpe (per-trade) | Max DD (R) | Avg Hold (bars) |")
    L.append("|--------|--------|----------|--------|---------|--------------------|------------|-----------------|")
    L.append(row(c_tr,  "Crypto train"))
    L.append(row(c_te,  "Crypto test"))
    L.append(row(c_all, "Crypto all"))
    L.append("")
    L.append("### Exit-Reason Breakdown")
    L.append("")
    for label, d in [("Crypto train", c_tr), ("Crypto test", c_te),
                     ("Crypto all", c_all)]:
        L.append(f"**{label}** ({d['n_trades']} trades):")
        if d.get("exit_reasons"):
            items = sorted(d["exit_reasons"].items(), key=lambda x: -x[1])
            L.append("  " + " . ".join(f"{k}={v}" for k, v in items))
        else:
            L.append("  (no trades)")
        L.append("")
    L.append("## 6. Verdict")
    L.append("")
    def verdict(tr, te):
        if te["n_trades"] < 10:
            return "INSUFFICIENT SAMPLE (test < 10 trades) - no conclusion"
        if te["mean_r"] > 0.05 and te["win_rate"] >= 0.40:
            return ("POSITIVE OOS - test-period mean R positive with adequate hit rate; "
                    "candidate for forward paper-trading at reduced size.")
        if te["mean_r"] > 0:
            return ("MARGINAL OOS - test mean R positive but thin; monitor before "
                    "allocating capital.")
        return "NEGATIVE OOS - edge did not survive out-of-sample; do not trade."
    L.append(f"- **Crypto:** {verdict(c_tr, c_te)}")
    L.append("")
    L.append("> Sharpe here is **per-trade, R-based** (mean R / std R), not the "
             "annualized portfolio Sharpe. For an episodic event strategy, per-trade "
             "Sharpe is the honest unit; annualization would require an assumption "
             "about trade frequency that the data do not support.")
    L.append("")
    L.append("## 7. Survivorship & Data-Quality Notes (repeated for emphasis)")
    L.append("")
    L.append(f"- Crypto universe: **{uni['n_crypto']}** Hyperliquid markets (survivorship-biased).")
    L.append(f"- Crypto train/test cutoff: `{uni['crypto_cutoff']}`")
    L.append("- Delisted coins during the backtest window are excluded -> "
             "forward-looking survivorship bias, *most acute for a hype strategy* "
             "because many hyped assets subsequently collapsed to zero.")
    L.append("")
    return "\n".join(L)


# ═════════════════════════════════════════════════════════════════════════════
# Output / main
# ═════════════════════════════════════════════════════════════════════════════

REPORT_DIR = REPO_ROOT / "05-Research" / "Strategy-Validation"
MD_PATH  = REPORT_DIR / "STR-H-Hype-WalkForward.md"
JSON_PATH = REPORT_DIR / "STR-H-results.json"


def write_outputs(results: dict):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = build_markdown_report(results)
    MD_PATH.write_text(md, encoding="utf-8")
    # JSON: drop the (possibly large) sample_trades for the raw file? keep them.
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[written] {MD_PATH}", file=sys.stderr)
    print(f"[written] {JSON_PATH}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="STR-H Hype strategy walk-forward")
    ap.add_argument("--json", action="store_true", help="dump JSON summary to stdout")
    ap.add_argument("--no-write", action="store_true",
                    help="do not write report/json files")
    args = ap.parse_args()

    results = run_walk_forward()

    if not args.no_write:
        write_outputs(results)

    # stdout summary (always)
    print("\n--- STR-H RESULTS (stdout) ---")
    for label, d in [
        ("CRYPTO  train", results["crypto"]["train"]),
        ("CRYPTO  test",  results["crypto"]["test"]),
        ("CRYPTO  all",   results["crypto"]["all"]),
    ]:
        print(_fmt_stats(d, label))

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
