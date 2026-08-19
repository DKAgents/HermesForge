#!/usr/bin/env python3
"""
edge_discovery_engine.py — Autonomous Multi-Source Edge Discovery

Scans all 20+ data sources to discover tradable edges:
  1. Breadth divergences (A/D line vs price, new highs/lows imbalances)
  2. Volatility risk premium anomalies (VIX vs realized, term structure)
  3. Sector rotation momentum (leading/lagging sector switches)
  4. Cross-asset correlation breakdowns/regimes
  5. Crypto performance dispersion (mean reversion vs momentum)
  6. Insider trading clusters (SEC Form 4 buying patterns)
  7. Short interest squeeze candidates
  8. Put/Call ratio extremes
  9. DeFi TVL + stablecoin supply divergences (crypto macro)
  10. Fear & Greed extremes
  11. Funding rate extremes (crypto positioning)
  12. LunarCrush sentiment divergences
  13. Economic event proximity effects
  14. GitHub activity vs price divergence (crypto fundamentals)
  15. Strategy-regime performance feedback (which strategies work where)

Each edge is scored on: signal strength, confidence, data quality, 
actionability, and historical precedent.

Output: ranked list of testable hypotheses with specific entry/exit rules.

Usage:
    python3 edge_discovery_engine.py                # scan all sources
    python3 edge_discovery_engine.py --json          # JSON output
    python3 edge_discovery_engine.py --source breadth  # single source
"""

import sys
import json
import argparse
import pathlib
import numpy as np
import pandas as pd
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

EDGE_CANDIDATES_DIR = REPO_ROOT / "05-Research" / "Edge-Candidates"


