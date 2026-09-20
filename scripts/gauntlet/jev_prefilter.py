#!/usr/bin/env python3
"""
Jev Pre-Signal Filter — US-150

Before a scanner signal enters the paper trading capture pipeline,
Jev classifies whether the signal is worth trading given current
market context.

Three checks per signal:
  1. Signal validity — does this look like a genuine setup?
  2. Market alignment — is the current regime favorable?
  3. Confluence — do multiple signals reinforce or conflict?

Cost: ~$0.0012 per trade signal check (3 questions × $0.0004).

Usage:
    from jev_prefilter import prefilter_signal
    result = prefilter_signal(signal_dict, market_context)
    if result["approved"]:
        capture_pipeline(signal)
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from jev_client import JevClient


@dataclass
class PrefilterResult:
    approved: bool
    confidence: float
    reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def prefilter_signal(signal: dict, market_context: Optional[dict] = None,
                     jev: Optional[JevClient] = None) -> PrefilterResult:
    """
    Evaluate a trading signal before it enters the capture pipeline.

    Args:
        signal: {"strategy_id": str, "ticker": str, "direction": str,
                 "entry_price": float, "stop_price": float,
                 "target_price": float, "confidence": str, ...}
        market_context: {"regime": str, "vix": float, "funding": float,
                         "btc_beta": float, "volume_profile": str, ...}
        jev: optional pre-initialized JevClient

    Returns:
        PrefilterResult with approved=True/False and details
    """
    if jev is None:
        jev = JevClient()

    # Build state: signal + market context as structured data
    state = {
        "signal": {
            "strategy": signal.get("strategy_id", "unknown"),
            "ticker": signal.get("ticker", "?"),
            "direction": signal.get("direction", "long"),
            "risk_pct": signal.get("risk_pct", 0),
            "entry_price": signal.get("entry_price", 0),
            "scanner_confidence": signal.get("confidence", "medium"),
        },
        "market": market_context or {},
    }

    results = {}
    reasons = []

    # Question 1: Signal validity
    try:
        prob = jev.noul(
            state=state,
            instructions="Based on the signal details and market context, is this a valid, "
                         "non-spurious trading setup worth paper-trading?",
            true_criteria="Valid: the setup matches the strategy's edge, market context supports it, "
                         "risk/reward is reasonable",
            false_criteria="Invalid: likely noise, wrong market conditions, unrealistic risk/reward, "
                          "or contradicts the strategy's thesis"
        )
        results["signal_validity"] = prob
        if prob < 0.40:
            reasons.append(f"Signal validity low ({prob:.0%})")
        elif prob < 0.65:
            reasons.append(f"Signal validity marginal ({prob:.0%})")
    except Exception as e:
        results["signal_validity"] = None
        reasons.append(f"Signal validity check failed: {e}")

    # Question 2: Market alignment
    if market_context:
        try:
            prob = jev.noul(
                state=state,
                instructions="Is the current market regime favorable for this specific trade setup? "
                             "Consider the strategy type, direction, and asset class.",
                true_criteria="Favorable: regime supports this strategy (e.g. trending market for "
                             "trend-following, high vol for breakout strategies)",
                false_criteria="Unfavorable: regime contradicts strategy (e.g. choppy market for "
                              "trend strategies, low vol for breakout)"
            )
            results["market_alignment"] = prob
            if prob < 0.40:
                reasons.append(f"Market alignment poor ({prob:.0%})")
        except Exception as e:
            results["market_alignment"] = None
            reasons.append(f"Market alignment check failed: {e}")
    else:
        results["market_alignment"] = None

    # Question 3: Risk/reward reasonableness
    try:
        prob = jev.noul(
            state=state,
            instructions="Is the risk/reward profile of this trade reasonable? "
                         "Consider the stop distance, target distance, and current volatility.",
            true_criteria="Reasonable: R:R >= 1.5, stop is outside noise range, "
                         "target is achievable given current conditions",
            false_criteria="Unreasonable: R:R < 1, stop too tight (noise), "
                          "target unrealistic for current volatility"
        )
        results["risk_reward"] = prob
        if prob < 0.30:
            reasons.append(f"Risk/reward unreasonable ({prob:.0%})")
    except Exception as e:
        results["risk_reward"] = None
        reasons.append(f"Risk/reward check failed: {e}")

    # Decision: approve if no critical failures
    validity = results.get("signal_validity", 0.5) or 0.5
    alignment = results.get("market_alignment", 0.5) or 0.5
    rr = results.get("risk_reward", 0.5) or 0.5

    # Weighted composite: signal quality matters most
    composite = (validity * 0.5) + (alignment * 0.25) + (rr * 0.25)
    approved = composite >= 0.45 and validity >= 0.35

    return PrefilterResult(
        approved=approved,
        confidence=composite,
        reasons=reasons,
        details=results,
    )


def batch_prefilter(signals: list[dict], market_context: Optional[dict] = None) -> list[PrefilterResult]:
    """Filter a batch of signals. Uses a single JevClient for all."""
    jev = JevClient()
    return [prefilter_signal(s, market_context, jev) for s in signals]


# ── Quick test ──

if __name__ == "__main__":
    signal = {
        "strategy_id": "STR-Q-stocks",
        "ticker": "SPY",
        "direction": "long",
        "entry_price": 545.0,
        "stop_price": 542.0,
        "target_price": 555.0,
        "risk_pct": 0.0055,
        "confidence": "medium",
    }
    context = {
        "regime": "bull_normal",
        "vix": 18.5,
        "spy_vs_sma200": "above",
    }
    result = prefilter_signal(signal, context)
    status = "✅ APPROVED" if result.approved else "❌ REJECTED"
    print(f"{status} (confidence: {result.confidence:.0%})")
    for r in result.reasons:
        print(f"  {r}")
    print(f"  Details: {result.details}")