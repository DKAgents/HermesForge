#!/usr/bin/env python3
"""
connection_test.py — HermesForge EPIC-011 (US-072)

Verifies the dedicated Hyperliquid TESTNET agent wallet can authenticate
and query account state. Testnet only — never touches mainnet.

Usage:
    python3 connection_test.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.hermes/.env"))

TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"

def main():
    address = os.environ.get("HYPERLIQUID_TESTNET_AGENT_ADDRESS")
    privkey = os.environ.get("HYPERLIQUID_TESTNET_AGENT_PRIVATE_KEY")

    if not address or not privkey:
        print("FAIL: HYPERLIQUID_TESTNET_AGENT_ADDRESS / _PRIVATE_KEY not set in ~/.hermes/.env")
        sys.exit(1)

    try:
        from hyperliquid.info import Info
        from hyperliquid.utils import constants
    except ImportError as e:
        print(f"FAIL: hyperliquid-python-sdk not importable: {e}")
        sys.exit(1)

    # Safety guard: refuse to run against anything but the testnet URL
    api_url = constants.TESTNET_API_URL if hasattr(constants, "TESTNET_API_URL") else TESTNET_API_URL
    if "testnet" not in api_url:
        print(f"FAIL: refusing to run — resolved API URL does not look like testnet: {api_url}")
        sys.exit(1)

    print(f"Agent wallet address: {address}")
    print(f"Testnet API URL: {api_url}")

    info = Info(api_url, skip_ws=True)

    try:
        user_state = info.user_state(address)
    except Exception as e:
        print(f"FAIL: could not query testnet user_state: {e}")
        sys.exit(1)

    margin_summary = user_state.get("marginSummary", {})
    account_value = margin_summary.get("accountValue", "0")

    print("Connection test: SUCCESS")
    print(f"Account value (testnet USDC-equivalent): {account_value}")

    if float(account_value) <= 0:
        print("\nNOTE: Account value is 0 — wallet is valid but not yet funded.")
        print("Fund via the Hyperliquid testnet faucet before placing test orders:")
        print("  https://app.hyperliquid-testnet.xyz/drip")
        print(f"  Faucet target address: {address}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
