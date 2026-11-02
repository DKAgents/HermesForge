"""
signal_class.py — Hard signal-class intake gate (US-191).

Turns the soft "negative prior" that previously lived only in the
strategy-gauntlet skill (see skills/research/strategy-gauntlet SKILL.md
"Signal-Class Prior") into CODE-LEVEL enforcement. The prior:

    Retail technical-analysis / chart-pattern / ICT-SMC "liquidity-sweep"
    strategies carry a heavy NEGATIVE prior:
      - sweep/reversal detectors are a coin flip (zero raw predictive content);
      - classic chart-pattern OOS edges (0.08-0.22 R) sit BELOW realistic
        friction (~0.1-0.3 R), so they promote-and-die as a CLASS;
      - the stop-hunt / liquidity-grab mechanism is empirically false.

These classes are fast-failed BEFORE G0 (cost screen). Persistent edges are
STRUCTURAL (funding/basis carry, vol/VRP, cost-aware cross-sectional momentum),
and are explicitly NOT blocked here.

Classification is keyword-driven over the concatenated strategy metadata
(id, name, description, core_idea, edge, tags, primitives), matched on
alphanumeric WORD BOUNDARIES so a bare token like "rsi" cannot false-positive
inside "mean-reversion". Keyword phrases are deliberately SPECIFIC so that
systematic/macro/factor strategies (term-structure, funding carry,
cross-sectional, capitulation, supply-crunch, skew) are not mis-tagged.

Generic single-word tokens (e.g. "imbalance", "flag", "wedge", "hammer",
"engulf") are NOT listed on their own: they over-match mundane prose
("order-flow imbalance", "set a data-quality flag", "hammer out") and
false-block structural/systematic edges. Each is replaced by an unambiguous
phrase ("bull flag", "rising wedge", "hammer candle", "bullish engulfing",
"outside day reversal", ...) so that only a genuine retail-TA / chart-pattern /
ICT-SMC NAME matches.

Usage:
    from signal_class import classify, is_blocked, intake_verdict, BLOCKED_CLASSES
"""

from __future__ import annotations

import re
from typing import Dict, Iterable

# ── The blocked signal classes ──────────────────────────────────────────────
RICT_SMC = "ict-smc"
CHART_PATTERN = "chart-pattern"
RETAIL_TA = "retail-ta"
SYSTEMATIC = "systematic"
UNCLASSIFIED = "unclassified"

BLOCKED_CLASSES = frozenset({RICT_SMC, CHART_PATTERN, RETAIL_TA})

# ── Keyword classifiers (matched on word boundaries) ────────────────────────
_ICT_SMC_KEYWORDS = (
    "liquidity sweep", "liquidity grab", "liquidity-sweep", "sweep reversal",
    "stop hunt", "stop-hunt", "order block", "orderblock", "fair value gap",
    "fvg", "smart money", "breaker block", "market structure shift",
    "judas swing", "induced liquidity", "equal highs",
    "equal lows", "sweep of",
)

_CHART_PATTERN_KEYWORDS = (
    "head and shoulder", "head & shoulder", "double top", "double bottom",
    "triple top", "triple bottom", "triangle breakout",
    "rising wedge", "falling wedge", "wedge pattern",
    "bull flag", "bear flag", "flag pattern",
    "pennant", "candlestick", "candle pattern",
    "hammer candle", "hammer candlestick", "hammer pattern", "inverted hammer",
    "bullish engulfing", "bearish engulfing", "engulfing pattern",
    "outside day reversal", "outside day key reversal", "outside bar reversal",
    "elliott", "morning star", "doji", "chart pattern", "neckline",
    "key reversal",
)

_RETAIL_TA_KEYWORDS = (
    "ma pullback", "moving average pullback", "fibonacci", "fib retracement",
    "rsi", "macd", "bollinger", "cci", "stochastic", "williams",
    "obv", "keltner", "donchian", "4-week rule", "adx", "dmi",
    "parabolic sar", "alligator", "ema20", "ema cross", "sma cross",
    "ema50", "golden cross", "death cross", "role reversal",
    "first pullback", "gap continuation", "oscillator", "selling climax",
    "breakout volume",
)

