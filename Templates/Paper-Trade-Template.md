---
trade_id: {{trade_id}}
strategy: {{strategy}}
ticker: {{ticker}}
date: {{date}}
tags: [paper-trade, {{strategy}}]
---

# Paper Trade — {{ticker}} {{date}}

## Setup
- **Strategy:** {{strategy}}
- **Direction:** {{direction}}
- **Entry:** ${{entry_price}} | **Stop:** ${{stop_price}} | **Target:** ${{target_price}}
- **Confirmation level:** {{confirmation_level}}
- **Weekly gates passing:** {{weekly_gates}}/3
- **Trigger:** {{trigger_type}}

## Execution
- **Exit:** ${{exit_price}} ({{exit_reason}}, {{bars_held}} bars)
- **R-multiple:** {{r_multiple}}

## Pre-Trade Checklist
- [ ] Maturity gate passed (MACD above/below zero ≥ 15 bars)
- [ ] Stage 1 confirmed (histogram narrowing 2+ bars)
- [ ] Stage 2 confirmed (MACD line diverging)
- [ ] Entry trigger fired
- [ ] Stop calculated (0.5 × ATR above/below swing extreme)
- [ ] R:R ≥ 3:1 confirmed
- [ ] Regime-aware direction check passed
- [ ] Earnings date >5 days away
- [ ] Position sized correctly

## What I Observed
(Fill in after the trade)

## What I Learned
(Fill in after the trade)

## Would I Take This Again?
- [ ] Yes — exactly as executed
- [ ] Yes — with these changes:
- [ ] No — because:
