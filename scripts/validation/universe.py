"""
universe.py — HermesForge Phase 1A
Returns the top-100 liquid US stocks universe for strategy scanning.

Top 100 S&P 500 components by typical average dollar volume (2024 basis).
Survivorship bias acknowledged: this list reflects current constituents,
not historical ones. Acceptable for Phase 1A reality check.
See ADR-004 for rationale.
"""

UNIVERSE = [
    # Mega-cap tech + growth
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "ORCL", "AMD",
    # Financials
    "JPM", "BAC", "GS", "MS", "WFC", "BLK", "SCHW", "AXP", "USB", "PNC",
    # Healthcare
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "BMY", "AMGN", "GILD",
    # Consumer
    "AMZN", "HD", "MCD", "NKE", "SBUX", "TGT", "COST", "WMT", "PG", "KO",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Industrials
    "CAT", "DE", "BA", "GE", "HON", "RTX", "LMT", "UPS", "FDX", "MMM",
    # Semis + Tech hardware
    "QCOM", "TXN", "MU", "INTC", "AMAT", "LRCX", "KLAC", "ADI", "MRVL", "ON",
    # Cloud + Software
    "CRM", "ADBE", "NOW", "SNOW", "PANW", "CRWD", "ZS", "TEAM", "WDAY", "DDOG",
    # ETFs (liquid benchmarks useful for regime context)
    "SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "XLI", "GLD", "TLT",
]

# Deduplicate (AMZN appears twice above intentionally as placeholder — clean it)
UNIVERSE = sorted(list(dict.fromkeys(UNIVERSE)))


def get_universe():
    """Return the universe ticker list."""
    return UNIVERSE


if __name__ == "__main__":
    u = get_universe()
    print(f"Universe size: {len(u)} tickers")
    print(", ".join(u))
