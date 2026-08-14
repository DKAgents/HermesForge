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
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Print full regime report
    regime = get_regime()
    print(format_regime_report(regime))
    print("\n--- Raw Data ---")
    import json
    print(json.dumps(regime, indent=2, default=str))
