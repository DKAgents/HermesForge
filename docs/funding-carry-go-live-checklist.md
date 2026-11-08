# Funding Carry (STR-FNDCARRY) — Go-Live Checklist

> Status: paper-forward, running hourly. This is the path from paper → real money,
> gated per the strategy-gauntlet rules (G3 passed, independent validation pending).

## Phase 0 — Strategy state (already done)
- **HYP-28**: real, ~15–21% unlevered APR, funding-true (not basis).
- **HYP-29**: survives G3 fill-realism (maker-only; ~10–12% conservative), ~$24.5M capacity.
- **US-229**: paper-forward stand-up running (maker-only, funding-vs-basis split).

## Phase 1 — Account & capital
1. Create (or reuse) a Hyperliquid account.
2. Decide capital allocation. The carry is **unlevered yield** — it is "% of capital
   parked", NOT "risk-per-trade". Start SMALL (a test allocation) to validate live
   execution before scaling.
3. Deposit the capital. *(You do this — I never move funds.)*

## Phase 2 — The hedge (load-bearing execution detail)
4. Hedge = **HL spot** for BTC/ETH/SOL. Do NOT use cross-venue — HYP-31 proved
   cross-venue is *dominated* (the HL-spot hedge is free; the OKX perp leg pays
   funding and nets down).
5. Verify the HL spot pairs (BTC/USDC, ETH/USDC, SOL/USDC) exist and are liquid.
6. Confirm hedge accounting: spot = hedge leg, perp = funding leg.

## Phase 3 — Execution (maker-only — the binding constraint)
7. **Maker/post-only on BOTH legs.** HYP-29: taker is decisively net-negative
   (−7% to −14% APR). A taker fill must be impossible, not discouraged.
8. Verify post-only is genuinely enforced (no taker fill slips through).
9. Entry gate: rolling 24h mean APR ≥ 8% AND ≥ 75% of window hours positive
   (the HYP-28 gate, not a single reading).

## Phase 4 — Live spot-spread validation (the ONE assumed input)
10. HYP-29's honest caveat: the spot ask/bid spread was *assumed* (~5–10bp), not
    measured (no L2 spot book). Measure it live and confirm it is inside the band
    (break-even is ~16–23bp, so there is margin — but verify).
11. Confirm maker fills on the perp actually fill at the modeled rate.

## Phase 5 — Independent validation pass (BEFORE any live flip)
12. A second, independent review (not me, not the original backtester) of: the
    funding-vs-basis split, the maker-only enforcement, the sizing, the paper PnL.
13. Confirm paper-forward PnL is tracking ~15% funding-only (not inflated by basis).

## Phase 6 — Go-live approval (the hard gate)
14. **You** flip `LIVE_TRADING_ENABLED=ON`. *(Your action — I do not flip it.)*
15. Sizing: unlevered, conservative capital allocation (this is a yield, sized as
    % of capital, not a 1%-risk directional trade).

## Phase 7 — Monitoring + kill-switch (ongoing)
16. Monitor: funding gate, maker fills, basis (mark−oracle), spot spread.
17. Kill-switch (exit, also maker-only — never taker to "get out"): if maker fills
    stop filling, OR the funding floor compresses below the gate, OR basis drifts
    fat — close.
18. Normal exit: when the gate clears (funding < 8% sustained), close maker-side.

## Hard rules (non-negotiable)
- Maker-only · no leverage · delta-neutral only on BTC/ETH/SOL.
- `LIVE_TRADING_ENABLED` flips ONLY after Phase 5 + your explicit approval.
- I do not execute trades, move funds, or flip live settings — you approve and execute.
