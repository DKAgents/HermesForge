# US-179 Funding-Carry Validation — Independent Backtester Re-Derivation

Date: 2026-11-01
Author: Backtester (HermesForge)
Scope: Independent re-derivation. I did NOT trust the coder's self-report; I re-read the code,
re-loaded the live funding store, re-ran `simulate_carry` / `carry_g3_record` / `partition_regime`,
and decomposed the P&L. Read-only; no code/post/cron touched.

Data actually used: `~/.hermes/market_data/hl_funding/funding.db` — 35 coins, ~9,600 hourly rows
per coin, ~400 days, ZERO intra-run gaps >1.5h (fundingHistory is complete and continuous).

---

## 1. Sustained-funding gate + APR canonicalization — CORRECT

Verified in `funding_carry.py`:

- `HOURS_PER_YEAR = 8760` (365 * 24). `hourly_to_apr = rate * 8760`, `apr_to_hourly = apr / 8760`.
  Round-trips cleanly (unit test asserts + golden vectors pass).
- Entry gate `funding_window_signal` implements exactly S1…S4:
  - S1: `mean(hourly over W=24) >= apr_to_hourly(0.08)` (8%/yr floor)
  - S2: `count(rate > 0) >= 0.75 * 24` (>= 18 positive hours)
  - S3: `current rate > 0`
  - S4: `cost_clears(mean_apr)`
- "Sustained" is correctly a rolling 24-hour statistic; a single spike is rejected on both S1 (mean)
  and S2 (positive fraction).

One inconsistency to log (not a defect that inflates the edge — it is fail-safe/conservative):

- `funding_window_signal` calls `cost_clears(mean_apr)` with the **taker** default
  (`CARRY_ROUND_TRIP_BPS = 24`) → the ENTRY gate requires clearing **~12.5%/yr**, even though the
  backtest then credits cost at the **maker** rate (12 bps → ~6.3%/yr). Net effect: entry is gated at
  taker economics while P&L is honored at maker economics. Safe direction, but it means the gate
  occupancy is low (see below) and the 6.3–12.5%/yr "maker-only" band is left unconsumed.

Gate occupancy (fraction of hours the S1–S4 gate fires): BTC 2.7%, ETH 1.6%, SOL 1.5%, HYPE 17.2%,
PUMP 10.8%, AAVE 3.7%. The signal is **not** "always-on"; it is genuinely selective for elevated
funding (>~12.5%/yr), i.e. premium sitting on top of HL's structural interest floor.

---

## 2. Backtest result — re-derived, and it is NET of cost, but the coder's numbers do NOT reproduce

My independent run (35 coins, ~400 days, `simulate_carry` default = maker-fill):

| metric | my value |
|---|---|
| episodes | 313 |
| exit reasons | rate_flip 310, basis_widen 2, decay 1 |
| mean funding_pnl | $535.1 |
| mean basis_pnl | $345.8 |
| mean execution_cost | $240.0 |
| mean net_carry | $640.9 |
| mean hold | 139.9 h (~5.8 d) |
| notional | $200k (20% gross rail binds) |
| basis_risk (1R) | $1,000 = **0.1% of capital, not 1%** |
| optimistic (0 fee) mean R | 0.8809 |
| **realistic (maker 12 bp) mean R** | **0.6409** |
| pessimistic PF | 5.28 |
| edge-decay ratio | 0.7276 |
| G3 passed | **True** |

`carry_g3_record` is fed `net_r = net_carry / basis_risk`, and cost is subtracted inside
(`net_carry = funding_pnl + basis_pnl - execution_cost`), so **yes, the reported metrics are net of
cost**. The G3 record's "realistic" leg is maker-fill (12 bp), "pessimistic" is taker (24 bp) + a +1 bp
basis-gap on kill exits.

Regime partition (BTC 30-day return, ±2% thresholds) on my run:

| regime | n | mean net_r | PF |
|---|---|---|---|
| bull | 179 | **0.8510** | 30.7 |
| bear | 100 | **0.2929** | 9.0 |
| neutral | 34 | **0.5585** | 9.1 |

I could **not reproduce the coder's claimed bull +0.76 / bear +0.31 / neutral +0.76**. My numbers are
bull +0.85 / bear +0.29 / neutral +0.56 (portfolio realistic mean R +0.64). Close but not equal; the
claimed "bull +0.76 == neutral +0.76" pairing is a red flag (two regimes landing on the same two-decim
mean is unlikely). Most probable cause: the coder ran on an earlier/smaller snapshot of the store (the
DB was still being backfilled/ingested Nov 1 21:31) or a different coin subset / BTC-regime source.
Direction (positive in all three regimes) is consistent; the exact magnitudes are not. Do not rely on
the coder's figures.

