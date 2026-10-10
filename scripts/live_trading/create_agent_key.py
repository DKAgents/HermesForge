#!/usr/bin/env python3
"""
create_agent_key.py — Generate a Hyperliquid agent keypair for delegated trading.

Run this ON YOUR LOCAL MACHINE (not the server), then:
1. Save the agent private key to the server as HYPERLIQUID_AGENT_KEY
2. Approve the agent on Hyperliquid from your main wallet
3. The agent can trade but CANNOT withdraw — funds stay safe

Usage:
    python3 create_agent_key.py              # generate new keypair
    python3 create_agent_key.py --approve    # print the approve_agent command
"""

import sys
import eth_account
from eth_account import Account

def main():
    # Generate a fresh Ethereum keypair
    acct = Account.create()
    address = acct.address
    private_key = acct.key.hex()

    print("=" * 60)
    print("NEW HYPERLIQUID AGENT KEYPAIR")
    print("=" * 60)
    print()
    print(f"Agent Address:    {address}")
    print(f"Agent Private Key: {private_key}")
    print()
    print("── SETUP STEPS ──")
    print()
    print("1. Save the private key on the HERMES SERVER:")
    print(f"   echo 'HYPERLIQUID_AGENT_KEY={private_key}' >> ~/.hermes/.env")
    print()
    print("2. Set your main account address on the server:")
    print("   echo 'HYPERLIQUID_ACCOUNT=<your-main-hyperliquid-address>' >> ~/.hermes/.env")
    print()
    print("3. Approve this agent to trade on your behalf.")
    print("   Run this ON YOUR LOCAL MACHINE with your main wallet private key:")
    print()
    print(f"   python3 create_agent_key.py --approve {private_key}")
    print()
    print("── SECURITY ──")
    print(f"  • This agent can PLACE/CANCEL ORDERS on your account")
    print(f"  • This agent CANNOT WITHDRAW funds")
    print(f"  • If the server is compromised, your funds stay safe")
    print(f"  • Revoke anytime: Hyperliquid UI → Revoke Agent")
    print()

    if "--approve" in sys.argv:
        # Find the agent key in args
        agent_key = None
        for i, arg in enumerate(sys.argv):
            if arg == "--approve" and i + 1 < len(sys.argv):
                agent_key = sys.argv[i + 1]
                break

        if not agent_key:
            print("ERROR: provide agent private key as argument")
            print("Usage: python3 create_agent_key.py --approve <agent_private_key>")
            return

        print("── APPROVAL CODE ──")
        print("Run this Python code on a machine with your MAIN wallet private key:")
        print()
        print("```python")
        print("from hyperliquid.exchange import Exchange")
        print("from hyperliquid.utils import constants")
        print("from eth_account import Account")
        print()
        print("# Your MAIN wallet private key (keep this SAFE)")
        print("MAIN_KEY = '<your-main-wallet-private-key>'")
        print()
        print(f"AGENT_ADDRESS = '{address}'")
        print()
        print("account = Account.from_key(MAIN_KEY)")
        print("exchange = Exchange(account, base_url=constants.MAINNET_API_URL)")
        print()
        print("# Approve the agent to trade on your behalf")
        print("result = exchange.approve_agent(AGENT_ADDRESS)")
        print("print('Agent approved:', result)")
        print("```")
        print()
        print("After running this, the agent can trade on Hyperliquid.")

if __name__ == "__main__":
    main()