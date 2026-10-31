#!/usr/bin/env python3
"""
publisher_templates.py — Publisher-owned single source of truth for HermesForge
Discord publishing (H architecture).

This module is the ONLY place that formats a Discord message (setup embed,
exit/lifecycle alert, performance-report embed) or decides cross-posting.
Every other publisher script imports from here instead of duplicating template
or crosspost logic.

Public API:
    build_setup_embed(signal_dict, color=None, short_id="")   -> embed dict
    build_exit_message(trade, exit_info=None, event_type="STOP") -> str
    build_report_embed(report_text, color=None)               -> {"embeds":[...]}
    should_crosspost(channel_id)                              -> bool
    crosspost_message(payload, channel_id, chart_path=None, source_message_id=None)
    forward_all_channels(dry_run=False)                       -> cron batch forwarder

CROSSPOST_ALLOWLIST maps source channel ID -> crosspost-enabled (all enabled;
the principal's 2026-10-31 decision widens scope to ALL post types).

Crosspost scope (FINAL DECISION): setups, exits, paper-trading report,
research reports, strategy-status dashboard, heatmaps, and the daily market
briefing ALL cross-post. research_publisher.py / strategy_status.py /
post_heatmaps.py keep their existing crosspost; this module's allow-list
authorizes all 8 channels.
"""

import os
import json
import re
import sys
import time
import logging
import pathlib
import subprocess
import tempfile
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from timezone_utils import now_pt
from alert_publisher import get_quality_tier, _tradingview_link

# paper-trading helpers (trade_id) — no embed_publisher import, avoids a cycle
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
from trade_id import make_discord_link, make_discord_url

logger = logging.getLogger(__name__)

API_BASE = "https://discord.com/api/v10"

# ── Channel IDs (single source of truth for routing + crosspost) ──────────────
DISCORD_STOCK_SETUPS_CHANNEL = "1528555538848153640"
DISCORD_CRYPTO_SETUPS_CHANNEL = "1528555885310513213"
DISCORD_DAILY_BRIEFING_CHANNEL = "1532020053548208328"
DISCORD_STRATEGY_STATUS_CHANNEL = "1533332485641998386"
DISCORD_STRATEGY_RESEARCH_CHANNEL = "1534834809451450409"
DISCORD_PAPER_TRADING_CHANNEL = "1537225420120793088"
DISCORD_DAYTRADE_CRYPTO_CHANNEL = "1540951134200402071"
DISCORD_DAYTRADE_STOCK_CHANNEL = "1540951208028803142"

# Crosspost allow-list: source channel ID -> enabled. ALL 8 enabled (final decision).
CROSSPOST_ALLOWLIST = {
    DISCORD_STOCK_SETUPS_CHANNEL: True,       # #stock-setups
    DISCORD_CRYPTO_SETUPS_CHANNEL: True,      # #crypto-setups
    DISCORD_DAILY_BRIEFING_CHANNEL: True,     # #daily-market-briefing
    DISCORD_STRATEGY_STATUS_CHANNEL: True,    # #strategy-status
    DISCORD_STRATEGY_RESEARCH_CHANNEL: True,  # #strategy-research
    DISCORD_PAPER_TRADING_CHANNEL: True,      # #paper-trading
    DISCORD_DAYTRADE_CRYPTO_CHANNEL: True,    # #day-trade-crypto
    DISCORD_DAYTRADE_STOCK_CHANNEL: True,     # #day-trade-stocks
}

# Deduplication state shared by BOTH the real-time crosspost path and the cron
# forwarder, so a message cross-posted in real-time is never forwarded again
# (prevents double-posting). Same file the cron historically used.
STATE_FILE = pathlib.Path("/root/.hermes/crosspost_state.json")

WEBHOOK_NAME = "HermesForge Bot"


def should_crosspost(channel_id) -> bool:
    """Routing decision: is this source channel allowed to cross-post?"""
    return bool(CROSSPOST_ALLOWLIST.get(str(channel_id), False))


def get_webhook_url(channel_id) -> str:
    """Per-channel webhook URL from the environment ("" if unconfigured)."""
    return os.environ.get(f"CROSSPOST_WEBHOOK_{channel_id}", "")


# ── Day-of-week color ─────────────────────────────────────────────────────────
DAY_COLORS = {
    0: 0x3498db,  # Monday
    1: 0x2ecc71,  # Tuesday
    2: 0xe67e22,  # Wednesday
    3: 0x9b59b6,  # Thursday
    4: 0xe74c3c,  # Friday
    5: 0x1abc9c,  # Saturday
    6: 0xf1c40f,  # Sunday
}


def _get_day_color() -> int:
    return DAY_COLORS.get(now_pt().weekday(), 0x58a6ff)


