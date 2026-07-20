#!/usr/bin/env python3
"""
alert_publisher.py — HermesForge EPIC-009 (US-060)

Formats a trade setup signal as a rich Discord message and publishes it
(with chart image attachment) to the correct channel based on the
strategy's publish_channel frontmatter field.

Usage (smoke test / dry-run):
    python3 alert_publisher.py --smoke-test

Programmatic:
    from alert_publisher import publish_signal
    publish_signal(signal_dict, chart_path, publish_channel="stocks", dry_run=True)
"""

import sys
import datetime
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import config


def format_alert(signal_dict: dict) -> str:
    """Format a signal dict into the Discord alert message body (US-060 template)."""
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    direction = signal_dict.get("direction", "long")

    stop_pct = abs(entry - stop) / entry * 100
    reward = abs(target - entry)
    risk = abs(entry - stop)
    rr = reward / risk if risk else 0.0

    risk_pct = signal_dict.get("risk_pct", config.RISK_PCT_DEFAULT)
    account_size = config.EXAMPLE_ACCOUNT_SIZE
    dollar_risk = account_size * (risk_pct / 100)
    example_shares = int(dollar_risk / risk) if risk else 0

    strategy_name = signal_dict.get("strategy_name", signal_dict.get("strategy_id", "Strategy"))
    version = signal_dict.get("strategy_version", "1.0")
    confidence = signal_dict.get("confidence", "medium")
    key_conditions = signal_dict.get("key_conditions", "See strategy note for full criteria")
    subperiod = signal_dict.get("subperiod", "n/a")
    ticker = signal_dict["ticker"]

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    return (
        f"📊 **{strategy_name} v{version}** — {confidence} confidence\n\n"
        f"**{ticker}** · {direction} · Daily\n\n"
        f"📍 Entry:  ${entry:.2f}\n"
        f"🛑 Stop:   ${stop:.2f}  ({stop_pct:.1f}% risk)\n"
        f"🎯 Target: ${target:.2f}  (R:R {rr:.1f}:1)\n"
        f"💰 Size:   {risk_pct:.1f}% account risk → {example_shares} shares @ ${account_size:,}\n\n"
        f"**Signal:** {key_conditions}\n"
        f"**Regime:** {subperiod}\n\n"
        f"_Posted: {now} UTC_"
    )


def publish_signal(signal_dict: dict, chart_path: str, publish_channel: str,
                    dry_run: bool = False) -> dict:
    """
    Format and publish a signal alert.

    Returns a result dict: {status, target, message, chart_path}
    status is one of: 'dry_run', 'posted', 'error'
    """
    message = format_alert(signal_dict)

    if dry_run:
        return {
            "status": "dry_run",
            "target": f"({publish_channel} — not resolved in dry-run)",
            "message": message,
            "chart_path": chart_path,
        }

    try:
        target = config.get_channel_target(publish_channel)
    except ValueError as e:
        return {"status": "error", "target": None, "message": str(e), "chart_path": chart_path}

    # NOTE: actual posting is done by the caller (daily_publish.py, US-062)
    # via the Hermes send_message tool, since this module has no direct
    # Hermes tool access when run as a standalone script. This function
    # returns the fully-formed payload for the caller to dispatch.
    return {
        "status": "ready_to_post",
        "target": target,
        "message": f"{message}\n\nMEDIA:{chart_path}",
        "chart_path": chart_path,
    }


def _smoke_test():
    signal = {
        "ticker": "SPY",
        "direction": "short",
        "entry_price": 743.29,
        "stop_price": 750.00,
        "target_price": 720.00,
        "strategy_name": "MACD Histogram Divergence",
        "strategy_id": "STR-B-macd-histogram-divergence",
        "strategy_version": "1.1",
        "confidence": "medium",
        "key_conditions": "Bearish MACD line divergence confirmed, weekly filter neutral",
        "subperiod": "period3_current",
        "risk_pct": 1.0,
    }
    result = publish_signal(signal, "/tmp/chart_generator_smoke_test.png",
                             publish_channel="stocks", dry_run=True)
    assert result["status"] == "dry_run"
    assert "SPY" in result["message"]
    assert "Entry:  $743.29" in result["message"]
    print("✅ Smoke test passed — formatted message:\n")
    print(result["message"])


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    else:
        print(__doc__)
