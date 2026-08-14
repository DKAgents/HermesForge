#!/usr/bin/env python3
"""
compute_confluence.py — Multi-Signal Confluence Scoring

When a trade signal has multiple confirming factors from different data
sources, the probability of success increases. This module computes a
confluence score for any given signal by checking how many independent
data sources agree.

Confluence factors:
  1. Regime alignment (does the current regime favor this strategy?)
  2. Breadth confirmation (breadth supports the direction)
  3. Volatility environment (VRP favors the trade type)
  4. Sector rotation (sector momentum supports the direction)
  5. Correlation regime (low correlation = stock-picking edge)
  6. Insider activity (insider buying in same stock)
  7. Short interest (squeeze potential for longs)
  8. Sentiment (F&G, put/call support the direction)
  9. Funding rates (crypto positioning supports direction)
  10. Economic calendar (no high-impact event within 24h)
  11. LunarCrush social sentiment (crypto)
  12. Intermarket (commodities, VIX term structure)

Score: 0-100 (each factor contributes up to ~8 points)
High confluence (>60) = high conviction trade, boost position size
Low confluence (<30) = low conviction, reduce or skip

Usage:
    from compute_confluence import score_confluence
    score = score_confluence(signal_dict, regime_dict)
"""

import sys
import json
import argparse
import pathlib
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "research"))


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return None


