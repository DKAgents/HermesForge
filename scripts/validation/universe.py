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

    # --- Expansion batch (2026-07-23): broaden universe for more signal
    # opportunities per Phase 1A option-5 decision (do not touch strategy
    # thresholds; widen the pool of candidates instead). Static list of
    # additional well-known, highly liquid S&P 500 constituents across
    # sectors that were thin above. Same survivorship-bias caveat applies.

    # More mega/large-cap tech, communications, internet
    "NFLX", "CSCO", "IBM", "UBER", "ABNB", "SHOP", "PYPL", "XYZ", "SPOT", "BKNG",
    "CMCSA", "TMUS", "VZ", "T", "DIS", "WBD", "EA", "TTWO", "PLTR", "SNPS",
    # More financials + insurance + payments
    "V", "MA", "C", "COF", "TFC", "STT", "MET", "PRU", "AIG",
    "TRV", "ALL", "PGR", "CB", "ICE", "CME", "SPGI", "MCO", "AON", "MRSH",
    # More healthcare + biotech + medtech
    "PFE", "CVS", "CI", "HUM", "ELV", "MDT", "SYK", "BSX", "ISRG", "VRTX",
    "REGN", "ZTS", "DHR", "BDX", "IDXX", "IQV", "MRNA", "BIIB",
    # More consumer discretionary + staples
    "LOW", "TJX", "ROST", "YUM", "CMG", "DPZ", "MAR", "HLT", "LULU", "DECK",
    "PEP", "MDLZ", "CL", "KMB", "GIS", "STZ", "MNST", "KDP", "HSY", "SYY",
    # More industrials + materials + transport
    "UNP", "CSX", "NSC", "WM", "EMR", "ETN", "PH", "ITW", "ROK", "CMI",
    "LIN", "APD", "SHW", "ECL", "NUE", "FCX", "NEM", "DOW", "DD", "PPG",
    # More energy + utilities
    "KMI", "WMB", "OKE", "BKR", "DVN", "FANG", "NEE", "DUK", "SO", "D",
    # More semis + hardware + industrial tech
    "ASML", "TSM", "ARM", "SMCI", "HPE", "DELL", "NXPI", "MCHP", "STX", "WDC",
    # Additional broad/sector ETFs (regime + breadth context)
    "DIA", "VTI", "XLY", "XLP", "XLU", "XLC", "XLB", "XBI", "SMH", "ARKK",
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
