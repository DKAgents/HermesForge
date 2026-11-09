---
hypothesis_id: HYP-38
source: human
venue: hyperliquid
instruments: [BTC-PERP, ETH-PERP, SOL-PERP]
horizon: 1d (signal at day-t close -> next-day return)
entry_logic: "Follow the net positioning of the SKILLED wallet cohort and fade the
  UNSKILLED cohort (crypto analog of the futures Commitment of Traders
  commercial-vs-noncommercial spread). Skilled = consistent positive realized PnL,
  high win rate, maker discipline; unskilled = the over-paying flow they fade."
exit_logic: "Daily rebalance: establish sign(cohort_net) at day-t close, realize the
  next-day close-to-close return, reopen."
expected_gross_edge_bps: 5
cost_hurdle_bps: 3
data_dependencies:
  - hl.wallet_daily (Ironflow /v1/query; per-wallet daily closed PnL, maker/taker,
    net_size_signed) — free key, 2026-10-10..2026-11-09
  - bars_1d (local sqlite) for next-day close-to-close forward returns (BTC/ETH/SOL)
counterparty: "Unskilled flow that over-pays and gets picked off — taker-heavy
  wallets with persistent negative realized PnL and sub-coin-flip win rate; the
  skilled cohort is the maker-disciplined counterparty capturing that flow."
execution_mode: maker
falsification_criteria: "Follow-skilled and fade-unskilled both report |IC| below
  the M-5 MDE floor at this sample depth (i.e. not detected above MDE), and no
  cohort net P&L is positive at maker cost."
primitives: [wallet_skill_score, cohort_net_position, maker_ratio, realized_pnl]
description: "Wallet-cohort positioning (on-chain Commitment of Traders). Label
  wallets by realized PnL / win rate / maker discipline / consistency, then test
  whether skilled net position predicts next-period returns (follow) and unskilled
  (fade). PRELIMINARY: this run proves the LABELING MACHINERY + gives a first-look
  directional sniff on the ~30-day free-key window."
tier: T2
timeframe: 1d
note: "Renumbered from the directive label 'HYP-29'. Collision chain:
  'HYP-29' is already assigned to Funding-carry G3 fill-realism + capacity gate
  (hypothesis file HYP-29-funding-carry-g3-capacity.md, backtest script, report,
  and trials.jsonl hypothesis_id 'HYP-29'). The ingest_hl_fills.py docstring and
  US-07 report carry the same stale 'wallet-cohort (HYP-29)' label. Assigned next
  free ID HYP-38 (HYP-37 is the current max)."
holding_period_note: "The 5-dimension skill rubric intends holding period as a
  feature, but it is NOT computable from hl.wallet_daily (no per-wallet
  open/close timestamps) and the raw-fills store holds only ~1 day. Holding period
  is therefore DATA-GATED: pre-registered as a required dimension, explicitly
  deferred to the Explorer-tier raw-fills (90-day) run, and does NOT enter the
  first-look label. Documented, not silently dropped."
---

# HYP-38 — Wallet-cohort positioning (on-chain Commitment of Traders)

## Motivation

Crypto's futures markets have no aggregated weekly COT report, but the on-chain
perpetuals venue (Hyperliquid) exposes the per-address closed PnL and maker/taker
role of every fill. That lets us reconstruct the COT split directly: a persistent
**skilled** cohort (consistent positive realized PnL, high win rate, maker
discipline) and an **unskilled** cohort (taker-heavy flow that over-pays and gets
picked off). The hypothesis is that the skilled cohort's net positioning is a
persistent, exploitable signal — follow their net position, fade the unskilled.

## Pre-registered operationalization (fixed, no tuning)

RUBRIC (frozen; thresholds are the principled neutral points 0 / 0.5, NOT fitted):

- **Labeling window** (skill assignment, ex-ante): 2026-10-10 → 2026-10-24.
- **Min labelable**: a wallet must have >= 10 fills, >= 3 distinct active days,
  and >= 5 closing fills in the labeling window (across BTC/ETH/SOL). Below this,
  the wallet is UNLABELED (excluded from both cohorts).
- Wallet-level features (summed across the 3 markets over the labeling window):
  - realized_pnl_usd (sum)
  - win_rate = winning_fills / closing_fills
  - maker_ratio = maker_fills / (maker_fills + taker_fills)
  - consistency = Sharpe of the wallet's daily realized_pnl_usd series
  - holding period — DATA-GATED (see frontmatter note).
- **SKILLED**  := realized_pnl_usd > 0 AND win_rate >= 0.5 AND maker_ratio >= 0.5.
- **UNSKILLED** := realized_pnl_usd < 0 AND win_rate < 0.5 AND maker_ratio < 0.5.
- Wallets not in either set (mixed) are neutral and excluded.

COHORT SIGNAL (frozen):

- Cohort net position for coin c on day t = sum over cohort wallets of
  `net_size_signed` (signed net flow; positive = net long, negative = net short).
  Semantics assumed from the field name + `net_buy_notional` companion; flagged.
- Two signals tested *separately*, then a combined:
  - FOLLOW-SKILLED: position = sign(skilled_net(c,t))
  - FADE-UNSKILLED: position = sign(-unskilled_net(c,t))
  - COMBINED: position = sign(skilled_net(c,t) - unskilled_net(c,t))
- Forward return: day-t close → day-(t+1) close from bars_1d.

LEAKAGE: labels fixed on the 10-10..10-24 labeling window ONLY (before any signal
day); signal uses day-t end-of-day net flow to predict t→t+1 return. No look-ahead.

COST: maker round-trip (1.5 bps × 2 = 3 bps) charged per held day (daily
rebalance, maker fill). No leverage. LIVE off.

## Falsification / promotion

- FALSIFY (this preliminary run) if neither follow-skilled nor fade-unskilled
  clears its M-5 MDE floor and no net P&L at maker cost is positive.
- The 90-day Explorer-tier run is the real test; this run only proves machinery.

## Boundary (stated explicitly)

~30 days is far too short to establish skill persistence or a stable cohort
signal. This run demonstrates the LABELING MACHINERY end-to-end and gives a
directional sniff. What the 90-day Explorer tier adds: (1) 3x sample depth for
label stability, (2) raw-fills holding-period feature, (3) regime coverage
(funding/unwind cycles), (4) enough non-overlapping forward periods for a real
IC with acceptable MDE.