def score_confluence(signal: dict, regime: dict = None) -> dict:
    """
    Compute confluence score for a trading signal.
    
    Args:
        signal: dict with at minimum: ticker, direction, strategy_id
        regime: dict from regime_filter.get_regime() (optional, will fetch if not provided)
    
    Returns:
    {
        "score": int (0-100),
        "factors": {factor_name: {score: int, reason: str}},
        "conviction": "high" | "medium" | "low",
        "recommendation": str,
    }
    """
    if regime is None:
        from regime_filter import get_regime
        regime = _safe_call(get_regime) or {}
    
    ticker = signal.get("ticker", "")
    direction = signal.get("direction", "long")
    strategy_id = signal.get("strategy_id", "")
    is_long = direction == "long"
    
    factors = {}
    total_score = 0
    max_score = 0
    
    # 1. Regime alignment (8 pts)
    max_score += 8
    from regime_strategy_selector import STRATEGY_REGISTRY, get_strategy_directives
    directives = _safe_call(get_strategy_directives) or {}
    dirs = directives.get("directives", {})
    
    strat_prefix = strategy_id.split("-")[0] if "-" in strategy_id else strategy_id
    directive = dirs.get(f"STR-{strat_prefix}") or dirs.get(strategy_id)
    
    if directive:
        action = directive.get("action", "run")
        if action == "boost":
            factors["regime_alignment"] = {"score": 8, "reason": f"Regime boosts {strategy_id} (x{directive['risk_multiplier']:.1f})"}
            total_score += 8
        elif action == "run":
            factors["regime_alignment"] = {"score": 5, "reason": "Regime neutral for this strategy"}
            total_score += 5
        elif action == "suppress":
            factors["regime_alignment"] = {"score": 0, "reason": f"⚠️ Regime suppresses {strategy_id}: {directive.get('reason', '')}"}
        else:
            factors["regime_alignment"] = {"score": 3, "reason": f"Regime: {action}"}
            total_score += 3
    else:
        factors["regime_alignment"] = {"score": 4, "reason": "No directive available"}
        total_score += 4
    
    # 2. Breadth confirmation (8 pts)
    max_score += 8
    breadth = regime.get("breadth", {})
    if breadth:
        pct_above_50 = breadth.get("pct_above_50ma", 50)
        if is_long and pct_above_50 > 60:
            factors["breadth"] = {"score": 7, "reason": f"Breadth confirms long: {pct_above_50:.0f}% > 50MA"}
            total_score += 7
        elif not is_long and pct_above_50 < 40:
            factors["breadth"] = {"score": 7, "reason": f"Breadth confirms short: only {pct_above_50:.0f}% > 50MA"}
            total_score += 7
        elif breadth.get("divergence", "none") != "none":
            factors["breadth"] = {"score": 3, "reason": f"Breadth divergence: {breadth['divergence']}"}
            total_score += 3
        else:
            factors["breadth"] = {"score": 4, "reason": f"Breadth neutral: {pct_above_50:.0f}% > 50MA"}
            total_score += 4
    else:
        factors["breadth"] = {"score": 0, "reason": "No breadth data"}
    
    # 3. Volatility environment (8 pts)
    max_score += 8
    vrp = regime.get("vol_risk_premium", {})
    if vrp:
        vol_premium = vrp.get("vol_risk_premium", 0)
        signal_type = "breakout"  # default assumption
        # Check strategy type from registry
        strat_info = STRATEGY_REGISTRY.get(f"STR-{strat_prefix}", {})
        signal_type = strat_info.get("type", "unknown")
        
        if signal_type == "breakout" and vol_premium > 2:
            factors["volatility"] = {"score": 7, "reason": f"VRP={vol_premium:+.1f}% — VIX should compress, bullish for breakouts"}
            total_score += 7
        elif signal_type == "mean_reversion" and abs(vol_premium) > 3:
            factors["volatility"] = {"score": 6, "reason": f"VRP={vol_premium:+.1f}% — high vol favors mean reversion"}
            total_score += 6
        else:
            factors["volatility"] = {"score": 4, "reason": f"VRP={vol_premium:+.1f}% — neutral"}
            total_score += 4
    else:
        factors["volatility"] = {"score": 0, "reason": "No VRP data"}
    
    # 4. Correlation regime (8 pts)
    max_score += 8
    corr = regime.get("correlation", {})
    corr_regime = corr.get("correlation_regime", "normal")
    if corr_regime == "diversified" and signal.get("asset_class", "stock") == "stock":
        factors["correlation"] = {"score": 7, "reason": "Low correlation — stock-picking edge is live"}
        total_score += 7
    elif corr_regime == "unified":
        factors["correlation"] = {"score": 2, "reason": "High correlation — stock-specific edge is muted"}
        total_score += 2
    else:
        factors["correlation"] = {"score": 5, "reason": f"Correlation regime: {corr_regime}"}
        total_score += 5
    
    # 5. Sentiment confirmation (8 pts)
    max_score += 8
    fg = regime.get("fear_greed", {})
    fg_val = fg.get("value", 50) if fg else 50
    if is_long and fg_val < 30:
        factors["sentiment"] = {"score": 7, "reason": f"F&G={fg_val} (Fear) — contrarian bullish for longs"}
        total_score += 7
    elif not is_long and fg_val > 70:
        factors["sentiment"] = {"score": 7, "reason": f"F&G={fg_val} (Greed) — contrarian bearish for longs"}
        total_score += 7
    elif is_long and fg_val > 75:
        factors["sentiment"] = {"score": 2, "reason": f"F&G={fg_val} (Extreme Greed) — risky for new longs"}
        total_score += 2
    else:
        factors["sentiment"] = {"score": 4, "reason": f"F&G={fg_val} — neutral"}
        total_score += 4
    
    # 6. Put/Call ratio (6 pts)
    max_score += 6
    pc = regime.get("put_call", {})
    if pc:
        pc_ratio = pc.get("total_ratio", 1.0)
        if is_long and pc_ratio > 1.2:
            factors["put_call"] = {"score": 6, "reason": f"P/C={pc_ratio} — extreme bearishness, contrarian long signal"}
            total_score += 6
        elif not is_long and pc_ratio < 0.6:
            factors["put_call"] = {"score": 5, "reason": f"P/C={pc_ratio} — extreme complacency, contrarian short signal"}
            total_score += 5
        else:
            factors["put_call"] = {"score": 3, "reason": f"P/C={pc_ratio} — neutral"}
            total_score += 3
    else:
        factors["put_call"] = {"score": 0, "reason": "No P/C data"}
    
    # 7. Economic calendar (6 pts)
    max_score += 6
    events = regime.get("economic_events", [])
    if not events:
        factors["economic"] = {"score": 6, "reason": "No high-impact events in next 7 days"}
        total_score += 6
    elif len(events) <= 2:
        factors["economic"] = {"score": 4, "reason": f"{len(events)} upcoming high-impact events — check timing"}
        total_score += 4
    else:
        factors["economic"] = {"score": 2, "reason": f"⚠️ {len(events)} high-impact events — elevated event risk"}
        total_score += 2
    
    # 8. Insider activity (6 pts)
    max_score += 6
    si = regime.get("short_interest", {})
    if is_long and si and si.get("top"):
        # Check if this ticker has high short interest (squeeze potential)
        ticker_upper = ticker.upper()
        for s in si["top"]:
            if s.get("ticker", "").upper() == ticker_upper:
                factors["short_interest"] = {"score": 6, "reason": f"High SI {s['pct_float']:.1f}% — squeeze potential for long"}
                total_score += 6
                break
        else:
            factors["short_interest"] = {"score": 3, "reason": "No high short interest for this ticker"}
            total_score += 3
    else:
        factors["short_interest"] = {"score": 3, "reason": "No SI data or not applicable"}
        total_score += 3
    
    # 9. LunarCrush (crypto only, 6 pts)
    max_score += 6
    lc = regime.get("lunarcrush_crypto", {})
    if lc and signal.get("asset_class") == "crypto" and ticker in lc:
        lc_data = lc[ticker]
        sentiment = lc_data.get("sentiment", 50)
        trend = lc_data.get("trend", "flat")
        if is_long and sentiment > 70 and trend == "up":
            factors["lunarcrush"] = {"score": 6, "reason": f"Social sentiment {sentiment:.0f} + uptrend — confirms long"}
            total_score += 6
        elif is_long and sentiment > 80 and trend == "down":
            factors["lunarcrush"] = {"score": 2, "reason": f"⚠️ High sentiment {sentiment:.0f} but downtrend — divergence (bearish)"}
            total_score += 2
        else:
            factors["lunarcrush"] = {"score": 3, "reason": f"Sentiment {sentiment:.0f}, trend {trend}"}
            total_score += 3
    else:
        factors["lunarcrush"] = {"score": 3, "reason": "Not applicable or no data"}
        total_score += 3
    
    # 10. Crypto macro (crypto only, 6 pts)
    max_score += 6
    tvl = regime.get("tvl", {})
    sc_supply = regime.get("stablecoin", {})
    if signal.get("asset_class") == "crypto":
        tvl_trend = tvl.get("trend", "") if tvl else ""
        sc_trend = sc_supply.get("trend", "") if sc_supply else ""
        if tvl_trend == "rising" and sc_trend == "rising":
            factors["crypto_macro"] = {"score": 6, "reason": "TVL + stablecoin supply both rising — capital inflow"}
            total_score += 6
        elif tvl_trend == "declining":
            factors["crypto_macro"] = {"score": 2, "reason": "⚠️ TVL declining — capital leaving DeFi"}
            total_score += 2
        else:
            factors["crypto_macro"] = {"score": 4, "reason": f"TVL {tvl_trend}, stablecoin {sc_trend}"}
            total_score += 4
    else:
        factors["crypto_macro"] = {"score": 3, "reason": "Not applicable (stock trade)"}
        total_score += 3
    
    # 11. Intermarket (6 pts)
    max_score += 6
    # Check if intermarket data is available
    try:
        from fetch_intermarket import get_intermarket_summary
        im = _safe_call(get_intermarket_summary) or {}
        if im:
            # Simple check: VIX term structure contango = bullish, backwardation = bearish
            vix_ts = im.get("vix_term_structure", {})
            ts_state = vix_ts.get("state", "contango")
            if is_long and ts_state == "contango":
                factors["intermarket"] = {"score": 5, "reason": "VIX contango — normal/complacent, bullish"}
                total_score += 5
            elif ts_state == "backwardation":
                factors["intermarket"] = {"score": 2, "reason": "⚠️ VIX backwardation — stress regime"}
                total_score += 2
            else:
                factors["intermarket"] = {"score": 4, "reason": f"VIX TS: {ts_state}"}
                total_score += 4
        else:
            factors["intermarket"] = {"score": 3, "reason": "No intermarket data"}
            total_score += 3
    except ImportError:
        factors["intermarket"] = {"score": 3, "reason": "Intermarket module not available"}
        total_score += 3
    
    # Normalize to 0-100
    normalized = round(total_score / max_score * 100) if max_score > 0 else 0
    
    # Conviction level
    if normalized >= 65:
        conviction = "high"
        recommendation = "High confluence — boost position size by 25-50%"
    elif normalized >= 45:
        conviction = "medium"
        recommendation = "Medium confluence — standard position size"
    elif normalized >= 30:
        conviction = "low"
        recommendation = "Low confluence — reduce position size by 25-50%"
    else:
        conviction = "very_low"
        recommendation = "⚠️ Very low confluence — consider skipping this trade"
    
    return {
        "score": normalized,
        "total_points": total_score,
        "max_points": max_score,
        "factors": factors,
        "conviction": conviction,
        "recommendation": recommendation,
    }


def print_score(result: dict):
    print(f"\n🎯 **Confluence Score: {result['score']}/100** ({result['conviction'].upper()})")
    print(f"   {result['recommendation']}\n")
    for name, data in result["factors"].items():
        score = data["score"]
        bar = "█" * int(score) + "░" * (8 - int(score))
        print(f"  {bar} {name}: {score}/8 — {data['reason']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Confluence Scoring")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ticker", type=str, default="AAPL")
    ap.add_argument("--direction", type=str, default="long")
    args = ap.parse_args()
    
    test_signal = {"ticker": args.ticker, "direction": args.direction,
                   "strategy_id": "STR-B-macd-histogram-divergence", "asset_class": "stock"}
    
    result = score_confluence(test_signal)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_score(result)
