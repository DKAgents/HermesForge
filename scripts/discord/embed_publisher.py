#!/usr/bin/env python3
"""
embed_publisher.py — Posts trade signals as Discord rich embeds.

Each day of the week gets a distinct left-border color:
  Mon=Blue  Tue=Green  Wed=Orange  Thu=Purple  Fri=Red  Sat=Teal  Sun=Gold

Posts directly via Discord Bot API (multipart for chart attachments).
Includes daily header embed.

Usage (programmatic):
    from embed_publisher import post_daily_batch, post_embed_signal
    post_daily_batch(signals, channel_id, asset_class, regime_data)
"""

import os
import json
import subprocess
import datetime
import pathlib
import time
import sys
import logging

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from timezone_utils import now_pt

from alert_publisher import get_quality_tier, _tradingview_link

# Trade tracking
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
from trade_id import generate_short_id, make_discord_url, get_strategy_code
import trade_log

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

# Day-of-week colors (Discord embed color is a single integer, 0xRRGGBB)
DAY_COLORS = {
    0: 0x3498db,  # Monday    — Blue
    1: 0x2ecc71,  # Tuesday   — Green
    2: 0xe67e22,  # Wednesday — Orange
    3: 0x9b59b6,  # Thursday  — Purple
    4: 0xe74c3c,  # Friday    — Red
    5: 0x1abc9c,  # Saturday  — Teal
    6: 0xf1c40f,  # Sunday    — Gold
}

DAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ── Trade ID generation ───────────────────────────────────────────────────────

def _generate_short_id_for_signal(signal_dict: dict, used_ids: set) -> str:
    """
    Generate a unique terse trade ID for a signal.
    Handles sequence letters for duplicate ticker/strategy/date combos.

    Args:
        signal_dict: Signal dict with ticker, strategy_id, date
        used_ids: Set of already-generated short_ids in this batch

    Returns:
        Terse ID like "BTC-P-0727A"
    """
    ticker = signal_dict.get("ticker", "?")
    strategy_id = signal_dict.get("strategy_id", "")
    signal_date = str(signal_dict.get("date", signal_dict.get("entry_date", "")))[:10]

    seq = 0
    while True:
        short_id = generate_short_id(ticker, strategy_id, signal_date, sequence=seq)
        if short_id not in used_ids:
            used_ids.add(short_id)
            return short_id
        seq += 1


def _infer_asset_class(ticker: str, signal_dict: dict) -> str:
    """Infer asset class from signal metadata or ticker, not channel override.
    Channel override (publish_channel) is checked LAST to prevent
    cross-sectional scanners from mislabeling stock signals as crypto."""
    # Priority 1: explicit asset_class in signal dict
    ac = signal_dict.get("asset_class", "")
    if ac:
        return ac
    # Priority 2: known crypto ticker (case-insensitive)
    ticker_upper = ticker.upper()
    crypto_set = {
        'BTC','ETH','SOL','XRP','ADA','DOT','AVAX','LINK','UNI','ATOM',
        'LTC','BCH','TRX','ETC','FIL','APT','NEAR','ARB','OP','AAVE',
        'MKR','SNX','CRV','RUNE','INJ','SUI','SEI','TIA','RNDR','FTM',
        'ALGO','EGLD','FLOW','SAND','MANA','AXS','SUSHI','COMP','YFI',
        '1INCH','ZRX','BAL','KAVA','BAND','LRC','RENDER','HYPE','ZEC',
        'TRUMP','PAXG','KBONK','BONK','FARTCOIN','ENA','JUP','WIF','PYTH',
        'STX','ORDI','SATS','TON','STRAX','LOOM','BLUR','GALA','CHZ','LDO',
        'WLD','DYDX','PEPE','DOGE','SHIB','MATIC','KNEAR',
    }
    if ticker_upper in crypto_set:
        return "crypto"
    # Priority 3: if not a known crypto ticker, it's a stock
    # (even if publish_channel says crypto — could be channel override)
    # Priority 4: publish_channel as final fallback
    pc = signal_dict.get("publish_channel", "")
    if pc == "crypto":
        return "crypto"
    return "stock"