def _fmt_price(p):
    p = float(p)
    if abs(p) < 1.0:
        return f"${p:.6f}"
    elif abs(p) < 100.0:
        return f"${p:.4f}"
    else:
        return f"${p:.2f}"


# ── Gauntlet G3 net R (after costs) — trader-pertinent, KEPT ─────────────────
def _estimated_net_r_embed(signal_dict: dict) -> str:
    """Short net R string for embed inline field display."""
    try:
        entry = float(signal_dict.get("entry_price", 0))
        stop = float(signal_dict.get("stop_price", 0))
        target = float(signal_dict.get("target_price", 0))
    except (ValueError, TypeError):
        return "N/A"
    if entry <= 0 or stop <= 0:
        return "N/A"
    risk_pct = abs(entry - stop) / entry
    if risk_pct <= 0:
        return "N/A"
    ac = signal_dict.get("asset_class", signal_dict.get("publish_channel", "crypto"))
    venue_cost_bps = 2.0 if ac == "stock" else 12.0
    cost_drag_r = (venue_cost_bps / 10000.0) / risk_pct
    reward = abs(target - entry)
    risk = abs(entry - stop)
    gross_rr = reward / risk if risk else 0
    net_rr = gross_rr - cost_drag_r
    return f"{net_rr:+.2f}R"


