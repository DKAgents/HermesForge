# HYP-17 (funding-crowding volatility proxy) — verdict

Date: 2026-11-03 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-17-funding-crowding-expansion.md (pre-registered, thresholds FIXED)
Driver: scripts/gauntlet/revalidate_funding_crowding.py
Trial: data/gauntlet/trials.jsonl (HYP-17, param_hash a4fe2d52…, chain_hash b0892491…)

VERDICT: H1 FAILS (no crowding→volatility signal). H2 net <= 0 (HYP-01 confirmed).
The coach's "crowded positioning → big move" thesis, proxied by extreme funding,
is NOT supported. No thresholds were tuned (all pre-registered constants fixed).

---

## 1. Data window + n (explicit)

- Funding: hl_funding_store, 35 coins, ~9,504 hourly rows/coin (~396d),
  2025-09-27 → 2026-11-02.
- 1d bars: HL candleSnapshot (live fetch, cached), 35 coins, up to 1,461 bars
  (~4y), 2022-11-04 → 2026-11-03. NOTE: the on-disk bars_1d.db holds only ~18d;
  the ~4y series is fetched live (same path as revalidate_xsmom.py).
- Binding window = funding (~400d). After the 90d trailing-percentile warmup and
  5 forward bars, the usable event window is 2025-12-26 → 2026-10-29 (~310d).
- n: 3,753 extreme-funding events; 43,182 unconditional daily bars (full 4y);
  10,780 bars in the same ~310d window.

LIMITATION (stated): ~400d of funding is roughly ONE regime. The full-4y
unconditional baseline spans multiple vol regimes (2022-23 crypto winter), so a
naive regime-vs-full comparison is confounded. Both baselines are reported.

## 2. H1 (expansion) — does crowding predict bigger moves? NO.

| metric | value |
|---|---|
| regime mean \|move\| (1-5 bars) | 5.354% (n=3,753) |
| baseline mean \|move\| (full 4y) | 5.858% (n=43,182) |
| baseline mean \|move\| (same ~310d window) | 5.313% (n=10,780) |
| ratio regime/full | 0.914 |
| ratio regime/same-window | 1.008 |
| diff vs full (95% CI) | −0.505% [−0.674%, −0.332%] |
| diff vs same-window (95% CI) | +0.041% [−0.146%, +0.230%] |
| bootstrap p (regime ≤ full) | 1.000 |
| bootstrap p (regime ≤ same-window) | 0.342 |

Per-horizon (regime vs full baseline): h=1 0.906, h=2 0.919, h=3 0.914, h=4 0.912,
h=5 0.916 — uniformly below 1.0 against the full sample.

Interpretation: against the full 4y sample, the extreme-funding regime has
SIGNIFICANTLY SMALLER moves (ratio 0.91, p=1.0). But that is an artifact of
comparing a recent ~310d window to a 4y baseline that includes the high-vol
2022-23 winter. Against the SAME ~310d window, the ratio is 1.008 with a
difference of +0.04% whose 95% CI straddles zero (p=0.34) — i.e. NO detectable
expansion. Either way, the coach's claim ("crowding → bigger move") is not
supported: the effect is null at best, and the sign is opposite (smaller moves)
against the full sample.

H1 KILL RULE TRIGGERED: extreme-funding mean |move| is NOT statistically larger
than unconditional → the coach's kernel fails as proxied.

## 3. H2 (directional unwind) — net result

- n directional events: 3,753 (+funding 3,027, −funding 726).
- gross directional return (fade the crowd): −28.08 bps.
- round-trip cost (fee_source): 12.0 bps.
- NET directional return: −40.08 bps. Win rate 52.1%, PF 0.85.

The fade loses money GROSS (−28 bps), before fees. That means extreme funding is
followed by CONTINUATION in the crowd's direction (momentum), not the forced
unwind the counterparty thesis predicts. Net is deeply negative (−40 bps), so H2
KILL RULE TRIGGERED (net ≤ 0), confirming HYP-01: the crowding signal is not a
tradable directional edge at this tier.

## 4. Honest verdict on the coach's thesis (as proxied)

The coach's kernel — "OI particularly high → price ripe for a big move" — is
proxied here by extreme funding (directional crowding). The proxy FAILS on both
axes:

1. Expansion (H1): extreme funding does NOT predict larger subsequent moves.
   Same-window ratio ≈ 1.01 (null); full-sample ratio 0.91 (smaller moves).
2. Direction (H2): extreme funding is followed by continuation, not unwind —
   the "crowded side forced to exit" mechanism is not observed over 1-5 days.

Caveats (honest): this is a PROXY (funding ≠ OI). Funding is directional
long/short imbalance; OI is total positioning. A null here does not strictly
falsify the OI-specific claim — that remains untested (HYP-16, data-gated). But
the underlying "crowding → volatility expansion" mechanism, which is the
load-bearing part of the thesis, is not supported by the one crowding signal we
can actually measure. The claim should not inform any live or paper decision.
