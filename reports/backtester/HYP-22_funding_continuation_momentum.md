# HYP-22 — funding-continuation momentum (directional) — verdict

Date: 2026-11-07 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-22-funding-continuation-momentum.md (pre-registered, FIXED)
Driver: scripts/gauntlet/revalidate_hyp22_funding_continuation.py
Trial: data/gauntlet/trials.jsonl (HYP-22, param_hash 4a524db3…, chain_hash 2fc54f35…; chain verified OK; N=133)

VERDICT: KILL RULE FIRES. "Follow the funding crowd" is NOT net-harvestable.
The momentum exists GROSS (~+48 bps over a 5d hold) but the funding carry the
follower pays (~+152 bps) eats it ~3× over, and the continuation itself is a
BEAR-regime artifact — it REVERSES in bull regimes. CLOSED as a directional edge.

---

## 0. What was tested (the mirror of the failed carry)

The old funding-carry STRATEGY faded the crowd and was stopped out 20-39x —
because funding extremes are followed by CONTINUATION, not unwind. HYP-22 tests
the mirror: FOLLOW the crowd (long high-positive-funding, short high-negative-
funding) and ask whether the continuation momentum is NET-harvestable AFTER
paying the funding carry the follower owes the crowd. Directional (long/short)
by design; user approved.

Data: native-perp hourly funding (funding_rate, dex=='') + hourly mark_price,
both 2023-05-12 -> 2026-10-31. 235 coins x 1269 daily bars. This is genuinely
MULTI-REGIME (unlike the ~400d slice that HYP-17 was limited to): 2023
accumulation, 2024-25 bull, 2025Q4-2026 bear (BTC ~27k -> ~125k -> ~58k ->
~77k).

## 1. Funding data degeneracy (the load-bearing caveat)

52% of daily funding cells are pinned at the HL modal default rate (1.25e-5/hr,
≈0.125 bp/hr); only ~6 coins/day are GENUINELY above it. This is the exact
tie-degeneracy that dropped funding as a factor in HYP-20/21. Consequences:

- The "long high-positive-funding" leg is diluted: its mean signal is only
  +1.12 bp/hr — the top decile is a few genuinely-elevated coins padded by
  modal-default coins.
- The "short high-negative-funding" leg is more informative (-1.43 bp/hr).

Funding_rate sign tracks premium (corr 0.97), so the sign convention is sound:
positive funding = longs pay, negative funding = shorts pay.

## 2. H1 — is continuation REGIME-ROBUST? NO (bear artifact)

Extreme-|funding| events (coin's own trailing-90d top-decile AND cross-sectional
top-decile): n = 12,876. Directional return = sign(funding) x forward return.

| regime | n     | h1 hit | h1 dir(bp) | h2 dir(bp) | h3 dir(bp) | h4 dir(bp) | h5 dir(bp) |
|---|---|---|---|---|---|---|---|
| bull   | 4147  | 0.463  | +5.5  | -25.4  | -47.9  | -40.0  | -25.3  |
| flat   | 2647  | 0.522  | +10.0 | -22.6  | -76.6  | -106.1 | -120.7 |
| bear   | 6082  | 0.510  | +16.9 | +49.2  | +41.1  | +82.0  | +69.3  |

- BEAR: continuation holds (+17 to +82 bp across horizons; hit-rate ≈ 0.51).
- BULL: continuation FAILS — hit-rate 0.46 (< coin-flip), directional returns
  NEGATIVE from h2 onward. Crowded longs MEAN-REVERT in up-markets.
- FLAT: null-to-slightly-negative.
- POOLED: h1 +11.8, h2 +10.5, h3 -11.7, h4 +3.9, h5 -0.1 bp — ~zero in
  aggregate.

Answer: continuation is NOT universal. It is a BEAR-regime artifact (crowded
shorts keep getting squeezed/pressured down in falling markets), and it inverts
in bull markets. This is exactly what the ~400d HYP-17 slice could not answer:
averaged over one mostly-up regime, continuation looked positive; over the full
cycle it is regime-contingent and net-zero.

## 3. H2 — tradeable NET (long top-decile, short bottom-decile)

Cross-sectional on the signed daily funding rate; equal-weight deciles;
no-lookahead (signal at close[t], fill open[t+1]); funding = sum of hourly rate
over the exact holding window; fees = 2 legs x 2 taker fills.

| hold | gross | funding PAID | fee(real/cons) | NET@4.5b | NET@45b | win | PF |
|---|---|---|---|---|---|---|---|
| 1d   | +21.17 bps | 38.21 bps (16.44 long + 21.77 short) | 18 / 180 bps | -35.04 bps | -197.04 bps | 0.464 | 0.729 |
| 5d   | +47.69 bps | 152.17 bps (64.27 long + 87.90 short) | 18 / 180 bps | -122.48 bps | -284.48 bps | 0.407 | 0.605 |

The funding PAID is the point: the follower pays |funding| on BOTH legs (longs
pay positive funding; shorts pay negative funding — the "shorts receive" phrase
in the hypothesis applies only to funding>0 coins, which is not what H2 shorts).
Even so, the conclusion does not hinge on this sign: net is negative at every
fee tier and horizon, and would remain negative even if the short leg had
hypothetically "received" funding.

- 1d: funding (38 bp) already exceeds gross (21 bp) — net -35 bps.
- 5d (the carry-sensitive horizon): funding (152 bp) is ~3x gross (48 bp) —
  net -122 bps. Non-overlapping 5d sample: -108 bps (the overlap does not
  rescue it; it is the same sign).

KILL RULE FIRES on cost (net <= 0 at the realistic 4.5 bps/side). No escalation
to G4/G5 — the edge is dead before robustness, so CPCV/DSR/PBO are not
applicable (there is no positive net to overfit-test).

## 4. Honest verdict

Does "follow the funding crowd" harvest a directional edge net of carry + fees?
NO.

1. The continuation direction is REAL but REGIME-CONTINGENT and net-zero in
   aggregate: it lives only in bear regimes, and it reverses in bull regimes
   (crowded longs mean-revert). "Follow the funding crowd" cannot be traded
   unconditionally — the sign flips with the regime.

2. The funding carry eats whatever is left. The follower pays ~152 bps over a
   5-day hold to ride ~48 bps of gross momentum — a ~3:1 carry-to-edge ratio.
   Even at 1-day horizon the carry (38 bp) exceeds gross (21 bp). NET is
   negative at both realistic (4.5 bp/side) and fail-closed (45 bp/side) taker
   fees, at both 1d and 5d holds.

3. The structural reason is the same one that killed funding as a factor in
   HYP-20/21: the funding signal is massively degenerate (52% of cells pinned
   at the HL default rate), so "extreme funding" is a thin, noisy, mostly-
   default signal — and the carry cost is dominated by the default rate the
   follower pays every hour regardless of signal quality.

This closes funding-continuation as a tradeable directional edge. No promotion.
No paper-forward. LIVE off. The hypothesis's own falsification ("net must beat
carry cost + fees") fails by a wide margin — the carry cost eats the momentum.