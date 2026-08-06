#!/usr/bin/env python3
"""
research_publisher.py — HermesForge Research Results Publisher

Posts the weekly research pipeline results to the #strategy-research
Discord channel as a rich embed with a colored left border that rotates
by day of week. Deletes all previous bot messages first, then crossposts.

Day-of-week color mapping (matches the trading-setup convention):
  Mon=#3498db (blue), Tue=#2ecc71 (green), Wed=#e67e22 (orange),
  Thu=#9b59b6 (purple), Fri=#e74c3c (red), Sat=#1abc9c (teal),
  Sun=#f1c40f (gold)

Usage:
    python3 research_publisher.py                    # post + crosspost
    python3 research_publisher.py --dry-run           # format only
    python3 research_publisher.py --channel-id <id>   # override channel
"""

import os
import sys
import json
import subprocess
import pathlib
import datetime
import time
import glob

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
API_BASE = "https://discord.com/api/v10"

CHANNEL_ID = os.environ.get("STRATEGY_RESEARCH_CHANNEL_ID", "1534834809451450409")

RESEARCH_DATA_DIR = REPO_ROOT / "data"

# ── Day-of-Week Color Mapping ────────────────────────────────────────────────

DAY_COLORS = {
    0: 0x3498db,  # Monday    — blue
    1: 0x2ecc71,  # Tuesday   — green
    2: 0xe67e22,  # Wednesday — orange
    3: 0x9b59b6,  # Thursday  — purple
    4: 0xe74c3c,  # Friday    — red
    5: 0x1abc9c,  # Saturday  — teal
    6: 0xf1c40f,  # Sunday    — gold
}

DAY_NAMES = {
    0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
    4: "Friday", 5: "Saturday", 6: "Sunday",
}


# ── Load Latest Research ──────────────────────────────────────────────────────