_SYSTEMATIC_KEYWORDS = (
    "cross-sectional", "funding", "basis", "carry", "vol-of-vol", "vrp",
    "variance risk premium", "term-structure", "term structure", "contango",
    "factor", "regime", "momentum", "supply crunch", "skew", "capitulation",
    "debasement", "intermarket", "breadth", "seasonal", "rotation", "sector",
    "treasury", "oil shock", "market maker", "market-maker",
)


def _normalize(s: str) -> str:
    # lowercase + collapse every non-alnum run to a single space, so
    # "mean_reversion", "mean-reversion" and "breakout-volume-trend" all become
    # space-separated word sequences for word-boundary matching.
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def classify(strategy_id: str = "", name: str = "", description: str = "",
             core_idea: str = "", edge: str = "", tags: Iterable[str] = (),
             primitives: Iterable[str] = (), **_) -> str:
    """Return the signal class for a strategy, from its metadata.

    Any metadata keys may be supplied; only the recognized text fields are
    inspected. Returns one of: ict-smc / chart-pattern / retail-ta /
    systematic / unclassified.
    """
    parts = [strategy_id, name, description, core_idea, edge]
    if tags:
        parts.append(" ".join(str(t) for t in tags))
    if primitives:
        parts.append(" ".join(str(p) for p in primitives))
    blob = _normalize(" ".join(p for p in parts if p))

    def _hit(keywords: Iterable[str]) -> bool:
        for k in keywords:
            kk = _normalize(k)
            if not kk:
                continue
            if re.search(r"(?<![a-z0-9])" + re.escape(kk) + r"(?![a-z0-9])", blob):
                return True
        return False

    if _hit(_ICT_SMC_KEYWORDS):
        return RICT_SMC
    if _hit(_CHART_PATTERN_KEYWORDS):
        return CHART_PATTERN
    if _hit(_RETAIL_TA_KEYWORDS):
        return RETAIL_TA
    if _hit(_SYSTEMATIC_KEYWORDS):
        return SYSTEMATIC
    return UNCLASSIFIED


def is_blocked(**strategy_meta) -> bool:
    """True if the strategy's signal class is in BLOCKED_CLASSES."""
    return classify(**strategy_meta) in BLOCKED_CLASSES


def intake_verdict(**strategy_meta) -> Dict[str, object]:
    """Hard intake verdict returned before G0.

    Returns {'admitted': bool, 'signal_class': str, 'reason': str}.
    Fast-fails (admitted=False) for any blocked signal class.
    """
    signal_class = classify(**strategy_meta)
    if signal_class in BLOCKED_CLASSES:
        return {
            "admitted": False,
            "signal_class": signal_class,
            "reason": (
                f"blocked signal class '{signal_class}' — retail-TA / "
                "chart-pattern / ICT-SMC carries a negative prior and is "
                "fast-failed before G0 (US-191)"
            ),
        }
    return {
        "admitted": True,
        "signal_class": signal_class,
        "reason": "",
    }


# ── Self-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    probes = [
        ("STR-Q-liquidity-sweep", "Liquidity Sweep Reversal",
         "Institutional stop-loss sweep detection; enters after price sweeps PDH/PDL and reverses"),
        ("STR-T-head-shoulders", "Head & Shoulders Reversal",
         "Classic 3-peak reversal, neckline break entry"),
        ("STR-B-macd-histogram-divergence", "MACD Histogram Divergence",
         "Price makes new high but MACD makes lower high"),
        ("STR-A-ma-pullback-fibonacci", "MA Pullback + Fibonacci",
         "Pullback to MA50, entry at 38-62% retracement"),
        ("STR-20260816-vix-vrp-contango", "VIX Term-Structure Contango Breakout",
         "Long vol risk premium via contango term structure"),
        ("STR-20260908-skew-predicted", "Predicted Skewness",
         "Option skew factor on equities"),
        ("STR-20260801-crosssectional", "Cross-sectional Factor",
         "Multi-factor cross-sectional ranking"),
        ("STR-20260917-CAP-BOTTOM", "Crypto Post-Capitulation Bounce",
         "mean_reversion dip-buying after capitulation"),
    ]
    for (sid, name, desc) in probes:
        c = classify(strategy_id=sid, name=name, description=desc)
        v = intake_verdict(strategy_id=sid, name=name, description=desc)
        mark = "BLOCK" if not v["admitted"] else "admit"
        print(f"{mark:5s} {sid:40s} -> {c}")