def _safe_call(fn, *args, **kwargs):
    """Call a function, return None on any error."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  Warning: {fn.__name__} failed: {e}", file=sys.stderr)
        return None


# ─── Edge Scoring ────────────────────────────────────────────────────────────

def _score_edge(signal_strength: float, confidence: str, data_quality: str,
                actionable: bool, historical_precedent: str) -> dict:
    """
    Score an edge on multiple dimensions.
    
    Returns composite score 0-100 and individual dimension scores.
    """
    # Signal strength (0-1 normalized)
    strength_score = min(max(signal_strength, 0), 1) * 30
    
    # Confidence (high=25, medium=15, low=5, speculative=2)
    conf_map = {"high": 25, "medium": 15, "low": 5, "speculative": 2}
    conf_score = conf_map.get(confidence, 5)
    
    # Data quality (real_time=20, daily=15, cached=10, estimated=5)
    quality_map = {"real_time": 20, "daily": 15, "cached": 10, "estimated": 5}
    quality_score = quality_map.get(data_quality, 10)
    
    # Actionability (yes=15, no=0)
    action_score = 15 if actionable else 0
    
    # Historical precedent (well_known=10, some_evidence=7, novel=5, untested=3)
    precedent_map = {"well_known": 10, "some_evidence": 7, "novel": 5, "untested": 3}
    precedent_score = precedent_map.get(historical_precedent, 3)
    
    composite = strength_score + conf_score + quality_score + action_score + precedent_score
    
    return {
        "composite": round(composite, 1),
        "signal_strength": round(strength_score, 1),
        "confidence": conf_score,
        "data_quality": quality_score,
        "actionable": action_score,
        "precedent": precedent_score,
    }


# ─── Individual Edge Scanners ──────────────────────────────────────────────

def scan_breadth_edges() -> list:
    """Scan market breadth for divergences and extremes."""
    from compute_breadth import get_breadth_summary
    
    edges = []
    breadth = _safe_call(get_breadth_summary)
    if not breadth:
        return edges
    
    # Edge 1: Breadth divergence (price up, breadth down = bearish)
    div = breadth.get("divergence", "none")
    if div != "none":
        pct_above_50 = breadth.get("pct_above_50ma", 50)
        pct_above_200 = breadth.get("pct_above_200ma", 50)
        strength = abs(50 - pct_above_50) / 50  # how far from neutral
        
        edges.append({
            "source": "breadth",
            "edge_type": "breadth_divergence",
            "description": f"{div.upper()} divergence: price moving one way, breadth the other",
            "signal": f"A/D ratio={breadth.get('ad_ratio', 0)}, "
                      f"{pct_above_50}% above 50MA, {pct_above_200}% above 200MA",
            "hypothesis": "Breadth divergences often precede reversals. "
                          "If bearish divergence: consider reducing longs or entering shorts. "
                          "If bullish divergence: look for bottoming setups.",
            "entry_rules": f"Wait for price confirmation in divergence direction. "
                           f"Entry on first close in divergence direction with volume > 20d avg.",
            "exit_rules": "Exit when breadth re-aligns with price or after 10 bars.",
            "score": _score_edge(
                signal_strength=strength,
                confidence="medium" if strength > 0.3 else "low",
                data_quality="daily",
                actionable=True,
                historical_precedent="well_known",
            ),
            "regime_fit": ["risk_on", "caution"],
        })
    
    # Edge 2: Extreme breadth (>80% or <20% above 50MA)
    pct_above_50 = breadth.get("pct_above_50ma", 50)
    if pct_above_50 > 80:
        edges.append({
            "source": "breadth",
            "edge_type": "overbought_breadth",
            "description": f"Extreme breadth: {pct_above_50:.0f}% above 50MA (overbought)",
            "signal": f"NH={breadth.get('new_highs', 0)}, NL={breadth.get('new_lows', 0)}",
            "hypothesis": "When >80% of stocks are above 50MA, market is overbought. "
                          "Mean reversion likely within 1-2 weeks. Short the weakest stocks "
                          "that made new highs on declining volume.",
            "entry_rules": "Find stocks at 52-week highs with RSI > 70 and volume declining. "
                           "Short on bearish engulfing or inside day.",
            "exit_rules": "Cover on first close above prior high or after 5 bars.",
            "score": _score_edge(
                signal_strength=(pct_above_50 - 80) / 20,
                confidence="medium",
                data_quality="daily",
                actionable=True,
                historical_precedent="some_evidence",
            ),
            "regime_fit": ["risk_on", "complacent"],
        })
    elif pct_above_50 < 20:
        edges.append({
            "source": "breadth",
            "edge_type": "oversold_breadth",
            "description": f"Extreme breadth: {pct_above_50:.0f}% above 50MA (oversold)",
            "signal": f"NH={breadth.get('new_highs', 0)}, NL={breadth.get('new_lows', 0)}",
            "hypothesis": "When <20% of stocks are above 50MA, market is oversold. "
                          "Bounce likely. Look for stocks showing relative strength "
                          "while market is weak — they'll lead the recovery.",
            "entry_rules": "Find stocks with RSI < 30 but holding above 200MA. "
                           "Buy on first green candle with volume > 1.5x 20d avg.",
            "exit_rules": "Exit on RSI > 60 or after 10 bars.",
            "score": _score_edge(
                signal_strength=(20 - pct_above_50) / 20,
                confidence="medium",
                data_quality="daily",
                actionable=True,
                historical_precedent="well_known",
            ),
            "regime_fit": ["risk_off", "caution"],
        })
    
    # Edge 3: New high/new low ratio extremes
    nh = breadth.get("new_highs", 0)
    nl = breadth.get("new_lows", 0)
    if nl > nh and nl > 20:
        edges.append({
            "source": "breadth",
            "edge_type": "new_low_dominance",
            "description": f"New lows dominate: NH={nh}, NL={nl}",
            "signal": f"NL/NH ratio = {nl/max(nh,1):.1f}",
            "hypothesis": "High new-low dominance signals broad selling pressure. "
                          "Wait for NL to drop below 10 before initiating longs. "
                          "Short setups: breakdown below recent support on high volume.",
            "entry_rules": "Short stocks breaking below 50-day support with NL > 20. "
                           "Stop above recent swing high.",
            "exit_rules": "Cover when NL drops below 5, or target = 2R.",
            "score": _score_edge(
                signal_strength=min(nl / 50, 1),
                confidence="medium",
                data_quality="daily",
                actionable=True,
                historical_precedent="some_evidence",
            ),
            "regime_fit": ["risk_off"],
        })
    
    return edges


def scan_volatility_edges() -> list:
    """Scan volatility risk premium for edges."""
    from compute_volatility import compute_vol_risk_premium, get_crypto_volatility
    
    edges = []
    vrp = _safe_call(compute_vol_risk_premium)
    if not vrp:
        return edges
    
    vol_premium = vrp.get("vol_risk_premium", 0)
    signal = vrp.get("signal", "neutral")
    
    # Edge: VRP extreme
    if abs(vol_premium) > 3:
        direction = "VIX overestimating fear" if vol_premium > 0 else "VIX underestimating risk"
        strength = min(abs(vol_premium) / 10, 1)
        
        edges.append({
            "source": "volatility",
            "edge_type": "vrp_extreme",
            "description": f"Volatility risk premium extreme: {vol_premium:+.1f}% ({direction})",
            "signal": f"VIX={vrp.get('vix', 0)}, Realized={vrp.get('realized_vol_20d', 0)}%",
            "hypothesis": f"Large positive VRP → market pricing in too much fear, "
                          f"likely to resolve with VIX compression (bullish). "
                          f"Large negative VRP → market too complacent, spike risk elevated.",
            "entry_rules": f"If VRP > +3%: buy stocks breaking out (VIX should compress). "
                           f"If VRP < -3%: reduce longs, add hedge.",
            "exit_rules": "Exit when VRP returns to ±1% range.",
            "score": _score_edge(
                signal_strength=strength,
                confidence="medium",
                data_quality="daily",
                actionable=True,
                historical_precedent="well_known",
            ),
            "regime_fit": ["risk_off"] if vol_premium > 3 else ["complacent"],
        })
    
    # Crypto volatility edges
    crypto_vol = _safe_call(get_crypto_volatility)
    if crypto_vol:
        # Find highest vol crypto
        sorted_vol = sorted(crypto_vol.items(), key=lambda x: x[1], reverse=True)
        if sorted_vol:
            highest_coin, highest_vol = sorted_vol[0]
            if highest_vol > 80:
                edges.append({
                    "source": "volatility",
                    "edge_type": "crypto_vol_extreme",
                    "description": f"Extreme crypto volatility: {highest_coin} at {highest_vol:.1f}%",
                    "signal": f"Top 3 vol: {dict(sorted_vol[:3])}",
                    "hypothesis": f"Crypto with >80% annualized vol is in high-stress regime. "
                                  f"Mean reversion likely — look for long entries when F&G < 20 "
                                  f"and vol starts declining from peak.",
                    "entry_rules": f"Buy {highest_coin} when vol drops 20% from peak AND "
                                   f"F&G < 25 AND price above 20MA.",
                    "exit_rules": "Exit when vol > 100 or F&G > 60.",
                    "score": _score_edge(
                        signal_strength=min(highest_vol / 150, 1),
                        confidence="low",
                        data_quality="daily",
                        actionable=True,
                        historical_precedent="some_evidence",
                    ),
                    "regime_fit": ["risk_off"],
                })
    
    return edges


def scan_rotation_edges() -> list:
    """Scan sector rotation and crypto performance for edges."""
    from compute_rotation import compute_sector_rotation, compute_crypto_heatmap
    
    edges = []
    
    # Sector rotation
    rotation = _safe_call(compute_sector_rotation)
    if rotation and rotation.get("sectors"):
        sectors = rotation["sectors"]
        
        # Find sector with strongest negative 20d RS (lagging)
        lagging = sorted(sectors.items(), key=lambda x: x[1].get("rs_vs_spy", {}).get("20d", 0))
        if lagging and lagging[0][1].get("rs_vs_spy", {}).get("20d", 0) < -3:
            lag_etf, lag_data = lagging[0]
            lag_name = lag_data.get("name", lag_etf)
            lag_rs = lag_data["rs_vs_spy"]["20d"]
            
            # Check if RS is improving (1d positive while 20d negative)
            rs_1d = lag_data["rs_vs_spy"].get("1d", 0)
            if rs_1d > 0:
                edges.append({
                    "source": "rotation",
                    "edge_type": "sector_rotation_reversal",
                    "description": f"{lag_name} ({lag_etf}) showing RS improvement after lagging",
                    "signal": f"20d RS: {lag_rs:+.2f}%, 1d RS: {rs_1d:+.2f}% — momentum shift",
                    "hypothesis": f"Sector that lagged badly is now gaining relative strength. "
                                  f"Buy the sector ETF or its strongest stocks when RS turns "
                                  f"positive on 5-day basis too.",
                    "entry_rules": f"Buy {lag_etf} when 5d RS > 0 AND 20d RS is still negative "
                                   f"(early rotation). Stop if 5d RS turns negative again.",
                    "exit_rules": "Exit when 20d RS > +3% (rotation complete) or 5d RS < -1%.",
                    "score": _score_edge(
                        signal_strength=min(abs(lag_rs) / 10, 1),
                        confidence="low",
                        data_quality="daily",
                        actionable=True,
                        historical_precedent="some_evidence",
                    ),
                    "regime_fit": ["neutral", "risk_on"],
                })
        
        # Find leading sector — momentum continuation
        leading = sorted(sectors.items(), key=lambda x: x[1].get("rs_vs_spy", {}).get("20d", 0), reverse=True)
        if leading and leading[0][1].get("rs_vs_spy", {}).get("20d", 0) > 3:
            lead_etf, lead_data = leading[0]
            lead_name = lead_data.get("name", lead_etf)
            lead_rs = lead_data["rs_vs_spy"]["20d"]
            lead_1d = lead_data["rs_vs_spy"].get("1d", 0)
            
            if lead_1d > 0:
                edges.append({
                    "source": "rotation",
                    "edge_type": "sector_momentum_continuation",
                    "description": f"{lead_name} ({lead_etf}) leading with momentum continuing",
                    "signal": f"20d RS: {lead_rs:+.2f}%, 1d RS: {lead_1d:+.2f}%",
                    "hypothesis": f"Strong sector with continued RS improvement. "
                                  f"Momentum persistence suggests more upside. "
                                  f"Buy top stocks in sector on pullbacks to 10MA.",
                    "entry_rules": f"Buy top 3 stocks in {lead_etf} sector on pullback to 10MA "
                                   f"with volume contraction. Stop below 20MA.",
                    "exit_rules": "Exit when sector RS turns negative on 5d, or target 3R.",
                    "score": _score_edge(
                        signal_strength=min(lead_rs / 10, 1),
                        confidence="medium",
                        data_quality="daily",
                        actionable=True,
                        historical_precedent="well_known",
                    ),
                    "regime_fit": ["risk_on"],
                })
    
    # Crypto performance dispersion
    crypto = _safe_call(compute_crypto_heatmap)
    if crypto:
        # Find biggest loser over 7d — mean reversion candidate
        sorted_7d = sorted(crypto.items(), key=lambda x: x[1].get("7d", 0))
        if sorted_7d and sorted_7d[0][1].get("7d", 0) < -10:
            loser_coin, loser_rets = sorted_7d[0]
            ret_7d = loser_rets["7d"]
            ret_30d = loser_rets.get("30d", 0)
            
            # Only if 30d is positive (uptrend pullback, not a falling knife)
            if ret_30d > 0:
                edges.append({
                    "source": "rotation",
                    "edge_type": "crypto_mean_reversion",
                    "description": f"{loser_coin} down {ret_7d:.1f}% in 7d but up {ret_30d:.1f}% in 30d",
                    "signal": f"7d: {ret_7d:+.1f}%, 30d: {ret_30d:+.1f}%",
                    "hypothesis": f"Short-term oversold in uptrend. Buy {loser_coin} "
                                  f"for mean reversion bounce. Typical recovery: 30-50% "
                                  f"of the 7d drop within 3-5 days.",
                    "entry_rules": f"Buy {loser_coin} when daily RSI < 35 AND price near 20MA. "
                                   f"Stop below recent swing low.",
                    "exit_rules": "Exit at 50% of 7d drop recovery, or RSI > 60, or 5 bars.",
                    "score": _score_edge(
                        signal_strength=min(abs(ret_7d) / 30, 1),
                        confidence="medium",
                        data_quality="daily",
                        actionable=True,
                        historical_precedent="some_evidence",
                    ),
                    "regime_fit": ["neutral", "risk_on"],
                })
    
    return edges


def scan_correlation_edges() -> list:
    """Scan cross-asset correlations for regime edges."""
    from compute_correlation import get_correlation_summary
    
    edges = []
    corr = _safe_call(get_correlation_summary)
    if not corr:
        return edges
    
    regime = corr.get("correlation_regime", "normal")
    avg = corr.get("avg_asset_correlation", 0)
    
    if regime == "unified":
        edges.append({
            "source": "correlation",
            "edge_type": "high_correlation_regime",
            "description": f"Unified market: avg correlation {avg:.2f} (everything moving together)",
            "signal": f"Avg 30d correlation = {avg}",
            "hypothesis": "When everything correlates > 0.7, stock-picking adds no value. "
                          "Use broad index ETFs (short or long) instead of individual stocks. "
                          "High correlation regimes are typically risk-off events.",
            "entry_rules": "Trade SPY/QQQ instead of individual stocks. "
                           "If VIX also elevated: consider short SPY. "
                           "If VIX low: risk-on bounce, go long QQQ.",
            "exit_rules": "Exit when correlation drops below 0.5 (diversification returning).",
            "score": _score_edge(
                signal_strength=(avg - 0.7) / 0.3,
                confidence="medium",
                data_quality="daily",
                actionable=True,
                historical_precedent="well_known",
            ),
            "regime_fit": ["risk_off"],
        })
    elif regime == "diversified":
        edges.append({
            "source": "correlation",
            "edge_type": "low_correlation_regime",
            "description": f"Diversified market: avg correlation {avg:.2f} (stock-picking environment)",
            "signal": f"Avg 30d correlation = {avg}",
            "hypothesis": "Low correlation = individual stock edge matters. "
                          "Best time for stock-specific strategies (STR-A, STR-B, STR-I). "
                          "Sector rotation and factor strategies work well here.",
            "entry_rules": "Run stock-picking scanners (MACD divergence, adaptive trend, "
                           "pullback to MA). Focus on stocks with idiosyncratic catalysts.",
            "exit_rules": "Continue until correlation rises above 0.5.",
            "score": _score_edge(
                signal_strength=(0.3 - avg) / 0.3,
                confidence="high",
                data_quality="daily",
                actionable=True,
                historical_precedent="well_known",
            ),
            "regime_fit": ["risk_on", "neutral"],
        })
    
    return edges


def scan_insider_edges() -> list:
    """Scan SEC Form 4 insider trading for cluster buying."""
    from fetch_sec_insider import get_insider_summary
    
    edges = []
    insider = _safe_call(get_insider_summary, days=7)
    if not insider:
        return edges
    
    # Find cluster buying (multiple insiders buying same stock)
    clusters = insider.get("clusters", [])
    if not clusters:
        # Also check top buys
        top_buys = insider.get("top_buys", [])
        for buy in top_buys[:5]:
            ticker = buy.get("ticker", "")
            n_insiders = buy.get("n_insiders", 1)
            total_value = buy.get("total_value", 0)
            if n_insiders >= 3 and total_value > 500000:
                edges.append({
                    "source": "insider",
                    "edge_type": "cluster_buying",
                    "description": f"Insider cluster buying: {n_insiders} insiders bought {ticker}",
                    "signal": f"Total value: ${total_value:,.0f} in last 7 days",
                    "hypothesis": f"Multiple insiders buying {ticker} within 7 days is a strong "
                                  f"bullish signal. Insiders have material non-public information. "
                                  f"Follow-on price appreciation typically 5-15% in 1-3 months.",
                    "entry_rules": f"Buy {ticker} on next session open. "
                                   f"Position size: 0.5% risk (insider signals are high-conviction "
                                   f"but not guaranteed). Stop below recent swing low.",
                    "exit_rules": "Exit at +10% or 3 months, whichever comes first.",
                    "score": _score_edge(
                        signal_strength=min(n_insiders / 5, 1) * min(total_value / 2000000, 1),
                        confidence="medium",
                        data_quality="daily",
                        actionable=True,
                        historical_precedent="well_known",
                    ),
                    "regime_fit": ["neutral", "risk_on", "caution"],
                })
    
    return edges


def scan_short_interest_edges() -> list:
    """Scan short interest for squeeze candidates."""
    from fetch_short_interest import get_high_short_interest_stocks
    
    edges = []
    si_result = _safe_call(get_high_short_interest_stocks, threshold=10.0)
    if not si_result or not isinstance(si_result, dict):
        return edges
    
    stocks = si_result.get("stocks", [])
    for stock in stocks[:3]:
        ticker = stock.get("ticker", "")
        pct = stock.get("short_pct_of_float", 0)
        dtc = stock.get("days_to_cover", 0)
        change = stock.get("change_pct", 0)
        
        if pct > 20 and dtc > 5:
            edges.append({
                "source": "short_interest",
                "edge_type": "squeeze_candidate",
                "description": f"High short interest: {ticker} {pct:.1f}% float, {dtc:.1f} days to cover",
                "signal": f"SI: {pct:.1f}% of float, DTC: {dtc:.1f}, MoM change: {change:+.1f}%",
                "hypothesis": f"{ticker} has extreme short interest ({pct:.1f}% of float). "
                              f"If positive catalyst emerges, short squeeze potential is high. "
                              f"Watch for: insider buying, earnings beat, analyst upgrade, "
                              f"or sector rotation into its industry.",
                "entry_rules": f"Watch {ticker} for positive catalyst. Enter long on first "
                               f"green day with volume > 2x 20d avg after positive news. "
                               f"Stop below entry-day low. Very small size (0.25% risk) — "
                               f"high volatility.",
                "exit_rules": "Exit at +15% (squeeze targets often don't last), "
                              "or if short interest drops below 10%, or after 5 days.",
                "score": _score_edge(
                    signal_strength=min(pct / 50, 1) * min(dtc / 20, 1),
                    confidence="low",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="well_known",
                ),
                "regime_fit": ["risk_on", "neutral"],
            })
    
    return edges


def scan_sentiment_edges() -> list:
    """Scan Fear & Greed, LunarCrush, and put/call for sentiment extremes."""
    edges = []
    
    # Fear & Greed
    from fetch_fear_greed import get_current_fg
    fg = _safe_call(get_current_fg)
    if fg:
        fg_val = fg.get("value", 50)
        if fg_val < 20:
            edges.append({
                "source": "sentiment",
                "edge_type": "extreme_fear",
                "description": f"Extreme Fear: F&G = {fg_val} ({fg.get('classification', '')})",
                "signal": f"F&G = {fg_val}",
                "hypothesis": "Extreme fear historically marks crypto bottoms. "
                              "Buy BTC/ETH with small size. Typically 20-40% bounce "
                              "within 2-4 weeks when F&G < 15.",
                "entry_rules": "Buy BTC and ETH when F&G < 15. Scale in over 3 days. "
                               "Stop below recent low. 0.5% risk per asset.",
                "exit_rules": "Exit when F&G > 50 or +20% gain.",
                "score": _score_edge(
                    signal_strength=(20 - fg_val) / 20,
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="well_known",
                ),
                "regime_fit": ["risk_off"],
            })
        elif fg_val > 80:
            edges.append({
                "source": "sentiment",
                "edge_type": "extreme_greed",
                "description": f"Extreme Greed: F&G = {fg_val} ({fg.get('classification', '')})",
                "signal": f"F&G = {fg_val}",
                "hypothesis": "Extreme greed historically marks crypto tops. "
                              "Reduce crypto exposure. Consider shorting high-flyers.",
                "entry_rules": "Reduce crypto longs by 50%. Short the weakest altcoin "
                               "with RSI > 80. Stop above recent high.",
                "exit_rules": "Exit when F&G < 50 or +5R on short.",
                "score": _score_edge(
                    signal_strength=(fg_val - 80) / 20,
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="well_known",
                ),
                "regime_fit": ["complacent"],
            })
    
    # Put/Call ratio
    from fetch_put_call_ratio import get_put_call_summary
    pc = _safe_call(get_put_call_summary)
    if pc:
        total = pc.get("total_ratio", 1.0)
        equity = pc.get("equity_ratio", 1.0)
        
        if total > 1.3:
            edges.append({
                "source": "sentiment",
                "edge_type": "put_call_extreme",
                "description": f"Put/Call ratio extreme: {total} (equity: {equity})",
                "signal": f"Total P/C: {total}, Equity P/C: {equity}",
                "hypothesis": "Put/Call > 1.3 = extreme bearishness. "
                              "Contrarian bullish signal. Markets typically bounce "
                              "within 1-3 days from this extreme.",
                "entry_rules": "Buy SPY/QQQ on next session. Stop below recent low. "
                               "0.5% risk. This is a contrarian timing signal.",
                "exit_rules": "Exit at +3% or when P/C drops below 0.8.",
                "score": _score_edge(
                    signal_strength=min((total - 1.3) / 1.0, 1),
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="some_evidence",
                ),
                "regime_fit": ["risk_off", "caution"],
            })
        elif total < 0.6:
            edges.append({
                "source": "sentiment",
                "edge_type": "put_call_complacency",
                "description": f"Put/Call ratio low: {total} (equity: {equity})",
                "signal": f"Total P/C: {total}, Equity P/C: {equity}",
                "hypothesis": "Put/Call < 0.6 = extreme complacency. "
                              "Contrarian bearish signal. Consider hedging or reducing longs.",
                "entry_rules": "Reduce long exposure by 30%. Consider SPY puts 30 DTE. "
                               "Not a short signal by itself — wait for price confirmation.",
                "exit_rules": "Unwind hedge when P/C returns to 0.9-1.1 range.",
                "score": _score_edge(
                    signal_strength=min((0.6 - total) / 0.4, 1),
                    confidence="low",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="some_evidence",
                ),
                "regime_fit": ["complacent"],
            })
    
    # LunarCrush sentiment divergence
    from fetch_lunarcrush import get_crypto_sentiment_summary
    lc = _safe_call(get_crypto_sentiment_summary)
    if lc:
        for coin, data in lc.items():
            sentiment = data.get("sentiment", 50)
            trend = data.get("trend", "flat")
            galaxy = data.get("galaxy_score", 50)
            
            # High sentiment but downward trend = divergence
            if sentiment > 80 and trend == "down":
                edges.append({
                    "source": "sentiment",
                    "edge_type": "social_sentiment_divergence",
                    "description": f"{coin}: sentiment {sentiment:.0f} but price trend DOWN",
                    "signal": f"Sentiment: {sentiment:.0f}, Trend: {trend}, Galaxy: {galaxy:.0f}",
                    "hypothesis": f"Social sentiment for {coin} is very high ({sentiment:.0f}) "
                                  f"but price is trending down. This divergence suggests "
                                  f"smart money is distributing to retail. Bearish signal.",
                    "entry_rules": f"Short {coin} on next bounce to 10MA. "
                                   f"Stop above recent high. Small size (0.25% risk).",
                    "exit_rules": "Exit at -10% or when sentiment drops below 40.",
                    "score": _score_edge(
                        signal_strength=(sentiment - 80) / 20,
                        confidence="low",
                        data_quality="daily",
                        actionable=True,
                        historical_precedent="novel",
                    ),
                    "regime_fit": ["caution", "complacent"],
                })
    
    return edges


def scan_crypto_macro_edges() -> list:
    """Scan DeFi TVL, stablecoin supply, and funding rates for crypto macro edges."""
    edges = []
    
    # DeFi TVL trend
    from fetch_defillama import get_tvl_summary
    tvl = _safe_call(get_tvl_summary)
    if tvl:
        total_tvl = tvl.get("total_tvl", 0)
        trend = tvl.get("trend", "")
        
        if trend == "declining" and total_tvl > 0:
            edges.append({
                "source": "crypto_macro",
                "edge_type": "tvl_decline",
                "description": f"DeFi TVL declining (${total_tvl/1e9:.1f}B)",
                "signal": f"TVL: ${total_tvl/1e9:.1f}B, trend: {trend}",
                "hypothesis": "Declining TVL = capital leaving DeFi. Bearish for crypto. "
                              "Reduce altcoin exposure. BTC/ETH less affected but still at risk.",
                "entry_rules": "Reduce crypto longs by 30%. Avoid DeFi tokens. "
                               "If shorting, target high-beta altcoins (SOL, AVAX, ARB).",
                "exit_rules": "Re-enter when TVL stabilizes for 7+ days.",
                "score": _score_edge(
                    signal_strength=0.5,
                    confidence="low",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="some_evidence",
                ),
                "regime_fit": ["risk_off", "caution"],
            })
        elif trend == "rising" and total_tvl > 0:
            edges.append({
                "source": "crypto_macro",
                "edge_type": "tvl_growth",
                "description": f"DeFi TVL rising (${total_tvl/1e9:.1f}B)",
                "signal": f"TVL: ${total_tvl/1e9:.1f}B, trend: {trend}",
                "hypothesis": "Rising TVL = capital entering DeFi. Bullish for crypto. "
                              "DeFi tokens (UNI, AAVE, COMP) outperform in this regime.",
                "entry_rules": "Add DeFi token exposure. Long UNI/AAVE on pullbacks to 20MA.",
                "exit_rules": "Exit when TVL trend reverses or individual target reached.",
                "score": _score_edge(
                    signal_strength=0.5,
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="some_evidence",
                ),
                "regime_fit": ["risk_on", "neutral"],
            })
    
    # Stablecoin supply
    from fetch_stablecoin_supply import get_stablecoin_summary
    sc = _safe_call(get_stablecoin_summary)
    if sc:
        total_supply = sc.get("total_supply", 0)
        sc_trend = sc.get("trend", "")
        
        if sc_trend == "rising":
            edges.append({
                "source": "crypto_macro",
                "edge_type": "stablecoin_inflow",
                "description": f"Stablecoin supply rising (${total_supply/1e9:.1f}B)",
                "signal": f"Supply: ${total_supply/1e9:.1f}B, trend: {sc_trend}",
                "hypothesis": "Rising stablecoin supply = dry powder entering crypto. "
                              "Bullish — capital is positioned to buy. "
                              "Combined with extreme F&G fear = very bullish.",
                "entry_rules": "Build crypto longs (BTC, ETH) when stablecoin supply rising "
                               "AND F&G < 30.",
                "exit_rules": "Exit when stablecoin supply flattens or declines.",
                "score": _score_edge(
                    signal_strength=0.4,
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="novel",
                ),
                "regime_fit": ["risk_off", "caution"],
            })
    
    # Funding rate extremes
    from fetch_hyperliquid_metrics import get_funding_summary
    funding = _safe_call(get_funding_summary)
    if funding:
        extreme_pos = [k for k, v in funding.items() if v.get("extreme") == "positive_extreme"]
        extreme_neg = [k for k, v in funding.items() if v.get("extreme") == "negative_extreme"]
        
        if len(extreme_neg) >= 3:
            edges.append({
                "source": "crypto_macro",
                "edge_type": "negative_funding_cluster",
                "description": f"Negative funding extremes: {extreme_neg[:5]}",
                "signal": f"{len(extreme_neg)} coins with extreme negative funding",
                "hypothesis": "Multiple coins with extreme negative funding = crowded shorts. "
                              "Squeeze risk elevated. Long the ones with improving price action.",
                "entry_rules": "From extreme_neg list, pick coins with price above 10MA. "
                               "Buy with 0.25% risk each. These are high-volatility trades.",
                "exit_rules": "Exit when funding normalizes (> -0.01%) or +10% gain.",
                "score": _score_edge(
                    signal_strength=min(len(extreme_neg) / 5, 1),
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="some_evidence",
                ),
                "regime_fit": ["caution", "risk_off"],
            })
        elif len(extreme_pos) >= 3:
            edges.append({
                "source": "crypto_macro",
                "edge_type": "positive_funding_cluster",
                "description": f"Positive funding extremes: {extreme_pos[:5]}",
                "signal": f"{len(extreme_pos)} coins with extreme positive funding",
                "hypothesis": "Multiple coins with extreme positive funding = crowded longs. "
                              "Long squeeze risk. Reduce longs in these coins.",
                "entry_rules": "From extreme_pos list, reduce longs or short the weakest. "
                               "0.25% risk per short. High volatility.",
                "exit_rules": "Exit when funding normalizes or +10% gain on short.",
                "score": _score_edge(
                    signal_strength=min(len(extreme_pos) / 5, 1),
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="some_evidence",
                ),
                "regime_fit": ["complacent", "caution"],
            })
    
    return edges


def scan_strategy_regime_edges() -> list:
    """Use strategy-regime performance heatmap to find which strategies to run."""
    from compute_strategy_regime import compute_strategy_regime_heatmap
    
    edges = []
    heatmap = _safe_call(compute_strategy_regime_heatmap)
    if not heatmap or heatmap.get("note"):
        return edges
    
    matrix = heatmap.get("matrix", {})
    current_regime = _get_current_regime()
    
    if not current_regime:
        return edges
    
    # Find strategies that perform well in current regime
    good_strategies = []
    for strat, cells in matrix.items():
        cell = cells.get(current_regime, {})
        if cell.get("count", 0) >= 2 and cell.get("avg_r", 0) > 0:
            good_strategies.append({
                "strategy": strat,
                "count": cell["count"],
                "win_rate": cell["win_rate"],
                "avg_r": cell["avg_r"],
            })
    
    if good_strategies:
        good_strategies.sort(key=lambda x: x["avg_r"], reverse=True)
        best = good_strategies[0]
        
        edges.append({
            "source": "strategy_regime",
            "edge_type": "regime_matched_strategy",
            "description": f"{best['strategy']} performs well in {current_regime} regime",
            "signal": f"{best['count']} trades, WR={best['win_rate']}%, avg={best['avg_r']:+.2f}R",
            "hypothesis": f"Based on {best['count']} historical trades, {best['strategy']} "
                          f"has a positive edge in {current_regime} conditions. "
                          f"Increase scanning frequency for this strategy.",
            "entry_rules": f"Prioritize {best['strategy']} signals. Increase position size "
                           f"by 50% (from 1% to 1.5% risk) when regime matches.",
            "exit_rules": "Follow strategy's standard exit rules.",
            "score": _score_edge(
                signal_strength=min(best["avg_r"] / 2, 1),
                confidence="medium" if best["count"] >= 5 else "low",
                data_quality="daily",
                actionable=True,
                historical_precedent="some_evidence",
            ),
            "regime_fit": [current_regime],
        })
    
    # Find strategies to avoid in current regime
    bad_strategies = []
    for strat, cells in matrix.items():
        cell = cells.get(current_regime, {})
        if cell.get("count", 0) >= 2 and cell.get("avg_r", 0) < -0.2:
            bad_strategies.append({
                "strategy": strat,
                "count": cell["count"],
                "win_rate": cell["win_rate"],
                "avg_r": cell["avg_r"],
            })
    
    if bad_strategies:
        worst = sorted(bad_strategies, key=lambda x: x["avg_r"])[0]
        edges.append({
            "source": "strategy_regime",
            "edge_type": "regime_mismatched_strategy",
            "description": f"⚠️ {worst['strategy']} performs poorly in {current_regime} regime",
            "signal": f"{worst['count']} trades, WR={worst['win_rate']}%, avg={worst['avg_r']:+.2f}R",
            "hypothesis": f"Based on {worst['count']} historical trades, {worst['strategy']} "
                          f"has a negative edge in {current_regime} conditions. "
                          f"Reduce scanning frequency or skip signals from this strategy.",
            "entry_rules": f"Skip {worst['strategy']} signals when regime = {current_regime}. "
                           f"If already in a trade from this strategy, consider early exit.",
            "exit_rules": "N/A — filter signal, don't enter.",
            "score": _score_edge(
                signal_strength=min(abs(worst["avg_r"]) / 2, 1),
                confidence="medium" if worst["count"] >= 5 else "low",
                data_quality="daily",
                actionable=True,
                historical_precedent="some_evidence",
            ),
            "regime_fit": [current_regime],
        })
    
    return edges


def scan_economic_event_edges() -> list:
    """Scan economic calendar for event-driven edges."""
    from fetch_economic_calendar import get_next_high_impact_events
    
    edges = []
    events = _safe_call(get_next_high_impact_events, days_ahead=7)
    if not events:
        return edges
    
    for event in events[:3]:
        event_name = event.get("event", "")
        event_date = event.get("date", "")
        country = event.get("country", "")
        consensus = event.get("consensus", "")
        previous = event.get("previous", "")
        
        # FOMC meetings
        if "FOMC" in event_name or "Rate Decision" in event_name:
            edges.append({
                "source": "economic",
                "edge_type": "fomc_proximity",
                "description": f"FOMC event on {event_date}: {event_name}",
                "signal": f"Consensus: {consensus}, Previous: {previous}",
                "hypothesis": "FOMC events create volatility. Pre-event: reduce new entries. "
                              "Post-event: trade the reaction — if market rallies on hawkish news, "
                              "that's a strong bullish signal.",
                "entry_rules": "No new entries 24h before FOMC. Wait for decision, then "
                               "enter in direction of initial market reaction. "
                               "0.5% risk (event volatility is high).",
                "exit_rules": "Exit at +2R or 3 trading days post-event.",
                "score": _score_edge(
                    signal_strength=0.6,
                    confidence="high",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="well_known",
                ),
                "regime_fit": ["neutral", "caution", "risk_off"],
            })
        # CPI / inflation data
        elif "CPI" in event_name:
            edges.append({
                "source": "economic",
                "edge_type": "cpi_release",
                "description": f"CPI release on {event_date}: {event_name}",
                "signal": f"Consensus: {consensus}, Previous: {previous}",
                "hypothesis": "Hot CPI → risk-off (stocks down, dollar up, gold down). "
                              "Cold CPI → risk-on (stocks up, dollar down, gold up). "
                              "Trade the reaction, not the prediction.",
                "entry_rules": "Wait 30 min after release. If SPY up > 0.5% on cold CPI: "
                               "go long QQQ. If SPY down > 0.5% on hot CPI: short SPY. "
                               "0.5% risk.",
                "exit_rules": "Exit at end of day or +2R.",
                "score": _score_edge(
                    signal_strength=0.5,
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="well_known",
                ),
                "regime_fit": ["neutral", "caution"],
            })
        # NFP
        elif "Nonfarm" in event_name or "NFP" in event_name or "Employment" in event_name:
            edges.append({
                "source": "economic",
                "edge_type": "nfp_release",
                "description": f"NFP release on {event_date}: {event_name}",
                "signal": f"Consensus: {consensus}, Previous: {previous}",
                "hypothesis": "Strong NFP → dollar strengthens, risk assets mixed. "
                              "Weak NFP → dollar weakens, risk assets mixed-to-bullish "
                              "(rate cut hopes). High volatility in first 15 min.",
                "entry_rules": "Wait 15 min after release. Trade direction of initial "
                               "trend. 0.5% risk. Don't fade the initial move.",
                "exit_rules": "Exit at end of day or +1.5R.",
                "score": _score_edge(
                    signal_strength=0.4,
                    confidence="medium",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="well_known",
                ),
                "regime_fit": ["neutral"],
            })
    
    return edges


def scan_github_activity_edges() -> list:
    """Scan GitHub activity for crypto fundamentals divergence."""
    from fetch_github_activity import get_github_summary
    
    edges = []
    gh = _safe_call(get_github_summary)
    if not gh:
        return edges
    
    for coin, data in gh.items():
        commits = data.get("commits_4w", 0)
        prev_commits = data.get("prior_commits_4w", 0)
        change_pct = data.get("change_pct", 0)
        
        # Rising dev activity + price not yet reflecting = bullish
        if change_pct > 50 and commits > 30:
            edges.append({
                "source": "github",
                "edge_type": "dev_activity_surge",
                "description": f"{coin} GitHub activity surged {change_pct:+.0f}% ({commits} commits/4w)",
                "signal": f"Commits: {commits} (prior: {prev_commits}), change: {change_pct:+.0f}%",
                "hypothesis": f"Developer activity for {coin} increased {change_pct:.0f}%. "
                              f"Fundamental improvement often precedes price appreciation by 2-8 weeks. "
                              f"Accumulate on weakness.",
                "entry_rules": f"Long {coin} on next pullback to 50MA. "
                               f"0.5% risk. This is a medium-term thesis (4-8 weeks).",
                "exit_rules": "Exit at +15% or 8 weeks, or if dev activity reverts.",
                "score": _score_edge(
                    signal_strength=min(change_pct / 200, 1),
                    confidence="low",
                    data_quality="daily",
                    actionable=True,
                    historical_precedent="novel",
                ),
                "regime_fit": ["risk_on", "neutral"],
            })
    
    return edges


def _get_current_regime() -> str:
    """Get current overall regime for strategy-regime matching."""
    from fetch_macro import get_vix_signal
    from fetch_fear_greed import get_current_fg
    
    vix = _safe_call(get_vix_signal)
    fg = _safe_call(get_current_fg)
    
    stock_regime = vix.get("regime", "unknown") if vix else "unknown"
    fg_val = fg.get("value", 50) if fg else 50
    
    crypto_regime = "neutral"
    if fg_val > 75:
        crypto_regime = "greed"
    elif fg_val > 55:
        crypto_regime = "risk_on"
    elif fg_val < 25:
        crypto_regime = "risk_off"
    elif fg_val < 45:
        crypto_regime = "fear"
    
    if stock_regime == "risk_off" or crypto_regime == "risk_off":
        return "risk_off"
    elif stock_regime == "risk_on" and crypto_regime in ("risk_on", "neutral"):
        return "risk_on"
    elif stock_regime in ("elevated",) or crypto_regime in ("fear", "greed"):
        return "caution"
    else:
        return "neutral"


# ─── Main Engine ────────────────────────────────────────────────────────────

ALL_SCANNERS = {
    "breadth": scan_breadth_edges,
    "volatility": scan_volatility_edges,
    "rotation": scan_rotation_edges,
    "correlation": scan_correlation_edges,
    "insider": scan_insider_edges,
    "short_interest": scan_short_interest_edges,
    "sentiment": scan_sentiment_edges,
    "crypto_macro": scan_crypto_macro_edges,
    "strategy_regime": scan_strategy_regime_edges,
    "economic": scan_economic_event_edges,
    "github": scan_github_activity_edges,
}


def run_edge_discovery(sources: list = None) -> dict:
    """
    Run all edge scanners and return ranked, scored edges.
    
    Args:
        sources: list of source names to scan (None = all)
    
    Returns:
    {
        "timestamp": str,
        "total_edges": int,
        "edges": [list of scored edge dicts, sorted by composite score],
        "by_source": {source: [edges]},
        "top_edge": dict,
        "regime": str,
    }
    """
    scanners = ALL_SCANNERS if sources is None else {k: v for k, v in ALL_SCANNERS.items() if k in sources}
    
    all_edges = []
    by_source = {}
    
    for source_name, scanner_fn in scanners.items():
        print(f"  Scanning {source_name}...", file=sys.stderr)
        edges = _safe_call(scanner_fn) or []
        by_source[source_name] = edges
        all_edges.extend(edges)
        print(f"    Found {len(edges)} edge(s)", file=sys.stderr)
    
    # Sort by composite score (descending)
    all_edges.sort(key=lambda x: x.get("score", {}).get("composite", 0), reverse=True)
    
    # Get current regime
    regime = _get_current_regime()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "regime": regime,
        "total_edges": len(all_edges),
        "edges": all_edges,
        "by_source": {k: len(v) for k, v in by_source.items()},
        "top_edge": all_edges[0] if all_edges else None,
    }


def stage_top_edges(results: dict, max_stage: int = 3) -> list:
    """
    Stage top edges as candidate files for the autonomous pipeline.
    Only stages edges with composite score > 40 and confidence >= 'low'.
    """
    if not EDGE_CANDIDATES_DIR.exists():
        EDGE_CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    
    staged = []
    today = now_pt().strftime("%Y%m%d")
    
    for edge in results.get("edges", [])[:max_stage]:
        score = edge.get("score", {}).get("composite", 0)
        confidence = edge.get("confidence", "low") if "confidence" in edge else "low"
        
        # Actually get confidence from the score dict
        # confidence is embedded in the score dict via its point value
        conf_val = edge.get("score", {}).get("confidence", 0)
        confidence = "high" if conf_val >= 25 else "medium" if conf_val >= 15 else "low"
        
        if score < 40:
            continue
        
        # Generate candidate file
        edge_type = edge.get("edge_type", "unknown")
        short_name = edge_type.replace("_", "-")[:30]
        filename = f"CAND-{today}-{short_name}.md"
        filepath = EDGE_CANDIDATES_DIR / filename
        
        content = f"""---