def _register_trade_after_post(signal_dict: dict, short_id: str,
                                message_id: str, channel_id: str) -> str | None:
    """
    Register or update a trade in the trade log after posting the setup embed.

    If the trade already exists (from capture_signals.py), update it with
    Discord message info. Otherwise, create a new trade entry.

    Returns the trade_id, or None on failure.
    """
    try:
        strategy_id = signal_dict.get("strategy_id", "")
        ticker = signal_dict["ticker"]
        asset_class = _infer_asset_class(ticker, signal_dict)
        signal_date = str(signal_dict.get("date", signal_dict.get("entry_date", "")))[:10]

        post_url = make_discord_url(channel_id, message_id)

        # Compute position size using the strategy's sizing function
        import sys as _sys
        _paper_dir = str(pathlib.Path(__file__).parent.parent / "paper_trading")
        if _paper_dir not in _sys.path:
            _sys.path.insert(0, _paper_dir)
        try:
            from position_sizing import get_risk_pct
            risk_pct = get_risk_pct(strategy_id, signal_dict)
        except Exception:
            risk_pct = 0.5 if asset_class == "crypto" else 1.0

        trade_dict = {
            "strategy_id": strategy_id,
            "short_id": short_id,
            "ticker": ticker,
            "asset_class": asset_class,
            "data_source": "hyperliquid" if asset_class == "crypto" else "yfinance",
            "direction": signal_dict.get("direction", "long"),
            "signal_id": f"{strategy_id}_{ticker}_{signal_date}",
            "entry_date": signal_date,
            "entry_price": signal_dict["entry_price"],
            "stop_price": signal_dict["stop_price"],
            "target_price": signal_dict["target_price"],
            "position_size_pct": risk_pct,
            "discord_message_id": message_id,
            "discord_channel_id": channel_id,
            "discord_post_url": post_url,
        }

        try:
            trade_id = trade_log.open_trade(trade_dict)
            print(f"  📝 Trade registered: {short_id} ({trade_id})")
        except ValueError:
            # Trade already exists — update Discord info
            trade_id = trade_log.make_trade_id(strategy_id, ticker, signal_date)
            try:
                trade_log.register_discord_info(trade_id, message_id, channel_id, post_url)
                print(f"  📝 Trade updated: {short_id} ({trade_id})")
            except ValueError:
                print(f"  ⚠️ Could not register Discord info for {trade_id}")
                return None

        return trade_id
    except Exception as e:
        print(f"  ⚠️ Trade registration failed: {e}")
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_day_color(dt=None):
    if dt is None:
        dt = now_pt()
    return DAY_COLORS.get(dt.weekday(), 0x58a6ff)


def get_day_name(dt=None):
    if dt is None:
        dt = now_pt()
    return DAY_NAMES[dt.weekday()]


def _fmt_price(p):
    if abs(p) < 1.0:
        return f"${p:.6f}"
    elif abs(p) < 100.0:
        return f"${p:.4f}"
    else:
        return f"${p:.2f}"


# ── Per-strategy confluence explanation ─────────────────────────────────────

def _get_confluence(signal_dict: dict) -> str:
    """Return a human-readable explanation of how the strategy's indicators
    confluence to support this trade setup."""
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


# ── Embed formatting ──────────────────────────────────────────────────────────

