#!/usr/bin/env python3
"""
asset_eligibility.py — Per-asset strategy eligibility authority.
No strategy works on all assets. This module enforces that at capture time.

Every strategy declares its eligible tickers. Signals on non-eligible
tickers are suppressed before they reach the publishing pipeline.
"""

from typing import Dict, List, Set

# ── Eligibility Registry ────────────────────────────────────────────────────
# Updated 2026-09-20 — based on G3 net-R per-asset analysis.

ELIGIBLE: Dict[str, Set[str]] = {
    # STR-Q liquidity sweeps — STOCKS: 8 tickers proven net-positive
    "STR-Q-liquidity-sweep": {
        "NVDA", "AMZN", "TSLA", "MSFT",
        "AAPL", "SPY", "META", "GOOGL",
    },
    
    # STR-QW wider stops — CRYPTO: only AVAX and LINK survive
    "STR-QW-liquidity-sweep-wide": {
        "AVAX", "LINK",
    },
    
    # STR-B MACD divergence — universal on stocks, some crypto
    "STR-B-macd-histogram-divergence": {
        # Stocks (proven G3 PASS with 95-98% retention)
        "SPY", "QQQ", "IWM", "DIA",
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
        # Crypto (proven on select coins)
        "BTC", "ETH", "SOL",
    },
    
    # STR-A pullback — stocks only for now
    "STR-A-ma-pullback-fibonacci": {
        "SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA",
    },
}

# Strategies NOT in ELIGIBLE default to NO assets (must be added explicitly)
NO_DEFAULT: Set[str] = set()


def is_eligible(strategy_id: str, ticker: str) -> bool:
    """Check if a ticker is eligible for a given strategy."""
    eligible_set = ELIGIBLE.get(strategy_id)
    if eligible_set is None:
        return False
    return ticker.upper() in eligible_set


def get_eligible(strategy_id: str) -> Set[str]:
    """Return the set of eligible tickers for a strategy."""
    return ELIGIBLE.get(strategy_id, set())


def add_eligible(strategy_id: str, ticker: str):
    """Add a ticker to a strategy's eligibility list."""
    if strategy_id not in ELIGIBLE:
        ELIGIBLE[strategy_id] = set()
    ELIGIBLE[strategy_id].add(ticker.upper())


def get_all_eligible_tickers() -> Set[str]:
    """All tickers eligible for at least one strategy."""
    all_tickers = set()
    for tickers in ELIGIBLE.values():
        all_tickers.update(tickers)
    return all_tickers


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Asset Eligibility Registry")
    print("=" * 50)
    for sid, tickers in sorted(ELIGIBLE.items()):
        count = len(tickers)
        print(f"\n{sid} ({count} tickers):")
        for t in sorted(tickers)[:10]:
            print(f"  ✅ {t}")
        if count > 10:
            print(f"  ... +{count-10} more")
    
    total = sum(len(t) for t in ELIGIBLE.values())
    print(f"\nTotal: {len(ELIGIBLE)} strategies, {total} strategy×asset pairs")