# ── Per-strategy confluence narrative — trader-pertinent, KEPT ────────────────
def _get_confluence(signal_dict: dict) -> str:
    """Human-readable explanation of how the strategy's indicators support the setup."""
    sid = signal_dict.get("strategy_id", "")
    direction = signal_dict.get("direction", "long")

    if "STR-B" in sid:
        return (
            "**MACD Divergence confluence:**\n"
            "\u2022 Price makes a new swing high but MACD makes a lower high \u2192 momentum is waning (the divergence)\n"
            "\u2022 MACD line crosses below signal line \u2192 entry trigger confirms the reversal\n"
            "\u2022 Maturity gate: MACD stayed above zero for 15+ bars \u2192 trend is mature, ripe for reversal\n"
            f"\u2022 RSI {'near 70 (overbought)' if direction == 'short' else 'near 30 (oversold)'} \u2192 confirms exhausted sentiment\n"
            "\u2022 ATR-based stop \u2192 volatility-adjusted risk, not a fixed percentage"
        )
    elif "STR-Q" in sid:
        level_type = signal_dict.get("level_type", "unknown")
        quality = signal_dict.get("quality_score", 0)
        sweep_dir = signal_dict.get("sweep_direction", "")
        return (
            "**Liquidity Sweep confluence:**\n"
            f"\u2022 Price swept {level_type} level then reversed \u2192 institutional liquidity grab confirmed\n"
            f"\u2022 Sweep direction: {sweep_dir} \u2192 alignment with trade direction\n"
            f"\u2022 Quality score: {quality}/100 \u2192 data-driven scoring (level type weighted)\n"
            "\u2022 Stop behind sweep wick \u2192 tight risk, minimal adverse excursion\n"
            "\u2022 3R target \u2192 favorable risk-reward ratio\n"
            "\u2022 5-minute intraday execution \u2192 precise timing, post-sweep entry"
        )
    elif "STR-R" in sid:
        jaw = signal_dict.get("alligator_jaw", 0)
        teeth = signal_dict.get("alligator_teeth", 0)
        lips = signal_dict.get("alligator_lips", 0)
        direction = signal_dict.get("direction", "long")
        fan_order = "Lips > Teeth > Jaw" if direction == "long" else "Lips < Teeth < Jaw"
        return (
            "**Williams Alligator confluence:**\n"
            f"\u2022 Alligator lines fanning in {fan_order} \u2192 trend awakening confirmed\n"
            f"\u2022 Jaw (SMMA 13)={jaw:.2f}, Teeth (SMMA 8)={teeth:.2f}, Lips (SMMA 5)={lips:.2f}\n"
            "\u2022 Lines were sleeping (tangled) within last 5 bars \u2192 catching the awakening, not a mature trend\n"
            "\u2022 Lines are spreading (gap increasing) \u2192 momentum is building\n"
            "\u2022 Price in front of Alligator's mouth (beyond Lips) \u2192 trend is real\n"
            "\u2022 1.5 ATR stop, 3R target \u2192 volatility-adjusted risk with favorable R:R"
        )
    elif "STR-P" in sid:
        mom = signal_dict.get("factor_mom12_1", 0)
        liq = signal_dict.get("factor_liquid", 0)
        pm = signal_dict.get("factor_pricemom", 0)
        composite = signal_dict.get("composite_score", 0)
        rank = signal_dict.get("rank", "?")
        return (
            "**Cross-Sectional Factor confluence:**\n"
            f"\u2022 MOM12_1 = {mom:+.2f} \u2192 12-month momentum ranking, persistent trend signal\n"
            f"\u2022 LIQUID = ${liq/1e6:.0f}M \u2192 high dollar volume = institutional interest & liquidity\n"
            f"\u2022 PRICEMOM = {pm:+.2f} \u2192 price relative to SMA200, trend confirmation\n"
            f"\u2022 Composite score = {composite:+.2f}, ranked #{rank}/42 \u2192 top/bottom quintile selection\n"
            "\u2022 ATR(14)-based stop (1.5x) \u2192 volatility-adjusted risk for ranging regime"
        )
    elif "STR-I" in sid:
        mom = signal_dict.get("momentum", 0)
        threshold = signal_dict.get("entry_threshold", 0.20)
        atr_mult = signal_dict.get("atr_multiplier", 2.0)
        lookback = signal_dict.get("lookback", 10)
        return (
            "**AdaptiveTrend confluence:**\n"
            f"\u2022 Momentum ({lookback}-bar) = {mom:+.1%} \u2192 exceeds +/-{threshold:.0%} entry threshold\n"
            "\u2022 Price above/below SMA200 \u2192 trend filter confirms direction\n"
            f"\u2022 ATR(14) trailing stop at {atr_mult:.1f}x \u2192 adaptive risk that ratchets with the trend\n"
            "\u2022 RSI context \u2192 identifies overbought/oversold conditions at entry\n"
            "\u2022 Time stop at 120 bars \u2192 prevents capital lockup in sideways drift"
        )
    elif "STR-A" in sid:
        return (
            "**MA Pullback + Fibonacci confluence:**\n"
            "\u2022 Price pulls back to MA50 \u2192 mean reversion within an established trend\n"
            "\u2022 MA50 above MA200 \u2192 trend alignment confirms bullish bias\n"
            "\u2022 Price enters Fibonacci 38-62% retracement zone \u2192 natural support area\n"
            "\u2022 Fibonacci extensions (127.2%, 161.8%) \u2192 projected target levels\n"
            "\u2022 RSI near 30/50 \u2192 oversold or neutral, room to bounce\n"
            "\u2022 Volume profile \u2192 high-volume nodes act as support/resistance"
        )
    elif "STR-C" in sid:
        vr = signal_dict.get("volume_ratio", 0)
        return (
            "**Breakout + Volume confluence:**\n"
            "\u2022 Price breaks above 20-bar high \u2192 breakout from established range\n"
            f"\u2022 Volume = {vr:.1f}x average \u2192 institutional participation confirms the breakout\n"
            "\u2022 20-bar high/low channel \u2192 defines the volatility range that was broken\n"
            "\u2022 Prior 20-bar high becomes new support \u2192 role reversal for stop placement\n"
            "\u2022 Breakout candle highlighted \u2192 the specific bar that triggered the signal"
        )
    elif "STR-D" in sid:
        age = signal_dict.get("level_age_bars", 0)
        depth = signal_dict.get("touch_depth_pct", 0)
        return (
            "**S/R Role Reversal confluence:**\n"
            "\u2022 Prior resistance level (max high 60 bars back, excluding recent 20) \u2192 established ceiling\n"
            "\u2022 Price pulls back to the level \u2192 tests whether old resistance holds as new support\n"
            "\u2022 Close above the level \u2192 two-bar reclaim confirms support\n"
            f"\u2022 Level age: {age} bars \u2192 older levels carry more structural weight\n"
            f"\u2022 Touch depth: {depth:.2f}% \u2192 precision of the pullback to the level\n"
            "\u2022 ATR(14) stop below support \u2192 gives the level one ATR of breathing room\n"
            "\u2022 Target = next resistance above \u2192 the next ceiling from prior 100 bars"
        )
    return ""


def _build_g3_fill_field(signal_dict: dict) -> dict:
    """G3 fill-simulation field (trader-pertinent execution realism)."""
    pessimistic_slip = signal_dict.get("gauntlet_pessimistic_slip")
    if pessimistic_slip is not None:
        slip_str = f"{pessimistic_slip:.1f} bps"
        book_mid = signal_dict.get("gauntlet_book_mid")
        if book_mid:
            slip_str += f" (mid: ${book_mid:,.2f})"
        return {"name": "\u26a1 G3 Fill", "value": f"Sim: {slip_str}", "inline": True}
    return {"name": "\u26a1 G3 Fill", "value": "N/A", "inline": True}


