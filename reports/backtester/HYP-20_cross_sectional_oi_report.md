# HYP-20 (cross-sectional OI/funding momentum) — verdict

Date: 2026-11-06 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-20-cross-sectional-oi-momentum.md (pre-registered, thresholds FIXED, no tuning)
Driver: scripts/gauntlet/revalidate_hyp20_cross_sectional_oi.py
Trials: data/gauntlet/trials.jsonl (HYP-20 x3: H1 param_hash e7267b84…, V-A 8140ae56…, H2 07b442b0…; chain intact, verified OK)

VERDICT: the question HYP-16 never answered — does a coin's positioning RELATIVE
to other coins predict its RELATIVE future return — is YES GROSS, NO NET.
Cross-sectional OI momentum has a real, positive, price-independent gross signal
(+11.5 bps/reb, momentum direction, as hypothesized), but it does NOT clear the
pre-registered 45bps both-legs cost (nor the realistic 24bps both-legs cost).
Kill rule H1 fires. V-A (30d) is gross-reversal/null. H2 (funding) is not
data-gated but its signal is degenerate (57% of cells pinned at HL's default
rate) and fails cost either direction.

---

## 0. Data reality (read first)

- OI: /root/.hermes/market_data/hl_oi_hf/*.parquet, hourly OI+mark, 42 monthly
  files. After native-only filter (dex == '') and drop-null: 235 native perp
  coins, 1261 daily bars (2023-05-20 -> 2026-10-31). Daily resample: open =
  first mark, close = last mark, OI = last hourly OI.
- Funding: hl_funding/funding.db, 35 coins, 406d span (~405d, 2025-09-27 ->
  2026-11-06). 405d > 200d floor -> H2 NOT data-gated (it runs).

Cost model (single owner = fee_source + pre-registered hurdle, charged ONCE):
- Hurdle (pre-registered): 45bps fail-closed taker PER LEG, charged to BOTH the
  long and short leg of the spread = 90bps per round trip. (45bps = repo's
  established "4x" conservative stress hurdle, matching HYP-16.)
- Realistic (honesty cross-check): fee_source round-trip 12bps (taker 4.5x2 +
  slip 2.5 + funding 0.5) PER LEG, x2 legs = 24bps per round trip.

Fill: next-open both sides. Signal at close[t] uses OI through day t only;
enter open[t+1], exit open[t+1+hold]. No look-ahead. ±1x long/short, no leverage.
LIVE off. Reconcile total R == sum(by-trade R) verified True in every config.

---

## 1. H1 (primary) — cross-sectional 7d OI log-change rank, decile spread

Holding 1d (daily rebalance), n=1237 rebalances, mean 141 coins/day, ~13.7/leg:

| metric | value |
|---|---|
| gross spread (mean/reb) | +11.543 bps (annualized ~+4213 bps) |
| sign | MOMENTUM (positive — rising OI -> relative strength) |
| net @ 90bps hurdle (both legs) | -78.457 bps/reb |
| net @ 24bps fee_source (both legs) | -12.457 bps/reb |
| net sharpe @ hurdle | -0.290 |

Holding 5d (turnover sensitivity), n=1233 rebalances:

| metric | value |
|---|---|
| gross spread (mean/reb) | +2.470 bps (annualized ~+180 bps) |
| net @ 90bps hurdle | -87.530 bps/reb |
| net @ 24bps fee_source | -21.530 bps/reb |

Two facts:
1. Gross is POSITIVE and in the MOMENTUM direction (the hypothesized sign). The
   relative-positioning signal is real — not the time-series null HYP-16 found.
2. It is a FAST, 1-day effect: the 5d hold captures only +2.5 bps over five days
   vs +11.5 bps over one, so the signal decays/partially reverts within days and
   cannot be harvested by slowing turnover.
3. It does NOT clear cost at any tier: -78 bps/reb at the hurdle; even at
   realistic 24bps it is -12.5 bps/reb. H1 KILL RULE FIRES (net <= 0 net of
   45bps both-legs). G4/G5 overfit controls are NOT run (pre-registered: only
   escalate if net R > 0).

## 2. V-A (pre-committed variant) — 30d OI log change

| hold | gross/reb | net @90bps | net @24bps | sign |
|---|---|---|---|---|
| 1d | -3.387 bps | -93.387 | -27.387 | REVERSAL |
| 5d | +1.778 bps | -88.222 | -22.222 | momentum |

The slower 30d signal is gross-REVERSAL at 1d (-3.4 bps) and a negligible
+1.8 bps at 5d. No cost-surviving edge. Consistent with the 7d finding that the
signal is near-horizon only.

## 3. H2 (secondary) — cross-sectional funding rank (35 coins)

Data gate: PASS (405d usable > 200d floor). But a data-quality finding dominates:

- 57.2% of all (coin,day) funding cells sit at the modal rate 0.00001250/hr —
  HL's DEFAULT 8h-baseline funding (0.01%/8h), i.e. no directional imbalance.
  Cross-sectional funding rank is therefore dominated by massive ties plus a
  handful of outlier coins; the tail deciles are near-arbitrary.

| direction | gross/reb | net @90bps | net @24bps |
|---|---|---|---|
| continuation (long top funding) | +13.219 bps | -76.781 | -10.781 |
| fade (mirror, exact negation) | -13.219 bps | -103.219 | -37.219 |

Gross continuation is positive (high funding -> relative outperformance),
matching HYP-17's "funding -> continuation" direction. But net is deeply
negative at the hurdle and still -10.8 bps/reb at realistic cost. Fade is the
mirror and also fails. H2 KILL RULE FIRES.

## 4. Independence check (supporting, not pre-registered)

Cross-sectional corr(7d OI log change, 7d price log change) = 0.13 (mean daily,
n pooled). The OI signal is NOT price momentum in disguise — it carries largely
independent relative-positioning information. This makes the positive gross a
genuine signal, not a re-labeled xsmom.

## Final verdict (honest)

The thesis "relative positioning -> relative returns" is: SUPPORTED GROSS,
REJECTED NET.

1. H1 (7d OI): positive gross momentum (+11.5 bps/reb), independent of price
   (corr 0.13), but does NOT clear 45bps both-legs (net -78 bps/reb) nor
   realistic 24bps (net -12.5 bps/reb). KILL fires.
2. V-A (30d OI): gross reversal/null. KILL fires.
3. H2 (funding): not data-gated, but the funding signal is degenerate (57% at
   default rate); continuation gross +13 bps fails cost; fade fails. KILL fires.

So relative positioning DOES predict relative returns (the answer HYP-16 could
not give) — but the edge is small (+11-13 bps gross), short-horizon (decays
within days), and economically non-tradable once both legs of a daily-rebalanced
spread pay taker. Higher-turnover cost, not the signal, is the binding constraint.
The thesis fails its pre-registered kill rule and is NOT promotable; it closes
the cross-sectional-positioning class as a cost-surviving alpha on real data.

No promotion. No paper-forward. LIVE off. Report is genuine in-sample verdict,
not a data-gate punt (OI 1260d x 235 coins full coverage; funding 405d x 35).