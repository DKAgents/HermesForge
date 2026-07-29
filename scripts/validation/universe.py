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

    # --- Expansion batch (2026-07-27): full S&P 500 coverage
    # Added all remaining S&P 500 constituents not already in the universe.
    # Survivorship bias caveat still applies (ADR-004).
    "A", "ACGL", "ACN", "ADM", "ADP", "ADSK", "AEE", "AEP", "AES", "AFL",
    "AIZ", "AJG", "AKAM", "ALB", "ALGN", "ALLE", "AMCR", "AME", "AMP", "AMT",
    "ANET", "AOS", "APA", "APH", "APO", "APP", "APTV", "ARE", "ARES", "ATO",
    "AVB", "AVY", "AWK", "AXON", "AZO", "BALL", "BAX", "BBY", "BEN", "BF-B",
    "BG", "BLDR", "BNY", "BR", "BRK-B", "BRO", "BX", "BXP", "CAH", "CARR",
    "CASY", "CBOE", "CBRE", "CCI", "CCL", "CDNS", "CDW", "CEG", "CF", "CFG",
    "CHD", "CHRW", "CHTR", "CIEN", "CINF", "CLX", "CMS", "CNC", "CNP", "COHR",
    "COIN", "COO", "COR", "CPAY", "CPRT", "CPT", "CRH", "CRL", "CSGP", "CTAS",
    "CTSH", "CTVA", "CVNA", "DAL", "DASH", "DG", "DGX", "DHI", "DLR", "DLTR",
    "DOC", "DOV", "DRI", "DTE", "DVA", "DXCM", "EBAY", "ECHO", "ED", "EFX",
    "EG", "EIX", "EL", "EME", "EQIX", "EQR", "EQT", "ERIE", "ES", "ESS",
    "ETR", "EVRG", "EW", "EXC", "EXE", "EXPD", "EXPE", "EXR", "F", "FAST",
    "FDS", "FDXF", "FE", "FFIV", "FICO", "FIS", "FISV", "FITB", "FIX", "FLEX",
    "FOX", "FOXA", "FRT", "FSLR", "FTNT", "FTV", "GD", "GDDY", "GEHC", "GEN",
    "GEV", "GL", "GLW", "GM", "GNRC", "GOOG", "GPC", "GPN", "GRMN", "GWW",
    "HAS", "HBAN", "HCA", "HIG", "HII", "HONA", "HOOD", "HPQ", "HRL", "HSIC",
    "HST", "HUBB", "HWM", "IBKR", "IEX", "IFF", "INCY", "INTU", "INVH", "IP",
    "IR", "IRM", "IT", "IVZ", "J", "JBHT", "JBL", "JCI", "JKHY", "KEY",
    "KEYS", "KHC", "KIM", "KKR", "KR", "KVUE", "L", "LDOS", "LEN", "LH",
    "LHX", "LII", "LITE", "LNT", "LUV", "LVS", "LYB", "LYV", "MAA", "MAS",
    "MCK", "MGM", "MKC", "MLM", "MO", "MOS", "MPWR", "MSCI", "MSI", "MTB",
    "MTD", "NCLH", "NDAQ", "NDSN", "NI", "NOC", "NRG", "NTAP", "NTRS", "NVR",
    "NWS", "NWSA", "O", "ODFL", "OMC", "ORLY", "OTIS", "PAYX", "PCAR", "PCG",
    "PEG", "PFG", "PHM", "PKG", "PLD", "PM", "PNR", "PNW", "PODD", "PPL",
    "PSA", "PSKY", "PTC", "PWR", "Q", "RCL", "REG", "RF", "RJF", "RL",
    "RMD", "ROL", "ROP", "RSG", "RVTY", "SBAC", "SJM", "SNA", "SNDK", "SOLV",
    "SPG", "SRE", "STE", "STLD", "SW", "SWK", "SWKS", "SYF", "TAP", "TDG",
    "TDY", "TECH", "TEL", "TER", "TKO", "TPL", "TPR", "TRGP", "TRMB", "TROW",
    "TSCO", "TSN", "TT", "TTD", "TXT", "TYL", "UAL", "UDR", "UHS", "ULTA",
    "URI", "VEEV", "VICI", "VLTO", "VMC", "VRSK", "VRSN", "VRT", "VST", "VTR",
    "VTRS", "WAB", "WAT", "WEC", "WELL", "WRB", "WSM", "WST", "WTW", "WY",
    "WYNN", "XEL", "XYL", "ZBH", "ZBRA",
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
