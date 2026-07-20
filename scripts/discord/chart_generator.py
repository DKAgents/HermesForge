#!/usr/bin/env python3
"""
chart_generator.py — HermesForge EPIC-009 (US-059, enhanced US-064)

Generates an annotated dark-theme candlestick chart PNG for a given trade
setup signal, tailored to the indicators/concepts the specific strategy
actually uses (not a generic MACD+RSI chart for every strategy).

Strategy chart profiles:
    STR-B-macd-histogram-divergence  -> MACD panel + RSI panel + divergence markers
    STR-A-ma-pullback-fibonacci      -> MA50/MA200 overlay + Fib retracement zone + RSI panel
    STR-C-breakout-volume            -> Volume panel (highlighted breakout bar) + breakout level line
    STR-D-sr-role-reversal           -> Support/resistance zone overlay only (price panel)
    (unknown strategy_id)            -> falls back to the generic MACD+RSI profile

Usage (smoke test):
    python3 chart_generator.py --smoke-test [--strategy a|b|c|d]

Programmatic:
    from chart_generator import generate_setup_chart
    path = generate_setup_chart(ticker, signal_dict, output_path)
"""

import sys
import pathlib
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
LOOKBACK_BARS = 60

COLOR_ENTRY = "#3fb950"
COLOR_STOP = "#f85149"
COLOR_TARGET = "#58a6ff"
COLOR_MARKER = "#e3b341"
COLOR_MA50 = "#f0883e"
COLOR_MA200 = "#a371f7"
COLOR_FIB_ZONE = "#f0883e"
COLOR_SR_ZONE = "#a371f7"


def _load_ohlcv(ticker: str) -> pd.DataFrame:
    """Load cached OHLCV parquet for a ticker. Raises if not cached."""
    path = CACHE_DIR / f"{ticker}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No cached data for {ticker} at {path}. "
            f"Run scripts/validation/fetch_data.py first."
        )
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume",
    })
    return df[["Open", "High", "Low", "Close", "Volume"]]


# ---------------------------------------------------------------------------
# Indicator helpers
# ---------------------------------------------------------------------------

def _macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def _rsi(close: pd.Series, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def _sma(close: pd.Series, period: int):
    return close.rolling(period).mean()


# ---------------------------------------------------------------------------
# Shared setup: base plot with entry/stop/target lines + labels + marker
# ---------------------------------------------------------------------------

def _base_plot(df: pd.DataFrame, dark_style, entry, stop, target, apds, hlines_extra_colors=None,
                panel_ratios=(4, 2), volume=True, volume_panel=None, title=""):
    hline_prices = [entry, stop, target]
    hline_colors = [COLOR_ENTRY, COLOR_STOP, COLOR_TARGET]
    if hlines_extra_colors:
        for price, color in hlines_extra_colors:
            hline_prices.append(price)
            hline_colors.append(color)

    hlines = dict(hlines=hline_prices, colors=hline_colors, linestyle="--", linewidths=1.2)

    kwargs = dict(
        type="candle",
        style=dark_style,
        hlines=hlines,
        volume=volume,
        panel_ratios=panel_ratios,
        figsize=(12, 8),
        returnfig=True,
        title=title,
    )
    if apds:
        kwargs["addplot"] = apds
    if volume_panel is not None:
        kwargs["volume_panel"] = volume_panel

    fig, axes = mpf.plot(df, **kwargs)
    ax = axes[0]
    ax.text(len(df) - 1, entry, f" Entry ${entry:.2f}", color=COLOR_ENTRY, fontsize=8, va="center", fontweight="bold")
    ax.text(len(df) - 1, stop, f" Stop ${stop:.2f}", color=COLOR_STOP, fontsize=8, va="center", fontweight="bold")
    ax.text(len(df) - 1, target, f" Target ${target:.2f}", color=COLOR_TARGET, fontsize=8, va="center", fontweight="bold")
    ax.axvline(x=len(df) - 1, color=COLOR_MARKER, linestyle=":", linewidth=1.2, alpha=0.8)
    return fig, axes


def _dark_style():
    return mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        rc={"figure.facecolor": "#0d1117", "axes.facecolor": "#0d1117",
            "savefig.facecolor": "#0d1117"},
    )


# ---------------------------------------------------------------------------
# Strategy B — MACD Histogram Divergence: MACD panel + RSI panel + markers
# ---------------------------------------------------------------------------