---

## 3. Maker vs taker — the maker path helps but is NOT "load-bearing"

Break-even math the coder cited is correct as a static fact: taker 24 bps over a 1-week
(168 h) amortization = 0.0024 / (168/8760) = **12.5%/yr**; maker 12 bps = 6.3%/yr.

But "US-180's maker path is genuinely load-bearing" overstates it. My taker re-derivation (24 bps
round-trip on the same episodes):

- taker mean net_r = **+0.4009** (median +0.19), PF = 5.29, 65.8% of episodes positive.

The edge **survives taker fills** (still positive mean R and PF >> 1). Maker improves mean R from
0.40 → 0.64 (~60% uplift), but maker is not what makes the carry positive. The correct statement:
maker-fill is a meaningful **enhancement**, not a viability gate. (Note the entry gate already runs at
taker economics, so the realized maker cost is a free upgrade on an already-conservative entry.)

---

## 4. Regime robustness — NOT single-regime, but the mix matters more than the regime

All three regimes positive (bull 0.85 / bear 0.29 / neutral 0.56), n >= 34 each. So on this metric the
edge is regime-robust. Bear is the weakest (0.29) but still comfortably positive.

The more important partition is **not regime but coin identity** — see §6.

---

## 5. Kill rules — `basis_widen` is effectively inert, and that IS a material risk

`basis_widen` fired **2 times in 313 episodes (0.6%)**; `decay` once. The prime exit is `rate_flip`
(310/313). Two causes, and the second is the real risk:

1. **Structural (benign):** `rate_flip` (current hourly funding <= 0) almost always precedes a 50 bps
   basis widening. Funding is the whole carry; it flips negative long before the perp mark runs 50 bps
   against the short leg on most coins. So `basis_widen` is a backstop, rarely exercised.
2. **Proxy compression (material):** the backtest's basis stop uses the fundingHistory `premium`
   column (impact-price premium that feeds the funding calc), **not** the real mark-vs-oracle basis
   held in `assetCtxs` (`(markPx - oraclePx)/oraclePx`). These differ. Live probe (Nov 1):
   BTC funding premium −3.12 bps vs mark−oracle −3.74 bps; the two are close in calm conditions but the
   funding premium is impact-price-based and smoothed. When the mark basis *widens* against the short
   perp while funding *stays positive* (a plausible violent-bull-tail), the compressed premium proxy
   does not move 50 bps, so the stop does not fire and the backtest understates that basis loss. This
   tail is the exact "got paid, lost the position" death the §1.6.2 kill was meant to stop, and it is
   **not priced** in the current backtest. Material, unquantified (no historical mark/oracle series is
   in this store to close the gap).

---

## 6. THE HARD QUESTION — real edge or measurement artifact?

Decomposition of the mean episode (net of cost):

- funding flow: +$535 (genuine — the funding received for being short the perp)
- basis convergence: +$346 (**54% of net carry**)
- execution cost: −$240

