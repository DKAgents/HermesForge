#!/usr/bin/env python3
"""
alert_publisher.py — HermesForge EPIC-009 (US-060, enhanced US-064)

Formats a trade setup signal as a rich Discord message — including a
quality/confidence tier and strategy-specific key-conditions bullets — and
returns a ready_to_post payload (with chart image attachment) for the
correct channel based on the strategy's publish_channel frontmatter field.

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


# ---------------------------------------------------------------------------
# Quality tier + key conditions: strategy-specific, built only from fields
# the scanners actually emit (see scripts/validation/scanners/*.py)
# ---------------------------------------------------------------------------

def _tier_and_conditions_macd_divergence(s: dict) -> tuple[str, str, list[str]]:
    """Strategy B — MACD Histogram Divergence."""
    conf_level = s.get("confirmation_level", "Level 1")
    macd_bars = s.get("macd_bars_above_zero", 0)
    narrowing_bars = s.get("narrowing_bars", 0)
    rsi_val = s.get("rsi_at_signal")

    conditions = [
        f"MACD trend maturity: {macd_bars} bars above/below zero (min 15)",
        f"Stage 1: histogram narrowing confirmed ({narrowing_bars} bars)",
        "Stage 2: MACD line divergence confirmed vs. prior swing",
    ]

    if conf_level == "Level 2":
        rsi_note = f"RSI {rsi_val}" if rsi_val is not None else "oscillator extreme"
        conditions.append(f"Oscillator corroboration: {rsi_note} — Level 2 full size")
        tier, label = "A", "High"
        met, total = 4, 4
    else:
        conditions.append("Oscillator corroboration: not met — Level 1 reduced size")
        tier, label = "B", "Medium"
        met, total = 3, 4

    tag = f"{tier} ({label})"
    return tag, f"{met}/{total}", conditions


def _tier_and_conditions_ma_pullback(s: dict) -> tuple[str, str, list[str]]:
    """Strategy A — MA Pullback with Fibonacci Entry (not yet publish-enabled)."""
    conditions = [
        "Price above 50/200-day MA (trend filter)",
        "Pullback within 38.2%-61.8% Fibonacci retracement zone",
        "RSI(14) crossed above 40 (entry trigger)",
    ]
    tag, ratio = "B (Medium)", "3/3"
    return tag, ratio, conditions


def _tier_and_conditions_breakout_volume(s: dict) -> tuple[str, str, list[str]]:
    """Strategy C — Breakout + Volume (not yet publish-enabled)."""
    volume_ratio = s.get("volume_ratio")
    conditions = [
        "Price closed above prior 20-bar high",
        f"Breakout volume: {volume_ratio:.1f}x 20-bar average (min 1.5x)" if volume_ratio else
        "Breakout volume >= 1.5x 20-bar average",
    ]
    tag, ratio = "B (Medium)", "2/2"
    return tag, ratio, conditions


def _tier_and_conditions_sr_reversal(s: dict) -> tuple[str, str, list[str]]:
    """Strategy D — Support/Resistance Role Reversal (not yet publish-enabled)."""
    conditions = [
        "Price pulled back to prior resistance zone (within 1%)",
        "Price reclaimed the level on the signal bar (role reversal confirmed)",
    ]
    tag, ratio = "B (Medium)", "2/2"
    return tag, ratio, conditions


def _tier_and_conditions_adaptive_trend(s: dict) -> tuple[str, str, list[str]]:
    """Strategy I — AdaptiveTrend (Momentum + ATR Trailing Stop)."""
    momentum = s.get("momentum", 0)
    atr_mult = s.get("atr_multiplier", 2.0)
    lookback = s.get("lookback", 10)
    direction = s.get("direction", "long")

    if direction == "short":
        trend_filter_text = "Price below SMA200 (trend filter confirmed)"
    else:
        trend_filter_text = "Price above SMA200 (trend filter confirmed)"

    conditions = [
        f"Momentum: {momentum:+.1%} over {lookback} bars (threshold: ±20%)",
        trend_filter_text,
        f"ATR trailing stop: {atr_mult:.1f}x ATR (alpha={atr_mult:.1f})",
        "Trailing stop exit (no fixed target — trend follows until stop hit)",
    ]

    # Tier based on momentum strength
    if abs(momentum) >= 0.40:
        tier, label = "A", "High"
        conditions.append(f"Strong momentum: {abs(momentum):.1%} >> 20% threshold — Level A full size")
    elif abs(momentum) >= 0.25:
        tier, label = "B", "Medium"
        conditions.append(f"Moderate momentum: {abs(momentum):.1%} — Level B standard size")
    else:
        tier, label = "C", "Low"
        conditions.append(f"Marginal momentum: {abs(momentum):.1%} — Level C reduced size")

    tag = f"{tier} ({label})"
    return tag, "4/4", conditions


def _tier_and_conditions_generic(s: dict) -> tuple[str, str, list[str]]:
    return "B (Medium)", "n/a", [s.get("key_conditions", "See strategy note for full criteria")]


def _tier_and_conditions_crosssectional(s: dict) -> tuple[str, str, list[str]]:
    """Strategy P — Cross-Sectional Factor Ranking."""
    direction = s.get("direction", "long")
    rank = s.get("rank", 0)
    composite_score = s.get("composite_zscore", 0)

    conditions = [
        f"Cross-sectional rank: {'top' if direction == 'long' else 'bottom'} quintile (#{rank} of 42)",
        f"Composite z-score: {composite_score:+.2f} (MOM12_1 + LIQUID + PRICEMOM)",
        "Monthly rebalance (21-bar cycle)",
        "1.5x ATR trailing stop",
    ]

    tier, label = "C", "Low"
    tag = f"{tier} ({label})"
    return tag, "4/4", conditions


TIER_PROFILES = {
    "STR-B-macd-histogram-divergence": _tier_and_conditions_macd_divergence,
    "STR-A-ma-pullback-fibonacci":     _tier_and_conditions_ma_pullback,
    "STR-C-breakout-volume":           _tier_and_conditions_breakout_volume,
    "STR-D-sr-role-reversal":          _tier_and_conditions_sr_reversal,
    "STR-I-adaptive-trend":           _tier_and_conditions_adaptive_trend,
    "STR-P-crosssectional":           _tier_and_conditions_crosssectional,
}


def get_quality_tier(signal_dict: dict) -> tuple[str, str, list[str]]:
    """
    Returns (tier_tag, met_ratio_str, key_conditions_list) for a signal,
    using the profile matched to strategy_id (falls back to generic).
    """
    strategy_id = signal_dict.get("strategy_id", "")
    fn = TIER_PROFILES.get(strategy_id, _tier_and_conditions_generic)
    return fn(signal_dict)


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------

def _tradingview_link(ticker: str, publish_channel: str) -> str:
    """Build a TradingView chart link for the ticker.
    Stocks: https://www.tradingview.com/chart/?symbol=AAPL
    Crypto: https://www.tradingview.com/chart/?symbol=BTCUSDT
    """
    if publish_channel == "crypto":
        symbol = f"{ticker}USDT"
    else:
        symbol = ticker
    return f"https://www.tradingview.com/chart/?symbol={symbol}"


def format_alert(signal_dict: dict) -> str:
    """Format a signal dict into the Discord alert message body.

    Template (consistent across all strategies):
      Strategy name + version | Confidence tier
      Ticker (TradingView link) | Direction | Timeframe
      Entry / Stop / Target / R:R
      Regime
      Key Conditions
      Chart (attached as MEDIA)
      Timestamp
    """
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    direction = signal_dict.get("direction", "long")
    direction_label = direction.capitalize()

    stop_pct = abs(entry - stop) / entry * 100 if entry else 0
    reward = abs(target - entry)
    risk = abs(entry - stop)
    rr = reward / risk if risk else 0.0

    strategy_name = signal_dict.get("strategy_name", signal_dict.get("strategy_id", "Strategy"))
    version = signal_dict.get("strategy_version", "1.0")
    ticker = signal_dict["ticker"]
    publish_channel = signal_dict.get("publish_channel", "stocks")

    tier_tag, met_ratio, conditions = get_quality_tier(signal_dict)
    conditions_block = "\n".join(f"• {c}" for c in conditions)

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    # Regime: use the regime field (set by portfolio_publish.py), fall back to subperiod
    regime = signal_dict.get("regime", signal_dict.get("subperiod", "unknown"))
    regime_label = regime.capitalize() if regime != "unknown" else "Unknown"
    benchmark = signal_dict.get("regime_benchmark", "")
    adx = signal_dict.get("regime_adx", "")
    extras = []
    if benchmark:
        extras.append(benchmark)
    if adx:
        extras.append(f"ADX {adx}")
    regime_str = regime_label
    if extras:
        regime_str += f" ({', '.join(extras)})"

    # TradingView link
    tv_url = _tradingview_link(ticker, publish_channel)

    # Format prices adaptively: small crypto prices need more decimals
    def _fmt_price(p):
        if abs(p) < 1.0:
            return f"${p:.6f}"
        elif abs(p) < 100.0:
            return f"${p:.4f}"
        else:
            return f"${p:.2f}"

    entry_str = _fmt_price(entry)
    stop_str = _fmt_price(stop)
    target_str = _fmt_price(target)

    return (
        f"📊 **{strategy_name} v{version}** | Confidence: {tier_tag}\n\n"
        f"**[{ticker}]({tv_url})** | {direction_label} | Daily\n\n"
        f"📍 Entry:  {entry_str}\n"
        f"🛑 Stop:   {stop_str}  ({stop_pct:.1f}% risk)\n"
        f"🎯 Target: {target_str}  (R:R {rr:.1f}:1)\n\n"
        f"**Regime:** {regime_str}\n\n"
        f"**Key Conditions:** ({met_ratio} met)\n{conditions_block}\n\n"
        f"_Posted: {now} UTC_"
    )


def publish_signal(signal_dict: dict, chart_path: str, publish_channel: str,
                    dry_run: bool = False) -> dict:
    """
    Format and publish a signal alert.

    Returns a result dict: {status, target, message, chart_path}
    status is one of: 'dry_run', 'ready_to_post', 'error'
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
        "ticker": "NVDA",
        "direction": "short",
        "entry_price": 875.00,
        "stop_price": 882.50,
        "target_price": 850.00,
        "strategy_name": "MACD Histogram Divergence",
        "strategy_id": "STR-B-macd-histogram-divergence",
        "strategy_version": "1.1",
        "confirmation_level": "Level 2",
        "macd_bars_above_zero": 22,
        "narrowing_bars": 3,
        "rsi_at_signal": 74.0,
        "subperiod": "period3_current",
    }
    result = publish_signal(signal, "/tmp/chart_generator_smoke_test_b.png",
                             publish_channel="stocks", dry_run=True)
    assert result["status"] == "dry_run"
    assert "NVDA" in result["message"]
    assert "Confidence: A (High)" in result["message"]
    assert "Entry:  $875.00" in result["message"]
    assert "tradingview.com" in result["message"]
    assert "Short" in result["message"]
    print("✅ Smoke test passed — formatted message:\n")
    print(result["message"])

    # Also verify the Level-1 (lower tier) path
    signal_l1 = dict(signal, confirmation_level="Level 1", macd_bars_above_zero=16)
    result_l1 = publish_signal(signal_l1, "/tmp/chart_generator_smoke_test_b.png",
                                publish_channel="stocks", dry_run=True)
    assert "Confidence: B (Medium)" in result_l1["message"]
    print("\n✅ Level 1 -> Tier B verified")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    else:
        print(__doc__)