def _chart_macd_divergence(df_full, df, signal_dict, entry, stop, target, title):
    close_full = df_full["Close"]
    macd_line, signal_line, hist = _macd(close_full)
    rsi = _rsi(close_full)
    macd_line, signal_line, hist, rsi = (s.tail(LOOKBACK_BARS) for s in (macd_line, signal_line, hist, rsi))

    apds = [
        mpf.make_addplot(macd_line, panel=1, color="#58a6ff", width=1.0, ylabel="MACD"),
        mpf.make_addplot(signal_line, panel=1, color="#f0883e", width=1.0),
        mpf.make_addplot(hist, panel=1, type="bar", color="#484f58", alpha=0.5),
        mpf.make_addplot(rsi, panel=2, color="#a371f7", width=1.0, ylabel="RSI"),
    ]

    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds,
        panel_ratios=(4, 2, 2, 1.5), volume=True, volume_panel=3, title=title,
    )

    # Mark the two swing points being compared for divergence, if we have
    # the offset the scanner surfaced (prior_swing_bar_offset).
    signal_idx_in_window = len(df) - 1  # signal bar is always the last bar we trimmed to
    offset = signal_dict.get("prior_swing_bar_offset")
    if offset and 0 < offset < len(df):
        prior_idx = signal_idx_in_window - offset
        macd_ax = axes[2] if len(axes) > 2 else None  # MACD panel axis
        if macd_ax is not None and 0 <= prior_idx < len(macd_line):
            macd_ax.plot([prior_idx, signal_idx_in_window],
                         [macd_line.iloc[prior_idx], macd_line.iloc[-1]],
                         color=COLOR_MARKER, linestyle="-", linewidth=1.5, marker="o", markersize=4)

    return fig


# ---------------------------------------------------------------------------
# Strategy A — MA Pullback + Fibonacci: MA overlay + fib zone + RSI panel
# ---------------------------------------------------------------------------

def _chart_ma_pullback(df_full, df, signal_dict, entry, stop, target, title):
    close_full = df_full["Close"]
    ma50 = _sma(close_full, 50).tail(LOOKBACK_BARS)
    ma200 = _sma(close_full, 200).tail(LOOKBACK_BARS)
    rsi = _rsi(close_full).tail(LOOKBACK_BARS)

    apds = [
        mpf.make_addplot(ma50, color=COLOR_MA50, width=1.2),
        mpf.make_addplot(ma200, color=COLOR_MA200, width=1.2),
        mpf.make_addplot(rsi, panel=1, color="#a371f7", width=1.0, ylabel="RSI"),
    ]

    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds,
        panel_ratios=(4, 2, 1.5), volume=True, volume_panel=2, title=title,
    )

    # Shade the Fibonacci retracement zone (38.2%-61.8%) if swing high/low
    # info is available in the signal dict.
    swing_high = signal_dict.get("swing_high")
    swing_low = signal_dict.get("swing_low")
    if swing_high is not None and swing_low is not None:
        rng = swing_high - swing_low
        fib_382 = swing_high - 0.382 * rng
        fib_618 = swing_high - 0.618 * rng
        axes[0].axhspan(min(fib_382, fib_618), max(fib_382, fib_618),
                         color=COLOR_FIB_ZONE, alpha=0.12)
        axes[0].text(0, max(fib_382, fib_618), " Fib 38-62%", color=COLOR_FIB_ZONE, fontsize=7, va="bottom")

    return fig


# ---------------------------------------------------------------------------
# Strategy C — Breakout + Volume: volume panel with highlighted bar
# ---------------------------------------------------------------------------

def _chart_breakout_volume(df_full, df, signal_dict, entry, stop, target, title):
    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds=None,
        panel_ratios=(4, 1.5), volume=True, volume_panel=1, title=title,
    )

    # Draw the prior breakout level (20-bar high before the signal bar) as
    # an extra reference line if the scanner supplied it.
    breakout_level = signal_dict.get("breakout_level")
    if breakout_level is not None:
        axes[0].axhline(breakout_level, color="#8b949e", linestyle=":", linewidth=1.0)
        axes[0].text(0, breakout_level, " Prior 20-bar high", color="#8b949e", fontsize=7, va="bottom")

    # Highlight the breakout bar's volume in the volume panel if we can find it
    volume_ratio = signal_dict.get("volume_ratio")
    if volume_ratio is not None and len(axes) > 1:
        vol_ax = axes[1]
        vol_ax.text(0.02, 0.92, f"Breakout volume: {volume_ratio:.1f}x avg",
                    color="#3fb950", fontsize=8, transform=vol_ax.transAxes)

    return fig


# ---------------------------------------------------------------------------
# Strategy D — S/R Role Reversal: shaded S/R zone on price panel only
# ---------------------------------------------------------------------------

