#!/usr/bin/env python3
"""
chart_generator.py — HermesForge EPIC-009 (US-059)

Generates an annotated dark-theme candlestick chart PNG for a given trade
setup signal, for use in Discord alert publishing.

Usage (smoke test):
    python3 chart_generator.py --smoke-test

Usage (programmatic):
    from chart_generator import generate_setup_chart
    path = generate_setup_chart(ticker, signal_dict, output_path)
"""

import sys
import pathlib
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
LOOKBACK_BARS = 60


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
    # mplfinance requires capitalized OHLCV column names
    df = df.rename(columns={
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume",
    })
    return df[["Open", "High", "Low", "Close", "Volume"]]


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


def generate_setup_chart(ticker: str, signal_dict: dict, output_path: str) -> str:
    """
    Generate an annotated setup chart PNG.

    signal_dict keys used: date, entry_price, stop_price, target_price,
    strategy_id (or strategy_version), for the title/labels. See US-059 schema.
    """
    df_full = _load_ohlcv(ticker)

    signal_date = pd.to_datetime(signal_dict["date"])
    df_full = df_full[df_full.index <= signal_date]
    if len(df_full) < 2:
        raise ValueError(f"Not enough bars for {ticker} up to {signal_date.date()}")

    df = df_full.tail(LOOKBACK_BARS).copy()

    macd_line, signal_line, hist = _macd(df_full["Close"])
    rsi = _rsi(df_full["Close"])
    macd_line = macd_line.tail(LOOKBACK_BARS)
    signal_line = signal_line.tail(LOOKBACK_BARS)
    hist = hist.tail(LOOKBACK_BARS)
    rsi = rsi.tail(LOOKBACK_BARS)

    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    strategy_name = signal_dict.get("strategy_id", signal_dict.get("strategy_name", "Strategy"))
    date_str = signal_date.strftime("%Y-%m-%d")

    dark_style = mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        rc={"figure.facecolor": "#0d1117", "axes.facecolor": "#0d1117",
            "savefig.facecolor": "#0d1117"},
    )

    hlines = dict(
        hlines=[entry, stop, target],
        colors=["#3fb950", "#f85149", "#58a6ff"],
        linestyle="--",
        linewidths=1.2,
    )

    apds = [
        mpf.make_addplot(macd_line, panel=1, color="#58a6ff", width=1.0, ylabel="MACD"),
        mpf.make_addplot(signal_line, panel=1, color="#f0883e", width=1.0),
        mpf.make_addplot(hist, panel=1, type="bar", color="#484f58", alpha=0.5),
        mpf.make_addplot(rsi, panel=2, color="#a371f7", width=1.0, ylabel="RSI"),
    ]

    fig, axes = mpf.plot(
        df,
        type="candle",
        style=dark_style,
        addplot=apds,
        hlines=hlines,
        volume=True,
        volume_panel=3,
        panel_ratios=(4, 2, 2, 1.5),
        figsize=(12, 8),
        returnfig=True,
        title=f"\n{ticker} — {strategy_name} — {date_str}",
    )

    ax = axes[0]
    ax.text(len(df) - 1, entry, f" Entry ${entry:.2f}", color="#3fb950", fontsize=8, va="center")
    ax.text(len(df) - 1, stop, f" Stop ${stop:.2f}", color="#f85149", fontsize=8, va="center")
    ax.text(len(df) - 1, target, f" Target ${target:.2f}", color="#58a6ff", fontsize=8, va="center")

    # Vertical marker at signal bar (last bar in the window since we trimmed to signal_date)
    ax.axvline(x=len(df) - 1, color="#e3b341", linestyle=":", linewidth=1.2, alpha=0.8)

    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100, facecolor="#0d1117")
    plt.close(fig)
    return str(out)


def _smoke_test():
    signal = {
        "ticker": "SPY",
        "date": "2026-07-17",
        "direction": "short",
        "entry_price": 743.29,
        "stop_price": 750.00,
        "target_price": 720.00,
        "r_multiple": 3.47,
        "strategy_id": "STR-B-macd-histogram-divergence",
        "strategy_version": "1.1",
        "confirmation_level": "Level 1",
        "subperiod": "period3_current",
    }
    out_path = "/tmp/chart_generator_smoke_test.png"
    result = generate_setup_chart("SPY", signal, out_path)
    p = pathlib.Path(result)
    assert p.exists(), "PNG was not created"
    assert p.stat().st_size > 10_000, "PNG suspiciously small"
    print(f"✅ Smoke test passed: {result} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    else:
        print(__doc__)
