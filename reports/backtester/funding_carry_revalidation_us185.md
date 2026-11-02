# US-185 Funding-Carry Re-validation — directional gate + real-basis kill-stop (REAL data)

Date: 2026-11-01
Author: Coder (HermesForge), re-run via `scripts/gauntlet/revalidate_funding_carry.py`
Scope: reconstituted funding-carry (§ spec architect_us185_spec.md). All numbers below
are REAL output from live Hyperliquid data + the same-venue stores (funding.db /
bars_5m.db / assetctx.db). basis is the real mark-oracle spread, never the compressed
fundingHistory `premium`.

## D. Real-basis kill-stop re-sourced (assetCtxs mark/oracle vs premium)

| coin | mark | oracle | real_basis | fundingPremium |
|---|---|---|---|---|
| BTC | 78384.00 | 78404.20 | -2.58 bp | -2.93 bp |
| ETH | 2279.70 | 2280.70 | -4.38 bp | -4.20 bp |
| SOL | 94.66 | 94.69 | -3.17 bp | -1.82 bp |

The `basis_widen` kill-stop now reads `mark_px`/`oracle_px` (real mark-oracle spread),
NOT the compressed premium. When a real basis series is unavailable the kill is DISABLED
(never falls back to premium). Helper proven: `basis_widen(mark, oracle) == basis_bps`.

## A. Full-universe execution-form dispatch (live library, 235 perps)

Non-delisted perps: **179** (56 delisted). Dispatch from CURRENT funding sign:
- `directional_short`  170 (95.0%)
- `directional_long`    9  (5.0%)
- `skip`                0
(delta_neutral is GATED OFF by default → funding>0 routes to directional_short.)

## B. Directional funding gate on REAL data (λ × realized vol)

Realized σ from 5m-bar closes; current funding APR from fundingHistory. At λ=0.5,
**177/179 perps DO NOT clear the hurdle** — funding (the ~10.95%/yr interest floor)
does not exceed 0.5 × σ for crypto names. Only low-vol PAXG (σ=17.3%, hurdle 8.65%)
is eligible.

λ sensitivity (eligible count, 35-coin CRYPTO_UNIVERSE sample):
- λ=0.25 → 3/35 eligible
- λ=0.50 → 1/35 eligible
- λ=1.00 → 0/35 eligible

## C. Directional hard-stop backtest (REAL 17-day mark window) + λ sensitivity

| λ | episodes | funding_pnl | direction_pnl | loss/fund | G3 real R | G3 passed |
|---|---|---|---|---|---|---|
| 0.25 | 29 | +$3,680.4 | -$61,546.3 | 38.81× | -0.2595 | **False** |
| 0.50 | 11 | +$1,341.9 | -$29,402.6 | 29.65× | -0.3151 | **False** |
| 1.00 |  7 |   +$952.3 | -$10,555.4 | 20.14× | -0.1972 | **False** |

λ=0.5 exit reasons: `rate_flip` 8, `directional_stop` 3. Forms: `directional_long` 10,
`directional_short` 1. The 3 hard-stop episodes realize exactly -1R each
(direction_pnl -$30,000 = 3 × -$10,000 = 3 × 1% of $1M capital).

## Verdict (honest)

- Sizing fix verified: directional notional = 0.5× capital (1% capital / 2% stop),
  `risk_usd` == exactly 1% capital (no more $1,000 = 0.1% misstatement).
- The 2% directional hard stop FIRES on real mark data and nets (direction_pnl).
- The λ gate correctly rejects nearly all naked directional entries.
- **The directional short/long form is NOT profitable in paper**: the hard stop wipes
  out 20-39× the funding earned at every λ, and G3 fails at every λ. Per the
  principal's F2 lock, leverage stays GATED (ENABLE_DELTA_NEUTRAL=False, 1× cap only)
  until the directional form proves profitable through G3 — it does not.
- Deep directional re-validation is bounded by mark history (~17 days of 5m bars now);
  the assetCtxs store accumulates real hourly mark/oracle going forward (F3), which
  will extend this window over time.