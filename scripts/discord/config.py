"""
config.py — HermesForge EPIC-009 Discord signal distribution config.

Channel IDs are NOT hardcoded here — they are read from environment
variables so the same code works across dev/prod without editing source.

Set these in ~/.hermes/.env (see US-062):
    DISCORD_STOCK_CHANNEL_ID=<channel id for #stock-setups>
    DISCORD_CRYPTO_CHANNEL_ID=<channel id for #crypto-setups>

TODO (blocking live posting, non-blocking for dry-run/dev):
    Actual Discord channel IDs for #stock-setups and #crypto-setups
    have not been provided yet. Until they are set, publish_signal()
    will raise a clear error in non-dry-run mode rather than posting
    to the wrong place.
"""

import os

PUBLISH_CHANNEL_MAP = {
    "stocks": os.environ.get("DISCORD_STOCK_CHANNEL_ID", ""),
    "crypto": os.environ.get("DISCORD_CRYPTO_CHANNEL_ID", ""),
    "daytrade-stocks": os.environ.get("DISCORD_DAYTRADE_STOCK_CHANNEL_ID", ""),
    "daytrade-crypto": os.environ.get("DISCORD_DAYTRADE_CRYPTO_CHANNEL_ID", ""),
}

DEDUP_LOG_PATH = os.path.expanduser("~/HermesForge/scripts/discord/published_signals.csv")
DEFAULT_LOOKBACK_DAYS = 30  # Don't repost same setup for 30 days (trade lifecycle)
RISK_PCT_DEFAULT = 1.0          # % account risk per trade, matches SOUL.md hard rule ceiling
EXAMPLE_ACCOUNT_SIZE = 100_000  # for illustrative share-count sizing in alerts


def get_channel_target(publish_channel: str) -> str:
    """
    Resolve a publish_channel value ('stocks' | 'crypto') to a send_message
    target string. Raises ValueError if unset or unrecognized.
    """
    if publish_channel not in PUBLISH_CHANNEL_MAP:
        raise ValueError(
            f"Unknown publish_channel '{publish_channel}'. "
            f"Expected one of: {list(PUBLISH_CHANNEL_MAP)}"
        )
    channel_id = PUBLISH_CHANNEL_MAP[publish_channel]
    if not channel_id:
        raise ValueError(
            f"No Discord channel ID configured for publish_channel='{publish_channel}'. "
            f"Set DISCORD_{publish_channel.upper()}_CHANNEL_ID in ~/.hermes/.env"
        )
    return f"discord:{channel_id}"