def format_signal_embed(signal_dict: dict, color: int, short_id: str = "") -> dict:
    """Format a signal as a Discord embed JSON object."""
    ticker = signal_dict["ticker"]
    direction = signal_dict.get("direction", "long")
    direction_label = direction.capitalize()
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]
    strategy_name = signal_dict.get("strategy_name", "Strategy")
    version = signal_dict.get("strategy_version", "1.0")
    publish_channel = signal_dict.get("publish_channel", "stocks")

    tv_url = _tradingview_link(ticker, publish_channel)

    entry_str = _fmt_price(entry)
    stop_pct = abs(entry - stop) / entry * 100 if entry else 0
    stop_str = _fmt_price(stop)
    target_str = _fmt_price(target)
    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr = reward / risk if risk else 0.0

    # Regime
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

    # Quality tier + key conditions
    tier_tag, met_ratio, conditions = get_quality_tier(signal_dict)
    conditions_text = "\n".join(f"• {c}" for c in conditions)

    # Status
    is_live = signal_dict.get("is_live", False)
    status_str = "LIVE" if is_live else "WATCH"

    # Trade ID line
    id_line = f" | `{short_id}`" if short_id else ""

    # Build embed fields
    fields = [
        {"name": "📍 Entry", "value": entry_str, "inline": True},
        {"name": "🛑 Stop", "value": f"{stop_str} ({stop_pct:.1f}% risk)", "inline": True},
        {"name": "🎯 Target", "value": target_str, "inline": True},
        {"name": "⚖️ R:R", "value": f"{rr:.1f}:1", "inline": True},
        {"name": "Regime", "value": regime_str, "inline": True},
        {"name": "Confidence", "value": f"{tier_tag} ({met_ratio})", "inline": True},
        {"name": "Key Conditions", "value": conditions_text, "inline": False},
        {"name": "Indicator Confluence", "value": _get_confluence(signal_dict), "inline": False},
    ]

    embed = {
        "title": f"📊 {strategy_name} v{version}",
        "description": f"**{ticker}** | {direction_label} | Daily | [TradingView Chart]({tv_url}){id_line}",
        "color": color,
        "fields": fields,
        "footer": {"text": "HermesForge Signal Pipeline"},
        "timestamp": now_pt().isoformat(),
    }

    # ── Options recommendations (stocks only) ─────────────────────────────
    # Fetch live options chain and suggest single-leg, debit spread, and
    # credit spread strategies aligned with the signal's entry/stop/target.
    if publish_channel == "stocks" and entry and stop and target:
        try:
            from options_recommender import (
                get_options_recommendations,
                format_options_embed,
            )
            recs = get_options_recommendations(
                ticker, direction, entry, stop, target
            )
            options_text = format_options_embed(recs)
            if options_text and "No liquid options" not in options_text:
                embed["fields"].append({
                    "name": "📉 Options Ideas",
                    "value": options_text[:1024],  # Discord field value limit
                    "inline": False,
                })
        except Exception as e:
            logger.debug(f"Options rec failed for {ticker}: {e}")

    return embed


# ── Centralized publisher ────────────────────────────────────────────────────
# Single entry point for ALL trade setup posts (daily signals + intraday sweeps).
# Ensures every post has: chart attachment, TradingView link, confidence field,
# consistent field ordering, correct channel routing, and Pacific Time timestamps.

# Channel routing — swing (daily) vs day trading (intraday)
# Swing setups: higher timeframe, daily bars, multi-day holds
DISCORD_STOCK_SETUPS_CHANNEL = "1528555538848153640"
DISCORD_CRYPTO_SETUPS_CHANNEL = "1528555885310513213"
# Day trading setups: intraday bars, same-day holds (STR-Q sweep, etc.)
DISCORD_DAYTRADE_STOCK_CHANNEL = "1540951208028803142"
DISCORD_DAYTRADE_CRYPTO_CHANNEL = "1540951134200402071"

# Day-of-week colors (shared between daily and sweep)
DAY_COLORS = {
    0: 0x3498db, 1: 0x2ecc71, 2: 0xe67e22, 3: 0x9b59b6,
    4: 0xe74c3c, 5: 0x1abc9c, 6: 0xf1c40f,
}


def _get_day_color() -> int:
    """Get the day-of-week color for today (Pacific Time)."""
    dt = now_pt()
    return DAY_COLORS.get(dt.weekday(), 0x58a6ff)


