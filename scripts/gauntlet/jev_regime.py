#!/usr/bin/env python3
"""
Jev Regime Classifier — US-152

Replaces/augments crypto_regime.py heuristics with Jev classification.
Classifies market regime using structured market data as input.

Regime labels: bull/bear/flat × high/normal/low vol = 9 regimes.
Also classifies: trending vs ranging, risk-on vs risk-off.

Cost: ~$0.0008 per classification (2 questions × $0.0004).
Latency: ~70-150ms — usable intra-bar for STR-Q 5m sweeps.

Usage:
    from jev_regime import classify_regime
    regime = classify_regime(market_data)
    # {"regime": "bear_high", "trend": "ranging", "confidence": 0.87, ...}
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import json
from jev_client import JevClient


REGIME_LEVELS = [
    "bull_low — strong uptrend, low volatility, orderly grind higher",
    "bull_normal — uptrend with normal volatility, healthy price action",
    "bull_high — volatile uptrend, possible blow-off top or euphoria",
    "flat_low — low-volatility sideways, consolidation before next move",
    "flat_normal — normal chop, no clear direction, mean-reversion friendly",
    "flat_high — high-volatility sideways, whipsaw danger, wide ranges",
    "bear_low — orderly decline, low panic, grinding lower",
    "bear_normal — downtrend with normal volatility, trending lower",
    "bear_high — panic selling, capitulation, extreme fear, VIX spike",
]

TREND_LEVELS = [
    "strong_uptrend — clear higher highs and higher lows, above key MAs",
    "weak_uptrend — grinding higher but momentum fading",
    "ranging — no clear direction, oscillating between support and resistance",
    "weak_downtrend — grinding lower, support levels holding tentatively",
    "strong_downtrend — clear lower lows and lower highs, below key MAs",
]


@dataclass
class RegimeResult:
    regime: str                    # e.g. "bear_high"
    regime_confidence: float       # 0-1
    trend: str                     # e.g. "ranging"
    trend_confidence: float        # 0-1
    risk_environment: str          # "risk_on", "risk_off", "neutral"
    details: dict[str, Any] = field(default_factory=dict)


def classify_regime(market_data: dict,
                    jev: Optional[JevClient] = None) -> RegimeResult:
    """
    Classify current market regime from structured market data.

    Args:
        market_data: {
            "ticker": str,
            "price": float,
            "sma50": float, "sma200": float,
            "atr_pct": float,           # ATR as % of price
            "atr_percentile_20d": float, # where current ATR sits in 20d range
            "rsi": float,
            "vix": float,               # if stock
            "funding_rate": float,      # if crypto (8h rate as decimal)
            "funding_z": float,         # funding z-score
            "volume_profile": str,       # "increasing", "declining", "average"
            "recent_returns_5d": float,  # 5-day return as decimal
        }
        jev: optional pre-initialized JevClient

    Returns:
        RegimeResult with regime, trend, and risk environment
    """
    if jev is None:
        jev = JevClient()

    details = {}

    # Question 1: Regime classification (9-way score)
    try:
        result = jev.score(
            state=market_data,
            instructions="Classify the current market regime based on trend direction, "
                         "volatility level, and momentum. Consider price vs key moving averages, "
                         "recent returns, ATR percentile, RSI, and any sentiment indicators.",
            levels=REGIME_LEVELS,
        )
        level_idx = round(result["score"])
        regime = REGIME_LEVELS[min(level_idx, len(REGIME_LEVELS) - 1)].split(" —")[0]
        details["regime_score"] = result["score"]
        details["regime_probabilities"] = result.get("probabilities", {})
        details["regime_confidence"] = result.get("confidence", 0)
    except Exception as e:
        regime = "flat_normal"
        details["regime_score"] = None
        details["regime_confidence"] = None
        details["regime_error"] = str(e)

    # Question 2: Trend classification (5-way score)
    try:
        result = jev.score(
            state=market_data,
            instructions="Classify the current trend structure. Consider: "
                         "higher highs/lower lows pattern, moving average relationships, "
                         "momentum indicators, and recent price action.",
            levels=TREND_LEVELS,
        )
        level_idx = round(result["score"])
        trend = TREND_LEVELS[min(level_idx, len(TREND_LEVELS) - 1)].split(" —")[0]
        details["trend_score"] = result["score"]
        details["trend_probabilities"] = result.get("probabilities", {})
        details["trend_confidence"] = result.get("confidence", 0)
    except Exception as e:
        trend = "ranging"
        details["trend_score"] = None
        details["trend_confidence"] = None
        details["trend_error"] = str(e)

    # Question 3: Risk environment (noul)
    try:
        risk_prob = jev.noul(
            state=market_data,
            instructions="Is the current market in a risk-on or risk-off environment? "
                         "Consider: volatility, correlations, funding rates, VIX levels.",
            true_criteria="Risk-on: low VIX, positive funding, bullish correlations, "
                         "investors seeking risk assets",
            false_criteria="Risk-off: high VIX, negative funding, flight to safety, "
                          "de-risking behavior"
        )
        details["risk_on_probability"] = risk_prob
        if risk_prob > 0.65:
            risk_environment = "risk_on"
        elif risk_prob < 0.35:
            risk_environment = "risk_off"
        else:
            risk_environment = "neutral"
    except Exception as e:
        risk_environment = "neutral"
        details["risk_on_probability"] = None
        details["risk_error"] = str(e)

    return RegimeResult(
        regime=regime,
        regime_confidence=details.get("regime_confidence", 0) or 0,
        trend=trend,
        trend_confidence=details.get("trend_confidence", 0) or 0,
        risk_environment=risk_environment,
        details=details,
    )


# ── Quick test ──

if __name__ == "__main__":
    btc_data = {
        "ticker": "BTC",
        "price": 62000,
        "sma50": 63500,
        "sma200": 58000,
        "atr_pct": 0.032,
        "atr_percentile_20d": 0.75,
        "rsi": 38,
        "funding_rate": -0.0003,
        "funding_z": -2.1,
        "volume_profile": "increasing",
        "recent_returns_5d": -0.065,
    }
    result = classify_regime(btc_data)
    print(f"Regime: {result.regime} (confidence: {result.regime_confidence:.0%})")
    print(f"Trend: {result.trend} (confidence: {result.trend_confidence:.0%})")
    print(f"Risk: {result.risk_environment}")
    print(f"Details: {json.dumps(result.details, indent=2, default=str)}")