# ── SETUP EMBED (single tight template; swing + intraday) ─────────────────────
# FINAL DECISION: KEEP Net R (after costs), Regime, Key Conditions,
# Indicator Confluence, Options Ideas, Sweep Details.  REMOVE only non-trader
# internal markers: "[GAUNTLET]" prefix, strategy version strings, the
# "Pessimistic fills + cost-adjusted" footer, and server-health telemetry.

def build_setup_embed(signal_dict: dict, color: int = None, short_id: str = "") -> dict:
    """Build a standardized Discord embed for a trade setup (swing or sweep).

    Same field order everywhere; only field *content* differs between swing
    and intraday (STR-Q) setups.
    """
    ticker = signal_dict.get("ticker", "?")
    direction = signal_dict.get("direction", "long")
    strategy_id = signal_dict.get("strategy_id", "")
    is_sweep = ("STR-Q" in strategy_id) or bool(signal_dict.get("level_type"))

    if color is None:
        color = _get_day_color()

    id_line = f" | \U0001f516 Trade ID: `{short_id}`" if short_id else ""

    if is_sweep:
        return _build_sweep_embed(signal_dict, color, id_line)

    # ── Swing (daily) setup ──
    direction_label = direction.capitalize()
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    strategy_name = signal_dict.get("strategy_name", "Strategy")
    publish_channel = signal_dict.get("publish_channel", "stocks")

    tv_url = _tradingview_link(ticker, publish_channel)

    entry_str = _fmt_price(entry)
    stop_pct = abs(entry - stop) / entry * 100 if entry else 0
    stop_str = _fmt_price(stop)
    target_str = _fmt_price(target)
    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr = reward / risk if risk else 0.0

    regime = signal_dict.get("regime", "unknown")
    regime_label = regime.capitalize() if regime != "unknown" else "Unknown"
    benchmark = signal_dict.get("regime_benchmark", "")
    adx = signal_dict.get("regime_adx", "")
    regime_str = regime_label
    extras = []
    if benchmark:
        extras.append(benchmark)
    if adx:
        extras.append(f"ADX {adx}")
    if extras:
        regime_str += f" ({', '.join(extras)})"

    tier_tag, met_ratio, conditions = get_quality_tier(signal_dict)
    conditions_text = "\n".join(f"\u2022 {c}" for c in conditions)

    fields = [
        {"name": "\U0001f4cd Entry", "value": entry_str, "inline": True},
        {"name": "\U0001f6d1 Stop", "value": f"{stop_str} ({stop_pct:.1f}% risk)", "inline": True},
        {"name": "\U0001f3af Target", "value": target_str, "inline": True},
        {"name": "\u2696\ufe0f R:R", "value": f"{rr:.1f}:1", "inline": True},
        {"name": "Net R (after costs)", "value": _estimated_net_r_embed(signal_dict), "inline": True},
        {"name": "Regime", "value": regime_str, "inline": True},
        {"name": "Confidence", "value": f"{tier_tag} ({met_ratio})", "inline": True},
        {"name": "Key Conditions", "value": conditions_text, "inline": False},
        {"name": "Indicator Confluence", "value": _get_confluence(signal_dict), "inline": False},
    ]

    embed = {
        # FINAL DECISION: no "[GAUNTLET]" prefix, no strategy version string.
        "title": f"\U0001f4ca {strategy_name}",
        "description": (
            f"**{ticker}** | {direction_label} | Daily | "
            f"[TradingView Chart]({tv_url}){id_line}"
        ),
        "color": color,
        "fields": fields,
        # FINAL DECISION: no "Pessimistic fills + cost-adjusted" telemetry.
        "footer": {"text": "HermesForge"},
        "timestamp": now_pt().isoformat(),
    }

    # Options recommendations (stocks only) — trader-pertinent, KEPT.
    if publish_channel == "stocks" and entry and stop and target:
        try:
            from options_recommender import (
                get_options_recommendations,
                format_options_embed,
            )
            recs = get_options_recommendations(ticker, direction, entry, stop, target)
            options_text = format_options_embed(recs)
            if options_text and "No liquid options" not in options_text:
                embed["fields"].append({
                    "name": "\U0001f4c9 Options Ideas",
                    "value": options_text[:1024],
                    "inline": False,
                })
        except Exception as e:
            logger.debug(f"Options rec failed for {ticker}: {e}")

    return embed