def _chart_sr_reversal(df_full, df, signal_dict, entry, stop, target, title):
    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds=None,
        panel_ratios=(4, 1.5), volume=True, volume_panel=1, title=title,
    )

    resistance_level = signal_dict.get("resistance_level")
    if resistance_level is not None:
        band = resistance_level * 0.01
        axes[0].axhspan(resistance_level - band, resistance_level + band,
                         color=COLOR_SR_ZONE, alpha=0.15)
        axes[0].text(0, resistance_level, " Old resistance -> new support", color=COLOR_SR_ZONE,
                     fontsize=7, va="bottom")

    return fig


# ---------------------------------------------------------------------------
# Generic fallback — original MACD+RSI layout, used for unknown strategy_id
# ---------------------------------------------------------------------------

def _chart_generic(df_full, df, signal_dict, entry, stop, target, title):
    return _chart_macd_divergence(df_full, df, signal_dict, entry, stop, target, title)


CHART_PROFILES = {
    "STR-B-macd-histogram-divergence": _chart_macd_divergence,
    "STR-A-ma-pullback-fibonacci":     _chart_ma_pullback,
    "STR-C-breakout-volume":           _chart_breakout_volume,
    "STR-D-sr-role-reversal":          _chart_sr_reversal,
}


def generate_setup_chart(ticker: str, signal_dict: dict, output_path: str) -> str:
    """
    Generate an annotated setup chart PNG, using the chart profile matched
    to signal_dict['strategy_id'] (falls back to the generic MACD+RSI
    profile for unrecognized strategy IDs).
    """
    df_full = _load_ohlcv(ticker)

    signal_date = pd.to_datetime(signal_dict["date"])
    df_full = df_full[df_full.index <= signal_date]
    if len(df_full) < 2:
        raise ValueError(f"Not enough bars for {ticker} up to {signal_date.date()}")

    df = df_full.tail(LOOKBACK_BARS).copy()

    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    strategy_name = signal_dict.get("strategy_name", signal_dict.get("strategy_id", "Strategy"))
    date_str = signal_date.strftime("%Y-%m-%d")
    title = f"\n{ticker} — {strategy_name} — {date_str}"

    strategy_id = signal_dict.get("strategy_id", "")
    chart_fn = CHART_PROFILES.get(strategy_id, _chart_generic)

    fig = chart_fn(df_full, df, signal_dict, entry, stop, target, title)

    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor="#0d1117")
    plt.close(fig)
    return str(out)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _smoke_test(strategy_key: str = "b"):
    base_signal = {
        "ticker": "SPY",
        "date": "2026-07-17",
        "direction": "short",
        "entry_price": 743.29,
        "stop_price": 750.00,
        "target_price": 720.00,
        "r_multiple": 3.47,
        "confirmation_level": "Level 1",
        "subperiod": "period3_current",
    }

    variants = {
        "b": {**base_signal, "strategy_id": "STR-B-macd-histogram-divergence",
              "strategy_name": "MACD Histogram Divergence", "strategy_version": "1.1",
              "prior_swing_bar_offset": 12},
        "a": {**base_signal, "strategy_id": "STR-A-ma-pullback-fibonacci",
              "strategy_name": "MA Pullback Fibonacci Entry", "strategy_version": "1.0",
              "direction": "long", "entry_price": 720.00, "stop_price": 710.00, "target_price": 760.00,
              "swing_high": 755.0, "swing_low": 690.0},
        "c": {**base_signal, "strategy_id": "STR-C-breakout-volume",
              "strategy_name": "Breakout Volume Trend", "strategy_version": "1.0",
              "direction": "long", "entry_price": 745.00, "stop_price": 738.00, "target_price": 770.00,
              "breakout_level": 740.0, "volume_ratio": 1.8},
        "d": {**base_signal, "strategy_id": "STR-D-sr-role-reversal",
              "strategy_name": "S/R Role Reversal", "strategy_version": "1.0",
              "direction": "long", "entry_price": 745.00, "stop_price": 738.00, "target_price": 765.00,
              "resistance_level": 743.0},
    }

    signal = variants[strategy_key]
    out_path = f"/tmp/chart_generator_smoke_test_{strategy_key}.png"
    result = generate_setup_chart("SPY", signal, out_path)
    p = pathlib.Path(result)
    assert p.exists(), "PNG was not created"
    assert p.stat().st_size > 10_000, "PNG suspiciously small"
    print(f"✅ Smoke test passed ({strategy_key}): {result} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        key = "b"
        if "--strategy" in sys.argv:
            key = sys.argv[sys.argv.index("--strategy") + 1]
            _smoke_test(key)
        else:
            for k in ("a", "b", "c", "d"):
                _smoke_test(k)
    else:
        print(__doc__)
