#!/usr/bin/env python3
"""
regime_strategy_selector.py — Regime-Aware Strategy Selector

Uses all available data sources to determine the current market regime
and recommends which strategies to activate, which to suppress, and
what position sizing adjustments to make.

This module is the "brain" that connects the regime filter to the 
strategy execution layer. It reads the full regime assessment and
produces actionable strategy directives.

Usage:
    from regime_strategy_selector import get_strategy_directives
    directives = get_strategy_directives()
    
    python3 regime_strategy_selector.py              # print recommendations
    python3 regime_strategy_selector.py --json        # JSON output
"""

import sys
import json
import argparse
import pathlib
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

# Strategy registry — all known strategies and their characteristics
STRATEGY_REGISTRY = {
    "STR-A": {"name": "MA Pullback + Fibonacci", "asset": "stock", "status": "KILLED",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "mean_reversion"},
    "STR-B": {"name": "MACD Histogram Divergence", "asset": "stock", "status": "LIVE",
              "regime_best": ["neutral", "diversified"], "regime_avoid": ["risk_off", "unified"],
              "base_risk": 1.0, "type": "divergence"},
    "STR-C": {"name": "Breakout + Volume", "asset": "stock", "status": "KILLED",
              "regime_best": ["risk_on"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "breakout"},
    "STR-D": {"name": "S/R Role Reversal", "asset": "stock", "status": "KILLED",
              "regime_best": ["neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "reversal"},
    "STR-E": {"name": "RSI Mean Reversion", "asset": "stock", "status": "KILLED",
              "regime_best": ["caution", "risk_off"], "regime_avoid": ["risk_on"],
              "base_risk": 1.0, "type": "mean_reversion"},
    "STR-F": {"name": "Bollinger Squeeze Breakout", "asset": "stock", "status": "KILLED",
              "regime_best": ["neutral", "risk_on"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "breakout"},
    "STR-G": {"name": "Relative Strength Rotation", "asset": "stock", "status": "KILLED",
              "regime_best": ["risk_on"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "momentum"},
    "STR-H": {"name": "First Pullback Trend Swing", "asset": "stock", "status": "KILLED",
              "regime_best": ["risk_on"], "regime_avoid": ["risk_off"],
              "base_risk": 0.5, "type": "trend_following"},
    "STR-I": {"name": "Adaptive Trend", "asset": "stock", "status": "LIVE",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "trend_following"},
    "STR-L": {"name": "ATR Contraction", "asset": "stock", "status": "WATCH",
              "regime_best": ["neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "volatility_breakout"},
    "STR-P": {"name": "Cross-Sectional Factor", "asset": "crypto", "status": "WATCH",
              "regime_best": ["neutral", "caution"], "regime_avoid": ["risk_off"],
              "base_risk": 0.5, "type": "factor"},
    # Autonomous-pipeline deployed 2026-08-16 (walk-forward OOS ROBUST EDGE,
    # but 2022-bear OOS window mean R -0.34 → WATCH risk + risk_off suppress).
    "STR-VIXC": {"name": "VIX Term-Structure Contango Breakout", "asset": "stock", "status": "WATCH",
                 "regime_best": ["risk_on", "neutral", "complacent"], "regime_avoid": ["risk_off"],
                 "base_risk": 0.5, "type": "breakout"},
    # ── US-114/US-115 pipeline strategies (2026-08-16) ──────────────────────
    "STR-Q": {"name": "Liquidity Sweep Reversal", "asset": "stock", "status": "LIVE",
              "regime_best": ["all"], "regime_avoid": [],
              "base_risk": 1.0, "type": "reversal"},
    "STR-R": {"name": "Williams Alligator Trend", "asset": "stock", "status": "LIVE",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "trend_following"},
    "STR-T": {"name": "Head & Shoulders Reversal", "asset": "stock", "status": "LIVE",
              "regime_best": ["neutral", "caution"], "regime_avoid": ["risk_on"],
              "base_risk": 1.0, "type": "reversal"},
    "STR-U": {"name": "Double Top/Bottom", "asset": "stock", "status": "LIVE",
              "regime_best": ["neutral", "caution"], "regime_avoid": ["risk_on"],
              "base_risk": 1.0, "type": "reversal"},
    "STR-V": {"name": "Triangle Breakout", "asset": "stock", "status": "LIVE",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "breakout"},
    "STR-W": {"name": "Flags & Pennants", "asset": "stock", "status": "LIVE",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "breakout"},
    "STR-X": {"name": "Parabolic SAR", "asset": "stock", "status": "LIVE",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "trend_following"},
    "STR-Y": {"name": "ADX/DMI Directional", "asset": "stock", "status": "LIVE",
              "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
              "base_risk": 1.0, "type": "trend_following"},
    "STR-Z": {"name": "Stochastic Oscillator", "asset": "stock", "status": "LIVE",
              "regime_best": ["neutral", "diversified"], "regime_avoid": ["risk_on"],
              "base_risk": 1.0, "type": "mean_reversion"},
    "STR-AA": {"name": "Williams %R", "asset": "stock", "status": "LIVE",
               "regime_best": ["neutral", "diversified"], "regime_avoid": ["risk_on"],
               "base_risk": 1.0, "type": "mean_reversion"},
    "STR-AB": {"name": "OBV Divergence", "asset": "stock", "status": "LIVE",
               "regime_best": ["neutral", "caution"], "regime_avoid": ["risk_on"],
               "base_risk": 1.0, "type": "divergence"},
    "STR-AC": {"name": "CCI Oscillator", "asset": "stock", "status": "LIVE",
               "regime_best": ["neutral", "diversified"], "regime_avoid": ["risk_on"],
               "base_risk": 1.0, "type": "mean_reversion"},
    "STR-AD": {"name": "Keltner Channel", "asset": "stock", "status": "LIVE",
               "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
               "base_risk": 1.0, "type": "breakout"},
    "STR-AE": {"name": "4-Week Rule (Donchian)", "asset": "stock", "status": "LIVE",
               "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
               "base_risk": 1.0, "type": "breakout"},
    "STR-AF": {"name": "Candlestick Reversal", "asset": "stock", "status": "LIVE",
               "regime_best": ["neutral", "diversified", "caution"], "regime_avoid": [],
               "base_risk": 1.0, "type": "reversal"},
    "STR-AG": {"name": "Wedge Breakout", "asset": "stock", "status": "LIVE",
               "regime_best": ["neutral", "caution"], "regime_avoid": ["risk_on"],
               "base_risk": 1.0, "type": "reversal"},
    "STR-AJ": {"name": "Intermarket Rotation", "asset": "stock", "status": "LIVE",
               "regime_best": ["risk_on", "neutral"], "regime_avoid": ["risk_off"],
               "base_risk": 1.0, "type": "macro"},
    # Autonomous-pipeline deployed 2026-08-18 (Phase 1A positive, WATCH risk).
    "STR-LOWCORR": {"name": "Low-Correlation Regime Stock Picker", "asset": "stock", "status": "WATCH",
                    "regime_best": ["risk_on", "neutral", "diversified"], "regime_avoid": ["risk_off", "unified"],
                    "base_risk": 0.5, "type": "regime_factor"},
    # Autonomous-pipeline deployed 2026-08-25 (Phase 1A p=0.157 SPECULATIVE,
    # walk-forward OOS mean R +0.131 but p=0.553 → WATCH risk).
    "STR-DEBASE": {"name": "Treasury Buyback Debasement Regime", "asset": "crypto", "status": "WATCH",
                   "regime_best": ["risk_on", "neutral", "complacent"], "regime_avoid": ["risk_off"],
                   "base_risk": 0.5, "type": "macro_regime"},
}


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  Warning: {fn.__name__} failed: {e}", file=sys.stderr)
        return None


def get_regime_state() -> dict:
    """Get the full current regime state from all data sources."""
    from regime_filter import get_regime
    
    regime = _safe_call(get_regime)
    if not regime:
        return {"available": False, "reason": "regime filter unavailable"}
    
    return {
        "available": True,
        "overall": regime.get("overall", "neutral"),
        "stock_regime": regime.get("stock_regime", "unknown"),
        "crypto_regime": regime.get("crypto_regime", "unknown"),
        "vix": regime.get("vix", {}).get("current", 0),
        "vix_regime": regime.get("vix", {}).get("regime", "unknown"),
        "fear_greed": regime.get("fear_greed", {}).get("value", 50),
        "breadth_pct_50ma": regime.get("breadth", {}).get("pct_above_50ma", 50),
        "breadth_divergence": regime.get("breadth", {}).get("divergence", "none"),
        "vol_risk_premium": regime.get("vol_risk_premium", {}).get("vol_risk_premium", 0),
        "correlation_regime": regime.get("correlation", {}).get("correlation_regime", "normal"),
        "put_call": regime.get("put_call", {}).get("total_ratio", 1.0),
        "tvl_trend": regime.get("tvl", {}).get("trend", ""),
        "stablecoin_trend": regime.get("stablecoin", {}).get("trend", ""),
        "leading_sector": regime.get("rotation", {}).get("leading_sector", ""),
        "lagging_sector": regime.get("rotation", {}).get("lagging_sector", ""),
        "funding_extremes": len([k for k, v in regime.get("funding", {}).items()
                                  if v.get("extreme", "neutral") != "neutral"]),
        "high_impact_events": len(regime.get("economic_events", [])),
    }


def get_strategy_directives() -> dict:
    """
    Generate strategy directives based on current regime.
    
    Returns:
    {
        "timestamp": str,
        "regime": {...},
        "directives": {
            "STR-X": {
                "action": "run" | "suppress" | "boost" | "reduce",
                "risk_multiplier": float,  # 0.0 to 2.0
                "reason": str,
                "filter_conditions": [list of conditions to check],
            }
        },
        "overall_posture": str,  # "aggressive", "normal", "defensive", "opportunistic"
        "summary": str,
    }
    """
    state = get_regime_state()
    if not state.get("available"):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "regime": state,
            "directives": {},
            "overall_posture": "unknown",
            "summary": "Regime filter unavailable — running all strategies at default risk.",
        }
    
    overall = state["overall"]
    vix = state["vix"]
    fg = state["fear_greed"]
    breadth_50 = state["breadth_pct_50ma"]
    corr_regime = state["correlation_regime"]
    vol_premium = state["vol_risk_premium"]
    pc_ratio = state["put_call"]
    funding_extremes = state["funding_extremes"]
    high_impact = state["high_impact_events"]
    
    # Determine correlation regime for strategy matching
    corr_tag = "diversified" if corr_regime == "diversified" else "unified" if corr_regime == "unified" else "normal"
    
    # Overall posture
    posture = "normal"
    posture_reasons = []
    
    if overall == "risk_off":
        posture = "defensive"
        posture_reasons.append(f"Overall regime = risk_off (VIX={vix:.1f})")
    elif overall == "risk_on":
        if corr_tag == "diversified":
            posture = "aggressive"
            posture_reasons.append("Risk-on regime + diversified correlations = stock-picking environment")
        else:
            posture = "normal"
            posture_reasons.append("Risk-on but high correlations — broad index preferred")
    elif overall == "complacent":
        posture = "opportunistic"
        posture_reasons.append(f"Complacent regime — F&G={fg}, P/C={pc_ratio}")
    elif overall == "caution":
        posture = "opportunistic"
        posture_reasons.append(f"Caution regime — VIX={vix:.1f}, F&G={fg}")
    
    # Additional posture adjustments
    if vol_premium > 3:
        posture_reasons.append(f"VRP={vol_premium:+.1f}% — VIX overestimating fear, contrarian bullish")
    elif vol_premium < -3:
        posture_reasons.append(f"VRP={vol_premium:+.1f}% — VIX underestimating risk, cautious")
    
    if funding_extremes >= 3:
        posture_reasons.append(f"{funding_extremes} funding extremes — squeeze risk elevated")
    
    if high_impact > 0:
        posture_reasons.append(f"{high_impact} high-impact economic events in next 7 days — reduce new entries 24h before/after")
    
    # Generate per-strategy directives
    directives = {}
    
    for strat_id, strat_info in STRATEGY_REGISTRY.items():
        if strat_info["status"] == "KILLED":
            directives[strat_id] = {
                "action": "skip",
                "risk_multiplier": 0.0,
                "reason": f"Strategy KILLED — do not run",
            }
            continue
        
        action = "run"
        risk_mult = 1.0
        reasons = []
        filter_conditions = []
        
        # Check regime fit
        regime_best = strat_info["regime_best"]
        regime_avoid = strat_info["regime_avoid"]
        
        # Map overall regime to strategy regime tags
        regime_tags = [overall]
        if corr_tag == "diversified":
            regime_tags.append("diversified")
        elif corr_tag == "unified":
            regime_tags.append("unified")
        
        # Check if current regime is in avoid list
        if any(r in regime_avoid for r in regime_tags):
            action = "suppress"
            risk_mult = 0.0
            reasons.append(f"Current regime ({overall}) is in avoid list for {strat_id}")
        # Check if current regime is in best list
        elif any(r in regime_best for r in regime_tags):
            action = "boost"
            risk_mult = 1.5
            reasons.append(f"Current regime ({overall}) is optimal for {strat_id}")
        
        # Volatility adjustment
        if strat_info["type"] == "mean_reversion" and vix > 30:
            # Mean reversion works well in high vol
            risk_mult = min(risk_mult * 1.2, 2.0)
            reasons.append(f"High VIX ({vix:.1f}) — favorable for mean reversion")
        elif strat_info["type"] == "trend_following" and vix > 30:
            # Trend following struggles in high vol (whipsaws)
            risk_mult = max(risk_mult * 0.7, 0.0)
            reasons.append(f"High VIX ({vix:.1f}) — reduce trend following (whipsaw risk)")
        
        # Correlation adjustment
        if corr_tag == "diversified" and strat_info["asset"] == "stock":
            if strat_info["type"] in ("divergence", "mean_reversion", "reversal"):
                risk_mult = min(risk_mult * 1.2, 2.0)
                reasons.append("Low correlation regime — stock-picking strategies boosted")
        elif corr_tag == "unified" and strat_info["asset"] == "stock":
            if strat_info["type"] != "factor":
                risk_mult = max(risk_mult * 0.5, 0.0)
                reasons.append("High correlation regime — stock-picking adds no value, reduce")
        
        # Breadth adjustment
        if strat_info["asset"] == "stock":
            if breadth_50 > 80 and strat_info["type"] in ("breakout", "trend_following"):
                risk_mult = max(risk_mult * 0.7, 0.0)
                reasons.append(f"Extreme breadth ({breadth_50:.0f}% > 50MA) — overbought, reduce breakout entries")
            elif breadth_50 < 20 and strat_info["type"] == "mean_reversion":
                risk_mult = min(risk_mult * 1.3, 2.0)
                reasons.append(f"Oversold breadth ({breadth_50:.0f}% > 50MA) — mean reversion boosted")
        
        # Crypto-specific adjustments
        if strat_info["asset"] == "crypto":
            if fg < 25 and strat_info["type"] == "factor":
                risk_mult = max(risk_mult * 0.5, 0.0)
                reasons.append(f"Extreme F&G fear ({fg}) — reduce crypto factor strategies")
            elif fg > 75 and strat_info["type"] == "factor":
                risk_mult = max(risk_mult * 0.5, 0.0)
                reasons.append(f"Extreme F&G greed ({fg}) — reduce crypto factor strategies")
        
        # VRP adjustment
        if vol_premium > 3 and strat_info["type"] == "breakout":
            risk_mult = min(risk_mult * 1.2, 2.0)
            reasons.append(f"Positive VRP ({vol_premium:+.1f}%) — VIX should compress, bullish for breakouts")
        elif vol_premium < -3 and strat_info["type"] == "breakout":
            risk_mult = max(risk_mult * 0.7, 0.0)
            reasons.append(f"Negative VRP ({vol_premium:+.1f}%) — VIX spike risk, reduce breakouts")
        
        # Economic event proximity
        if high_impact > 0:
            filter_conditions.append("Check if high-impact event is within 24h — if so, skip new entries")
        
        # Funding extremes (crypto)
        if strat_info["asset"] == "crypto" and funding_extremes >= 3:
            filter_conditions.append(f"Check funding rate for specific coin — skip if extreme")
        
        # Determine final action
        if action == "suppress" or risk_mult == 0:
            final_action = "suppress"
        elif risk_mult > 1.3:
            final_action = "boost"
        elif risk_mult < 0.7:
            final_action = "reduce"
        else:
            final_action = "run"
        
        directives[strat_id] = {
            "action": final_action,
            "risk_multiplier": round(risk_mult, 2),
            "reason": "; ".join(reasons) if reasons else "No regime-based adjustments",
            "filter_conditions": filter_conditions,
            "strategy_name": strat_info["name"],
            "strategy_status": strat_info["status"],
            "strategy_type": strat_info["type"],
            "base_risk": strat_info["base_risk"],
            "adjusted_risk": round(strat_info["base_risk"] * risk_mult, 2),
        }
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "regime": state,
        "directives": directives,
        "overall_posture": posture,
        "posture_reasons": posture_reasons,
        "summary": _build_summary(posture, directives, state),
    }


def _build_summary(posture: str, directives: dict, regime: dict) -> str:
    """Build a concise human-readable summary."""
    lines = []
    
    # Posture
    posture_emoji = {
        "aggressive": "🟢",
        "normal": "⚪",
        "opportunistic": "🟡",
        "defensive": "🔴",
    }
    lines.append(f"Posture: {posture_emoji.get(posture, '⚪')} {posture.upper()}")
    lines.append(f"Regime: {regime.get('overall', 'neutral')} | VIX={regime.get('vix', 0):.1f} | F&G={regime.get('fear_greed', 50)}")
    
    # Active strategies
    active = [d for d in directives.values() if d["action"] in ("run", "boost")]
    suppressed = [d for d in directives.values() if d["action"] == "suppress"]
    reduced = [d for d in directives.values() if d["action"] == "reduce"]
    boosted = [d for d in directives.values() if d["action"] == "boost"]
    
    if boosted:
        names = [d["strategy_name"] for d in boosted]
        lines.append(f"Boosted: {', '.join(names)}")
    if reduced:
        names = [d["strategy_name"] for d in reduced]
        lines.append(f"Reduced: {', '.join(names)}")
    if suppressed:
        names = [d["strategy_name"] for d in suppressed]
        lines.append(f"Suppressed: {', '.join(names)}")
    
    lines.append(f"Active: {len(active)} strategies | Adjusted risk range: "
                 f"{min(d['adjusted_risk'] for d in active):.2f}%-{max(d['adjusted_risk'] for d in active):.2f}%")
    
    return "\n".join(lines)


def print_directives(result: dict):
    """Print strategy directives in human-readable format."""
    print(f"\n🎯 **Regime-Aware Strategy Selector**")
    print(f"   {result['timestamp'][:19]}\n")
    
    print(f"**Posture:** {result['overall_posture'].upper()}")
    for reason in result.get("posture_reasons", []):
        print(f"  • {reason}")
    
    regime = result.get("regime", {})
    print(f"\n**Current Regime:**")
    print(f"  Overall: {regime.get('overall', '?')}")
    print(f"  VIX: {regime.get('vix', 0):.1f} | F&G: {regime.get('fear_greed', 50)}")
    print(f"  Breadth: {regime.get('breadth_pct_50ma', 50):.0f}% > 50MA")
    print(f"  Correlation: {regime.get('correlation_regime', '?')}")
    print(f"  VRP: {regime.get('vol_risk_premium', 0):+.1f}%")
    print(f"  P/C: {regime.get('put_call', 1.0)}")
    
    print(f"\n**Strategy Directives:**")
    for strat_id, d in sorted(result.get("directives", {}).items()):
        action_emoji = {
            "boost": "🚀",
            "run": "✅",
            "reduce": "⬇️",
            "suppress": "🚫",
            "skip": "⏭️",
        }
        emoji = action_emoji.get(d["action"], "❓")
        print(f"\n  {emoji} {strat_id} ({d.get('strategy_name', '')}) — {d['action'].upper()}")
        print(f"     Risk: {d.get('base_risk', 0)}% → {d.get('adjusted_risk', 0)}% (x{d['risk_multiplier']})")
        print(f"     Reason: {d.get('reason', '')}")
        if d.get("filter_conditions"):
            for fc in d["filter_conditions"]:
                print(f"     Filter: {fc}")
    
    print(f"\n**Summary:**")
    print(result.get("summary", ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Regime-Aware Strategy Selector")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()
    
    result = get_strategy_directives()
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_directives(result)
