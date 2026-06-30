---
type: risk-guide
created: 2026-06-30
tags: [risk, position-sizing]
---

# Position Sizing Guide

## The Formula
Position Size = (Account Capital × Risk Per Trade %) ÷ (Entry Price - Stop Loss Price)

For options specifically:
Contracts = (Account Capital × 0.01) ÷ (Option Premium × 100)

## Examples
Example 1: $10,000 account, 1% risk = $100 max loss per trade
- If buying a $2.00 option (cost = $200 per contract): max 0.5 contracts → round down to 0 (too small) or reduce risk
- If buying a $0.50 option (cost = $50 per contract): max 2 contracts
- If buying a $1.00 option (cost = $100 per contract): max 1 contract

Example 2: $50,000 account, 1% risk = $500 max loss per trade  
- $2.00 option → max 2 contracts ($400 at risk — within limit)
- $1.00 option → max 5 contracts ($500 at risk — at limit)

## Hard Limits Table
| Account Size | Max Risk/Trade (1%) | Max Total Risk (5%) |
|---|---|---|
| $10,000 | $100 | $500 |
| $25,000 | $250 | $1,250 |
| $50,000 | $500 | $2,500 |
| $100,000 | $1,000 | $5,000 |

## Implementation Note
The position size calculator (US-032) will enforce these limits programmatically. Until it is built, manual calculation is required before every entry.
