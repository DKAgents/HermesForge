"""
universe.py — Single source of truth for HermesForge asset universes.

All scripts that need the crypto trading universe should import from here.
This replaces the 9+ hardcoded copies that had drifted out of sync.
Update this file once and every script picks up the change.

Usage:
    # If scripts/ is on sys.path:
    from config.universe import CRYPTO_UNIVERSE
    # or:
    from config.universe import COINS_TO_TRACK
    # or the function form:
    from config.universe import get_crypto_universe
"""

# ---------------------------------------------------------------------------
# Crypto Universe
# ---------------------------------------------------------------------------
# All Hyperliquid perpetual markets in our active trading universe.
# Expanded 2026-07-27 to full high-liquidity coverage (max leverage >= 10).
# Removed 7 delisted tickers 2026-08-02: STRAX, RNDR, MATIC, LOOM, FTM, MKR, TON.
#
# To add/remove a coin: edit this list, then restart any running services
# (hermesforge-listener, cron jobs) that cache the universe at startup.
CRYPTO_UNIVERSE = [
    "BTC", "ETH", "SOL",
    "AVAX", "LINK", "DOGE", "ARB", "OP", "SUI",
    "AAVE", "ADA", "APT", "BCH", "BNB", "CRV", "DOT", "ENA",
    "FARTCOIN", "HYPE", "JUP", "LTC",
    "NEAR", "ONDO", "PAXG", "PUMP", "TRUMP", "TRX", "UNI", "WLD",
    "XPL", "XRP", "ZEC",
    "kBONK", "kPEPE", "kSHIB",
]

# Convenience alias (some scripts use this name)
COINS_TO_TRACK = CRYPTO_UNIVERSE


def get_crypto_universe() -> list:
    """Return the current crypto universe as a list of symbol strings."""
    return list(CRYPTO_UNIVERSE)
