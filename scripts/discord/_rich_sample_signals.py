#!/usr/bin/env python3
"""
_rich_sample_signals.py — generate two RICH sample/test trade setup payloads
(one stocks, one crypto), built on real cached OHLCV data via the actual
EPIC-009 pipeline (alert_publisher + chart_generator), with extended
narrative context appended (catalyst, invalidation, sizing illustration,
correlated assets). Every payload is clearly and repeatedly marked as
SAMPLE — never to be read as a live signal.
"""
import sys
import pathlib
import json
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import alert_publisher
from chart_generator import generate_setup_chart
import config as pub_config

BANNER = (
    "🧪 **SAMPLE TRADE SETUP — FOR DEMONSTRATION ONLY, NOT A LIVE SIGNAL** 🧪\n"
    "_This is a manually-generated SAMPLE post to show the rich alert format. "
    "No trade action implied — do not act on this._\n\n"
)

FOOTER_REMINDER = "\n\n🧪 _Reminder: the setup above is a SAMPLE for formatting demonstration only._"

CHART_OUT = pathlib.Path("/root/HermesForge/scripts/discord/_test_charts")
CHART_OUT.mkdir(exist_ok=True)


def build(ticker, parquet_path, entry, stop, target, direction, strategy_id,
          strategy_name, confirmation_level, macd_bars, narrowing_bars, rsi,
          publish_channel, extra_context):
    df = pd.read_parquet(parquet_path)
    last_date = df.index[-1]
    last_date_str = str(pd.Timestamp(last_date).date())

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
        "subperiod": "SAMPLE_DEMO",
        "date": last_date_str,
    }

    chart_path = CHART_OUT / f"SAMPLE_{ticker}.png"
    generate_setup_chart(ticker, signal, str(chart_path))

    base_message = alert_publisher.format_alert(signal)

    # --- risk sizing illustration (1% account risk, per SOUL.md ceiling) ---
    account_size = pub_config.EXAMPLE_ACCOUNT_SIZE
    risk_pct = pub_config.RISK_PCT_DEFAULT
    risk_dollars = account_size * (risk_pct / 100)
    risk_per_share = abs(entry - stop)
    shares = int(risk_dollars / risk_per_share) if risk_per_share else 0
    position_value = shares * entry

    sizing_block = (
        f"\n\n**💰 Illustrative Position Sizing** (example ${account_size:,} account, "
        f"{risk_pct:.0f}% risk ceiling):\n"
        f"• Risk budget: ${risk_dollars:,.0f}\n"
        f"• Risk/unit: ${risk_per_share:,.2f}\n"
        f"• Illustrative size: {shares:,} units (~${position_value:,.0f} notional)\n"
        f"_Sizing shown for education only — always confirm against your own account "
        f"and risk rules before any real trade._"
    )

    extra_block = "\n\n" + extra_context

    message = BANNER + base_message + sizing_block + extra_block + FOOTER_REMINDER

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
    # --- Stock sample: AAPL, real last close 333.74 (2026-07-17) ---
    aapl_context = (
        "**🏢 Company/Sector Context (illustrative):**\n"
        "• Sector: Technology / Consumer Hardware\n"
        "• Recent price action: AAPL rallied from ~$314 (07-14) to ~$334 (07-17), "
        "+6.2% over 3 sessions — real cached data, shown for demo realism.\n"
        "• Illustrative catalyst: hypothetical product-cycle optimism into earnings.\n\n"
        "**🚫 Invalidation:** A daily close back below $317.50 (below the recent "
        "breakout base) would invalidate this sample thesis.\n\n"
        "**🔗 Correlated Watch:** QQQ, XLK (tech sector breadth) — sample context only."
    )
    stock_payload = build(
        ticker="AAPL",
        parquet_path="/root/.hermes/market_data/AAPL.parquet",
        entry=333.74, stop=322.00, target=360.00,
        direction="long",
        strategy_id="STR-B-macd-histogram-divergence",
        strategy_name="MACD Histogram Divergence",
        confirmation_level="Level 2",
        macd_bars=19, narrowing_bars=4, rsi=63.5,
        publish_channel="stocks",
        extra_context=aapl_context,
    )

    # --- Crypto sample: ETH, real last close 1874.5 (2026-07-20) ---
    eth_context = (
        "**⛓️ Market Context (illustrative):**\n"
        "• Recent price action: ETH consolidated $1,803–$1,929 over the last week "
        "(07-16 to 07-20) — real cached data, shown for demo realism.\n"
        "• Illustrative catalyst: hypothetical network-upgrade narrative + BTC "
        "correlation strength.\n\n"
        "**🚫 Invalidation:** A daily close below $1,800 (below the recent range low) "
        "would invalidate this sample thesis.\n\n"
        "**🔗 Correlated Watch:** BTC, SOL — sample context only, not a basket trade recommendation."
    )
    crypto_payload = build(
        ticker="ETH",
        parquet_path="/root/.hermes/market_data/crypto/ETH.parquet",
        entry=1874.5, stop=1795.0, target=2050.0,
        direction="long",
        strategy_id="STR-B-macd-histogram-divergence",
        strategy_name="MACD Histogram Divergence",
        confirmation_level="Level 1",
        macd_bars=15, narrowing_bars=2, rsi=None,
        publish_channel="crypto",
        extra_context=eth_context,
    )

    print(json.dumps({"payloads": [stock_payload, crypto_payload]}, indent=2))


if __name__ == "__main__":
    main()
