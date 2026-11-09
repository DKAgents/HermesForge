# Funding Carry — Phase-0 Carry-Accounting Fixes (C-1, C-2, C-3)

Researcher report. Executes §4 items C-1, C-2, C-3 from the
"HermesForge Strategy Review & Research Directive" (v1.0, 2026-11-09).
All numbers computed from real stored history, not estimated.

Data:
- C-1: `~/.hermes/market_data/hl_funding_hf/` (hourly funding) +
  `hl_oi_hf_clean/` (mark/oracle → basis), 2023-06-08 → 2026-10-31.
- C-2: Binance public funding archive (`data.binance.vision`), 8h cadence,
  BTC/ETH 2020-01 → 2026-10, SOL 2020-09 → 2026-10; BTC daily klines for regime.
- C-3: C-1 episode results + DefiLlama yields snapshot (2026-11-09) + HL HLP vault.

---

## C-1 — Churn decomposition + hold-through

### Churn decomposition by cause

The paper delta-neutral construction is short-perp + long-spot, held 1:1.
On inspection, exactly **one** churn cause exists in this construction:

- **Funding-triggered entries/exits: ~100% of churn.** The `delta_neutral_gate`
  (rolling-24h mean APR ≥ 8% AND ≥ 75% hours positive) is evaluated hourly and
  toggles the position on every cross, because HL's structural base funding
  (≈10.95% APR) sits *near* the 8% threshold. Every toggle = one full round-trip
  fee on both legs.
- **Hedge rebalancing: 0%.** The hedge is a static 1:1 short-perp/long-spot.
  Delta is exactly neutral by construction — there is no delta drift to
  rebalance, so no rebalancing churn exists.
- **Margin transfers: 0%.** None modeled; no cross-leg margin movement in the
  paper path.
- **Forced fills: 0% (modeled), but a real live risk.** No liquidation/fill
  forcing is simulated; this is a live-only risk (see C-5 in the directive).

The directive's hypothesis is confirmed: **the churn is a funding-timing signal
in disguise** — the exact class the search already found does not work.

### Churn cost at the corrected fee model

C-6 is already implemented in the codebase (commit `e542918b`): the paper
driver's `DELTA_NEUTRAL_MAKER_RT_BPS` now resolves via
`carry_round_trip_fee_bps("maker")` = 11 bps round-trip =
(perp maker 1.5 + spot maker 4.0) × 2 sides; taker 23 bps =
(perp 4.5 + spot 7.0) × 2 sides. The older 6 bps / 18 bps figures undercharged
the spot leg; those are already corrected. (The HYP-28 *backtest script*
`backtest_hyp28_delta_neutral_funding_carry.py` still hardcodes the stale 6/18
bps constants — flag for the dev swarm to sync it, but the live paper ledger is
correct.)

Pooled over BTC/ETH/SOL, corrected maker fees (11 bps), ~3.42y:

| variant (entry / exit)                        | episodes | gross funding | churn (maker fees % of gross) |
|---|---|---|---|
| baseline (24h gate both ways — current driver) | 542      | +14,343 bps   | **41.6%**                     |
| hold7 (same entry; exit 7d mean < 0)          | 561      | +14,977 bps   | 41.2%                         |
| hold14 (same entry; exit 14d mean < 0)        | 648      | +14,913 bps   | 47.8%                         |
| **regime7 (enter 7d mean > 0; exit < 0)**     | 70       | +14,850 bps   | **5.2%**                      |
| **regime14 (enter 14d mean > 0; exit < 0)**   | 41       | +14,666 bps   | **3.1%**                      |

Key finding: **changing only the exit rule does not help.** `hold7`/`hold14`
keep the twitchy 24h entry gate, so re-entries still churn (SOL actually gets
worse — 336 and 432 episodes). The churn only disappears when the *entry* is
also made structural (sign-hysteresis on a 7–14 day trailing funding mean),
i.e. a true "hold-through" — which is what a structural carry should be anyway.
The base funding floor is the persistent feature; it should be collected almost
continuously, not gate-timed.

