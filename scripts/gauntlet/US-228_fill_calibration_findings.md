# US-228 Phase 1 — Empirical G3 fill-cost calibration (findings)

Read-only data gathering only. Source: Ironflow API (`/v1/query`, keyless,
24 h rolling history), `hl.fills` + `hl.mark_prices`. 2026-11-06.

Data: per-side fill rows with `is_taker`, `fee` (negative = rebate), `notional`,
`price`; slippage measured vs most-recent 10 s mark sample (ASOF, no look-ahead).

## Access
- No key in repo/.env (only LUNARCRUSH_API_KEY present). No placeholder config.
- Keyless read works: 24 h history, 10 req/min, 1 h per request / SQL budget
  60 s/hr. Free key (no card) at ironflow.sh/key → 60 req/min, 30 d history.
- hl.mark_prices available from 2026-04-29 onward; fills 365 d rolling.

## Empirical findings (24 h sample; BTC/ETH/SOL/HYPE liquid + 10 mid-caps)

1. Maker/taker split of ALL fills is 50/50 BY CONSTRUCTION (every trade = one
   taker + one maker). It is NOT a cost signal for a rebalancer; aggressiveness
   is a strategy choice, not a market base-rate. G3's maker fill_prob=0.35 is
   the real lever, and it is not measurable from aggregate fills.

2. Fee per side (bps, weighted by notional):
   - Taker: ~3.0–3.7 liquid (BTC 3.54, ETH 3.05, SOL 3.72, HYPE 3.05);
     mid-caps ~2.8–4.7. Retail (<$1k) up to 4.7; large ($1m+) down to ~2.9.
   - Maker: ~0.0 (median −0.1 bps). NO meaningful rebate. fee_source's
     1.5 bps maker fee overstates the true ~0.

3. Taker slippage vs mark (half-spread + impact), median bps by notional:
   - <$1k:      ~1–3
   - $1k–10k:   ~1.3–7 (liquid ~1.3, mid-caps ~2.6–3.7, INJ 6.9)
   - $10k–100k: liquid ~1.4–2.5; mid-caps ~4–30 (sparse n)
   - $100k–1m:  liquid ~3.6–5.8; mid-caps ~15–29 (n=2–3, noisy)
   - p90 tails at size routinely 25–80+ bps (mark-lag during dislocations).

## Comparison to the HYP-21 hinge (24 bps vs 90 bps round-trip)
- G3 anchors: hurdle 45 bps/leg ×2 = 90 bps round-trip; fee_source 12 bps
  round-trip ×2 = 24 bps "both-legs" realistic; maker fill_prob 0.35 +
  1.5 bps adverse selection (g0_cost_screen).
- Empirical all-taker per-leg all-in (fee + median slip) ≈ ~5–11 bps on liquid
  coins, ~13–35 bps on mid-caps at $10k–100k/leg.
- Empirical 2-leg (long+short entry) all-taker: ~10–14 bps liquid, ~14–38 bps
  mid-cap, at realistic cross-sectional size; higher tail on illiquid coins.
- → The 24 bps "realistic" figure is a reasonable CENTRAL estimate (arguably
  slightly conservative for liquid-only, roughly right for the mixed universe).
  The 90 bps hurdle is a ~4–6× tail, NOT the expected cost.
- Maker-executed legs would collapse cost toward ~0 fee + adverse selection
  (unmeasured; 1.5 bps assumed) — a MUCH larger swing than the fee itself.

## Caveats / unblock
- 24 h window (keyless). "A few days" needs the free key (30 d max anyway;
  mark_prices ≥2026-04-29).
- Slippage is size-of-notional dependent; per-coin AUM is undefined in HYP-21,
  so cost must be treated as a function of per-leg notional + universe breadth.
- mark is a ~10 s oracle-ish sample; p90/max slip inflates during fast moves
  (median robust). Small-n large-size buckets on mid-caps are noisy.
- NOT yet measured: passive/maker adverse selection (the fill_prob question),
  and full-universe (all native perps, incl. illiquid) slippage tail.

## Next step (phase 2 — not started, gate code untouched)
Refit G3 cost model against this, keeping the pessimistic path fail-closed:
- taker fee ~4.5 bps (already in fee_source) is fine; maker ~0 (drop the 1.5
  maker fee, or set to 0 rebate).
- Reprice the "45 bps/leg" hurdle as a data-grounded tail, not the default.
- The real open question is maker fill_prob / adverse selection — needs a
  passive-execution study, not aggregate-fill statistics.