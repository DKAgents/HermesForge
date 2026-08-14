#!/usr/bin/env python3
"""
regime_filter.py — Universal Market Regime Filter

Combines multiple free data sources into a single regime assessment:
  - VIX (volatility regime)
  - DXY (dollar trend)
  - Yield curve (recession risk)
  - Crypto Fear & Greed (crypto sentiment)
  - Hyperliquid funding rates (crypto positioning)

This filter does NOT block trades (data collection phase). It TAGS each
signal with regime context so we can analyze performance by regime later.
When we have enough data, the filter can be upgraded to block or size
adjust based on regime.

Usage:
    from regime_filter import get_regime, tag_signal
    regime = get_regime()
    tagged = tag_signal(signal_dict, regime)
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from fetch_macro import get_vix_signal, get_dxy_signal, get_yield_curve_signal
from fetch_fear_greed import get_current_fg
from fetch_hyperliquid_metrics import get_funding_summary
from fetch_lunarcrush import get_crypto_sentiment_summary, get_topic_sentiment_summary
from fetch_defillama import get_tvl_summary
from fetch_stablecoin_supply import get_stablecoin_summary
from fetch_put_call_ratio import get_put_call_summary
from compute_breadth import get_breadth_summary
from compute_volatility import compute_vol_risk_premium, get_crypto_volatility
from compute_rotation import get_rotation_summary
from compute_correlation import get_correlation_summary
from fetch_economic_calendar import get_next_high_impact_events
from fetch_short_interest import get_high_short_interest_stocks
from compute_strategy_regime import get_strategy_regime_summary


def get_regime() -> dict:
    """
    Get current market regime assessment from all available data sources.
    
    Returns:
    {
        "vix": {...},           # VIX regime
        "dxy": {...},           # Dollar trend
        "yield_curve": {...},   # Yield curve shape
        "fear_greed": {...},    # Crypto sentiment
        "funding": {...},       # Crypto positioning
        "stock_regime": str,    # "risk_on" / "elevated" / "risk_off" / "complacent"
        "crypto_regime": str,   # "risk_on" / "neutral" / "risk_off" / "greed"
        "overall": str,         # Combined assessment
        "timestamp": str,
    }
    """
    vix = get_vix_signal()
    dxy = get_dxy_signal()
    yc = get_yield_curve_signal()
    fg = get_current_fg()
    
    funding = {}
    try:
        funding = get_funding_summary()
    except Exception:
        pass  # funding is optional, don't fail the whole filter
    
    lunarcrush_crypto = {}
    try:
        lunarcrush_crypto = get_crypto_sentiment_summary()
    except Exception:
        pass  # LunarCrush is optional, don't fail the whole filter
    
    lunarcrush_topics = {}
    try:
        lunarcrush_topics = get_topic_sentiment_summary()
    except Exception:
        pass
    
    # New data sources (all optional — don't fail the regime if any is down)
    tvl = {}
    try:
        tvl = get_tvl_summary()
    except Exception:
        pass
    
    stablecoin = {}
    try:
        stablecoin = get_stablecoin_summary()
    except Exception:
        pass
    
    put_call = {}
    try:
        put_call = get_put_call_summary()
    except Exception:
        pass
    
    breadth = {}
    try:
        breadth = get_breadth_summary()
    except Exception:
        pass
    
    vol_premium = {}
    try:
        vol_premium = compute_vol_risk_premium()
    except Exception:
        pass
    
    rotation = {}
    try:
        rotation = get_rotation_summary()
    except Exception:
        pass
    
    correlation = {}
    try:
        correlation = get_correlation_summary()
    except Exception:
        pass
    
    # Economic calendar (upcoming high-impact events)
    economic_events = []
    try:
        economic_events = get_next_high_impact_events(days_ahead=7)
    except Exception:
        pass
    
    # Short interest (high short interest stocks)
    short_interest = {}
    try:
        si_result = get_high_short_interest_stocks(threshold=10.0)
        si_stocks = si_result.get("stocks", []) if isinstance(si_result, dict) else []
        if si_stocks:
            short_interest = {
                "count": si_result.get("count", len(si_stocks)),
                "top": [{"ticker": s.get("ticker", ""), "pct_float": s.get("short_pct_of_float", 0),
                         "days_to_cover": s.get("days_to_cover", 0)}
                        for s in si_stocks[:5]],
            }
    except Exception:
        pass
    
    # Strategy-regime performance heatmap
    strategy_regime = {}
    try:
        strategy_regime = get_strategy_regime_summary()
    except Exception:
        pass
    
    # --- Stock regime from VIX ---
    stock_regime = vix.get("regime", "unknown") if vix else "unknown"
    
    # --- Crypto regime from F&G + funding ---
    crypto_regime = "unknown"
    if fg:
        fg_val = fg.get("value", 50)
        if fg_val > 75:
            crypto_regime = "greed"
        elif fg_val > 55:
            crypto_regime = "risk_on"
        elif fg_val < 25:
            crypto_regime = "risk_off"
        elif fg_val < 45:
            crypto_regime = "fear"
        else:
            crypto_regime = "neutral"
    
    # Override if funding shows extreme positioning
    if funding:
        extreme_positive = sum(1 for f in funding.values() if f.get("extreme") == "positive_extreme")
        extreme_negative = sum(1 for f in funding.values() if f.get("extreme") == "negative_extreme")
        if extreme_positive >= 3:
            crypto_regime = "overheated"  # too many crowded longs
        elif extreme_negative >= 3:
            crypto_regime = "capitulation"  # too many crowded shorts, potential bounce
    
    # --- Overall regime ---
    overall = "neutral"
    if stock_regime in ("risk_off",) or crypto_regime in ("risk_off", "capitulation"):
        overall = "risk_off"
    elif stock_regime == "complacent" and crypto_regime == "greed":
        overall = "complacent"
    elif stock_regime in ("risk_on",) and crypto_regime in ("risk_on", "neutral"):
        overall = "risk_on"
    elif yc.get("inverted"):
        overall = "caution"  # inverted yield curve
    
    from datetime import datetime, timezone
    return {
        "vix": vix,
        "dxy": dxy,
        "yield_curve": yc,
        "fear_greed": fg,
        "funding": {k: {"current_rate": v["current_rate"], "extreme": v["extreme"]}
                     for k, v in funding.items()} if funding else {},
        "lunarcrush_crypto": {k: {"galaxy_score": v.get("galaxy_score", 0),
                                    "sentiment": v.get("sentiment", 50),
                                    "trend": v.get("trend", "flat")}
                                for k, v in lunarcrush_crypto.items()} if lunarcrush_crypto else {},
        "lunarcrush_topics": lunarcrush_topics,
        "tvl": {"total": tvl.get("total_tvl", 0), "trend": tvl.get("trend", "")} if tvl else {},
        "stablecoin": {"total_supply": stablecoin.get("total_supply", 0), "trend": stablecoin.get("trend", "")} if stablecoin else {},
        "put_call": put_call,
        "breadth": breadth,
        "vol_risk_premium": vol_premium,
        "rotation": rotation,
        "correlation": correlation,
        "economic_events": economic_events,
        "short_interest": short_interest,
        "strategy_regime": strategy_regime,
        "stock_regime": stock_regime,
        "crypto_regime": crypto_regime,
        "overall": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def tag_signal(signal: dict, regime: dict = None) -> dict:
    """
    Tag a trading signal with the current market regime context.
    
    This adds regime metadata to the signal for later analysis:
    - signal["regime_stock"] = "risk_on" / "elevated" / etc.
    - signal["regime_crypto"] = "risk_on" / "fear" / etc.
    - signal["regime_overall"] = "risk_on" / "risk_off" / etc.
    - signal["vix"] = 15.2
    - signal["dxy_trend"] = "up" / "down" / "flat"
    - signal["yield_curve"] = "normal" / "inverted" / etc.
    - signal["fear_greed"] = 45
    """
    if regime is None:
        regime = get_regime()
    
    signal["regime_stock"] = regime.get("stock_regime", "unknown")
    signal["regime_crypto"] = regime.get("crypto_regime", "unknown")
    signal["regime_overall"] = regime.get("overall", "neutral")
    
    vix = regime.get("vix", {})
    signal["vix"] = vix.get("current", 0)
    
    dxy = regime.get("dxy", {})
    signal["dxy_trend"] = dxy.get("trend", "unknown")
    
    yc = regime.get("yield_curve", {})
    signal["yield_curve"] = yc.get("steepness", "unknown")
    
    fg = regime.get("fear_greed", {})
    signal["fear_greed"] = fg.get("value", 50)
    
    # LunarCrush per-coin sentiment (if available for this ticker)
    lc_crypto = regime.get("lunarcrush_crypto", {})
    ticker = signal.get("ticker", "")
    if ticker in lc_crypto:
        signal["lc_galaxy_score"] = lc_crypto[ticker].get("galaxy_score", 0)
        signal["lc_sentiment"] = lc_crypto[ticker].get("sentiment", 50)
        signal["lc_trend"] = lc_crypto[ticker].get("trend", "flat")
    
    # Market breadth
    breadth = regime.get("breadth", {})
    if breadth:
        signal["breadth_pct_above_50ma"] = breadth.get("pct_above_50ma", 50)
        signal["breadth_divergence"] = breadth.get("divergence", "none")
    
    # Volatility risk premium
    vrp = regime.get("vol_risk_premium", {})
    if vrp:
        signal["vol_risk_premium"] = vrp.get("vol_risk_premium", 0)
        signal["vol_signal"] = vrp.get("signal", "neutral")
    
    # Correlation regime
    corr = regime.get("correlation", {})
    if corr:
        signal["correlation_regime"] = corr.get("correlation_regime", "normal")
    
    # Economic calendar (tag with next high-impact event if within 3 days)
    events = regime.get("economic_events", [])
    if events:
        signal["next_high_impact_event"] = events[0].get("event", "")
        signal["next_event_date"] = events[0].get("date", "")
    
    # Short interest (if this ticker has high short interest)
    si = regime.get("short_interest", {})
    if si and si.get("top"):
        ticker_upper = ticker.upper()
        for s in si["top"]:
            if s.get("ticker", "").upper() == ticker_upper:
                signal["short_interest_pct"] = s.get("pct_float", 0)
                signal["short_interest_dtc"] = s.get("days_to_cover", 0)
                break
    
    return signal


def format_regime_report(regime: dict = None) -> str:
    """Format regime as a concise text block for Discord/integration."""
    if regime is None:
        regime = get_regime()
    
    lines = ["📊 **Market Regime Assessment**\n"]
    
    # Overall
    overall_emoji = {
        "risk_on": "🟢",
        "neutral": "⚪",
        "caution": "🟡",
        "risk_off": "🔴",
        "complacent": "⚠️",
    }.get(regime["overall"], "⚪")
    lines.append(f"**Overall:** {overall_emoji} {regime['overall'].upper()}")
    lines.append("")
    
    # VIX
    vix = regime.get("vix", {})
    if vix:
        lines.append(f"**VIX:** {vix.get('current', 0):.1f} (20d MA: {vix.get('ma_20', 0):.1f}) → {vix.get('regime', '?')}")
    
    # DXY
    dxy = regime.get("dxy", {})
    if dxy:
        lines.append(f"**DXY:** {dxy.get('current', 0):.2f} → trend: {dxy.get('trend', '?')}")
    
    # Yield curve
    yc = regime.get("yield_curve", {})
    if yc:
        inv = " ⚠️ INVERTED" if yc.get("inverted") else ""
        lines.append(f"**Yield Curve:** {yc.get('steepness', '?')} (10Y={yc.get('tnx', 0):.2f}%, 13W={yc.get('irx', 0):.2f}%){inv}")
    
    # Fear & Greed
    fg = regime.get("fear_greed", {})
    if fg:
        lines.append(f"**Fear & Greed:** {fg.get('value', 0)} ({fg.get('classification', '?')})")
    
    # Stock regime
    lines.append(f"**Stock Regime:** {regime.get('stock_regime', '?')}")
    
    # Crypto regime
    lines.append(f"**Crypto Regime:** {regime.get('crypto_regime', '?')}")
    
    # Funding highlights
    funding = regime.get("funding", {})
    if funding:
        extremes = {k: v["extreme"] for k, v in funding.items() if v["extreme"] != "neutral"}
        if extremes:
            lines.append(f"**Funding Extremes:** {extremes}")
    
    # LunarCrush
    lc_crypto = regime.get("lunarcrush_crypto", {})
    if lc_crypto:
        lines.append(f"**LunarCrush Galaxy Scores:** {dict({k: v['galaxy_score'] for k, v in lc_crypto.items() if v.get('galaxy_score')})}")
    
    lc_topics = regime.get("lunarcrush_topics", {})
    if lc_topics:
        topic_summary = {k: f'{v.get("sentiment",0):.0f} ({v.get("trend","")})' for k, v in lc_topics.items() if v.get("sentiment")}
        if topic_summary:
            lines.append(f"**Topic Sentiment:** {topic_summary}")
    
    # Market breadth
    breadth = regime.get("breadth", {})
    if breadth:
        lines.append(f"**Breadth:** A/D={breadth.get('ad_ratio',0)}, "
                      f"{breadth.get('pct_above_50ma',0)}% > 50MA, "
                      f"{breadth.get('pct_above_200ma',0)}% > 200MA, "
                      f"NH={breadth.get('new_highs',0)} NL={breadth.get('new_lows',0)}")
        if breadth.get("divergence") != "none":
            lines.append(f"  ⚠️ **{breadth['divergence'].upper()} divergence detected**")
    
    # Volatility risk premium
    vrp = regime.get("vol_risk_premium", {})
    if vrp:
        lines.append(f"**Vol Risk Premium:** VIX={vrp.get('vix',0)} vs Realized={vrp.get('realized_vol_20d',0)}% "
                      f"(VRP={vrp.get('vol_risk_premium',0):+.1f}%) → {vrp.get('signal','')}")
    
    # Put/Call ratio
    pc = regime.get("put_call", {})
    if pc:
        lines.append(f"**Put/Call:** {pc.get('total_ratio',0)} (equity: {pc.get('equity_ratio',0)}) → {pc.get('regime','')}")
    
    # DeFi TVL
    tvl = regime.get("tvl", {})
    if tvl:
        lines.append(f"**DeFi TVL:** ${tvl.get('total',0)/1e9:.1f}B ({tvl.get('trend','')})")
    
    # Stablecoin supply
    sc = regime.get("stablecoin", {})
    if sc:
        lines.append(f"**Stablecoin Supply:** ${sc.get('total_supply',0)/1e9:.1f}B ({sc.get('trend','')})")
    
    # Sector rotation
    rot = regime.get("rotation", {})
    if rot:
        lines.append(f"**Sector Rotation:** Leading={rot.get('leading_sector','')}, "
                      f"Lagging={rot.get('lagging_sector','')}")
    
    # Correlation regime
    corr = regime.get("correlation", {})
    if corr:
        lines.append(f"**Correlation Regime:** {corr.get('correlation_regime','')} "
                      f"(avg={corr.get('avg_asset_correlation',0)})")
    
    # Economic calendar
    events = regime.get("economic_events", [])
    if events:
        lines.append(f"**Upcoming High-Impact Events:** {len(events)}")
        for ev in events[:3]:
            lines.append(f"  • {ev.get('date','')} {ev.get('time','')} — {ev.get('event','')} ({ev.get('country','')})")
    
    # Short interest
    si = regime.get("short_interest", {})
    if si and si.get("top"):
        top_si = ", ".join(f"{s['ticker']} {s['pct_float']:.1f}% (DTC {s['days_to_cover']:.1f})"
                           for s in si["top"])
        lines.append(f"**High Short Interest:** {si['count']} stocks — {top_si}")
    
    # Strategy-regime performance
    sr = regime.get("strategy_regime", {})
    if sr and sr.get("available"):
        lines.append(f"**Strategy-Regime Performance:** {sr.get('total_closed',0)} closed trades")
        if sr.get("best_combo"):
            bc = sr["best_combo"]
            lines.append(f"  ✅ Best: {bc['strategy']} @ {bc['regime']} → WR={bc['win_rate']}%, avg={bc['avg_r']:+.2f}R")
        if sr.get("worst_combo"):
            wc = sr["worst_combo"]
            lines.append(f"  ❌ Worst: {wc['strategy']} @ {wc['regime']} → WR={wc['win_rate']}%, avg={wc['avg_r']:+.2f}R")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Print full regime report
    regime = get_regime()
    print(format_regime_report(regime))
    print("\n--- Raw Data ---")
    import json
    print(json.dumps(regime, indent=2, default=str))
