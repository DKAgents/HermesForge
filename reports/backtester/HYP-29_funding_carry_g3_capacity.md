# HYP-29 — Funding carry: G3 fill-realism + capacity gate

Verdict: PROMOTE-TO-PAPER (maker/queue execution only).

The delta-neutral funding carry HYP-28 proved is REAL and survives honest
fills on BOTH legs at realistic (maker + adverse spot spread) execution, and
yields on non-trivial notional. It does NOT survive pessimistic (taker +
stressed spread) fills — that tier turns it net-negative, so paper-forward
must be maker/queue-only.

## What was tested (pre-registered, fixed — no tuning)

Same gate as HYP-28 (rolling 24h mean APR >= 8% AND >= 75% hours positive),
same sample (2023-06-08 -> 2026-10-31), same universe (BTC/ETH/SOL), unlevered
1x notional. The NEW load-bearing work:

1. G3 fill-realism on BOTH legs — the hedge is the load-bearing leg:
   - optimistic  = mid fills, maker fee only (HYP-28 baseline 6 bps RT)
   - realistic   = maker fee + spot bought at ASK/sold at BID (full RT spread)
                    + perp short at BID/cover at ASK (full RT spread)
   - pessimistic = taker fee (18 bps RT) + a STRESSED spot RT spread (20 bps)
   Cost charged on both legs, entry + exit, every episode.
2. Capacity via a conservative liquidity proxy (no L2 spot book held).
3. Risk check: enumerated the uncompensated risks behind the ~11% floor.

## Results

| leg  | gross APR | net-maker (HYP-28) | realistic net APR | pessimistic net APR |
|------|----------:|-------------------:|------------------:|--------------------:|
| BTC  | 19.97%    | 15.74%             | 12.14%            | -6.89%              |
| ETH  | 20.77%    | 15.33%             | 10.43%            | -14.05%             |
| SOL  | 26.81%    | 21.22%             | 11.81%            | -8.68%              |

The hedge does NOT eat the carry at realistic fills. The adverse spot spread
(5-10 bps RT assumed) + ~48-59 churns/yr shaves the headline but leaves a
~10-12% unlevered APR in place. The break-even spot RT spread is ~16-23 bps —
roughly 3-4x the realistic assumption — so the carry has comfortable margin
to the spread that would kill it.

The pessimism is honest: taker fills + a stressed spot spread (what you'd pay
churning a stressed book) turns all three legs net-negative. Maker execution is
mandatory.

## Capacity (flagged estimate — no L2 spot book held)

Conservative floor = min(2% OI, 0.5% daily perp notional vol, 5% of an assumed
spot depth of 20% of perp volume). The binding rail everywhere is 0.5% of daily
perp volume:

| leg  | ceiling USD | APR at ceiling |
|------|------------:|---------------:|
| BTC  | $17.2M      | 12.14%         |
| ETH  | $5.7M       | 10.43%         |
| SOL  | $1.5M       | 11.81%         |
| TOTAL| $24.45M     | —              |

~$24M combined is NOT pocket-sized — it is a real, multi-million notional
capacity ceiling. Flagged: spot depth is assumed (20% of perp vol), and the
0.5%-of-daily-volume rail is deliberately conservative.

## Risk check (why is the floor ~11%?)

1. Hedge basis drift (mark-oracle): median -1.7 to -2.8 bps across legs, but
   fat tails — |basis| > 10bps on 6-10% of hours, with episodic extremes
   (BTC min -207 bps, SOL max +1050 bps). Unlevered, this is unrealized MTM on
   the hedge only; it is not funded out, but a levered/basis-stopped version
   would realize the tail.
2. Exchange/custody: capital sits on one venue (Hyperliquid) plus the spot
   hedge venue. The 10.95% structural floor is, in part, a charge for
   counterparty/withdrawal-suspension tail risk that cannot be hedged inside
   the carry itself. This is uncompensated residual risk borne by the trader.
3. Churn forced-fill cost: the gate toggles ~48-59x/yr, and the forced fills
   consume 39% (BTC) / 50% (ETH) / 56% (SOL) of gross funding at realistic
   spreads. This is the biggest drag and the reason maker-only is mandatory.

## Decision

Promote to paper-forward under these constraints:
- MAKER/QUEUE execution only (post limit; never cross the book at entry/exit).
- Ceiling of ~$24M combined notional across BTC/ETH/SOL (conservative).
- Re-validate the spot spread assumption live (the one unmeasured input —
  no L2 spot book is held) before any live sizing.

Param hash: 04a88dac391f6602 (trial written to data/gauntlet/trials.jsonl).
