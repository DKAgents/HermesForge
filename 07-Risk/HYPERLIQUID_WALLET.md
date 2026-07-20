---
type: risk-note
epic: EPIC-011
story: US-072
created: 2026-07-20
tags: [hyperliquid, wallet, testnet, security]
---

# Hyperliquid Testnet Agent Wallet

## Purpose
Dedicated Ethereum wallet (EIP-712 signing) for EPIC-011 Hyperliquid **testnet** paper trading.
Generated fresh, never derived from or sharing keys with the user's main wallet.
**Testnet only — never used against mainnet, never holds real funds.**

## Address
`0xC81182a884D6fC6103F052B243CE9b259d3BE7A8`

## Storage
Private key stored in `~/.hermes/.env` as `HYPERLIQUID_TESTNET_AGENT_PRIVATE_KEY`
(mode 600, not committed to git). Address also stored as
`HYPERLIQUID_TESTNET_AGENT_ADDRESS` for scripts that only need the public address.

## Connection Verification (2026-07-20)
Verified via `scripts/hyperliquid/connection_test.py` against
`https://api.hyperliquid-testnet.xyz` using `hyperliquid-python-sdk`:
- Wallet authenticates and returns a valid `user_state` response
- Account value: `0.0` (unfunded — see blocker below)

## ⚠️ Funding Blocker (open, as of 2026-07-20)
The Hyperliquid testnet faucet (`https://app.hyperliquid-testnet.xyz/drip`) requires:
1. A connected browser wallet (no headless/API path for claiming)
2. **Mainnet deposit history on the connecting wallet** ("You can claim 1000 mock
   USDC once if you have deposited on mainnet")

Our agent wallet is intentionally fresh and testnet-only, so it has no mainnet
history and cannot self-serve the faucet. This blocks completing US-072's
"testnet USDC obtained via faucet" acceptance criterion, and by extension blocks
live order-placement testing for US-073/074/075.

Options raised with user (awaiting decision):
- Fund via a different wallet that does have mainnet deposit history, manually
  transferring/claiming to this agent address
- Check whether Hyperliquid offers an alternative (e.g. Discord-based) faucet path
- Proceed with code-complete-but-untested order placement logic, defer live
  verification until funding is resolved

## Status
- [x] Wallet generated (EIP-712, fresh, isolated from main wallet)
- [x] Private key stored securely, never committed
- [x] Connection test passes against testnet API
- [ ] Testnet USDC funding — **blocked**, awaiting user decision
- [ ] Full US-072 sign-off pending funding resolution