def _build_sweep_embed(signal_dict: dict, color: int, id_line: str) -> dict:
    """STR-Q liquidity-sweep setup embed (intraday)."""
    ticker = signal_dict.get("ticker", "?")
    direction = signal_dict.get("direction", "long")
    direction_label = "LONG" if direction == "long" else "SHORT"
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]

    tier = signal_dict.get("confidence_tier", "C")
    conf_label = signal_dict.get("confidence_label", "Low")
    conditions_text = signal_dict.get("conditions_text", "\u2022 See sweep details below")

    level_type = signal_dict.get("level_type", "unknown")
    quality_score = signal_dict.get("quality_score", 0)
    penetration_atr = signal_dict.get("penetration_atr", 0)
    wick_ratio = signal_dict.get("wick_ratio", 0)
    volume_surge = signal_dict.get("volume_surge", 0)
    level_price = signal_dict.get("level_price", 0)
    confirmation = signal_dict.get("confirmation", "confirmed")

    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0
    stop_pct = (risk / entry * 100) if entry else 0

    direction_emoji = "\U0001f7e2" if direction == "long" else "\U0001f534"

    embed = {
        # FINAL DECISION: no "[GAUNTLET]" prefix.
        "title": f"\U0001f4ca STR-Q Liquidity Sweep \u2014 {ticker}",
        "description": (
            f"{direction_emoji} **{direction_label}** | Intraday 5m | "
            f"Sweep: {signal_dict.get('sweep_direction', direction)} at **{level_type}**{id_line}\n"
            f"Quality: **{quality_score}/100** | Confirmation: {confirmation}"
        ),
        "color": color,
        "fields": [
            {"name": "\U0001f4cd Entry", "value": _fmt_price(entry), "inline": True},
            {"name": "\U0001f6d1 Stop", "value": f"{_fmt_price(stop)} ({stop_pct:.1f}% risk)", "inline": True},
            {"name": "\U0001f3af Target", "value": _fmt_price(target), "inline": True},
            {"name": "\u2696\ufe0f R:R", "value": f"{rr:.1f}:1", "inline": True},
            _build_g3_fill_field(signal_dict),
            {"name": "Confidence", "value": f"{tier} ({conf_label})", "inline": True},
            {"name": "\u23f1\ufe0f Time Stop", "value": "75 min (15 bars)", "inline": True},
            {"name": "Key Conditions", "value": conditions_text, "inline": False},
            {"name": "Sweep Details", "value": (
                f"\u2022 Penetration: {penetration_atr:.2f} ATR\n"
                f"\u2022 Wick ratio: {wick_ratio:.2f}\n"
                f"\u2022 Volume surge: {volume_surge:.2f}x\n"
                f"\u2022 Level: {_fmt_price(level_price)}\n"
                f"\u2022 Quality score: {quality_score}/100"
            ), "inline": False},
            {"name": "Indicator Confluence", "value": (
                "**Liquidity Sweep confluence:**\n"
                f"\u2022 Price swept {level_type} level then reversed \u2192 institutional liquidity grab confirmed\n"
                f"\u2022 Sweep direction: {signal_dict.get('sweep_direction', direction)} \u2192 alignment with trade direction\n"
                f"\u2022 Quality score: {quality_score}/100 \u2192 data-driven scoring (level type weighted)\n"
                "\u2022 Stop behind sweep wick \u2192 tight risk, minimal adverse excursion\n"
                "\u2022 3R target \u2192 favorable risk-reward ratio\n"
                "\u2022 5-minute intraday execution \u2192 precise timing, post-sweep entry"
            ), "inline": False},
        ],
        # FINAL DECISION: no "Pessimistic fills + cost-adjusted" internal footer.
        "footer": {"text": "HermesForge"},
        "timestamp": now_pt().isoformat(),
    }
    return embed


# ── EXIT / lifecycle alert (standalone one-liner + back-link) ─────────────────
_EXIT_LABELS = {
    "ENTRY": ("\U0001f7e2", "ENTRY"),
    "STOP": ("\U0001f6d1", "STOP"),
    "TARGET": ("\U0001f3af", "TARGET"),
    "TIME": ("\u23f1\ufe0f", "TIME STOP"),
}


def _compute_r(trade: dict, exit_price: float) -> float:
    entry = float(trade["entry_price"])
    stop = float(trade["stop_price"])
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    direction = trade.get("direction", "long")
    if direction == "long":
        return (exit_price - entry) / risk
    return (entry - exit_price) / risk


