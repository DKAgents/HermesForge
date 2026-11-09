# HYP-36 — Polymarket longshot overpricing vs options-implied probabilities (Phase 1)

*Pre-registered 2026-11-09. Phase 1 = live cross-sectional snapshot + data-feasibility verdict.
Phase 2 (the >= 40-cluster time-series falsification) is DATA-GATED and not yet runnable.*

---

## 1. Verdict (short)

The longshot-overpricing direction is **confirmed in the current cross-section**, but the wedge
is **small and not yet demonstrated harvestable**. Mean longshot wedge = **+1.5 cents** (all 4
independent clusters positive), but the traded net after spread + capital charge is ~1–5 cents per
$1 at risk, and the effective sample is only **4 independent (underlying, expiry) clusters** — far
below the ≥40 required to falsify. **Not promotable; needs a historical price feed before the
falsification test is even possible.**

## 2. What was measured

- Snapshot UTC 2026-11-09 ~18:20Z. BTC spot $75,025 · ETH spot $2,179 (Deribit index).
- Universe: the live BTC/ETH price-level series on Polymarket ("reach"/"dip" = one-touch barriers;
  "What price will X hit by Dec 31 2026" and "…in November"). 90 open markets priced, 29 already
  resolved.
- Fair value: one-touch barriers priced under GBM (reflection principle) with the Deribit IV at
  the barrier strike (ATM fallback when the wing mark is degenerate); European digitals via
  Breeden-Litzenberger call spreads. r = 0.
- Signal: wedge = Polymarket "Yes" price − fair risk-neutral probability.

## 3. Wedge magnitude

| Bucket | n | Mean wedge |
|---|---|---|
| Longshot (fair ≤ 0.20) | 70 | **+0.0148** |
| Non-longshot (fair > 0.20) | 20 | −0.0232 |
| All | 90 | +0.0063 |

Per-cluster longshot wedge (all positive — direction is consistent, not one market driving it):

| Cluster (underlying, expiry) | n | Mean wedge |
|---|---|---|
| BTC · 25DEC26 | 12 | +0.0128 |
| BTC · 29JAN27 | 27 | +0.0154 |
| ETH · 25DEC26 | 12 | +0.0090 |
| ETH · 29JAN27 | 19 | +0.0188 |

**Independent clusters = 4.** (Effective sample is the number of distinct underlying×expiry
clusters, not the 90 contracts — outcomes share the BTC/ETH price path.)

## 4. Traded net per variant (hold-to-resolution, longshot bucket)

Net = (bid_Yes − fair) − capital charge (3.21% USDC APY × holding days). Buy-No / sell-Yes at the
bid; spread is the Polymarket no-Yes width. Top nets:

| Market | fair | Yes | Net / $1 at risk |
|---|---|---|---|
| BTC dip $55,000 (Dec 31) | 0.040 | 0.105 | +0.0555 |
| BTC dip $62,500 (Nov) | 0.054 | 0.115 | +0.0542 |
| BTC dip $50,000 (Dec 31) | 0.007 | 0.065 | +0.0485 |
| ETH dip $1,500 (Dec 31) | 0.078 | 0.131 | +0.0415 |
| ETH dip $1,250 (Dec 31) | 0.008 | 0.065 | +0.0375 |

Median longshot net ≈ +1.3 cents; the tail is thin and several are ≤ 0 after spread. Exit-on-
gap-close vs hold-to-resolution, and the delta-hedged (HL perp) variant, are **pre-registered but
not computable** from a single snapshot (they need a price path over the holding period).

## 5. Two findings that complicate the thesis

1. **The biggest single wedge is a HIGH-probability down-touch, not a longshot.** ETH dip $2,100
   (21d): fair 0.793, Polymarket "Yes" 0.945 → **+15.2 cents**. The top 6 wedges are all
   *down-touch* ("dip") markets. This looks as much like a "Yes bias on dips" / put-skew
   mis-reflection as the favorite-longshot bias.
2. **Deep-longshot overpricing is bounded by the tick.** Markets with fair ≈ 0.000 quote 0.002–
   0.013 on Polymarket — the absolute "overpricing" is the minimum tick, not a harvestable gap.
   The +1.5-cent longshot mean is carried by the fair ∈ [0.02, 0.20] sub-bucket, not the tail.

## 6. Data-feasibility (why the falsification cannot run yet)

- **Polymarket exposes no free historical price time-series** (only current book + recent trades;
  full history is a paid Goldsky/Data API tier). A realized-edge test over ≥40 independent expiry
  clusters needs that feed.
- **The stored Deribit iv_surface.db holds ATM IV + DVOL only** (~8 days, no smile history). The
  full strike smile used here is pulled live; a backtest would need a smile-history store (US-231
  only backfills ATM-straddle premiums, not the smile).
- **Deribit deep-wing marks are degenerate** (far-OTM strikes carry >100% IV; used only when sane,
  ATM fallback otherwise) — a second reason a rigorous tail test needs better wing data.

## 7. Falsification status

- Mean realized edge per $ at risk **not measurable** (no time-series).
- Cluster-robust CI: not computable at n = 4 clusters (requires ≥40).
- Longshot bias direction: **present but not harvestable** at this capacity on the evidence
  currently obtainable.

**Do not promote. Do not trade (LIVE off throughout).** Next gate: a historical Polymarket price
feed + a Deribit smile-history store, then re-run the falsification over ≥40 independent expiry
clusters.
