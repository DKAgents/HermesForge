# HYP-16 robustness sweep — verdict (pre-registered, FIXED variations)

Date: 2026-11-06 (UTC)
Owner: backtester
Pre-registration: trading/strategies/Hypotheses/HYP-16-robustness-sweep.md (FIXED before run; no post-hoc additions/tuning)
Primary hypothesis: trading/strategies/Hypotheses/HYP-16-high-OI-expansion.md
Driver: scripts/gauntlet/sweep_hyp16_robustness.py
Ledger: data/gauntlet/trials.jsonl (3 new variation entries — V-A/B/C — fresh param_hash each; integrity OK, 125 entries total)

VERDICT: HYP-16 NULL IS CONFIRMED ROBUST across all three pre-committed
variations. No variation flips either sub-hypothesis into a live edge.

---

## 1. Data + universe (identical to primary run)

- Source: /root/.hermes/market_data/hl_oi_hf/*.parquet (42 monthly hourly files,
  2023-05-20 -> 2026-10-31 UTC; native perps = dex == '').
- Daily resample per coin: close = last mark_price, OI = last open_interest; drop
  null mark/OI. Universe = BTC, ETH, SOL + top-30 by mean open_interest_usd (30 coins).
- Binding window (after 90d trailing-percentile warmup): events span
  2023-08-21 -> 2026-10-26.
- No look-ahead (rotate-only trailing percentile/SMA, next-open fill), no
  leverage (+1x or flat), LIVE off, 45 bps fail-closed taker charged once per
  round trip.

The BASELINE row recomputed here reproduces the primary trial 269c55b8… exactly
(H1 ratio 1.0020, p=0.4556; H2 net@45bps +61.95; OI-marginal +1.14 bps),
confirming driver fidelity before the variations are read.

## 2. Variations (pre-committed, each in isolation)

- BASELINE: OI >= 90th pct (trailing 90d) AND close > SMA20; exit close < SMA20
  or 5-bar stop.
- V-A: SMA20 -> SMA50 (rest identical).
- V-B: 90th pct -> 80th pct (rest identical).
- V-C: 90th pct -> 95th pct (rest identical).

## 3. Results — compact table

H1 = extreme-OI |move| over next 1-5 daily bars vs unconditional baseline,
reported as ratio + bootstrap p, BOTH same-window (regime-confounding-free) and
full-sample. H2 = net expectancy @45bps fail-closed taker, plus the SMA-only
control (OI filter removed, SAME SMA window) to isolate the OI filter's marginal
contribution.

| variant | H1 ratio (same-win) | H1 p (same-win) | H1 ratio (full) | H1 p (full) | H2 net@45bps | OI-marginal bps |
|---|---|---|---|---|---|---|
| BASELINE (90/20) | 1.0020 | 0.4556 | 1.0135 | 0.1816 | +61.95 | +1.14 |
| V-A (90/50)      | 1.0020 | 0.4556 | 1.0135 | 0.1816 | +67.11 | -17.02 |
| V-B (80/20)      | 0.9809 | 0.9351 | 0.9914 | 0.7583 | +96.22 | +35.41 |
| V-C (95/20)      | 1.0176 | 0.1706 | 1.0308 | 0.0410 | +53.33 | -7.47 |

Event counts (H1): BASELINE/V-A 5,459; V-B 8,405; V-C 3,708.
H2 trade counts: BASELINE 998; V-A 953; V-B 1,329; V-C 772.

## 4. Interpretation (pre-committed rule applied)

H1 (expansion — "high OI predicts bigger moves"):
Same-window ratios cluster 0.98-1.02 with p = 0.46, 0.94, 0.17 — all >> 0.05.
The single borderline full-sample p (V-C = 0.041) is a regime-confounded
artifact: its regime-free same-window p is 0.17 (not significant), and V-C's
tighter threshold merely selects fewer events (3,708) whose full-sample mean is
biased by the bull-heavy 2023-26 window. V-B (looser OI) actually predicts
slightly SMALLER moves (ratio 0.98, p=0.94). There is no expansion effect at any
threshold. H1 KILL RULE confirmed at every variation.

H2 (OI filter marginal contribution):
The OI filter's marginal net edge vs its own SMA-only control is +1.14, -17.02,
+35.41, -7.47 bps across the four settings — it wanders around zero with NO
monotonic dose-response in the OI threshold (90->80 is +35, 90->95 is -7). The
one larger reading (V-B +35.41 bps) is NOT the hypothesized kernel: V-B's H1 is
still null (ratio 0.98, p=0.94), so the "high OI -> bigger move" mechanism is
absent at 80th too. The +35 bps is a threshold-dependent filter excursion (looser
OI dropping some losing SMA20-trend trades in this single bull-regime window),
not a robust edge.

## 5. Verdict (plain)

The HYP-16 null is CONFIRMED ROBUST across the three pre-committed variations.
- H1 stays ~1.00 with p >> 0.05 everywhere (same-window p 0.17-0.94). The coach's
  "OI particularly high -> price ripe for a big move" claim has no support at any
  OI threshold or trend speed tested.
- H2's OI-filter marginal contribution stays ~0 (or negative), non-monotonic, and
  the only non-zero reading (V-B +35 bps) is uncorroborated by H1 and is
  threshold/regime noise — it is reported honestly but NOT promoted, consistent
  with the pre-committed rule that a robustness sweep is not an edge discovery.

HYP-16 is CLOSED with higher confidence: high relative OI is not predictive of
larger subsequent moves and adds nothing robust to a bare trend filter. This
sweep found no scenario that clears; the null survives sensitivity testing.