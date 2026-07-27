#!/usr/bin/env python3
"""
_test_sample_signals.py — one-off script to generate two SAMPLE/TEST trade
setup payloads (one stocks, one crypto) using the real EPIC-009 pipeline
(alert_publisher.format_alert + chart_generator.generate_setup_chart), based
on real cached OHLCV data, for the user to visually confirm the pipeline
works end-to-end. NOT wired into any cron. Clearly banner-marked as TEST in
the message body so nobody mistakes these for live signals.
"""
import sys
import pathlib
import datetime
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import alert_publisher
from chart_generator import generate_setup_chart

BANNER = (
    "\u26a0\ufe0f **TEST / SAMPLE SETUP \u2014 NOT A LIVE SIGNAL** \u26a0\ufe0f\n"
    "_This is a manually-generated test post to verify the alert pipeline. "
    "No trade action implied._\n\n"
)

CHART_OUT = pathlib.Path("/root/HermesForge/scripts/discord/_test_charts")
CHART_OUT.mkdir(exist_ok=True)


def build(ticker, parquet_path, entry, stop, target, direction, strategy_id,
          strategy_name, confirmation_level, macd_bars, narrowing_bars, rsi,
          publish_channel):
    df = pd.read_parquet(parquet_path)
    last_date = df.index[-1]

    signal = {
        "ticker": ticker,
        "direction": direction,
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "strategy_name": strategy_name,
        "strategy_id": strategy_id,
        "strategy_version": "1.1",
        "confirmation_level": confirmation_level,
        "macd_bars_above_zero": macd_bars,
        "narrowing_bars": narrowing_bars,
        "rsi_at_signal": rsi,
        "subperiod": "TEST_SAMPLE",
        "date": str(last_date.date()) if hasattr(last_date, "date") else str(last_date),
    }

    chart_path = CHART_OUT / f"TEST_{ticker}.png"
    generate_setup_chart(ticker, signal, str(chart_path))

    message = BANNER + alert_publisher.format_alert(signal)
    target_str_map = {"stocks": "discord:1528555538848153640",
                       "crypto": "discord:1528555885310513213"}
    return {
        "ticker": ticker,
        "channel": publish_channel,
        "target": target_str_map[publish_channel],
        "message": f"{message}\n\nMEDIA:{chart_path}",
        "chart_path": str(chart_path),
    }


def main():
    # --- Stock sample: NVDA, real last close 202.81 (2026-07-17) ---
    stock_payload = build(
        ticker="NVDA",
        parquet_path="/root/.hermes/market_data/NVDA.parquet",
        entry=202.81, stop=197.50, target=216.00,
        direction="long",
        strategy_id="STR-B-macd-histogram-divergence",
        strategy_name="MACD Histogram Divergence",
        confirmation_level="Level 2",
        macd_bars=22, narrowing_bars=3, rsi=58.0,
        publish_channel="stocks",
    )

    # --- Crypto sample: BTC, real last close range through 2026-07-20 ---
    crypto_payload = build(
        ticker="BTC",
        parquet_path="/root/.hermes/market_data/crypto/BTC.parquet",
        entry=64719.0, stop=63200.0, target=68500.0,
        direction="long",
        strategy_id="STR-B-macd-histogram-divergence",
        strategy_name="MACD Histogram Divergence",
        confirmation_level="Level 1",
        macd_bars=18, narrowing_bars=2, rsi=None,
        publish_channel="crypto",
    )

    import json
    print(json.dumps({"payloads": [stock_payload, crypto_payload]}, indent=2))


if __name__ == "__main__":
    main()