status: staged
source: {edge.get('source', 'unknown')}
edge_type: {edge_type}
composite_score: {score}
confidence: {confidence}
regime_fit: {edge.get('regime_fit', [])}
created: {today}
---

# Edge Candidate: {edge.get('description', 'Unknown')}

## Source
{edge.get('source', 'unknown')} scanner

## Signal
{edge.get('signal', 'N/A')}

## Hypothesis
{edge.get('hypothesis', 'N/A')}

## Entry Rules
{edge.get('entry_rules', 'N/A')}

## Exit Rules
{edge.get('exit_rules', 'N/A')}

## Score Breakdown
- Composite: {score}
- Signal Strength: {edge.get('score', {}).get('signal_strength', 0)}
- Confidence: {confidence} ({conf_val} pts)
- Data Quality: {edge.get('score', {}).get('data_quality', 0)}
- Actionable: {edge.get('score', {}).get('actionable', 0)}
- Precedent: {edge.get('score', {}).get('precedent', 0)}

## Regime Fit
{edge.get('regime_fit', [])}

## Recommended Pipeline Action
"""
        if score >= 60 and confidence == "high":
            content += "PROMISING — proceed to full backtest and walk-forward validation.\n"
        elif score >= 40:
            content += "SPECULATIVE — quick Phase 1A backtest to check for edge.\n"
        else:
            content += "REJECT — insufficient signal strength or confidence.\n"
        
        filepath.write_text(content)
        staged.append(str(filepath))
        print(f"  Staged: {filepath.name} (score={score})", file=sys.stderr)
    
    return staged


def print_edge_report(results: dict):
    """Print edge discovery results in human-readable format."""
    print(f"\n🔍 **Edge Discovery Engine Report**")
    print(f"   {results['timestamp'][:19]}")
    print(f"   Current regime: {results['regime']}")
    print(f"   Total edges found: {results['total_edges']}\n")
    
    # By source
    print("Edges by source:")
    for source, count in results.get("by_source", {}).items():
        print(f"  {source}: {count}")
    
    print()
    
    # Top edges
    for i, edge in enumerate(results.get("edges", [])[:10]):
        score = edge["score"]["composite"]
        source = edge["source"]
        etype = edge["edge_type"]
        desc = edge["description"]
        print(f"  #{i+1} [{score:.0f}] {source}/{etype}")
        print(f"      {desc}")
        print(f"      Hypothesis: {edge['hypothesis'][:100]}...")
        print(f"      Regime fit: {edge.get('regime_fit', [])}")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Autonomous Edge Discovery Engine")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--source", type=str, help="Scan single source only")
    ap.add_argument("--stage", action="store_true", help="Stage top edges as candidate files")
    ap.add_argument("--max-stage", type=int, default=3, help="Max candidates to stage")
    args = ap.parse_args()
    
    sources = [args.source] if args.source else None
    
    results = run_edge_discovery(sources)
    
    if args.stage:
        staged = stage_top_edges(results, max_stage=args.max_stage)
        results["staged_candidates"] = staged
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_edge_report(results)