def _route_channel(asset_class: str, timeframe: str = "daily") -> str:
    """Route to the correct Discord channel based on asset class and timeframe.

    This is the SINGLE source of truth for channel routing.
    
    Day trading (intraday):  → #day-trade-stocks / #day-trade-crypto
    Swing (daily):           → #stock-setups / #crypto-setups
    """
    if timeframe == "intraday":
        return DISCORD_DAYTRADE_CRYPTO_CHANNEL if asset_class == "crypto" else DISCORD_DAYTRADE_STOCK_CHANNEL
    if asset_class == "crypto":
        return DISCORD_CRYPTO_SETUPS_CHANNEL
    return DISCORD_STOCK_SETUPS_CHANNEL


def publish_signal(signal_dict: dict, asset_class: str,
                   dry_run: bool = False, crosspost: bool = False) -> dict:
    """Centralized publish function for ALL trade setup posts.

    Takes a signal_dict (works for both daily signals and intraday sweeps),
    generates a chart, builds a standardized embed, and posts to the correct
    Discord channel with chart attachment.

    Required signal_dict fields:
        - ticker, direction, entry_price, stop_price, target_price
        - strategy_id, strategy_name, strategy_version
        - confidence_tier (e.g. "A (High)") or quality_tier + confirmation_level (for STR-Q)
        - regime (for daily signals)

    Optional fields:
        - level_type, level_price, penetration_atr, wick_ratio, volume_surge,
          quality_score, confirmation (for STR-Q sweeps)
        - regime_benchmark, regime_adx (for daily signals)
        - is_live, short_id, publish_channel

    Returns {status, message_id, channel_id, chart_path} or {status: error}.
    """
    import pathlib as _pl

    ticker = signal_dict.get("ticker", "?")
    strategy_id = signal_dict.get("strategy_id", "")
    strategy_name = signal_dict.get("strategy_name", "Strategy")
    version = signal_dict.get("strategy_version", "1.0")

    # ── Channel routing ──
    timeframe = signal_dict.get("timeframe", "daily")
    channel_id = _route_channel(asset_class, timeframe)
    signal_dict["publish_channel"] = asset_class

    # ── Generate chart ──
    chart_path = None
    try:
        from chart_generator import generate_setup_chart
        chart_dir = _pl.Path.home() / ".hermes" / "signal_charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        chart_path = str(chart_dir / f"{signal_dict.get('signal_id', ticker)}_{now_pt().strftime('%Y%m%d_%H%M%S')}.png")
        generate_setup_chart(ticker, signal_dict, chart_path)
    except Exception as e:
        logger.warning(f"Chart generation failed for {ticker}: {e}")
        chart_path = None

    # ── Build embed ──
    # If the signal already has a pre-built embed (STR-Q sweeps), augment it
    # with chart + TradingView link + any missing fields.
    # Otherwise, use format_signal_embed (daily signals).
    if signal_dict.get("_pre_built_embed"):
        embed = signal_dict["_pre_built_embed"]
        # Add TradingView link to description if not present
        tv_url = _tradingview_link(ticker, asset_class)
        desc = embed.get("description", "")
        if "TradingView" not in desc and "tradingview" not in desc.lower():
            embed["description"] = desc + f" | [TradingView Chart]({tv_url})"
        # Add chart image reference
        if chart_path and os.path.exists(chart_path):
            embed["image"] = {"url": "attachment://chart.png"}
    else:
        color = _get_day_color()
        short_id = signal_dict.get("short_id", "")
        embed = format_signal_embed(signal_dict, color, short_id)

    # ── Post to Discord ──
    payload = {"embeds": [embed]}

    if dry_run:
        print(f"  [dry-run] Would post {ticker} to channel {channel_id}")
        return {"status": "ok", "message_id": "dry_run", "channel_id": channel_id, "chart_path": chart_path}

    result = _post_to_discord(channel_id, payload, chart_path=chart_path, crosspost=crosspost)

    # Register in trade log if this is a new trade
    if result["status"] == "ok" and result.get("message_id") != "dry_run":
        try:
            short_id = signal_dict.get("short_id", "")
            if short_id:
                trade_id = signal_dict.get("trade_id", "")
                if trade_id:
                    post_url = make_discord_url(channel_id, result["message_id"])
                    trade_log.register_discord_info(trade_id, result["message_id"], channel_id, post_url)
        except Exception as e:
            logger.debug(f"Trade log registration failed: {e}")

    return {**result, "channel_id": channel_id, "chart_path": chart_path}