def build_exit_message(trade: dict, exit_info: dict = None, event_type: str = "STOP") -> str:
    """Build a standalone one-line lifecycle/exit alert with a hyperlinked
    back-link to the original setup. No threading (webhooks cannot thread);
    the back-link is the durable navigation path on both servers.

    The back-link `[SHORT_ID](url)` carries the short_id, satisfying the
    crosspost template gate (validate_crosspost matches the short-id link).
    """
    short_id = trade.get("short_id", "?")
    ticker = trade.get("ticker", "?")
    direction = str(trade.get("direction", "?")).upper()
    channel_id = trade.get("discord_channel_id", "")
    message_id = trade.get("discord_message_id", "")

    if channel_id and message_id:
        link = make_discord_link(short_id, channel_id, message_id)
    else:
        link = f"`{short_id}`"

    emoji, label = _EXIT_LABELS.get(event_type, ("\u2753", "UNKNOWN"))

    if event_type == "ENTRY":
        entry_price = float(trade["entry_price"])
        return f"{emoji} **{label}** | {link} | {ticker} {direction} entered at {_fmt_price(entry_price)}"

    exit_price = float((exit_info or {}).get("exit_price", 0))
    r_mult = (exit_info or {}).get("r_multiple")
    if r_mult is None:
        r_mult = _compute_r(trade, exit_price)

    if event_type == "STOP":
        body = f"stopped at {_fmt_price(exit_price)}"
        return f"{emoji} **{label}** | {link} | {ticker} {direction} {body} ({r_mult:+.1f}R)"
    elif event_type == "TARGET":
        body = f"target hit at {_fmt_price(exit_price)}"
        return f"{emoji} **{label}** | {link} | {ticker} {direction} {body} ({r_mult:+.1f}R)"
    elif event_type == "TIME":
        bars = (exit_info or {}).get("bars_held", "?") if exit_info else "?"
        body = f"time stop at {_fmt_price(exit_price)}"
        return f"{emoji} **{label}** | {link} | {ticker} {direction} {body} ({r_mult:+.1f}R, {bars} bars)"

    return f"{emoji} **{label}** | {link} | {ticker} {direction}"


# ── REPORT EMBED (D structure) ────────────────────────────────────────────────
def build_report_embed(report_text: str, color: int = None) -> dict:
    """Wrap the tightened performance-report text (D structure) into an embed."""
    if color is None:
        color = _get_day_color()
    return {
        "embeds": [{
            "title": "\U0001f4c8 Paper Trading Performance Report",
            "description": report_text,
            "color": color,
            "footer": {"text": "HermesForge \u2022 Paper Trading"},
            "timestamp": now_pt().isoformat(),
        }]
    }


