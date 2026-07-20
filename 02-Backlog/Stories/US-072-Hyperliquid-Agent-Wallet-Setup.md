---
id: US-072
epic: EPIC-011
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [hyperliquid, wallet, testnet]
---

# US-072: Hyperliquid Agent Wallet Setup (Testnet)

## Story
As the execution system, I need a dedicated agent wallet (separate from the user's main wallet) authenticated against Hyperliquid testnet, so that testnet trades can be placed without any exposure to real funds or the main wallet's keys.

## Acceptance Criteria
- [ ] New Ethereum wallet generated specifically for this purpose (EIP-712 signing) — never derived from or sharing keys with the user's main wallet
- [ ] Private key stored securely (env var via `~/.hermes/.env`, not committed to git)
- [ ] Testnet USDC obtained via faucet (https://api.hyperliquid-testnet.xyz)
- [ ] Connection test: query account state via `hyperliquid-python-sdk`, confirm testnet balance visible
- [ ] Document the wallet address and setup steps in a new `07-Risk/HYPERLIQUID_WALLET.md` note (address only — never the private key)

## Definition of Done
- Agent wallet created and funded on testnet
- Connection verified against testnet API
- Committed to main (setup doc only, never keys)