# ── STR-Q sweep embed builder ────────────────────────────────────────────────
# Builds a standardized embed for STR-Q sweep signals using the same field
# template as daily signals, then passes it to publish_signal().

def build_sweep_embed(signal_dict: dict) -> dict:
    """Build a standardized embed for STR-Q sweep signals.

    This produces the same field structure as format_signal_embed(),
    ensuring template consistency between daily and intraday posts.
    The embed is stored in signal_dict['_pre_built_embed'] and then
    passed to publish_signal() which handles chart + posting.
    """
    ticker = signal_dict["ticker"]
    direction = signal_dict.get("direction", "long")
    direction_label = "LONG" if direction == "long" else "SHORT"
    entry = signal_dict["entry_price"]
    stop = signal_dict["stop_price"]
    target = signal_dict["target_price"]

    # Confidence tier (already computed by capture_sweep_signals.py)
    tier = signal_dict.get("confidence_tier", "C")
    conf_label = signal_dict.get("confidence_label", "Low")
    conditions_text = signal_dict.get("conditions_text", "• See sweep details below")

    # Sweep details
    level_type = signal_dict.get("level_type", "unknown")
    quality_score = signal_dict.get("quality_score", 0)
    penetration_atr = signal_dict.get("penetration_atr", 0)
    wick_ratio = signal_dict.get("wick_ratio", 0)
    volume_surge = signal_dict.get("volume_surge", 0)
    level_price = signal_dict.get("level_price", 0)
    confirmation = signal_dict.get("confirmation", "confirmed")

    # Price formatting
    def _fmt(p):
        if abs(p) < 1.0: return f"${p:.6f}"
        elif abs(p) < 100.0: return f"${p:.4f}"
        else: return f"${p:,.2f}"

    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0
    stop_pct = (risk / entry * 100) if entry else 0

    direction_emoji = "🟢" if direction == "long" else "🔴"

    # Build the standardized embed — same field order as daily signals
    embed = {
        "title": f"📊 STR-Q Liquidity Sweep — {ticker}",
        "description": (
            f"{direction_emoji} **{direction_label}** | Intraday 5m | "
            f"Sweep: {signal_dict.get('sweep_direction', direction)} at **{level_type}**\n"
            f"Quality: **{quality_score}/100** | Confirmation: {confirmation}"
        ),
        "color": _get_day_color(),
        "fields": [
            {"name": "📍 Entry", "value": _fmt(entry), "inline": True},
            {"name": "🛑 Stop", "value": f"{_fmt(stop)} ({stop_pct:.1f}% risk)", "inline": True},
            {"name": "🎯 Target", "value": _fmt(target), "inline": True},
            {"name": "⚖️ R:R", "value": f"{rr:.1f}:1", "inline": True},
            {"name": "Confidence", "value": f"{tier} ({conf_label})", "inline": True},
            {"name": "⏱️ Time Stop", "value": "75 min (15 bars)", "inline": True},
            {"name": "Key Conditions", "value": conditions_text, "inline": False},
            {"name": "Sweep Details", "value": (
                f"• Penetration: {penetration_atr:.2f} ATR\n"
                f"• Wick ratio: {wick_ratio:.2f}\n"
                f"• Volume surge: {volume_surge:.2f}x\n"
                f"• Level: {_fmt(level_price)}\n"
                f"• Quality score: {quality_score}/100"
            ), "inline": False},
            {"name": "Indicator Confluence", "value": (
                "**Liquidity Sweep confluence:**\n"
                f"• Price swept {level_type} level then reversed → institutional liquidity grab confirmed\n"
                f"• Sweep direction: {signal_dict.get('sweep_direction', direction)} → alignment with trade direction\n"
                f"• Quality score: {quality_score}/100 → data-driven scoring (level type weighted)\n"
                f"• Stop behind sweep wick → tight risk, minimal adverse excursion\n"
                f"• 3R target → favorable risk-reward ratio\n"
                f"• 5-minute intraday execution → precise timing, post-sweep entry"
            ), "inline": False},
        ],
        "footer": {"text": "HermesForge STR-Q Intraday Pipeline"},
        "timestamp": now_pt().isoformat(),
    }

    return embed