The funding component is a **real, structural carry**: Hyperliquid pays perp shorts a baseline
interest (~0.01%/8h ≈ 10.95%/yr annualized) plus the premium index. That is a well-known, persistent
flow, not a price-mean-reversion that gets arbitraged away. My measured funding yield during
elevated-funding windows ≈ $535 / $200k × (8760/140h) ≈ **16–17%/yr on notional net of nothing
(that's the flow alone)**. This part is legitimately capturable.

The basis component is the suspect half, and the per-coin breakdown exposes it:

| coin | n | funding | basis | net_r |
|---|---|---|---|---|
| XRP | 4 | 1033 | 777 | 1.57 |
| kSHIB | 2 | 1546 | 243 | 1.55 |
| CRV | 6 | 867 | 437 | 1.06 |
| BCH / ENA | 3/6 | ~900 | ~300 | ~1.0 |
| SOL | 4 | 163 | **1041** | 0.96 |
| UNI | 10 | 799 | 212 | 0.77 |
| … | | | | |
| ETH | 4 | 566 | 256 | 0.58 |
| **BTC** | 6 | 371 | 254 | **0.38** |

Findings that matter:

- **The edge concentrates in the wrong coins.** The highest net_r is in thin/meme coins (XRP, kSHIB,
  CRV, BCH, ENA), and SOL's edge is ~86% basis_pnl ($1,041 of $1,204). These are precisely the coins
  where the long-spot leg **cannot be executed** (Hyperliquid has no liquid spot short and thin/no
  spot-book outside BTC/ETH — the spec §1.4 acknowledges this) and where the impact-price premium is
  least faithful to the mark basis.
- **The implementable coins have the lowest edge.** BTC + ETH = 10 of 313 episodes (3%), combined mean
  net_r = **0.48**, below the portfolio 0.64. The true delta-neutral long-spot/short-perp carry — the
  only construction that is actually executable as designed — earns ~0.38–0.58 R, not the claimed 0.76.
- **Delta-neutrality is assumed, not modeled.** `simulate_carry` never checks spot availability or
  residual delta. It runs long-spot/short-perp on all 35 coins uniformly, including ~30 with no liquid
  spot hedge. The spec's own DELTA_CAP / BTC-perp-overlay eligibility path is not wired into the
  backtest, so "delta-neutral" is an assumption that does not hold for most contributors to the number.
- **The "1R" unit is mis-sized.** `size_position` returns the 20% gross-notional rail as binding
  (notional $200k), so `basis_risk = $200k × 50 bps = $1,000 = 0.1% of capital`. The spec's stated
  1% capital risk budget ($10k) is unreachable because you would need $2M notional (200% of capital),
  blocked by the rail. So the reported "+0.64 R" is measured against a $1,000 risk unit, not the $10,000
  the "1R = 1% of capital" framing implies. The mean episode profit is $641 = **0.064% of capital**.

No double-counting found: `funding_pnl` uses the `funding_rate` column and `basis_pnl` uses the
`premium` column — distinct fields from the store, summed once each, entry-hour funding correctly
skipped, exit cost charged once. Funding data integrity is clean (no gaps, idempotent dedup).

---

## Bottom line / verdict

The funding carry has a **real, structural core** — Hyperliquid's baseline ~11%/yr interest + the
premium index, paid to perp shorts — and that part is not a curvature artifact: funding is a flow that
is genuinely received. But the backtest **overstates the implementable edge** by:

1. Running the long-spot/short-perp construction on ~30 coins with no liquid spot hedge, where the
   delta-neutral premise is false.
2. Attributing **~54% of net carry to basis_pnl** (premium-convergence proxy), the term most dependent
   on the impact-price proxy and least capturable without a real spot leg.
3. Crediting the highest edge to thin/meme coins (XRP, kSHIB, SOL, CRV) while the only truly
   executable legs (BTC/ETH) earn the **lowest** edge (0.38–0.58 R).
4. Measuring "1R" against a $1,000 risk unit (0.1% capital) rather than the stated 1%.

The coder's claimed bull +0.76 / bear +0.31 / neutral +0.76 does **not** reproduce under independent
re-run (I get bull +0.85 / bear +0.29 / neutral +0.56, portfolio realistic +0.64); the claimed figures
should not be used.

**Verdict on WATCH under G3:** Mechanically the gate *passes* as written (n=313, realistic mean R +0.64,
pessimistic PF 5.28, decay 0.73). But it passes only because the gate is fed a 35-coin universe where
the delta-neutral hedge is not executable and the basis-proxy term dominates. It does **not** merit
WATCH in that form. At most, a **narrowed, spot-available-only variant (BTC/ETH, possibly +1–2 liquid
alts) merits paper observation**, with an honest expected net ≈ **+0.4–0.6 R per position** (funding
flow ≈ +0.5 R, basis ≈ +0.1–0.3 R, minus 12 bp maker) and ≈ **10–15%/yr net on notional** during
elevated-funding windows — or a few %/yr on capital once the 20% notional rail and thin-coin capacity
bind.

Required before any promotion decision (recommend logging as follow-ups, not this review):
- Constrain the backtest to coins with a real, liquid spot leg (or model the BTC-perp overlay's
  residual delta honestly); re-run G3 on that subset.
- Either source historical mark/oracle basis (assetCtxs history is not in the store) to validate the
  premium proxy, or mark basis_pnl's alt-coin contribution as non-creditable.
- Fix the "1R" mis-sizing (basis_risk is 0.1% capital, not 1%) so promotion records do not misstate R.
- Tighten the basis_widen stop to fire on the real mark-vs-oracle basis, or acknowledge the inert stop
  leaves the "basis-widens-while-funding-stays-positive" tail unaddressed.