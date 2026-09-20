#!/usr/bin/env python3
"""
Jev Pre-Signal Filter — US-150

Before a scanner signal enters the capture pipeline, Jev classifies whether
the signal is worth trading given current market context.

Three noul checks per signal:
  1. Signal validity — does this look like a genuine setup?
  2. Market alignment — is the current regime favorable?
  3. Risk/reward — is the R:R profile reasonable?

Cost: ~$0.0012 per signal (3 questions × $0.0004).

── POLICY (US-150 §2) ─────────────────────────────────────────────────
Jev decides: signal coherence, market alignment, R:R reasonableness.
Jev does NOT decide: position size, max trades/day, symbol allowlist,
  session hours, kill switch, broker rejects, account limits.

COMPOSITE: weakest-link — min(noul1, noul2, noul3).
  A signal is only as strong as its weakest dimension.

THRESHOLDS:
  composite >= 0.75  → approved  (paper-trade, eligible for live)
  0.60 <= comp < 0.75 → marginal  (paper-trade ONLY, never live)
  composite < 0.60    → rejected  (skip entirely)

FAIL-CLOSED: any Jev error → composite = 0 → rejected.
  A dead API, bad key, or timeout blocks the signal.
  Kill switch: pass --jev-off to bypass Jev entirely.

SUPERVISION: these thresholds apply to paper trading.
  Before live money, user must confirm thresholds.
  Hard limits (max size, daily count, allowlist) are in position_manager.py
  and are NOT overridden by Jev.
────────────────────────────────────────────────────────────────────────

Usage:
    from jev_prefilter import prefilter_signal
    result = prefilter_signal(signal_dict, market_context)
    if result.tier == "approved":
        open_live_trade(signal)
    elif result.tier == "marginal":
        open_paper_trade(signal)  # never live
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from jev_client import JevClient

# ── US-150 §2b: tier thresholds ───────────────────────────────────────
APPROVED_THRESHOLD = 0.75   # composite >= 0.75 → paper + live eligible
MARGINAL_THRESHOLD = 0.60   # 0.60 <= comp < 0.75 → paper only, never live
# Below 0.60 → rejected outright


@dataclass
class PrefilterResult:
    approved: bool            # True if tier != "rejected"
    tier: str                 # "approved", "marginal", "rejected"
    confidence: float         # weakest-link composite (0.0-1.0)
    reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def prefilter_signal(signal: dict, market_context: Optional[dict] = None,
                     jev: Optional[JevClient] = None) -> PrefilterResult:
    """
    Evaluate a trading signal before it enters the capture pipeline.

    Args:
        signal: {"strategy_id": str, "ticker": str, "direction": str,
                 "entry_price": float, "stop_price": float,
                 "target_price": float, "confidence": str, ...}
        market_context: {"regime": str, "vix": float, "funding": float, ...}
        jev: optional pre-initialized JevClient

    Returns:
        PrefilterResult with tier in {"approved","marginal","rejected"}
    """
    errors = []
    if jev is None:
        try:
            jev = JevClient()
        except Exception as e:
            return PrefilterResult(
                approved=False, tier="rejected", confidence=0.0,
                reasons=["Jev unavailable — fail-closed"],
                errors=[f"JevClient init failed: {e}"],
            )

    # Build state: signal features ONLY — no keys, no account data
    state = {
        "signal": {
            "strategy": signal.get("strategy_id", "unknown"),
            "ticker": signal.get("ticker", "?"),
            "direction": signal.get("direction", "long"),
            "entry_price": signal.get("entry_price", 0),
            "stop_price": signal.get("stop_price", 0),
            "target_price": signal.get("target_price", 0),
            "scanner_confidence": signal.get("confidence", "medium"),
        },
        "market": market_context or {},
    }

    nouls = {}
    reasons = []

    # Question 1: Signal validity
    try:
        prob = jev.noul(
            state=state,
            instructions="Based on the signal details and market context, is this a valid, "
                         "non-spurious trading setup worth paper-trading?",
            true_criteria="Valid: the setup matches the strategy's edge, market context "
                         "supports it, risk/reward is reasonable",
            false_criteria="Invalid: likely noise, wrong market conditions, unrealistic "
                          "risk/reward, or contradicts the strategy's thesis"
        )
        nouls["signal_validity"] = prob
        if prob < 0.40:
            reasons.append(f"Signal validity low ({prob:.0%})")
        elif prob < 0.65:
            reasons.append(f"Signal validity marginal ({prob:.0%})")
    except Exception as e:
        errors.append(f"Signal validity failed: {e}")
        nouls["signal_validity"] = 0.0  # fail-closed

    # Question 2: Market alignment
    if market_context:
        try:
            prob = jev.noul(
                state=state,
                instructions="Is the current market regime favorable for this specific "
                             "trade setup? Consider strategy type, direction, asset class.",
                true_criteria="Favorable: regime supports this strategy (e.g. trending market "
                             "for trend-following, high vol for breakout)",
                false_criteria="Unfavorable: regime contradicts strategy (e.g. choppy market "
                              "for trend strategies, low vol for breakout)"
            )
            nouls["market_alignment"] = prob
            if prob < 0.40:
                reasons.append(f"Market alignment poor ({prob:.0%})")
        except Exception as e:
            errors.append(f"Market alignment failed: {e}")
            nouls["market_alignment"] = 0.0  # fail-closed
    else:
        nouls["market_alignment"] = 0.5  # neutral when no context

    # Question 3: Risk/reward reasonableness
    try:
        prob = jev.noul(
            state=state,
            instructions="Is the risk/reward profile of this trade reasonable? "
                         "Consider stop distance, target distance, and current volatility.",
            true_criteria="Reasonable: R:R >= 1.5, stop is outside noise range, "
                         "target is achievable given current conditions",
            false_criteria="Unreasonable: R:R < 1, stop too tight (noise), "
                          "target unrealistic for current volatility"
        )
        nouls["risk_reward"] = prob
        if prob < 0.30:
            reasons.append(f"Risk/reward unreasonable ({prob:.0%})")
    except Exception as e:
        errors.append(f"Risk/reward failed: {e}")
        nouls["risk_reward"] = 0.0  # fail-closed

    # ── Decision: weakest-link composite (US-150 §2b) ──
    # A signal is only as strong as its weakest dimension.
    # If any check failed (API error), composite = 0 → rejected.
    composite = min(nouls.values())

    if composite >= APPROVED_THRESHOLD:
        tier = "approved"
        approved = True
    elif composite >= MARGINAL_THRESHOLD:
        tier = "marginal"
        approved = True      # paper-trade only, never live
    else:
        tier = "rejected"
        approved = False

    if errors:
        reasons.append(f"Jev errors ({len(errors)}): fail-closed → rejected")

    return PrefilterResult(
        approved=approved,
        tier=tier,
        confidence=composite,
        reasons=reasons,
        details=nouls,
        errors=errors,
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
        "confidence": "medium",
    }
    context = {
        "regime": "bull_normal",
        "vix": 18.5,
        "spy_vs_sma200": "above",
    }
    result = prefilter_signal(signal, context)
    tier_icon = {"approved": "✅", "marginal": "🟡", "rejected": "❌"}
    print(f"{tier_icon[result.tier]} TIER={result.tier} confidence={result.confidence:.0%}")
    for r in result.reasons:
        print(f"  {r}")
    for e in result.errors:
        print(f"  ERROR: {e}")
    print(f"  Details: {result.details}")