def format_daily_header(asset_class: str, regime_data: dict, signal_count: int,
                        live_count: int, watch_count: int, strategies: list,
                        color: int) -> dict:
    """Format the daily header as a Discord embed — icon + day/date only."""
    dt = now_pt()
    day_name = get_day_name(dt)
    date_str = f"{day_name.upper()}, {MONTH_NAMES[dt.month - 1].upper()} {dt.day}, {dt.year}"

    embed = {
        "title": f"📅 {date_str}",
        "color": color,
        "footer": {"text": f"HermesForge Daily Pipeline — {dt.strftime('%H:%M %Z')}"},
    }

    return embed


# ── Discord API posting ───────────────────────────────────────────────────────

# Import webhook utilities for cross-server posting
try:
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from webhook_utils import create_crossposter, WebhookCrossposter
    WEBHOOK_AVAILABLE = True
except ImportError:
    WEBHOOK_AVAILABLE = False


def _get_crossposter(channel_id: str):
    """Get a webhook crossposter for the channel, or None if not configured."""
    if not WEBHOOK_AVAILABLE:
        return None
    return create_crossposter(str(channel_id), webhook_name="HermesForge Bot")


def delete_crossposted_messages(channel_id: str) -> int:
    """
    Delete all previously crossposted webhook messages for a channel.
    Call this before posting a new batch to clean up the follower server.

    Returns number of messages deleted.
    """
    wx = _get_crossposter(channel_id)
    if wx:
        return wx.delete_all()
    return 0


def _post_to_discord(channel_id: str, payload: dict, chart_path: str | None = None,
                     crosspost: bool = False) -> dict:
    """Post a message to Discord via Bot API. Returns {status, message_id}.
    If crosspost=True and a webhook is configured for this channel, posts
    a copy via webhook to the follower server. If no webhook is configured,
    falls back to native announcement channel crosspost.
    """
    url = f"{API_BASE}/channels/{channel_id}/messages"

    if chart_path and os.path.exists(chart_path):
        # Multipart: upload chart + embed. Use filename=chart.png to match
        # the embed's attachment://chart.png reference.
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
            "-F", f"payload_json={json.dumps(payload)}",
            "-F", f"files[0]=@{chart_path};filename=chart.png;type=image/png",
            url,
        ]
    else:
        # JSON only (no file)
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
            url,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    try:
        response = json.loads(result.stdout)
        if "id" in response:
            msg_id = response["id"]
            if crosspost:
                # Try webhook crosspost first (no tombstones in follower server)
                wx = _get_crossposter(channel_id)
                if wx:
                    # Post copy via webhook (without chart — webhooks can't upload files this way)
                    webhook_payload = dict(payload)
                    # Remove image attachment reference if present (webhook can't access bot's uploaded file)
                    # The chart image won't appear in the webhook copy — this is a known limitation
                    wx.post(webhook_payload)
                else:
                    # Fall back to native crosspost (may leave tombstones when deleted)
                    _crosspost_message(channel_id, msg_id)
            return {"status": "ok", "message_id": msg_id}
        else:
            return {"status": "error", "response": result.stdout[:500]}
    except (json.JSONDecodeError, KeyError):
        return {"status": "error", "response": result.stdout[:500]}


def _crosspost_message(channel_id: str, message_id: str) -> dict:
    """Crosspost (publish) a message from an announcement channel."""
    url = f"{API_BASE}/channels/{channel_id}/messages/{message_id}/crosspost"
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    try:
        response = json.loads(result.stdout)
        if "id" in response:
            return {"status": "ok", "message_id": response["id"]}
        else:
            return {"status": "error", "response": result.stdout[:200]}
    except (json.JSONDecodeError, KeyError):
        return {"status": "error", "response": result.stdout[:200]}