### Acceptance check — churn PASS, drawdown FAIL (naive hold-through)

- **Churn < 15% of gross: PASS.** regime7 → 5.2%, regime14 → 3.1% (vs 41.6%
  baseline). Well under the 15% target.
- **No increase in worst-case drawdown: FAIL.** Worst-case mark-to-market
  drawdown (all funding+basis MTM, pooled, bps of notional):

  baseline −4,192 bps → regime7 −7,770 bps → regime14 −8,809 bps.

  Holding through the funding dips means holding through the **basis
  (mark−oracle) widening tail** — the fat-tailed risk the directive already
  flags (|basis| > 10 bps on 6–10% of hours). The naive hold-through roughly
  doubles worst MTM drawdown. The drawdown is basis-driven, not funding-driven.

**Conclusion (C-1):** the correct fix is hold-through *combined with a
basis-drift band* — rebalance/exit the hedge when |basis| drift exceeds a band
(the directive's "delta drift" maps to basis drift in a 1:1 cash-and-carry),
not a funding dip. Churn target is achievable (3–5%); the drawdown target is
not met by a pure funding-sign hold-through and needs the basis band. This is a
`[CODE]` item for the dev swarm (narrow: replace the entry/exit gate with
sign-hysteresis + basis band; the paper driver's 6 bps fee constant is also
still 11 bps short).

---

## C-2 — Funding regime stress test (Binance proxy)

Binance uses the same anchor-and-clamp formula (P = 0.01%/8h, clamp ±0.05%);
8h funding cadence. **This is a stress PROXY — Binance premium dynamics differ
from HL (HL is hourly with a structural base floor). It is not a substitute for
HL data.**

Short-perp receiver (the carry's funding leg), 2020 → 2026:

| metric | BTCUSDT | ETHUSDT | SOLUSDT |
|---|---|---|---|
| % settlements negative | 14.0% | 13.9% | **28.5%** |
| longest negative streak | 8.0 d | 8.3 d | **17.7 d** |
| mean funding APR (short receiver) | +11.63% | +13.71% | **+0.27%** |
| worst 30d carry | −131 bps | −178 bps | **−3,133 bps** |
| worst 90d carry | −39 bps | −168 bps | **−4,257 bps** |

Carry by regime (BTC 30d ret > +10% = bull, < −10% = bear, else chop):

| regime | BTCUSDT | ETHUSDT | SOLUSDT |
|---|---|---|---|
| bull   | +25.6% APR | +32.7% | +17.9% |
| bear   | +3.8%      | +2.8%  | **−18.7%** |
| chop   | +7.1%      | +7.7%  | **−2.3%** |

**2022 (the bear regime of interest):** BTC carried **positively** (+4.16% APR,
22% hours negative); ETH roughly flat (+0.79%, 34% negative); **SOL was
catastrophic** (−35.6% APR, 46% negative, worst 90d −3,840 bps).

**Conclusion (C-2):** BTC/ETH funding is structurally positive even through a
crypto winter — a 7–14 day exit band sized against an 8-day negative streak is
adequate. **SOL is the weak link**: 28.5% negative hours, 17.7-day negative
streak, −4,257 bps worst 90d, and net-negative funding in bear/chop regimes.
On HL SOL has a structural floor that Binance lacks, so the HL SOL result is
better — but this proxy says **SOL's carry is not stress-safe** and should be
dropped or banded aggressively. Recommend the exit band be sized against the
8–18 day negative-streak range, and SOL either excluded from the carry or
subject to a tight basis/funding band (feeds C-1's basis band and C-8's
single-asset-at-$100 choice).

---

## C-3 — Restated returns on total capital + benchmark

The headline "~15–21% unlevered APR" / "~10–12% conservative" figures are
**NOTIONAL and gross of churn**, and they ignore the capital parked in the spot
leg and the perp margin. Restating on total deployed capital:

Capital accounting for 1:1 notional N:
- **Unified (portfolio) margin:** spot N collateralizes the short N → capital
  ≈ N. APR on capital ≈ notional APR.
- **Isolated margin (no unified margin):** spot N (not usable as perp
  collateral) + perp margin N (fully collateralized short) → capital ≈ 2N.
  APR on capital ≈ notional APR ÷ 2. (This is the directive's "roughly halves".)

Net of corrected maker fees + churn, on total capital, vs the benchmark:

| | gross notional | net notional (maker) | **cap APR unified** | **cap APR isolated** | **edge vs 3.21% idle** |
|---|---|---|---|---|---|
| baseline (current, 41.6% churn) | 22.2% | 13.0% | 13.0% | 6.5% | +9.8% / +3.3% |
| hold-through regime7 (5.2% churn) | 16.8% | 15.9% | 15.9% | 8.0% | +12.7% / +4.8% |
| hold-through regime14 (3.1% churn) | 16.6% | 16.0% | 16.0% | 8.0% | +12.8% / +4.8% |

Benchmark (idle low-risk stablecoin yield, 2026-11-09): HL `hyperliquid-earn`
USDC **3.21%** APY (the correct opportunity-cost benchmark); sUSDe 5.0%;
Aave V3 USDC 3.8%; Morpho USDC (Base) 5.6%; Spark Savings USDC 3.8%.

**The corrected, honest numbers:**

- Notional net maker APR (held hours): **~13%** at the current churny gate,
  **~16%** with hold-through.
- Net APR on **total deployed capital** (isolated margin): **~6.5%** as-now,
  **~8%** with hold-through — **roughly HALF the quoted notional figure**.
- Real edge over idle USDC (3.2%): **~3–5 points** on isolated margin,
  **~10–13 points** on unified margin.

So the quoted "~15–21% unlevered APR" should be restated as **~6.5–8% on
capital (isolated margin) net of corrected fees and churn**, or ~13–16% only if
portfolio margin (C-4) is available and approved. Idle USDC on HL already pays
3.2%, so the incremental edge of the carry is single-digit on isolated margin.

---

## Summary of the three corrected numbers

1. **C-1 (churn):** baseline churn is **41.6% of gross** at corrected fees (not
   the ~21% the old 6 bps model implied). Hold-through cuts it to **3–5% of
   gross** (passes <15%) — but the naive funding-sign hold-through **roughly
   doubles worst-case basis MTM drawdown**, so a basis-drift band is required
   to meet the "no increase in drawdown" acceptance.
2. **C-2 (stress):** BTC/ETH funding is positive even through 2022 (BTC +4.2%,
   ETH +0.8% in 2022); **SOL is the stress-fragile leg** (28.5% negative hours,
   17.7-day negative streak, −4,257 bps worst 90d, negative carry in bear/chop).
   Proxy caveat applies.
3. **C-3 (capital):** restated net APR on total capital is **~6.5% as-now,
   ~8% with hold-through** (isolated margin) — **roughly half** the quoted
   ~15–21% notional figure — for an edge of **~3–5 points over the 3.2% idle
   USDC benchmark** (or ~10–13 points with portfolio margin).

Root-cause framing: the overstatement was two stacked assumptions — (a) notional
(not capital) sizing, and (b) churn priced at the old 6 bps fee and treated as
acceptable. The fee model itself is already corrected (C-6, commit `e542918b`);
the remaining overstatement is notional-vs-capital plus churn. Correcting both
roughly halves the headline yield and shrinks the edge over idle stablecoin
yield to the single digits on isolated margin.

Investigations precede code changes: no production code was modified in this
pass. The `[CODE]` items arising (C-1 exit gate → sign-hysteresis + basis band;
sync the stale 6/18 bps constants in the HYP-28 backtest script) are flagged for
the dev swarm. The paper driver's gate logic remains unchanged until then.