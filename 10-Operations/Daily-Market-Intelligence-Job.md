---
type: automation-doc
id: CRON-001
job_id: 79c465c541f2
created: 2026-07-17
updated: 2026-07-17
owner: orchestrator
model_tier: T3
model: google/gemini-2.0-flash-001
tags: [automation, cron, market-intelligence, model-routing, T3]
---

# CRON-001: Daily Market Intelligence Briefing

## Purpose
Produces a structured daily market briefing covering US equities, crypto, macro catalysts,
sector momentum, and risk flags. Runs automatically every weekday morning before US market open.

## Schedule
- **Cron:** `0 13 * * 1-5` (Monday–Friday at 9:00 AM ET / 13:00 UTC)
- **Delivery:** Discord `#talk-to-bot` (origin thread)
- **Vault output:** `05-Research/Market-Intelligence/YYYY-MM-DD-Daily-Briefing.md`

## Model Routing Decision
**Model:** `google/gemini-2.0-flash-001` — **Tier 3**

**Why T3 for this job:**
- Daily structured synthesis from web search is a well-defined, repeatable task
- Output follows a fixed schema (5 sections + Discord summary)
- No novel reasoning, no trade recommendations, no risk decisions
- High frequency (daily) + structured output = ideal T3 use case
- Cost savings vs Sonnet: ~$0.30/1M vs $15/1M output tokens (~50x cheaper)

**Why NOT T4:**
- Briefing feeds human awareness and may surface ideas requiring T2 follow-up
- Web search synthesis requires coherent multi-source reasoning, not just classification
- Sector momentum identification needs more than keyword matching

**Why NOT T2:**
- This is informational aggregation, not strategy development or risk analysis
- No trading decisions are made from this output directly
- Rules AI-002 and AI-003 (RISK_RULES.md) permit T3 for data gathering steps

## Escalation Rule
Per **RISK_RULES.md Rule AI-002**: Any swing/position trade idea surfaced by this briefing
MUST be escalated to T2 (claude-sonnet-4.6) for proper thesis development before acting.
This job is the top of the research funnel — not the decision layer.

## Sections Covered
1. US Equity Market Overview (SPY/QQQ/IWM, VIX, market sentiment)
2. Macro & Catalyst Watch (Fed, economic data, earnings)
3. Crypto Snapshot (BTC/ETH prices, sentiment)
4. Swing Trading Opportunities (sector scans, notable setups — informational only)
5. Risk Flags (today's key watch-outs)

## Output Files
- **Discord:** Condensed 15-line summary with prices and key flags
- **Vault:** Full markdown briefing with all sources and detail

## Hermes Job Details
| Field | Value |
|---|---|
| Job ID | `79c465c541f2` |
| Model | `google/gemini-2.0-flash-001` |
| Provider | `openrouter` |
| Toolsets | `web`, `file` |
| Next Run | 2026-07-20 13:00 UTC |
| Frequency | Weekdays only (Mon–Fri) |

## Maintenance Notes
- If market structure changes significantly (new instruments, regime shift), update the prompt
- If output quality degrades, escalate to T2 and log the issue in INCIDENT_LOG.md
- Review briefing quality monthly as part of ForgeLoop quality cycle