def post_embed_signal(signal_dict: dict, chart_path: str, channel_id: str,
                      color: int, dry_run: bool = False,
                      short_id: str = "", crosspost: bool = False) -> dict:
    """Post a single signal as a Discord embed with chart attachment.
    If short_id is provided, it's included in the embed and the trade is
    registered in the trade log after successful posting.
    If crosspost=True, publishes the message to following servers.
    """
    embed = format_signal_embed(signal_dict, color, short_id=short_id)

    # Add image reference if chart exists
    has_chart = chart_path and os.path.exists(chart_path)
    if has_chart:
        embed["image"] = {"url": "attachment://chart.png"}

    payload = {"embeds": [embed]}

    if dry_run:
        return {
            "status": "dry_run",
            "embed": embed,
            "chart_path": chart_path if has_chart else None,
            "short_id": short_id,
        }

    result = _post_to_discord(channel_id, payload, chart_path if has_chart else None,
                              crosspost=crosspost)

    # Register trade after successful post
    if result["status"] == "ok" and short_id:
        _register_trade_after_post(
            signal_dict, short_id, result["message_id"], channel_id,
        )

    return result


def post_daily_header(asset_class: str, regime_data: dict, signal_count: int,
                      live_count: int, watch_count: int, strategies: list,
                      channel_id: str, color: int, dry_run: bool = False,
                      crosspost: bool = False) -> dict:
    """Post the daily header embed."""
    embed = format_daily_header(asset_class, regime_data, signal_count,
                                live_count, watch_count, strategies, color)
    payload = {"embeds": [embed]}

    if dry_run:
        return {"status": "dry_run", "embed": embed}

    return _post_to_discord(channel_id, payload, crosspost=crosspost)


def format_trade_summary(signals: list) -> str:
    """Format a concise trade summary list.
    Example line: BTC | SHORT | Confidence: Low | Entry: $63,000 | SL: $63,100 | TP: $62,000 | RR: 3:1
    """
    lines = []
    for sig in signals:
        ticker = sig.get("ticker", "?")
        direction = sig.get("direction", "long").upper()
        entry = sig.get("entry_price", 0)
        stop = sig.get("stop_price", 0)
        target = sig.get("target_price", 0)
        risk = abs(entry - stop)
        reward = abs(target - entry)
        rr = reward / risk if risk else 0

        # Confidence tier
        tier_tag, _, _ = get_quality_tier(sig)
        # Map tier tags to simple labels
        conf_map = {"A": "High", "B": "Medium", "C": "Low"}
        conf_label = conf_map.get(tier_tag, "Low")

        # Format prices
        def _p(v):
            if abs(v) < 1.0:
                return f"${v:.6f}"
            elif abs(v) < 100.0:
                return f"${v:.4f}"
            else:
                return f"${v:,.2f}"

        lines.append(
            f"{ticker} | {direction} | Confidence: {conf_label} | "
            f"Entry: {_p(entry)} | SL: {_p(stop)} | TP: {_p(target)} | RR: {rr:.0f}:1"
        )
    return "\n".join(lines)


def post_trade_summary(signals: list, channel_id: str, dry_run: bool = False) -> dict:
    """Post a concise trade summary list as a plain text message."""
    text = format_trade_summary(signals)
    # Discord message limit is 2000 chars; split if needed
    chunks = []
    while len(text) > 1900:
        split_at = text.rfind("\n", 0, 1900)
        if split_at == -1:
            split_at = 1900
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    chunks.append(text)

    last_id = None
    for chunk in chunks:
        payload = {"content": chunk}
        if dry_run:
            print(f"  [dry-run] Summary chunk: {chunk[:100]}...")
            last_id = "dry_run"
            continue
        result = _post_to_discord(channel_id, payload)
        if result["status"] == "ok":
            last_id = result["message_id"]
            time.sleep(0.5)
        else:
            return result
    return {"status": "ok", "message_id": last_id}


# ── Batch posting ─────────────────────────────────────────────────────────────

