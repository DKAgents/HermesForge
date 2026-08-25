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

# Ensure intraday data modules are importable
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

COLOR_ENTRY = "#3fb950"
COLOR_STOP = "#f85149"
COLOR_TARGET = "#58a6ff"
COLOR_MARKER = "#e3b341"
COLOR_MA50 = "#f0883e"
COLOR_MA200 = "#a371f7"
COLOR_FIB_ZONE = "#f0883e"
COLOR_SR_ZONE = "#a371f7"


def _load_ohlcv(ticker: str) -> pd.DataFrame:
    """Load cached OHLCV parquet for a ticker. Checks the flat cache dir
    first, then falls back to the crypto/ subfolder (BTC/ETH/SOL etc. are
    cached there, not flat). Raises if not found in either location."""
    path = CACHE_DIR / f"{ticker}.parquet"
    if not path.exists():
        crypto_path = CACHE_DIR / "crypto" / f"{ticker}.parquet"
        if crypto_path.exists():
            path = crypto_path
        else:
            raise FileNotFoundError(
                f"No cached data for {ticker} at {path} or {crypto_path}. "
                f"Run scripts/validation/fetch_data.py first."
            )
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume",
    })
    return df[["Open", "High", "Low", "Close", "Volume"]]


def _load_intraday_ohlcv(ticker: str, asset_class: str, interval: str = "5m") -> pd.DataFrame:
    """Load intraday OHLCV data for charting.

    Uses the appropriate data source based on asset_class:
    - crypto: fetch_intraday_crypto.get_intraday_candles (Hyperliquid API)
    - stock:  fetch_intraday_stocks.get_intraday_bars (yfinance/Alpaca)

    Returns a DataFrame with datetime index and columns Open/High/Low/Close/Volume
    compatible with the daily _load_ohlcv() output.
    """
    lookback = LOOKBACK_BARS + 200  # enough for indicator computation + display window

    if asset_class == "crypto":
        from fetch_intraday_crypto import get_intraday_candles
        df = get_intraday_candles(ticker, interval, lookback_bars=lookback)
    else:
        from fetch_intraday_stocks import get_intraday_bars
        df = get_intraday_bars(ticker, interval, lookback_bars=lookback)

    if df is None or len(df) == 0:
        raise FileNotFoundError(
            f"No intraday data for {ticker} ({asset_class}, {interval}). "
            f"Run fetch_intraday_{'crypto' if asset_class == 'crypto' else 'stocks'} first."
        )

    df = df.copy()
    df = df.set_index("timestamp")
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


def _atr_for_chart(df: pd.DataFrame, period: int = 14):
    """Average True Range for chart overlays (Wilder's smoothing)."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()




def _add_legend(ax, items, loc="upper left"):
    """Add a labeled indicator legend box to an axes.
    items: list of (color, label) tuples.
    """
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=c, edgecolor=c, label=l, alpha=0.8) for c, l in items]
    leg = ax.legend(handles=handles, loc=loc, fontsize=6, framealpha=0.7,
                   facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9")
    return leg

# ---------------------------------------------------------------------------
# Shared setup: base plot with entry/stop/target lines + labels + marker
# ---------------------------------------------------------------------------

def _base_plot(df: pd.DataFrame, dark_style, entry, stop, target, apds, hlines_extra_colors=None,
                panel_ratios=(4, 2), volume=True, volume_panel=None, title="", signal_dict=None):
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
    # Signal bar index: use stored value or default to last bar
    sig_idx = signal_dict.get("_signal_bar_idx", len(df) - 1) if isinstance(signal_dict, dict) else len(df) - 1
    ax.text(len(df) - 1, entry, f" Entry ${entry:.2f}", color=COLOR_ENTRY, fontsize=8, va="center", fontweight="bold")
    ax.text(len(df) - 1, stop, f" Stop ${stop:.2f}", color=COLOR_STOP, fontsize=8, va="center", fontweight="bold")
    ax.text(len(df) - 1, target, f" Target ${target:.2f}", color=COLOR_TARGET, fontsize=8, va="center", fontweight="bold")
    ax.axvline(x=sig_idx, color=COLOR_MARKER, linestyle=":", linewidth=1.2, alpha=0.8)
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
        panel_ratios=(4, 2, 2, 1.5), volume=True, volume_panel=3, title=title, signal_dict=signal_dict,
    )

    # ── MACD panel: zero-line + maturity gate shading ──
    macd_vals = macd_line.values
    signal_val = macd_vals[-1]
    macd_ax = axes[2] if len(axes) > 2 else None
    if macd_ax is not None:
        # Zero-line
        macd_ax.axhline(0, color="#484f58", linewidth=0.8, linestyle="-")

        # Maturity gate shading: shade the region where MACD stayed on
        # the same side of zero for 15+ consecutive bars (the maturity gate).
        # Find the current run from the end of the window.
        side = 1 if signal_val > 0 else -1
        run_start = len(macd_vals) - 1
        for j in range(len(macd_vals) - 2, -1, -1):
            if (macd_vals[j] > 0) == (side > 0):
                run_start = j
            else:
                break
        run_len = len(macd_vals) - run_start
        if run_len >= 15:
            gate_color = "#3fb950" if side > 0 else "#f85149"
            macd_ax.axvspan(run_start, len(macd_vals) - 1,
                            color=gate_color, alpha=0.08)
            macd_ax.text(run_start + 1, macd_ax.get_ylim()[1] * 0.9,
                         f" Maturity: {run_len} bars",
                         color=gate_color, fontsize=7, va="top")

    # ── RSI panel: 70/30 overbought/oversold lines ──
    rsi_ax = axes[3] if len(axes) > 3 else None
    if rsi_ax is not None:
        rsi_ax.axhline(70, color="#f85149", linewidth=0.8, linestyle="--", alpha=0.6)
        rsi_ax.axhline(30, color="#3fb950", linewidth=0.8, linestyle="--", alpha=0.6)
        rsi_ax.axhline(50, color="#484f58", linewidth=0.5, linestyle=":", alpha=0.4)
        # Shade O/B and O/S zones
        rsi_ax.axhspan(70, 100, color="#f85149", alpha=0.06)
        rsi_ax.axhspan(0, 30, color="#3fb950", alpha=0.06)
        # RSI value at signal
        rsi_val = signal_dict.get("rsi_at_signal")
        if rsi_val is not None:
            rsi_ax.text(0.02, 0.95, f"RSI: {rsi_val:.1f}",
                        color="#a371f7", fontsize=8, transform=rsi_ax.transAxes,
                        fontweight="bold")
        # Label the RSI threshold lines
        rsi_ax.text(len(df) - 1, 70.5, " 70 OB", color="#f85149", fontsize=6, va="bottom")
        rsi_ax.text(len(df) - 1, 30.5, " 30 OS", color="#3fb950", fontsize=6, va="bottom")

    # Add indicator legend on MACD panel
    if macd_ax is not None:
        _add_legend(macd_ax, [
            ("#58a6ff", "MACD line"),
            ("#f0883e", "Signal line"),
            ("#484f58", "Histogram"),
            ("#e3b341", "Divergence"),
        ], loc="upper left")
    # Label zero line
    if macd_ax is not None:
        macd_ax.text(len(df) - 1, 0.5, " Zero", color="#484f58", fontsize=6, va="bottom")

    # Mark the two swing points being compared for divergence
    signal_idx_in_window = len(df) - 1
    offset = signal_dict.get("prior_swing_bar_offset")
    if offset and 0 < offset < len(df):
        prior_idx = signal_idx_in_window - offset
        if macd_ax is not None and 0 <= prior_idx < len(macd_line):
            macd_ax.plot([prior_idx, signal_idx_in_window],
                         [macd_line.iloc[prior_idx], macd_line.iloc[-1]],
                         color=COLOR_MARKER, linestyle="-", linewidth=1.5, marker="o", markersize=4)
            # Mark the prior swing point
            macd_ax.plot(prior_idx, macd_line.iloc[prior_idx],
                         marker="v" if signal_val > 0 else "^",
                         color=COLOR_MARKER, markersize=7, zorder=5)
            # Mark the current swing point
            macd_ax.plot(signal_idx_in_window, macd_line.iloc[-1],
                         marker="v" if signal_val > 0 else "^",
                         color=COLOR_MARKER, markersize=7, zorder=5)

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
        panel_ratios=(4, 2, 1.5), volume=True, volume_panel=2, title=title, signal_dict=signal_dict,
    )

    price_ax = axes[0]

    # ── Fibonacci retracement zone (38.2%-61.8%) + extension levels ──
    swing_high = signal_dict.get("swing_high")
    swing_low = signal_dict.get("swing_low")
    if swing_high is not None and swing_low is not None:
        rng = swing_high - swing_low
        fib_382 = swing_high - 0.382 * rng
        fib_618 = swing_high - 0.618 * rng
        # Retracement zone (38.2%-61.8%)
        price_ax.axhspan(min(fib_382, fib_618), max(fib_382, fib_618),
                         color=COLOR_FIB_ZONE, alpha=0.12)
        price_ax.text(0, max(fib_382, fib_618), " Fib 38-62%", color=COLOR_FIB_ZONE, fontsize=7, va="bottom")

        # Extension levels: 127.2% and 161.8% (for target projection)
        fib_ext_1272 = swing_low + 1.272 * rng
        fib_ext_1618 = swing_low + 1.618 * rng
        for level, label in [(fib_ext_1272, "Ext 127.2%"), (fib_ext_1618, "Ext 161.8%")]:
            price_ax.axhline(level, color="#8b949e", linewidth=0.8, linestyle=":", alpha=0.6)
            price_ax.text(len(df) - 1, level, f" {label}", color="#8b949e", fontsize=6, va="center")

        # 50% mid-line
        fib_50 = swing_high - 0.5 * rng
        price_ax.axhline(fib_50, color="#484f58", linewidth=0.5, linestyle=":", alpha=0.5)
        price_ax.text(0, fib_50, " 50%", color="#484f58", fontsize=6, va="bottom")

    # Add indicator legend on price panel
    _add_legend(price_ax, [
        (COLOR_MA50, "MA50"),
        (COLOR_MA200, "MA200"),
        (COLOR_FIB_ZONE, "Fib 38-62% zone"),
        ("#484f58", "Volume Profile"),
    ], loc="upper left")

    # ── Volume profile (horizontal bars on price panel) ──
    # Build a simple volume-at-price histogram from the visible window
    vol = df["Volume"] if "Volume" in df.columns else None
    if vol is not None:
        price_range = price_ax.get_ylim()
        n_bins = 20
        bin_edges = np.linspace(price_range[0], price_range[1], n_bins + 1)
        # Assign each bar's volume to price bins by its close price
        close_prices = df["Close"].values
        vols = vol.values
        bin_indices = np.digitize(close_prices, bin_edges) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        vol_at_price = np.zeros(n_bins)
        for bi, vv in zip(bin_indices, vols):
            vol_at_price[bi] += vv
        # Normalize to max bar width = 15% of chart width
        max_vol = vol_at_price.max() if vol_at_price.max() > 0 else 1
        bar_width = (len(df) * 0.15)
        x_start = len(df) - bar_width - 1
        for i in range(n_bins):
            w = (vol_at_price[i] / max_vol) * bar_width
            y_low = bin_edges[i]
            y_high = bin_edges[i + 1]
            price_ax.barh((y_low + y_high) / 2, w, height=(y_high - y_low) * 0.8,
                         left=x_start, color="#484f58", alpha=0.3, edgecolor="none")
        price_ax.text(x_start, price_range[1] * 0.98, " Vol Profile",
                     color="#8b949e", fontsize=6, va="top")

    # ── RSI panel: 70/30 lines ──
    rsi_ax = axes[2] if len(axes) > 2 else None
    if rsi_ax is not None:
        rsi_ax.axhline(70, color="#f85149", linewidth=0.8, linestyle="--", alpha=0.5)
        rsi_ax.axhline(30, color="#3fb950", linewidth=0.8, linestyle="--", alpha=0.5)
        rsi_ax.axhline(50, color="#484f58", linewidth=0.5, linestyle=":", alpha=0.4)
        rsi_ax.text(len(df) - 1, 70.5, " 70", color="#f85149", fontsize=6, va="bottom")
        rsi_ax.text(len(df) - 1, 30.5, " 30", color="#3fb950", fontsize=6, va="bottom")

    return fig


# ---------------------------------------------------------------------------
# Strategy C — Breakout + Volume: volume panel with highlighted bar
# ---------------------------------------------------------------------------

def _chart_breakout_volume(df_full, df, signal_dict, entry, stop, target, title):
    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds=None,
        panel_ratios=(4, 1.5), volume=True, volume_panel=1, title=title, signal_dict=signal_dict,
    )

    price_ax = axes[0]

    # ── 20-bar high/low channel ──
    highs = df["High"].rolling(20).max()
    lows = df["Low"].rolling(20).min()
    price_ax.plot(range(len(df)), highs.values, color="#3fb950",
                 linewidth=0.8, linestyle="--", alpha=0.5, label="20-bar high")
    price_ax.plot(range(len(df)), lows.values, color="#f85149",
                 linewidth=0.8, linestyle="--", alpha=0.5, label="20-bar low")
    # Shade the channel
    price_ax.fill_between(range(len(df)), highs.values, lows.values,
                         color="#30363d", alpha=0.1)
    # Label the channel
    price_ax.text(0, highs.values[-1], " 20-bar High", color="#3fb950", fontsize=6, va="bottom")
    price_ax.text(0, lows.values[-1], " 20-bar Low", color="#f85149", fontsize=6, va="top")

    # Add indicator legend
    _add_legend(price_ax, [
        ("#3fb950", "20-bar High channel"),
        ("#f85149", "20-bar Low channel"),
        ("#8b949e", "Breakout level"),
        ("#e3b341", "Breakout candle"),
    ], loc="upper left")

    # Draw the prior breakout level (20-bar high before the signal bar) as
    # an extra reference line if the scanner supplied it.
    breakout_level = signal_dict.get("breakout_level")
    if breakout_level is not None:
        price_ax.axhline(breakout_level, color="#8b949e", linewidth=1.2, linestyle=":", alpha=0.8)
        price_ax.text(0, breakout_level, " Breakout level", color="#8b949e", fontsize=7, va="bottom")
    else:
        # Compute from data: 20-bar high before signal bar
        if len(df) > 20:
            computed_level = df["High"].iloc[-21:-1].max()
            price_ax.axhline(computed_level, color="#8b949e", linewidth=1.2, linestyle=":", alpha=0.8)
            price_ax.text(0, computed_level, " Prior 20-bar high", color="#8b949e", fontsize=7, va="bottom")

    # ── Highlight the breakout candle (signal bar = last bar) ──
    signal_idx = len(df) - 1
    signal_high = df["High"].iloc[-1]
    signal_low = df["Low"].iloc[-1]
    price_ax.axvspan(signal_idx - 0.4, signal_idx + 0.4,
                    color="#e3b341", alpha=0.15)
    price_ax.text(signal_idx, signal_high * 1.01, " Breakout",
                 color="#e3b341", fontsize=7, ha="center", fontweight="bold")

    # Highlight the breakout bar's volume in the volume panel
    volume_ratio = signal_dict.get("volume_ratio")
    vol_ax = axes[1] if len(axes) > 1 else None
    if vol_ax is not None:
        # Highlight signal bar's volume
        vol_ax.axvspan(signal_idx - 0.4, signal_idx + 0.4,
                      color="#e3b341", alpha=0.15)
        if volume_ratio is not None:
            vol_ax.text(0.02, 0.92, f"Breakout volume: {volume_ratio:.1f}x avg",
                        color="#3fb950", fontsize=8, transform=vol_ax.transAxes,
                        fontweight="bold")
        else:
            # Compute from data
            if len(df) > 20:
                avg_vol = df["Volume"].iloc[-21:-1].mean()
                signal_vol = df["Volume"].iloc[-1]
                if avg_vol > 0:
                    ratio = signal_vol / avg_vol
                    vol_ax.text(0.02, 0.92, f"Breakout volume: {ratio:.1f}x avg",
                                color="#3fb950", fontsize=8, transform=vol_ax.transAxes,
                                fontweight="bold")

    return fig


# ---------------------------------------------------------------------------
# Strategy D — S/R Role Reversal: shaded S/R zone on price panel only
# ---------------------------------------------------------------------------

def _chart_sr_reversal(df_full, df, signal_dict, entry, stop, target, title):
    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds=None,
        panel_ratios=(4, 1.5), volume=True, volume_panel=1, title=title, signal_dict=signal_dict,
    )

    price_ax = axes[0]

    # ── Compute resistance level from data if not in signal dict ──
    # Scanner logic: max(high[i-60:i-20]) — 60 bars back, skip recent 20
    resistance_level = signal_dict.get("resistance_level")
    if resistance_level is None and len(df_full) >= 60:
        # Compute from full data up to signal date
        full_highs = df_full["High"]
        resist_end = len(full_highs) - 20  # exclude recent 20
        resist_start = max(0, len(full_highs) - 60)
        if resist_end > resist_start:
            resistance_level = float(full_highs.iloc[resist_start:resist_end].max())

    # ── Draw S/R zone overlay ──
    if resistance_level is not None:
        band = resistance_level * 0.01
        price_ax.axhspan(resistance_level - band, resistance_level + band,
                         color=COLOR_SR_ZONE, alpha=0.15)
        price_ax.axhline(resistance_level, color=COLOR_SR_ZONE, linewidth=1.0,
                        linestyle="--", alpha=0.7)
        price_ax.text(0, resistance_level + band, " Old Resistance -> New Support",
                     color=COLOR_SR_ZONE, fontsize=7, va="bottom")

        # ── Mark S/R touch points: bars that traded through the zone ──
        touch_band = band
        for i in range(len(df)):
            bar_high = df["High"].iloc[i]
            bar_low = df["Low"].iloc[i]
            # Bar touched the S/R zone if its range overlaps the zone
            if bar_high >= resistance_level - touch_band and bar_low <= resistance_level + touch_band:
                price_ax.plot(i, resistance_level, marker="_",
                             color="#e3b341", markersize=8, markeredgewidth=1.5,
                             zorder=5, alpha=0.7)
        # Label touch points
        price_ax.text(len(df) - 1, resistance_level + band * 2, " Touch points",
                     color="#e3b341", fontsize=6, va="bottom", alpha=0.7)

    # Add indicator legend
    _add_legend(price_ax, [
        (COLOR_SR_ZONE, "S/R zone (1% band)"),
        ("#e3b341", "Touch points"),
        ("#f85149", "ATR stop zone"),
        ("#58a6ff", "Target (next resistance)"),
    ], loc="upper left")

    # ── Next resistance target line ──
    # Target is already drawn by _base_plot as a blue hline, but let's label it
    price_ax.text(len(df) - 1, target, " Next Resistance",
                 color=COLOR_TARGET, fontsize=6, va="center")

    # ── ATR stop zone: shade between entry and stop ──
    direction = signal_dict.get("direction", "long")
    if direction == "long":
        price_ax.axhspan(stop, entry, color="#f85149", alpha=0.08)
    else:
        price_ax.axhspan(entry, stop, color="#f85149", alpha=0.08)
    price_ax.text(0.02, 0.02, f"ATR stop: ${stop:.2f}",
                 color="#f85149", fontsize=7, transform=price_ax.transAxes,
                 fontweight="bold")

    # ── Level age annotation ──
    level_age = signal_dict.get("level_age_bars")
    touch_depth = signal_dict.get("touch_depth_pct")
    info_parts = []
    if level_age:
        info_parts.append(f"Level age: {level_age} bars")
    if touch_depth:
        info_parts.append(f"Touch depth: {touch_depth:.2f}%")
    if info_parts:
        price_ax.text(0.02, 0.95, " | ".join(info_parts),
                     color="#a371f7", fontsize=7, transform=price_ax.transAxes,
                     fontweight="bold")

    # ── Highlight the signal bar (touch + reclaim) ──
    signal_idx = len(df) - 1
    price_ax.axvspan(signal_idx - 1.4, signal_idx + 0.4,
                    color="#e3b341", alpha=0.10)

    return fig


# ---------------------------------------------------------------------------
# Strategy Q — Liquidity Sweep: sweep level + wick marker + volume panel
# ---------------------------------------------------------------------------

def _chart_liquidity_sweep(df_full, df, signal_dict, entry, stop, target, title):
    """Chart profile for STR-Q liquidity sweep strategy.

    Shows the swept liquidity level as a horizontal line, the sweep wick
    highlighted, entry/stop/target lines, and a volume panel with the
    surge bar highlighted. Also draws an ATR band around the sweep level
    to visualize penetration depth.
    """
    close_full = df_full["Close"]
    rsi = _rsi(close_full).tail(LOOKBACK_BARS)
    atr_full = _atr_for_chart(df_full, 14)
    atr_window = atr_full.tail(LOOKBACK_BARS)

    apds = [
        mpf.make_addplot(rsi, panel=1, color="#a371f7", width=1.0, ylabel="RSI"),
    ]

    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds,
        panel_ratios=(4, 2, 1.5), volume=True, volume_panel=2, title=title, signal_dict=signal_dict,
    )

    price_ax = axes[0]

    # ── Draw the swept liquidity level ──
    level_price = signal_dict.get("level_price") or signal_dict.get("sweep_level_price")
    level_type = signal_dict.get("level_type", "unknown")
    if level_price is not None and level_price > 0:
        # Draw the level as a distinct line (different from entry/stop/target)
        price_ax.axhline(level_price, color="#e3b341", linewidth=1.5,
                        linestyle="-", alpha=0.8)
        price_ax.text(0, level_price, f" {level_type.replace('_', ' ').title()}",
                     color="#e3b341", fontsize=7, va="bottom", fontweight="bold")

        # Draw ATR penetration band around the level
        atr_val = signal_dict.get("penetration_atr", 0.5)
        atr_at_signal = signal_dict.get("atr_at_signal")
        if atr_at_signal and atr_at_signal > 0:
            pen_price = atr_val * atr_at_signal
        else:
            # Estimate from visible ATR
            pen_price = atr_val * (atr_window.iloc[-1] if len(atr_window) > 0 else 1.0)

        # Shade the penetration zone (where price went beyond the level)
        direction = signal_dict.get("direction", "long")
        if direction == "long":
            # Bullish sweep: price went below the level, then reversed up
            price_ax.axhspan(level_price - pen_price, level_price,
                            color="#f85149", alpha=0.10)
            price_ax.text(len(df) - 1, level_price - pen_price * 0.5,
                         f" Sweep zone ({atr_val:.2f} ATR)",
                         color="#f85149", fontsize=6, va="center")
        else:
            # Bearish sweep: price went above the level, then reversed down
            price_ax.axhspan(level_price, level_price + pen_price,
                            color="#f85149", alpha=0.10)
            price_ax.text(len(df) - 1, level_price + pen_price * 0.5,
                         f" Sweep zone ({atr_val:.2f} ATR)",
                         color="#f85149", fontsize=6, va="center")

    # ── Highlight the sweep candle (signal bar) ──
    signal_idx = signal_dict.get("_signal_bar_idx", len(df) - 1)
    if isinstance(signal_idx, (int, float)) and 0 <= signal_idx < len(df):
        sweep_high = df["High"].iloc[int(signal_idx)]
        sweep_low = df["Low"].iloc[int(signal_idx)]
        price_ax.axvspan(int(signal_idx) - 0.4, int(signal_idx) + 0.4,
                        color="#e3b341", alpha=0.15)
        # Mark the sweep wick with an arrow
        direction = signal_dict.get("direction", "long")
        if direction == "long":
            # Wick went below the level (bullish sweep)
            price_ax.annotate("Sweep", xy=(int(signal_idx), sweep_low),
                             xytext=(int(signal_idx) + 3, sweep_low - (sweep_high - sweep_low) * 0.5),
                             color="#e3b341", fontsize=7, fontweight="bold",
                             arrowprops=dict(arrowstyle="->", color="#e3b341", lw=1.2))
        else:
            # Wick went above the level (bearish sweep)
            price_ax.annotate("Sweep", xy=(int(signal_idx), sweep_high),
                             xytext=(int(signal_idx) + 3, sweep_high + (sweep_high - sweep_low) * 0.5),
                             color="#e3b341", fontsize=7, fontweight="bold",
                             arrowprops=dict(arrowstyle="->", color="#e3b341", lw=1.2))

    # ── Volume panel: highlight the surge bar ──
    vol_ax = axes[1] if len(axes) > 1 else None
    volume_surge = signal_dict.get("volume_surge", 0)
    if vol_ax is not None and volume_surge > 0:
        sig_idx_int = int(signal_idx) if isinstance(signal_idx, (int, float)) else len(df) - 1
        if 0 <= sig_idx_int < len(df):
            vol_ax.axvspan(sig_idx_int - 0.4, sig_idx_int + 0.4,
                          color="#3fb950", alpha=0.15)
            vol_ax.text(0.02, 0.92, f"Volume surge: {volume_surge:.1f}x avg",
                        color="#3fb950", fontsize=8, transform=vol_ax.transAxes,
                        fontweight="bold")

    # ── Quality score annotation ──
    quality_score = signal_dict.get("quality_score", 0)
    confirmation = signal_dict.get("confirmation", "confirmed")
    wick_ratio = signal_dict.get("wick_ratio", 0)
    if quality_score:
        price_ax.text(0.02, 0.95,
                     f"Q: {quality_score}/100 | {confirmation} | Wick: {wick_ratio:.1f}",
                     color="#58a6ff", fontsize=8, transform=price_ax.transAxes,
                     fontweight="bold")

    # ── RSI panel: 70/30 lines ──
    rsi_ax = axes[2] if len(axes) > 2 else None
    if rsi_ax is not None:
        rsi_ax.axhline(70, color="#f85149", linewidth=0.8, linestyle="--", alpha=0.5)
        rsi_ax.axhline(30, color="#3fb950", linewidth=0.8, linestyle="--", alpha=0.5)
        rsi_ax.axhline(50, color="#484f58", linewidth=0.5, linestyle=":", alpha=0.4)
        rsi_ax.text(len(df) - 1, 70.5, " 70", color="#f85149", fontsize=6, va="bottom")
        rsi_ax.text(len(df) - 1, 30.5, " 30", color="#3fb950", fontsize=6, va="bottom")

    # ── Legend ──
    _add_legend(price_ax, [
        ("#e3b341", f"{level_type.replace('_', ' ').title()} (swept)"),
        ("#f85149", "Sweep penetration zone"),
        (COLOR_ENTRY, "Entry"),
        (COLOR_STOP, "Stop (beyond wick)"),
        (COLOR_TARGET, "Target (3R)"),
    ], loc="upper left")

    return fig


# ---------------------------------------------------------------------------
# Generic fallback — original MACD+RSI layout, used for unknown strategy_id
# ---------------------------------------------------------------------------

def _chart_generic(df_full, df, signal_dict, entry, stop, target, title):
    return _chart_macd_divergence(df_full, df, signal_dict, entry, stop, target, title)


# ---------------------------------------------------------------------------
# Strategy I — Adaptive Trend: SMA200 overlay + momentum annotation
# ---------------------------------------------------------------------------

def _chart_adaptive_trend(df_full, df, signal_dict, entry, stop, target, title):
    close_full = df_full["Close"]
    sma200 = _sma(close_full, 200).tail(LOOKBACK_BARS)
    rsi = _rsi(close_full).tail(LOOKBACK_BARS)

    # Compute ATR and momentum for subpanels
    atr_full = _atr_for_chart(df_full, 14)
    atr_window = atr_full.tail(LOOKBACK_BARS)

    # Momentum: MOM_t = (P_t - P_{t-L}) / P_{t-L}
    lookback = signal_dict.get("lookback", 10)
    momentum_full = close_full.pct_change(periods=lookback)
    momentum_window = momentum_full.tail(LOOKBACK_BARS)

    # ATR trailing stop line: entry - alpha * ATR (for longs)
    atr_mult = signal_dict.get("atr_multiplier", 2.0)
    direction = signal_dict.get("direction", "long")
    if direction == "long":
        trailing_stop = close_full.tail(LOOKBACK_BARS) - atr_mult * atr_window
    else:
        trailing_stop = close_full.tail(LOOKBACK_BARS) + atr_mult * atr_window

    apds = [
        mpf.make_addplot(sma200, color=COLOR_MA200, width=1.2),
        mpf.make_addplot(rsi, panel=1, color="#a371f7", width=1.0, ylabel="RSI"),
        mpf.make_addplot(momentum_window, panel=2, color="#3fb950", width=1.0, ylabel="Momentum"),
        mpf.make_addplot(trailing_stop, color="#f85149", width=1.0, linestyle="--"),
    ]

    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds,
        panel_ratios=(4, 2, 2, 1.5), volume=True, volume_panel=3, title=title, signal_dict=signal_dict,
    )

    # ── Momentum panel: threshold lines + zero line ──
    mom_ax = axes[3] if len(axes) > 3 else None
    if mom_ax is not None:
        threshold = signal_dict.get("entry_threshold", 0.20)
        mom_ax.axhline(0, color="#484f58", linewidth=0.5, linestyle="-")
        mom_ax.axhline(threshold, color="#3fb950", linewidth=0.8, linestyle="--", alpha=0.6)
        mom_ax.axhline(-threshold, color="#f85149", linewidth=0.8, linestyle="--", alpha=0.6)
        # Shade the entry trigger zones
        mom_ax.axhspan(threshold, max(threshold * 3, momentum_window.max() * 1.1),
                       color="#3fb950", alpha=0.06)
        mom_ax.axhspan(-max(threshold * 3, abs(momentum_window.min()) * 1.1), -threshold,
                       color="#f85149", alpha=0.06)
        mom_ax.text(0.02, 0.95, f"Threshold: +/-{threshold:.0%}",
                    color="#e3b341", fontsize=7, transform=mom_ax.transAxes,
                    fontweight="bold")
        # Current momentum value
        mom_val = signal_dict.get("momentum", 0)
        if mom_val:
            mom_color = "#3fb950" if mom_val > 0 else "#f85149"
            mom_ax.text(0.98, 0.95, f"MOM: {mom_val:+.1%}",
                       color=mom_color, fontsize=8, transform=mom_ax.transAxes,
                       fontweight="bold", ha="right")

    # ── RSI panel: 70/30 lines ──
    rsi_ax = axes[2] if len(axes) > 2 else None
    if rsi_ax is not None:
        rsi_ax.axhline(70, color="#f85149", linewidth=0.8, linestyle="--", alpha=0.5)
        rsi_ax.axhline(30, color="#3fb950", linewidth=0.8, linestyle="--", alpha=0.5)

    # Label SMA200 and trailing stop on price panel
    _add_legend(axes[0], [
        (COLOR_MA200, "SMA200 (trend filter)"),
        ("#f85149", "ATR trailing stop"),
        ("#3fb950", "Momentum"),
        ("#a371f7", "RSI"),
    ], loc="upper left")
    axes[0].text(len(df) - 1, sma200.iloc[-1], " SMA200", color=COLOR_MA200, fontsize=6, va="center")

    # Label RSI 70/30
    if rsi_ax is not None:
        rsi_ax.text(len(df) - 1, 70.5, " 70", color="#f85149", fontsize=6, va="bottom")
        rsi_ax.text(len(df) - 1, 30.5, " 30", color="#3fb950", fontsize=6, va="bottom")

    # Label momentum threshold lines
    if mom_ax is not None:
        mom_ax.text(len(df) - 1, threshold + 0.01, f" +{threshold:.0%}", color="#3fb950", fontsize=6, va="bottom")
        mom_ax.text(len(df) - 1, -threshold - 0.01, f" -{threshold:.0%}", color="#f85149", fontsize=6, va="top")
        mom_ax.text(len(df) - 1, 0.01, " 0", color="#484f58", fontsize=6, va="bottom")

    # Annotate momentum + ATR on price panel
    momentum = signal_dict.get("momentum", 0)
    if momentum:
        axes[0].text(0.02, 0.95, f"Momentum: {momentum:+.1%} (L={lookback})",
                     color="#3fb950", fontsize=9, transform=axes[0].transAxes,
                     fontweight="bold")
    atr_val = signal_dict.get("atr_at_signal", 0)
    if atr_val:
        axes[0].text(0.02, 0.90, f"ATR(14): {atr_val:.4f} x{atr_mult:.1f}",
                     color="#f0883e", fontsize=8, transform=axes[0].transAxes)

    return fig


# ---------------------------------------------------------------------------
# Strategy P — Cross-Sectional Factor: SMA200 overlay + z-score annotation
# ---------------------------------------------------------------------------

def _chart_crosssectional(df_full, df, signal_dict, entry, stop, target, title):
    close_full = df_full["Close"]
    sma200 = _sma(close_full, 200).tail(LOOKBACK_BARS)

    # Compute ATR for stop zone shading
    high_full = df_full["High"]
    low_full = df_full["Low"]
    atr_full = _atr_for_chart(df_full, 14)
    atr_window = atr_full.tail(LOOKBACK_BARS)

    apds = [
        mpf.make_addplot(sma200, color=COLOR_MA200, width=1.2),
        mpf.make_addplot(atr_window, panel=1, color="#f0883e", width=1.0, ylabel="ATR(14)"),
    ]

    fig, axes = _base_plot(
        df, _dark_style(), entry, stop, target, apds,
        panel_ratios=(4, 2, 1.5), volume=True, volume_panel=2, title=title, signal_dict=signal_dict,
    )

    # ── ATR stop zone: shade between entry and stop ──
    price_ax = axes[0]
    direction = signal_dict.get("direction", "long")
    stop_color = "#f85149"
    if direction == "long":
        price_ax.axhspan(stop, entry, color=stop_color, alpha=0.08)
    else:
        price_ax.axhspan(entry, stop, color=stop_color, alpha=0.08)
    price_ax.text(0.02, 0.02, f"ATR stop: ${stop:.4f}",
                 color=stop_color, fontsize=7, transform=price_ax.transAxes,
                 fontweight="bold")

    # ── Factor decomposition mini-panel ──
    # Draw a small bar chart on the ATR panel showing the 3 factor scores
    factor_mom = signal_dict.get("factor_mom12_1", 0)
    factor_liq = signal_dict.get("factor_liquid", 0)
    factor_pm = signal_dict.get("factor_pricemom", 0)
    composite = signal_dict.get("composite_score", 0)
    rank = signal_dict.get("rank", 0)

    if any([factor_mom, factor_liq, factor_pm]):
        atr_ax = axes[2] if len(axes) > 2 else None
        if atr_ax is not None:
            # Add factor bar chart as inset axes
            from mpl_toolkits.axes_grid1.inset_locator import inset_axes
            inset = inset_axes(atr_ax, width="40%", height="60%", loc="upper right",
                              borderpad=0.8)
            factors = ["MOM12", "LIQUID", "PRICEMOM"]
            values = [factor_mom, factor_liq, factor_pm]
            colors_f = ["#58a6ff", "#3fb950", "#a371f7"]
            # Normalize for display (factors have very different scales)
            import numpy as np
            vals_arr = np.array(values, dtype=float)
            max_abs = max(abs(vals_arr).max(), 1e-9)
            norm_vals = vals_arr / max_abs
            bars = inset.barh(factors, norm_vals, color=colors_f, height=0.6)
            inset.set_title("Factor Z-Scores", fontsize=6, color="#c9d1d9")
            inset.tick_params(axis="both", labelsize=6, colors="#8b949e")
            inset.set_facecolor("#161b22")
            for spine in inset.spines.values():
                spine.set_color("#30363d")
            # Show actual values as text
            for bar, val in zip(bars, values):
                inset.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                          f"{val:.2f}", fontsize=5, color="#c9d1d9", va="center")

    # Add indicator legend on price panel
    _add_legend(price_ax, [
        (COLOR_MA200, "SMA200 (trend ref)"),
        ("#f0883e", "ATR(14)"),
        ("#f85149", "ATR stop zone (1.5x)"),
        ("#58a6ff", "Factor composite"),
    ], loc="upper left")
    price_ax.text(len(df) - 1, sma200.iloc[-1], " SMA200", color=COLOR_MA200, fontsize=6, va="center")

    # Annotate composite score and rank
    zscore_text = f"Composite: {composite:+.4f}"
    if rank:
        zscore_text += f" | Rank #{rank}/42"
    price_ax.text(0.02, 0.95, zscore_text,
                 color="#58a6ff", fontsize=9, transform=price_ax.transAxes,
                 fontweight="bold")

    return fig


CHART_PROFILES = {
    "STR-B-macd-histogram-divergence": _chart_macd_divergence,
    "STR-A-ma-pullback-fibonacci":     _chart_ma_pullback,
    "STR-C-breakout-volume":           _chart_breakout_volume,
    "STR-D-sr-role-reversal":          _chart_sr_reversal,
    "STR-I-adaptive-trend":           _chart_adaptive_trend,
    "STR-P-crosssectional":           _chart_crosssectional,
    "STR-Q-liquidity-sweep":          _chart_liquidity_sweep,
}


def generate_setup_chart(ticker: str, signal_dict: dict, output_path: str) -> str:
    """
    Generate an annotated setup chart PNG, using the chart profile matched
    to signal_dict['strategy_id'] (falls back to the generic MACD+RSI
    profile for unrecognized strategy IDs).

    Charts always show the most recent data available, not just up to the
    signal date. The signal bar is marked with a vertical line at its
    position within the visible window. The title shows the latest data date.

    For intraday signals (timeframe == "intraday"), loads 5m bar data from
    the appropriate intraday source (Hyperliquid for crypto, yfinance/Alpaca
    for stocks) instead of daily parquet cache.
    """
    # ── Determine timeframe and load correct data source ──
    timeframe = signal_dict.get("timeframe", "daily")
    bar_interval_label = "Daily"  # default

    if timeframe == "intraday":
        # Parse interval from subperiod (e.g. "intraday_5m" → "5m")
        subperiod = signal_dict.get("subperiod", "intraday_5m")
        interval = "5m"  # default
        if "intraday_" in str(subperiod):
            interval = str(subperiod).replace("intraday_", "")
        bar_interval_label = interval

        asset_class = signal_dict.get("asset_class", "crypto")
        df_full = _load_intraday_ohlcv(ticker, asset_class, interval)
    else:
        df_full = _load_ohlcv(ticker)

    signal_date = pd.to_datetime(signal_dict["date"])

    # Use ALL available data (not filtered to signal_date) so charts show
    # the most recent bars. Indicators are computed on the full dataset.
    if len(df_full) < 2:
        raise ValueError(f"Not enough bars for {ticker}")

    df = df_full.tail(LOOKBACK_BARS).copy()

    # Find the signal bar position within the visible window.
    # For intraday data, the signal_date is just a date ("2026-08-25") without
    # time, and the bars have full timestamps.  Since all bars in the intraday
    # window will be from the same day, the comparison still works correctly
    # (dates after midnight are > midnight).  When signal_date falls before all
    # window bars, the fallback sets signal_bar_idx to the last bar — which is
    # correct for real-time intraday signals.
    signal_dates_in_window = df.index[df.index <= signal_date]
    if len(signal_dates_in_window) > 0:
        # Count bars from signal date to end of window
        bars_after_signal = (df.index > signal_date).sum()
        signal_bar_idx = len(df) - 1 - int(bars_after_signal)
        signal_bar_idx = max(0, min(signal_bar_idx, len(df) - 1))
    else:
        signal_bar_idx = len(df) - 1  # fallback: signal at right edge

    # Store signal bar index for chart functions
    signal_dict["_signal_bar_idx"] = signal_bar_idx

    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    strategy_name = signal_dict.get("strategy_name", signal_dict.get("strategy_id", "Strategy"))
    # Title shows the latest data date + timeframe interval
    latest_date = pd.Timestamp(df.index[-1])
    date_str = latest_date.strftime("%Y-%m-%d")
    title = f"\n{ticker} — {strategy_name} — {bar_interval_label} — {date_str}"

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
