# HYP-31 — Cross-venue funding spread + price basis (HL vs OKX) — Backtest Report

hypothesis_id: HYP-31
venue: hyperliquid + okx (cross-venue)
verdict: NOT PROMOTED — both channels net-negative / net-zero after two-venue maker cost
trial param_hash: 547b9a31d70482f6 (fresh; written to data/gauntlet/trials.jsonl)
period (H1 overlap): 2026-07-27 -> 2026-10-31
live: off  |  leverage: none (delta-neutral)  |  no-lookahead: true

---

## Data reality (the honest gate, reported first)

The load-bearing finding that shapes everything downstream:

* **OKX funding is HARD-CAPPED at ~90 days.** The public `/public/funding-rate-history`
  endpoint returns only the trailing ~3 months (verified live: 283 records back to
  2026-08-06). The stored `okx_funding` (2026-07-27 start) is the accumulated rolling
  window = the MAXIMUM retrievable depth. OKX funding **cannot** be backfilled to match
  HL's 3.5y depth — this is an endpoint limit, not a "partially accumulated" gap that
  a deeper backfill can close.
* **OKX price** (for the H2 basis leg) *was* backfilled via `/market/history-candles`:
  1H (~5.5mo) + 1D (deep), persisted to `basis.db.okx_candles`.
* **HL funding** = `hl_funding_hf/*.parquet` (hourly, 2023-05 -> 2026-10).
* **HL mark** = `hl_oi_hf/*.parquet` (hourly mark_price + oracle_price, 2023-05 -> 2026-10).

Consequence: H1 (funding spread) is testable only over the ~3.4-month OKX-funding
overlap (2026-07-27 -> 2026-10-31, 2,312 hourly observations per coin), NOT the full
HL depth. H2 (price basis) runs hourly over the OKX 1H-candle span (~5.5 months,
4,813 hourly windows per coin).

---

## Q1 — Funding spread: magnitude + persistence

Spread = HL funding APR - OKX funding APR (both %/yr; HL hourly x8760, OKX 8h x1095).

| coin | HL APR mean | OKX APR mean | spread mean | spread median | spread std | p10 | p90 |
|------|-------------|--------------|-------------|---------------|------------|-----|-----|
| BTC  | 8.55%       | 5.92%        | +2.63 pp    | +3.03 pp      | 5.62 pp    | -4.33 | +8.63 |
| ETH  | 8.32%       | 4.65%        | +3.67 pp    | +4.21 pp      | 6.55 pp    | -3.02 | +9.75 |

The spread is **real, positive, and persistent on the median** (+3 to +4 pp), but it is
**much thinner than the naive "10.95% floor - 6%" story**. Two corrections:

1. **10.95% APR is HL's *base/median* rate, not a hard floor.** In the overlap window,
   36% of hours are below 1.25e-5/hr and funding goes negative (min -13.97% APR), because
   HL funding = base + premium and premium turns negative. So "HL floor" overstates the
   spread's floor.
2. In this specific ~96-day window HL's *mean* funding (~8.5%) ran below its long-run
   median, so the realized spread under-represents the "typical" spread. (Cannot be
   verified deeper — OKX funding is the cap.)

**Is it large enough to clear two-venue maker cost?** No. The pre-committed cost model
(maker on BOTH venues): HL maker = 1.5 bps (fee_source crypto base tier), OKX maker =
2.0 bps (OKX USDT-margin base tier, fail-closed). Cross-venue round-trip = 2 legs x 2
sides = 7 bps. At the empirical ~4-day holds, the break-even spread is ~6.4% APR, but
gross carry is only ~4.4-5% APR -> **net negative**.

---

## Q2 — Net P&L (honest, both channels)

### H1 funding-spread carry (cross-venue delta-neutral)
Entry: rolling-24h-mean spread >= 3.0 pp. Exit: spread < 1.0 pp. Notional = 1x capital
per leg (net delta ~0). No look-ahead (accrual starts the bar after the signal bar).

| coin | episodes | mean hold | gross APR | fees APR | **net APR** |
|------|----------|-----------|-----------|----------|-------------|
| BTC  | 14       | 92h       | +439 bps  | 665 bps  | **-226 bps**|
| ETH  | 15       | 105h      | +503 bps  | 585 bps  | **-82 bps** |
| both | 29       | ~97h      | +474 bps  | 621 bps  | **-147 bps** |

Net = **-1.47% APR**. The spread grosses ~4.4-5% APR but the 7 bp two-venue round-trip,
amortized over ~4-day holds, costs ~6.2% APR. The churn (entry/exit on a std-5.6pp
spread) is what makes the fee drag bite — and the parameters are pre-committed (not
re-tunable, per the pre-registration).

### H2 price-basis mean-reversion
basis = (HL mark - OKX last)/OKX last. Entry |basis| >= 5 bp, fade, exit at ~0.

| coin | windows | \|basis\| mean | \|basis\| p90 | episodes | gross | **net** |
|------|---------|----------------|---------------|----------|-------|---------|
| BTC  | 4,813   | 1.01 bp        | 6.40 bp       | 324      | +2104 | **-164 bp** (-0.51/trade) |
| ETH  | 4,813   | 1.43 bp        | 7.98 bp       | 398      | +2913 | **+127 bp** (+0.32/trade) |

The BTC/ETH cross-venue price basis is **MM-arbitraged to ~1 bp mean / ~6-8 bp p90**.
The fade does capture gross (~7 bp/trade — it *does* converge), but that is exactly at
the 7 bp two-venue cost, so it nets to ~0 (BTC -0.5 bp/trade, ETH +0.3 bp/trade).
No harvestable edge.

---

## Q3 — Verdict

**Does the cross-venue channel add anything beyond the HL-only carry already validated? No. It is dominated.**

The HL-only carry (HYP-28/29) already harvests the FULL HL funding (~8.3-8.6% APR in
this window, 10.95% at base) by shorting the HL perp against a *free* HL-spot hedge.
The cross-venue version replaces that free spot hedge with a long OKX perp that
*PAYS* ~4.7-5.9% APR OKX funding, netting the carry down to HL - OKX = ~2.6-3.7 pp
(~31-44% of the HL-only gross). On top of that it adds:

* a **second venue's maker fees** (7 bp round-trip all-in),
* the **cross-venue risk** (transfer / custody / liquidation asymmetry on one leg while
  the other runs — the pre-registered "load-bearing honest unknown"), which is *not*
  quantified as a fee and only makes the channel worse,
* and it still nets NEGATIVE (-1.47% APR) after the two-venue fees.

So going cross-venue buys strictly *less* carry than the single-venue HL carry, for
strictly *more* cost and risk.

**Is the price basis a real mean-reversion edge? No.** The basis mean-reverts (it
converges), but BTC/ETH cross-venue basis is arbitraged to ~1 bp, far too thin to clear
the 7 bp two-venue cost — the fade nets to ~0.

## Bottom line

Both channels fail the pre-registered promotion test. H1 is dominated by the
already-validated HL-only carry and is net-negative after two-venue cost; H2 is a real
but MM-arbitraged process that nets to zero. HYP-31 is NOT PROMOTED. (Data caveat
standing: the result is measured over the ~90-day OKX-funding window forced by the
endpoint cap; a deeper OKX funding archive would let this be re-tested over the full
HL cycle.)