def post_daily_batch(signals: list, channel_id: str, asset_class: str,
                     regime_data: dict, dry_run: bool = False,
                     summary_channel_id: str = None,
                     crosspost: bool = True) -> dict:
    """
    Post a full daily batch: header → signal embeds.

    Args:
        signals: list of signal dicts (sorted by score, enriched with metadata)
        channel_id: Discord channel ID string for embeds
        asset_class: "stock" or "crypto"
        regime_data: regime dict from regime_detector
        dry_run: if True, format only (no posting)
        crosspost: if True, publish each message (announcement channels)

    Returns:
        {posted, errors, message_ids, header_id}
    """
    color = get_day_color()
    live_count = sum(1 for s in signals if s.get("is_live", False))
    watch_count = len(signals) - live_count

    # Collect unique strategy names
    strategy_names = sorted(set(s.get("strategy_name", "?") for s in signals))

    result = {
        "posted": 0,
        "errors": 0,
        "message_ids": [],
        "header_id": None,
    }

    # Clean up old crossposted webhook messages in follower server
    if crosspost and not dry_run:
        n_cleaned = delete_crossposted_messages(channel_id)
        if n_cleaned > 0:
            print(f"  🧹 Cleaned {n_cleaned} old webhook messages in follower server")

    # Post daily header
    header_result = post_daily_header(
        asset_class, regime_data, len(signals), live_count, watch_count,
        strategy_names, channel_id, color, dry_run,
        crosspost=crosspost,
    )
    if header_result["status"] in ("ok", "dry_run"):
        result["header_id"] = header_result.get("message_id")
        if not dry_run:
            print(f"  ✅ Daily header posted (ID: {result['header_id']})")
            time.sleep(1)
    else:
        result["errors"] += 1
        print(f"  ❌ Header failed: {header_result.get('response', '')}")
        return result

    # Post each signal
    used_short_ids: set = set()
    for i, sig in enumerate(signals):
        chart_path = sig.get("_chart_path")
        short_id = _generate_short_id_for_signal(sig, used_short_ids)
        sig_result = post_embed_signal(sig, chart_path, channel_id, color, dry_run,
                                       short_id=short_id, crosspost=crosspost)

        if sig_result["status"] in ("ok", "dry_run"):
            result["posted"] += 1
            if not dry_run:
                result["message_ids"].append(sig_result.get("message_id"))
                print(f"  ✅ {sig['ticker']} ({sig.get('direction', '?')}) posted [{short_id}]")
                time.sleep(1)
        else:
            result["errors"] += 1
            print(f"  ❌ {sig['ticker']} failed: {sig_result.get('response', '')}")

    return result


# ── Smoke test ────────────────────────────────────────────────────────────────

def _smoke_test():
    """Test embed formatting without posting."""
    signal = {
        "ticker": "BTC",
        "direction": "long",
        "entry_price": 66294.00,
        "stop_price": 62832.24,
        "target_price": 73217.53,
        "strategy_name": "Cross-Sectional Factor",
        "strategy_id": "STR-P-crosssectional",
        "strategy_version": "1.0",
        "publish_channel": "crypto",
        "regime": "ranging",
        "regime_benchmark": "BTC",
        "regime_adx": "10.8",
        "is_live": False,
        "composite_score": 1.88,
        "factor_mom12_1": -0.3,
        "factor_liquid": 2516000000,
        "factor_pricemom": -0.15,
    }

    color = get_day_color()
    embed = format_signal_embed(signal, color)

    print("=== Signal Embed ===")
    print(json.dumps(embed, indent=2))

    regime_data = {"regime": "ranging", "benchmark": "BTC", "adx": "10.8"}
    header = format_daily_header("crypto", regime_data, 16, 0, 16,
                                 ["Cross-Sectional Factor"], color)
    print("\n=== Daily Header ===")
    print(json.dumps(header, indent=2))

    print(f"\n✅ Smoke test passed — day color: 0x{color:06x} ({get_day_name()})")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    else:
        print(__doc__)