# ── CROSS-POST (single path; re-uploads chart attachment) ────────────────────
def _state_load() -> dict:
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text())
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _state_save_atomic(new_state: dict, old_state: dict) -> None:
    """Atomic write + regression guard (US-123/125/126/131).

    Refuses to persist a state with FEWER tracked IDs than the prior state
    minus legitimately pruned (>48h) entries — i.e. we only ever ADD or prune
    old entries; any other shrinkage is treated as silent data loss.
    """
    now_ms = int(time.time() * 1000)
    cutoff_ms = now_ms - (48 * 3600 * 1000)
    cleaned = {}
    for k, v in new_state.items():
        try:
            ts_ms = (int(k) >> 22) + 1420070400000
        except (ValueError, TypeError):
            ts_ms = now_ms
        if ts_ms > cutoff_ms:
            cleaned[k] = v

    if not cleaned:
        raise SystemExit("REFUSED: empty state payload")

    old_keys = set(old_state.keys())
    cleaned_keys = set(cleaned.keys())
    legitimately_pruned = len(old_keys - cleaned_keys)
    expected_min = len(old_keys) - legitimately_pruned
    if len(cleaned_keys) < expected_min:
        raise SystemExit(
            f"REFUSED: regression detected \u2014 "
            f"old={len(old_keys)} new={len(cleaned_keys)} pruned={legitimately_pruned} "
            f"expected_min={expected_min}"
        )

    payload = json.dumps(cleaned, separators=(",", ":"))
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    d = STATE_FILE.parent
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", prefix=".crosspost_state.", dir=str(d))
    try:
        os.write(fd, payload.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.rename(tmp_path, STATE_FILE)
    # fsync directory so the rename is durable
    try:
        dfd = os.open(str(d), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


def _record_crossposted(message_ids: list) -> None:
    """Add successfully-cross-posted source message IDs to the shared state."""
    old = _state_load()
    new = dict(old)
    for mid in message_ids:
        new[mid] = True
    _state_save_atomic(new, old)


# Legacy webhook-utils state — kept in sync so embed_publisher's
# delete_crossposted_messages() (daily-batch "replace" cleanup) still finds and
# deletes the follower-server messages we post here.
LEGACY_WEBHOOK_STATE = pathlib.Path.home() / ".hermes" / "webhook_crosspost_state.json"


def _track_follower_message(channel_id: str, follower_message_id: str) -> None:
    """Record the follower-server message ID in the legacy webhook-utils format."""
    try:
        if LEGACY_WEBHOOK_STATE.exists():
            data = json.loads(LEGACY_WEBHOOK_STATE.read_text())
        else:
            data = {}
        if not isinstance(data, dict):
            data = {}
        ch = data.setdefault(str(channel_id), {})
        ids = ch.setdefault("message_ids", [])
        if not isinstance(ids, list):
            ids = []
            ch["message_ids"] = ids
        if follower_message_id not in ids:
            ids.append(follower_message_id)
        LEGACY_WEBHOOK_STATE.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_WEBHOOK_STATE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.warning(f"legacy webhook state update failed: {e}")


def crosspost_message(payload: dict, channel_id: str,
                      chart_path: str = None, source_message_id: str = None) -> dict:
    """The ONE cross-post path.  Posts to the follower server via webhook,
    re-uploading the chart as a multipart `files[0]` attachment so the embed's
    `attachment://chart.png` resolves (fixes B1).  Records the source message
    ID in shared state so the cron forwarder will not re-forward it (dedup).

    Returns {"status": "ok"|"skipped"|"error", ...}.
    """
    channel_id = str(channel_id)
    if not should_crosspost(channel_id):
        return {"status": "skipped", "reason": "not-in-allowlist"}

    url = get_webhook_url(channel_id)
    if not url:
        return {"status": "skipped", "reason": "no-webhook"}

    p = dict(payload)
    p.setdefault("username", WEBHOOK_NAME)

    has_chart = bool(chart_path and os.path.exists(chart_path))

    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", "POST"]
    if has_chart:
        # Rewrite the embed image reference to the re-uploaded attachment.
        for emb in p.get("embeds", []):
            if isinstance(emb, dict) and "image" in emb:
                emb["image"] = {"url": "attachment://chart.png"}
        cmd += [
            "-F", f"payload_json={json.dumps(p)}",
            "-F", f"files[0]=@{chart_path};filename=chart.png;type=image/png",
        ]
    else:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(p)]

    cmd += ["--max-time", "30", f"{url}?wait=true"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "timeout"}

    stdout = result.stdout.strip()
    if not stdout:
        return {"status": "error", "error": "no-output"}

    lines = stdout.rsplit("\n", 1)
    body = lines[0] if len(lines) > 1 else stdout
    http_code = lines[1] if len(lines) > 1 else "0"

    try:
        resp = json.loads(body)
    except json.JSONDecodeError:
        return {"status": "error", "http_code": http_code, "raw": body[:500]}

    if resp.get("id"):
        if source_message_id:
            try:
                _record_crossposted([source_message_id])
            except SystemExit as e:
                logger.error(f"state write refused: {e}")
        _track_follower_message(channel_id, resp["id"])
        return {"status": "ok", "message_id": resp["id"]}
    return {"status": "error", "http_code": http_code,
            "discord_message": resp.get("message", "unknown")[:300]}


# ── CRON batch forwarder (forward-ALL, dedup, validate, re-upload) ────────────
def _fetch_messages(channel_id: str, token: str, limit: int = 50) -> list:
    url = f"{API_BASE}/channels/{channel_id}/messages?limit={limit}"
    cmd = ["curl", "-s", "-H", f"Authorization: Bot {token}", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _download_attachment(url: str, token: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    cmd = ["curl", "-s", "-L", "-H", f"Authorization: Bot {token}", "-o", tmp.name, url]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return tmp.name


def _build_payload(msg: dict) -> dict:
    payload = {}
    if msg.get("content"):
        payload["content"] = msg["content"]
    if msg.get("embeds"):
        payload["embeds"] = msg["embeds"]
    payload["username"] = WEBHOOK_NAME
    return payload


def forward_all_channels(dry_run: bool = False) -> int:
    """Forward ALL non-cross-posted bot messages in the last 24h, oldest-first,
    from every allow-listed channel, validating each against the template gate
    and re-uploading any chart attachment (fixes B2/G multi-part loss).
    """
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        print("ERROR: DISCORD_BOT_TOKEN not set")
        return 1

    from validate_crosspost import validate as _validate

    channels = [c for c, enabled in CROSSPOST_ALLOWLIST.items() if enabled]
    state = _state_load()
    cutoff = int(time.time() - 86400)

    crossposted = 0
    skipped = 0

    for ch in channels:
        url = get_webhook_url(ch)
        if not url:
            continue
        messages = _fetch_messages(ch, token, limit=50)
        if not messages:
            skipped += 1
            continue

        candidates = []
        for m in messages:
            try:
                ts_s = int(((int(m["id"]) >> 22) + 1420070400000) / 1000)
            except (KeyError, ValueError, TypeError):
                continue
            if ts_s < cutoff:
                continue
            if m["id"] in state:
                continue
            if not (m.get("content", "").strip() or m.get("embeds")):
                continue
            if not _validate(m, ch):
                continue
            candidates.append(m)

        candidates.sort(key=lambda m: int(m["id"]))  # oldest first

        for m in candidates:
            attachment = (m.get("attachments") or [None])[0]
            chart_path = None
            if attachment and attachment.get("url"):
                chart_path = _download_attachment(attachment["url"], token)

            if dry_run:
                print(f"[DRY-RUN] would crosspost {m['id']} from {ch}")
                crossposted += 1
            else:
                result = crosspost_message(
                    _build_payload(m), ch, chart_path=chart_path, source_message_id=m["id"],
                )
                if result.get("status") == "ok":
                    crossposted += 1
                else:
                    print(f"  \u26a0\ufe0f crosspost failed msg {m['id']} (ch {ch}): "
                          f"{result.get('reason') or result.get('error') or result}",
                          file=sys.stderr)

            if chart_path and os.path.exists(chart_path):
                try:
                    os.remove(chart_path)
                except OSError:
                    pass
            time.sleep(0.5)

    print(f"Crosspost: {crossposted} messages, {skipped} skipped")
    return 0


# ── Smoke test / CLI ──────────────────────────────────────────────────────────
def _sample_swing_signal() -> dict:
    return {
        "ticker": "BTC",
        "direction": "long",
        "entry_price": 66294.00,
        "stop_price": 62832.24,
        "target_price": 73217.53,
        "strategy_name": "Cross-Sectional Factor",
        "strategy_id": "STR-P-crosssectional",
        "strategy_version": "1.0",
        "publish_channel": "crypto",
        "asset_class": "crypto",
        "regime": "ranging",
        "regime_benchmark": "BTC",
        "regime_adx": "10.8",
        "is_live": False,
        "composite_score": 1.88,
        "factor_mom12_1": -0.3,
        "factor_liquid": 2516000000,
        "factor_pricemom": -0.15,
    }


def _sample_trade() -> dict:
    return {
        "short_id": "BTC-P-0727A",
        "ticker": "BTC",
        "direction": "short",
        "entry_price": 63000.0,
        "stop_price": 63100.0,
        "target_price": 62000.0,
        "discord_channel_id": DISCORD_CRYPTO_SETUPS_CHANNEL,
        "discord_message_id": "1234567890123456789",
    }


def _smoke_test():
    col = _get_day_color()
    embed = build_setup_embed(_sample_swing_signal(), color=col, short_id="BTC-P-0727A")
    print("=== SETUP EMBED (swing) ===")
    print(json.dumps(embed, indent=2, ensure_ascii=False))

    sweep = {
        "ticker": "SOL",
        "direction": "short",
        "entry_price": 150.0,
        "stop_price": 152.0,
        "target_price": 144.0,
        "strategy_id": "STR-Q-liquidity-sweep",
        "strategy_name": "STR-Q Liquidity Sweep",
        "confidence_tier": "B",
        "confidence_label": "Medium",
        "conditions_text": "\u2022 Sweep confirmed",
        "level_type": "equal_highs",
        "level_price": 151.5,
        "penetration_atr": 0.4,
        "wick_ratio": 2.1,
        "volume_surge": 1.6,
        "quality_score": 66,
        "confirmation": "confirmed",
        "sweep_direction": "short",
        "gauntlet_pessimistic_slip": 12.4,
        "gauntlet_book_mid": 150.2,
    }
    print("\n=== SETUP EMBED (STR-Q sweep) ===")
    print(json.dumps(build_setup_embed(sweep, color=col, short_id="SOL-Q-1031A"), indent=2, ensure_ascii=False))

    print("\n=== EXIT MESSAGES ===")
    t = _sample_trade()
    print(build_exit_message(t, exit_info={"exit_price": 63100.0}, event_type="STOP"))
    print(build_exit_message(t, exit_info={"exit_price": 62000.0}, event_type="TARGET"))
    print(build_exit_message(t, exit_info={"exit_price": 62500.0, "bars_held": 8}, event_type="TIME"))
    print(build_exit_message(t, event_type="ENTRY"))
    print("✅ smoke test complete")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    elif "--forward-all" in sys.argv or "--forward" in sys.argv:
        sys.exit(forward_all_channels(dry_run=("--dry-run" in sys.argv)))
    elif "--build-setup" in sys.argv:
        print(json.dumps(build_setup_embed(_sample_swing_signal(), short_id="BTC-P-0727A"),
                         indent=2, ensure_ascii=False))
    elif "--build-exit" in sys.argv:
        print(build_exit_message(_sample_trade(), exit_info={"exit_price": 63100.0}, event_type="STOP"))
    elif "--build-report" in sys.argv:
        import pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
        import performance_report
        print(performance_report.build_report())
    else:
        print(__doc__)