def _load_latest_research() -> dict:
    """Load the most recent research pipeline JSON output."""
    pattern = str(RESEARCH_DATA_DIR / "research-*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    with open(files[-1]) as f:
        return json.load(f)


# ── Layman Narratives ─────────────────────────────────────────────────────────
# Plain-English explanations of each factor and strategy for non-quant readers.

FACTOR_NARRATIVES = {
    "MOM12_1": {
        "what": "12-month price momentum (skipping the most recent month)",
        "why": "Classic academic discovery: assets that went up the most over the past year tend to keep outperforming. We skip the recent month to avoid short-term bounce effects.",
        "inverted_means": "Momentum is NOT working — assets that went up most are now underperforming. This suggests a regime shift where trend-following is failing.",
    },
    "REV1": {
        "what": "1-month price reversal",
        "why": "The idea that assets that dropped the most in the past month tend to bounce back (mean reversion). Short-term losers recover.",
        "inverted_means": "Reversal is NOT working — assets that dropped keep dropping. This confirms a momentum-dominant regime where trend-following beats mean-reversion.",
    },
    "LOWVOL": {
        "what": "Low-volatility anomaly (60-day price volatility)",
        "why": "Academic research shows less volatile assets tend to outperform over time, contradicting the textbook idea that higher risk always means higher reward.",
        "inverted_means": "Low-volatility is NOT working — volatile assets are outperforming calm ones. This happens during speculative or momentum-driven markets where risk-taking is rewarded.",
    },
    "LIQUID": {
        "what": "Liquidity factor (average trading volume over 60 days)",
        "why": "More liquid assets (heavily traded) behave differently from illiquid ones. The liquidity premium is a well-known market anomaly.",
        "inverted_means": "Less liquid assets are outperforming — smaller/illiquid assets are leading, which can happen during speculative rallies.",
    },
    "PRICEMOM": {
        "what": "Price level relative to 200-day moving average",
        "why": "If price is above its 200-day average, the asset is in a long-term uptrend. This is one of the simplest trend filters used by traders.",
        "inverted_means": "Assets below their 200-day average are outperforming those above it — a sign that mean reversion is dominating over trend following.",
    },
    "RSI14": {
        "what": "Relative Strength Index (14-period, 0-100 scale)",
        "why": "RSI measures the speed and size of price moves. Traditionally, RSI below 30 means 'oversold' (a buy signal) and above 70 means 'overbought' (a sell signal). This is the classic mean-reversion interpretation.",
        "inverted_means": "The traditional interpretation is BACKWARDS right now. Buying 'overbought' assets (RSI > 70) outperforms buying 'oversold' ones. This strongly confirms a momentum-dominant regime where strong assets keep going strong. A strategy that flips RSI logic — buying strength instead of buying weakness — could capture this edge.",
    },
    "BB_WIDTH": {
        "what": "Bollinger Band width (volatility squeeze/expansion measure)",
        "why": "When Bollinger Bands squeeze tight (low volatility), it often precedes a major move. The question is: does buying low-volatility periods predict future outperformance?",
        "inverted_means": "High-volatility periods are outperforming low-volatility ones — the market is rewarding risk-taking over calm periods.",
    },
    "ATR_PCT": {
        "what": "Average True Range as a percentage of price",
        "why": "Measures how much an asset typically moves per day relative to its price. Higher ATR% = more volatile asset. Tests whether low-volatility assets outperform.",
        "inverted_means": "Volatile assets are outperforming — the market is rewarding higher-risk, higher-movement assets. Consistent with a momentum/speculative regime.",
    },
    "VOL_ROC": {
        "what": "Volume rate of change (10-day)",
        "why": "Measures whether trading volume is increasing or decreasing. Rising volume can confirm a price move is real (more participation = stronger signal).",
        "inverted_means": "Falling volume assets are outperforming — price moves on low volume may be more sustainable than volume-driven spikes.",
    },
    "ADX_TREND": {
        "what": "Average Directional Index (trend strength, not direction)",
        "why": "ADX above 25 means a strong trend, below 20 means no clear trend. Tests whether trending assets outperform non-trending ones.",
        "inverted_means": "Non-trending (ranging) assets are outperforming — choppy markets are producing better returns than directional trends.",
    },
}

STRATEGY_HISTORIES = {
    "STR-A": {
        "name": "MA Pullback + Fibonacci",
        "hypothesis": "When price pulls back to the 50-day moving average within an established trend, entering at the Fibonacci 38-62% retracement zone should catch the next leg up. Targets via Fibonacci extensions.",
        "what_happened": "Walk-forward validation showed no statistical edge. The pullback entries didn't reliably predict which trends would continue versus reverse.",
    },
    "STR-B": {
        "name": "MACD Histogram Divergence",
        "hypothesis": "When price makes a new swing high but the MACD momentum indicator makes a lower high (or vice versa), it signals momentum exhaustion — the trend is running out of steam. Enter on the MACD line/signal cross with an ATR-based stop.",
        "what_happened": "This is one of our two LIVE strategies. It works because divergence genuinely captures momentum shifts. Current stats: Mean R=1.003, 50 signals, Sharpe 0.61. The edge is real but not statistically significant on its own (p=0.21) — it works best in combination with regime filtering.",
    },
    "STR-C": {
        "name": "Breakout + Volume",
        "hypothesis": "Breakouts above 20-day highs with 1.5x average volume are 'real' breakouts (institutional participation), not fakeouts. Prior high becomes new support.",
        "what_happened": "Walk-forward showed volume didn't distinguish real breakouts from fake ones. 241 signals but mean R=0.53 with p=0.19 — possible but unconfirmed edge.",
    },
    "STR-D": {
        "name": "S/R Role Reversal",
        "hypothesis": "Prior resistance tested as new support (role reversal) creates high-probability entries. Two-bar reclaim confirms the level holds.",
        "what_happened": "Walk-forward showed NO EDGE (p=0.435, R=0.033). The pattern looks great on charts but is statistically random. Killed in Phase 1B.",
    },
    "STR-E": {
        "name": "RSI Mean Reversion",
        "hypothesis": "RSI extremes (below 30 = oversold, above 70 = overbought) signal mean-reversion entries. Buy oversold, sell overbought, expecting return to RSI 50.",
        "what_happened": "Walk-forward showed no edge. In trending markets, RSI extremes persist rather than revert. Interestingly, the factor screener now confirms this — RSI is inverted, meaning the traditional mean-reversion interpretation is backwards in the current regime.",
    },
    "STR-F": {
        "name": "Bollinger Squeeze",
        "hypothesis": "When Bollinger Bands squeeze tight (low volatility), the subsequent expansion creates a tradeable breakout. Direction determined by candle close outside bands.",
        "what_happened": "Failed walk-forward — the direction of breakout was not predictable from the squeeze alone. 58 signals, mean R=-0.07. The squeeze predicts volatility expansion but not direction.",
    },
    "STR-G": {
        "name": "Relative Strength / Sector Rotation",
        "hypothesis": "Ranking sectors by relative strength and rotating into the strongest sectors captures sector rotation alpha. Long strongest, short weakest.",
        "what_happened": "Failed walk-forward — 417 signals but mean R=0.45 with p=0.30. Transaction costs from frequent rotation ate the edge. Possible but not robust enough.",
    },
    "STR-H": {
        "name": "First Pullback Trend Swing",
        "hypothesis": "The first pullback in a newly established trend offers the highest risk-reward entry. Swing-segmented leg definition identifies these pullbacks.",
        "what_happened": "Only 1 signal in recent data — the pattern is too rare to be practical as a standalone strategy. Killed for insufficient signal frequency.",
    },
    "STR-I": {
        "name": "Adaptive Trend (Momentum + ATR Trailing Stop)",
        "hypothesis": "When 10-bar price momentum exceeds +/-20%, enter in the direction of the trend. Use an ATR(14) trailing stop at 2.0x that ratchets (only moves in the favorable direction) with the trend. 120-bar time stop. Restricted to stocks (killed on crypto where Sharpe was only 0.151).",
        "what_happened": "LIVE and our strongest performer. Walk-forward confirmed robust edge: Sharpe 1.19, p=0.01, 56 signals, mean R=0.54. The key insight: momentum triggers + ratcheting ATR stops capture trends efficiently. Restricted to stocks per ADR-004 (asset-class independence rule).",
    },
    "STR-J": {
        "name": "EUFEARIA CCI Reversal",
        "hypothesis": "CCI (Commodity Channel Index) extremes as reversal signals. Based on EUFEARIA PRO 7 Pine Script. Multi-oscillator confirmation.",
        "what_happened": "Walk-forward showed no edge — 485 signals, mean R=-0.008, p=0.92. The indicator was curve-fit to historical data and didn't generalize.",
    },
    "STR-K": {
        "name": "Breadth Gap",
        "hypothesis": "When market breadth (advance/decline ratio) diverges from price, it signals an upcoming reversal. Extremes in breadth mark turning points.",
        "what_happened": "Failed — 0 signals in recent data. The breadth conditions were too restrictive and the pattern didn't appear.",
    },
    "STR-L": {
        "name": "ATR Contraction",
        "hypothesis": "When ATR contracts significantly (volatility compression), an expansion is imminent. Enter on the breakout from the contraction.",
        "what_happened": "WATCH status — only 6 signals in 7 years. Too rare to validate with walk-forward, but the concept (low volatility precedes expansion) is sound. Retained as WATCH pending more data.",
    },
    "STR-M": {
        "name": "Selling Climax",
        "hypothesis": "High-volume capitulation bars mark the end of selling pressure and the start of a reversal. Counter-trend entry after extreme selling.",
        "what_happened": "Only 1 signal — too rare. The pattern (capitulation volume) happens infrequently and didn't produce enough signals to validate.",
    },
    "STR-N": {
        "name": "Outside Day Key Reversal",
        "hypothesis": "An outside day (price makes both a higher high AND a lower low than the previous day, then closes in the direction of the reversal) signals a shift in supply/demand balance. The engulfing pattern suggests the opposing side has taken control.",
        "what_happened": "Originally KILLED — insufficient edge in the initial test. But the latest revival scan found 14 signals with a 71% hit rate and mean R=0.41 (p=0.064). This is a FRAGILE but interesting edge. The market may have shifted in a way that makes this pattern more reliable. Recommended for full walk-forward revalidation.",
    },
    "STR-O": {
        "name": "Price Momentum Factor",
        "hypothesis": "Single-factor price momentum for crypto: price relative to SMA200 as the sole signal. If price is above SMA200, go long; below, go short.",
        "what_happened": "Walk-forward showed no standalone edge — 384 signals, mean R=-0.07, p=0.16. Single-factor approaches don't work well for crypto; the cross-sectional approach (STR-P) is superior.",
    },
    "STR-P": {
        "name": "Cross-Sectional Factor Ranking",
        "hypothesis": "Rank all cryptos by a composite of 3 factors (12-month momentum, dollar volume liquidity, price vs SMA200). Long the top quintile (highest composite), short the bottom quintile. The edge is in RELATIVE ranking, not absolute thresholds — which cryptos are strongest vs which are weakest, not whether any individual crypto is 'high' or 'low'.",
        "what_happened": "WATCH status — walk-forward confirmed a thin but statistically significant edge: OOS R=0.12, p=0.032, 4 out of 5 test windows positive. The edge is small but real. Currently the only strategy producing crypto signals (14 setups). 358 recent signals but mean R=-0.055 — the edge has weakened in the current ranging regime.",
    },
}


# ── Format Embed ──────────────────────────────────────────────────────────────

def _format_factor_narrative(factor_name: str, sharpe: float, p_val: float,
                              ann_ret: float, asset_label: str) -> str:
    """Format a factor candidate with layman narrative."""
    narrative = FACTOR_NARRATIVES.get(factor_name, {})
    what = narrative.get("what", factor_name)
    why = narrative.get("why", "")
    direction = "inverted" if sharpe < 0 else "normal"
    inverted_text = narrative.get("inverted_means", "") if direction == "inverted" else ""

    lines = [
        f"★ **{factor_name} ({asset_label})**",
        f"  *What it measures:* {what}",
        f"  *The hypothesis:* {why}",
        f"  *Finding:* Sharpe {sharpe:.2f}, p={p_val:.4f}, annual {ann_ret*100:.1f}% ({direction})",
    ]
    if inverted_text:
        lines.append(f"  *What this means:* {inverted_text}")
    return "\n".join(lines)


def _format_strategy_narrative(strat_id: str, mean_r: float, p_val: float,
                                n_sig: int, hit_rate: float, context: str = "") -> str:
    """Format a strategy with its history and hypothesis."""
    history = STRATEGY_HISTORIES.get(strat_id, {})
    name = history.get("name", strat_id)
    hypothesis = history.get("hypothesis", "No hypothesis recorded.")
    what_happened = history.get("what_happened", "")

    lines = [
        f"★ **{strat_id} — {name}**",
        f"  *The hypothesis:* {hypothesis}",
    ]
    if context == "revival":
        lines.append(f"  *Why it was killed:* {what_happened}")
        lines.append(f"  *What's new:* {n_sig} recent signals, {hit_rate*100:.0f}% hit rate, mean R={mean_r:.4f}, p={p_val:.4f}")
        lines.append(f"  *What this means:* The market may have shifted in a way that makes this pattern work again. Worth a full revalidation.")
    elif context == "decay":
        lines.append(f"  *Current status:* {what_happened}")
    else:
        lines.append(f"  *What happened:* {what_happened}")
    return "\n".join(lines)


def _format_factor_summary(fs_data: dict, asset_label: str) -> list:
    """Format factor screener findings for one asset class with narratives. Returns lines."""
    lines = []
    n_cands = fs_data.get("n_candidates", 0)
    n_tested = fs_data.get("n_factors_tested", 0)
    lines.append(f"**{n_tested} factors tested | {n_cands} flagged as potential edges**")
    lines.append("")

    candidates = fs_data.get("candidates", [])
    if candidates:
        for c in candidates:
            factor = c.get("factor", "?")
            sharpe = c.get("sharpe", 0)
            p_val = c.get("p_value", 1)
            ann_ret = c.get("annualized_return", 0)
            lines.append(_format_factor_narrative(factor, sharpe, p_val, ann_ret, asset_label))
            lines.append("")
    else:
        lines.append("*No factor candidates this run.*")
    return lines


def _format_revival(rt_data: dict) -> list:
    """Format revival tester findings with strategy histories. Returns lines."""
    lines = []
    n_tested = rt_data.get("strategies_tested", 0)
    n_cands = rt_data.get("n_candidates", 0)
    lines.append(f"**{n_tested} killed strategies re-tested on recent data**")
    lines.append(f"**{n_cands} showing signs of life**")
    lines.append("")

    candidates = rt_data.get("candidates", [])
    if candidates:
        for c in candidates:
            strat = c.get("strategy", "?")
            name = c.get("name", "?")
            mean_r = c.get("mean_r", 0)
            p_val = c.get("p_value", 1)
            n_sig = c.get("n_signals", 0)
            hit_rate = c.get("hit_rate", 0)
            lines.append(_format_strategy_narrative(strat, mean_r, p_val, n_sig, hit_rate, context="revival"))
            lines.append("")
    else:
        lines.append("*No revival candidates — all 12 killed strategies remain dead in the current regime.*")
    return lines


def _format_decay(dm_data: dict) -> list:
    """Format decay monitor findings with strategy context. Returns lines."""
    lines = []
    n_monitored = dm_data.get("strategies_monitored", 0)
    n_decayed = dm_data.get("n_decayed", 0)
    lines.append(f"**{n_monitored} active strategies checked for edge erosion**")
    lines.append(f"**{n_decayed} showing significant decay**")
    lines.append("")

    decayed = dm_data.get("decayed", [])
    if decayed:
        for d in decayed:
            strat = d.get("strategy", "?")
            name = d.get("name", "?")
            decay_pct = d.get("decay_pct", 0)
            first_sharpe = d.get("first_sharpe", 0)
            curr_sharpe = d.get("sharpe_proxy", 0)
            history = STRATEGY_HISTORIES.get(strat, {})
            lines.append(f"⚠️ **{strat} ({history.get('name', name)})**")
            lines.append(f"  *Hypothesis:* {history.get('hypothesis', '?')}")
            lines.append(f"  *Decay:* Sharpe dropped from {first_sharpe:.2f} to {curr_sharpe:.2f} ({decay_pct*100:.0f}%)")
            lines.append(f"  *What this means:* The strategy's edge is eroding. May need parameter adjustment or retirement.")
            lines.append("")
    else:
        lines.append("✓ All monitored strategies stable — no edge decay detected.")
        lines.append("")

    # Show current health for each monitored strategy
    results = dm_data.get("results", [])
    if results:
        lines.append("*Current strategy health:*")
        for r in results:
            if "error" in r:
                continue
            strat = r.get("strategy", "?")
            name = r.get("name", "?")
            mean_r = r.get("mean_r", 0)
            sharpe = r.get("sharpe_proxy", 0)
            p_val = r.get("p_value", 1)
            n_sig = r.get("n_signals", 0)
            status = r.get("status", "?")
            history = STRATEGY_HISTORIES.get(strat, {})
            lines.append(f"  **{strat}** ({status}): R={mean_r:.3f}, Sharpe={sharpe:.2f}, p={p_val:.3f}, {n_sig} signals")
            if n_sig == 0:
                lines.append(f"    _{history.get('what_happened', 'No signals in current regime.')}_")
            elif p_val < 0.05:
                lines.append(f"    _Statistically significant edge confirmed._")
            elif p_val < 0.20 and mean_r > 0:
                lines.append(f"    _Possible edge, not yet statistically significant._")
            else:
                lines.append(f"    _Edge is thin or absent in current regime._")
    return lines


def _format_hypotheses(hg_data: dict, asset_label: str) -> list:
    """Format hypothesis generator findings with context. Returns lines."""
    lines = []
    n_tested = hg_data.get("n_hypotheses_tested", 0)
    n_cands = hg_data.get("n_candidates", 0)
    top_factors = hg_data.get("top_factors", [])
    lines.append(f"**{n_tested} combinations tested | {n_cands} candidate(s)**")
    if top_factors:
        # Add brief factor explanations
        factor_blurbs = []
        for f in top_factors[:3]:
            narr = FACTOR_NARRATIVES.get(f, {})
            blurb = narr.get("what", f)
            factor_blurbs.append(f"{f} ({blurb})")
        lines.append(f"  Top factors: {', '.join(factor_blurbs)}")
    lines.append("")

    candidates = hg_data.get("candidates", [])
    if candidates:
        for c in candidates:
            hyp = c.get("hypothesis", "?")
            sharpe = c.get("sharpe", 0)
            p_val = c.get("p_value", 1)
            desc = c.get("description", "")
            lines.append(f"  ★ **{hyp}**: Sharpe {sharpe:.2f}, p={p_val:.4f}")
            lines.append(f"    {desc}")
            lines.append("")
    else:
        lines.append(f"  *No new strategy candidates this run. The top factors individually show edges but combining them didn't improve results — the momentum regime is so dominant that diversification across factors doesn't add value right now.*")
    return lines


def format_research_embeds() -> list:
    """Format the research pipeline results as a list of Discord embeds.
    
    Uses multiple embeds to accommodate layman-friendly narratives
    while staying under Discord's 1024-char per-field and 6000-char per-embed limits.
    All embeds share the same day-of-week color (left border).
    """
    dt = datetime.datetime.utcnow()
    dow = dt.weekday()
    color = DAY_COLORS[dow]
    day_name = DAY_NAMES[dow]

    research = _load_latest_research()
    if not research:
        return [{
            "title": "📊 HermesForge Weekly Research Report",
            "description": "No research data found. Pipeline may not have run yet.",
            "color": color,
            "timestamp": dt.isoformat() + "Z",
        }]

    runtime = research.get("runtime_seconds", 0)
    total_items = research.get("total_action_items", 0)

    fs = research.get("factor_screener", {})
    rt = research.get("revival_tester", {})
    dm = research.get("decay_monitor", {})
    hg = research.get("hypothesis_generator", {})

    stock_fs = fs.get("stock", {})
    crypto_fs = fs.get("crypto", {})
    stock_hg = hg.get("stock", {})
    crypto_hg = hg.get("crypto", {})

    embeds = []

    # ── Embed 1: Executive Summary + Factor Screener ──
    desc_lines = [
        f"**{day_name}, {dt.strftime('%Y-%m-%d %H:%M')} UTC**",
        f"Pipeline runtime: {runtime:.0f}s | Action items: {total_items}",
        "",
        f"🔬 Factor anomalies: {stock_fs.get('n_candidates',0)} stocks, {crypto_fs.get('n_candidates',0)} crypto",
        f"♻️ Revival candidates: {rt.get('n_candidates',0)}",
        f"📉 Edge decay: {dm.get('n_decayed',0)}",
        f"💡 New strategy candidates: {stock_hg.get('n_candidates',0)} stocks, {crypto_hg.get('n_candidates',0)} crypto",
    ]

    fields1 = []

    # Factor screener — stocks (may need multiple fields for narratives)
    stock_lines = _format_factor_summary(stock_fs, "Stocks")
    stock_text = "\n".join(stock_lines)
    if len(stock_text) > 1024:
        # Split into individual candidate entries
        entries = stock_text.split("\n\n")
        chunk, chunk_len = [], 0
        part = 1
        for entry in entries:
            if chunk_len + len(entry) + 2 > 1000 and chunk:
                label = "🔬 Factor Screener — Stocks" if part == 1 else "🔬 Factor Screener — Stocks (cont.)"
                fields1.append({"name": label, "value": "\n\n".join(chunk)[:1024], "inline": False})
                chunk, chunk_len = [], 0
                part += 1
            chunk.append(entry)
            chunk_len += len(entry) + 2
        if chunk:
            label = "🔬 Factor Screener — Stocks" if part == 1 else "🔬 Factor Screener — Stocks (cont.)"
            fields1.append({"name": label, "value": "\n\n".join(chunk)[:1024], "inline": False})
    else:
        fields1.append({"name": "🔬 Factor Screener — Stocks", "value": stock_text[:1024], "inline": False})

    # Factor screener — crypto
    crypto_lines = _format_factor_summary(crypto_fs, "Crypto")
    crypto_text = "\n".join(crypto_lines)
    if len(crypto_text) > 1024:
        entries = crypto_text.split("\n\n")
        chunk, chunk_len = [], 0
        part = 1
        for entry in entries:
            if chunk_len + len(entry) + 2 > 1000 and chunk:
                label = "🔬 Factor Screener — Crypto" if part == 1 else "🔬 Factor Screener — Crypto (cont.)"
                fields1.append({"name": label, "value": "\n\n".join(chunk)[:1024], "inline": False})
                chunk, chunk_len = [], 0
                part += 1
            chunk.append(entry)
            chunk_len += len(entry) + 2
        if chunk:
            label = "🔬 Factor Screener — Crypto" if part == 1 else "🔬 Factor Screener — Crypto (cont.)"
            fields1.append({"name": label, "value": "\n\n".join(chunk)[:1024], "inline": False})
    else:
        fields1.append({"name": "🔬 Factor Screener — Crypto", "value": crypto_text[:1024], "inline": False})

    embeds.append({
        "title": "📊 HermesForge Weekly Research Report",
        "description": "\n".join(desc_lines),
        "color": color,
        "fields": fields1,
        "footer": {"text": f"Research Pipeline (1/3) | {day_name} #{color:06x}"},
        "timestamp": dt.isoformat() + "Z",
    })

    # ── Embed 2: Revival Tester + Decay Monitor ──
    fields2 = []

    revival_lines = _format_revival(rt)
    fields2.append({
        "name": "♻️ Killed Strategy Revival",
        "value": "\n".join(revival_lines)[:1024],
        "inline": False,
    })

    decay_lines = _format_decay(dm)
    # Split decay if too long
    decay_text = "\n".join(decay_lines)
    if len(decay_text) > 1024:
        # Split at a reasonable point
        mid = decay_text[:1000].rfind("\n\n")
        if mid < 500:
            mid = 1024
        fields2.append({
            "name": "📉 Edge Decay Monitor",
            "value": decay_text[:mid][:1024],
            "inline": False,
        })
        fields2.append({
            "name": "📉 Edge Decay (cont.)",
            "value": decay_text[mid:].strip()[:1024],
            "inline": False,
        })
    else:
        fields2.append({
            "name": "📉 Edge Decay Monitor",
            "value": decay_text,
            "inline": False,
        })

    embeds.append({
        "title": "📊 Research Report (continued)",
        "description": "Strategy revival and edge decay monitoring.",
        "color": color,
        "fields": fields2,
        "footer": {"text": f"Research Pipeline (2/3) | {day_name} #{color:06x}"},
        "timestamp": dt.isoformat() + "Z",
    })

    # ── Embed 3: Hypothesis Generator + Action Items ──
    fields3 = []

    # Hypothesis generator — stocks
    stock_hyp_lines = ["**Stocks:**"]
    stock_hyp_lines.extend(_format_hypotheses(stock_hg, "Stocks"))
    fields3.append({
        "name": "💡 Hypothesis Generator — Stocks",
        "value": "\n".join(stock_hyp_lines)[:1024],
        "inline": False,
    })

    # Hypothesis generator — crypto
    crypto_hyp_lines = ["**Crypto:**"]
    crypto_hyp_lines.extend(_format_hypotheses(crypto_hg, "Crypto"))
    fields3.append({
        "name": "💡 Hypothesis Generator — Crypto",
        "value": "\n".join(crypto_hyp_lines)[:1024],
        "inline": False,
    })

    # Action items summary
    action_lines = []
    if total_items == 0:
        action_lines.append("*No new edges found this week. All strategies stable.*")
    else:
        action_lines.append(f"**{total_items} item(s) require investigation:**")
        if stock_fs.get("n_candidates",0) + crypto_fs.get("n_candidates",0) > 0:
            action_lines.append("  • Factor anomalies: design strategies around inverted factors")
        if rt.get("n_candidates",0) > 0:
            action_lines.append("  • Revival candidates: re-run full walk-forward validation")
        if dm.get("n_decayed",0) > 0:
            action_lines.append("  • Decay flags: investigate and consider strategy retirement")
        if stock_hg.get("n_candidates",0) + crypto_hg.get("n_candidates",0) > 0:
            action_lines.append("  • New hypotheses: full walk-forward validation needed")
    action_lines.append("")
    action_lines.append(f"Full report: `vault/research/research-{dt.strftime('%Y-%m-%d')}.md`")

    fields3.append({
        "name": "🎯 Action Items",
        "value": "\n".join(action_lines)[:1024],
        "inline": False,
    })

    embeds.append({
        "title": "📊 Research Report (continued)",
        "description": "New strategy hypotheses and action items.",
        "color": color,
        "fields": fields3,
        "footer": {"text": f"Research Pipeline (3/3) | {day_name} #{color:06x}"},
        "timestamp": dt.isoformat() + "Z",
    })

    return embeds


def format_research_embed() -> dict:
    """Legacy: return first embed only. Use format_research_embeds() for full report."""
    embeds = format_research_embeds()
    return embeds[0] if embeds else {}


# ── Discord API helpers ──────────────────────────────────────────────────────

def _api_request(method: str, url: str, data: dict = None) -> dict:
    """Make a Discord API request."""
    cmd = ["curl", "-s", "-X", method, "-H", f"Authorization: Bot {DISCORD_BOT_TOKEN}"]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd += [url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {"error": result.stdout[:500]}


def _get_all_messages(channel_id: str) -> list:
    """Fetch all messages from the channel (up to 100)."""
    url = f"{API_BASE}/channels/{channel_id}/messages?limit=100"
    result = _api_request("GET", url)
    if isinstance(result, list):
        return result
    return []


def _delete_message(channel_id: str, message_id: str) -> dict:
    """Delete a message from a channel."""
    return _api_request("DELETE", f"{API_BASE}/channels/{channel_id}/messages/{message_id}")


def _crosspost_message(channel_id: str, message_id: str) -> dict:
    """Crosspost (publish) a message from an announcement channel."""
    return _api_request("POST", f"{API_BASE}/channels/{channel_id}/messages/{message_id}/crosspost")


def _delete_all_bot_messages(channel_id: str) -> int:
    """Delete all messages posted by the bot in the channel. Returns count deleted."""
    messages = _get_all_messages(channel_id)
    deleted = 0
    for msg in messages:
        author = msg.get("author", {})
        if author.get("bot") and author.get("username", "").startswith("Trading Swarm"):
            msg_id = msg.get("id")
            if msg_id:
                _delete_message(channel_id, msg_id)
                deleted += 1
                time.sleep(0.6)
    return deleted


# ── Main ──────────────────────────────────────────────────────────────────────

def post_research_report(channel_id: str = CHANNEL_ID, dry_run: bool = False) -> dict:
    """Post the research report as multiple messages (one embed each), replacing all previous posts, then crosspost the first."""
    embeds = format_research_embeds()

    if dry_run:
        print("=== DRY RUN ===")
        for i, emb in enumerate(embeds):
            print(f"\n--- Embed {i+1}/{len(embeds)} ---")
            print(f"Title: {emb.get('title','')}")
            print(f"Color: #{emb.get('color',0):06x}")
            print(f"Description ({len(emb.get('description',''))} chars):")
            print(emb.get('description','')[:200])
            for j, f in enumerate(emb.get('fields',[])):
                print(f"  Field {j}: {f['name']} -> {len(f['value'])} chars")
            total = len(emb.get('description','')) + sum(len(f['value']) for f in emb.get('fields',[]))
            print(f"Total embed chars: {total}")
        return {"status": "dry_run", "n_embeds": len(embeds)}

    if not DISCORD_BOT_TOKEN:
        return {"error": "DISCORD_BOT_TOKEN not set"}

    # 1. Delete all previous bot messages AND webhook messages
    print("  Deleting all previous bot messages...")
    n_deleted = _delete_all_bot_messages(channel_id)
    if n_deleted > 0:
        print(f"  ✅ Deleted {n_deleted} previous message(s)")
    else:
        print("  ℹ️ No previous messages to delete")

    # Also delete old webhook crossposted messages in follower server
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        from webhook_utils import create_crossposter
        wx = create_crossposter(str(channel_id), webhook_name="HermesForge Bot")
        if wx:
            n_wx = wx.delete_all()
            if n_wx > 0:
                print(f"  🧹 Deleted {n_wx} webhook messages in follower server")
    except Exception as e:
        print(f"  ℹ️ Webhook cleanup skipped: {e}")
    time.sleep(1)

    # 2. Post each embed as a separate message (Discord 6000-char total limit per message)
    msg_ids = []
    for i, embed in enumerate(embeds):
        payload = {"embeds": [embed]}
        result = _api_request("POST", f"{API_BASE}/channels/{channel_id}/messages", payload)
        if "id" not in result:
            return {"error": f"Failed to post embed {i+1}", "response": result}
        msg_ids.append(result["id"])
        print(f"  ✅ Embed {i+1}/{len(embeds)} posted (msg {result['id']})")

        # Crosspost via webhook (no tombstones) or native (fallback)
        wx = create_crossposter(str(channel_id), webhook_name="HermesForge Bot") if i == 0 else wx if 'wx' in dir() else None
        if wx:
            wx.post(payload)
        else:
            _crosspost_message(channel_id, result["id"])

        if i < len(embeds) - 1:
            time.sleep(0.8)  # Rate limit safety

    return {"status": "ok", "message_ids": msg_ids, "n_embeds": len(embeds)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="HermesForge Research Publisher")
    ap.add_argument("--dry-run", action="store_true", help="Format only, no posting")
    ap.add_argument("--channel-id", type=str, default=None, help="Override channel ID")
    args = ap.parse_args()

    ch_id = args.channel_id or CHANNEL_ID
    result = post_research_report(ch_id, dry_run=args.dry_run)
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    print("Done.")
