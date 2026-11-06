# HYP-16 (high-OI expansion + trend) — verdict (REAL OI history)

Date: 2026-11-06 (UTC)
Owner: backtester
Hypothesis: trading/strategies/Hypotheses/HYP-16-high-OI-expansion.md (pre-registered, thresholds FIXED)
Driver: scripts/gauntlet/revalidate_high_oi_expansion.py
Trial: data/gauntlet/trials.jsonl (HYP-16, param_hash 269c55b8…, universe_hash = sha256(sorted top-30 native perps))

VERDICT: H1 NULL (no OI→bigger-move expansion). H2 fails G4/G5 (apparent net
profit is trend-following beta, not the OI kernel). The coach's "high OI → ripe
for a big move" kernel has NO support, now testable for the first time on real OI.
This is the first honest run of HYP-16 — the prior attempt (2026-11-02) was
DATA-GATED on ~19.5h of OI; the full ~3.4y Hyperliquid OI archive is now local.

---

## 1. Data + universe (explicit)

- Source: /root/.hermes/market_data/hl_oi_hf/*.parquet — 42 monthly hourly files.
- 5,938,268 rows, 2023-05-20 02:00 → 2026-10-31 23:00 UTC, 553 markets.
- Filter: native perps only (dex == ''), drop null mark_price / open_interest →
  4,846,666 rows, 235 native coins.
- Universe: BTC, ETH, SOL + top-30 by mean open_interest_usd (BTC/ETH/SOL are
  ranks 1-3, so top-30 holds all three). 30 coins tested.
- Daily resample per coin: close = last mark_price, open = first mark_price,
  OI = last open_interest of the UTC day. mark_price is the sole price source
  (no separate bar join).
- Binding window: after the 90d trailing-percentile warmup, usable events span
  2023-08-21 → 2026-10-26.

---

## 2. H1 (expansion) — does high OI predict BIGGER moves? NO (null).

Metric: mean |forward return| over next 1-5 daily bars, conditional on extreme OI
(OI >= 90th pct of the coin's own trailing-90d), vs unconditional baselines.

| metric | value |
|---|---|
| regime mean \|move\| (1-5 bars) | 6.2484% (n=5,459) |
| baseline mean \|move\| (full ~3.4y) | 6.1651% (n=23,309) |
| baseline mean \|move\| (same window) | 6.2357% (n=22,372) |
| ratio regime / full | 1.0135 |
| ratio regime / same-window | 1.0020 |
| diff vs full (95% CI) | +0.0832% [−0.0929%, +0.2657%] |
| diff vs same-window (95% CI) | +0.0127% [−0.1645%, +0.1987%] |
| bootstrap p (regime ≤ full) | 0.1816 |
| bootstrap p (regime ≤ same-window) | 0.4556 |

Per-horizon ratio (regime/full): h1=1.0263, h2=1.0267, h3=1.0153, h4=1.0120,
h5=0.9996 — all clustered tightly around 1.0.

Interpretation: extreme OI is followed by moves that are statistically
INDISTINGUISHABLE from unconditional moves. Against the same ~3.2y window the
ratio is 1.002 (CI straddles zero, p=0.46); against the full sample it is 1.014
(p=0.18). Neither is significant. The coach's literal claim — "OI particularly
high → price ripe for a big move" — is a NULL. No expansion effect exists.

H1 KILL RULE TRIGGERED: extreme-OI mean |move| is NOT statistically larger.

---

## 3. H2 (directional) — net expectancy + cost, and where it comes from

Pre-registered entry: LONG when extreme OI AND close > SMA20. Exit: close < SMA20
or 5-bar time stop. Next-open fill (no look-ahead). One ±1x position per coin at
a time (state machine — no stacked leverage). Cost charged once per round trip.

| metric | value |
|---|---|
| n trades | 998 (SMA exits 380, time-stop 618) |
| gross mean return | +106.945 bps |
| cost (fail-closed 45bps taker) | 45.0 bps |
| NET mean @45bps | +61.945 bps |
| cost (fee_source 1x realistic) | 12.0 bps |
| NET mean @12bps | +94.945 bps |
| win rate (net@45) | 41.6% |
| PF (net@45) | 1.172 |
| sharpe | 0.050 |
| total R == sum(by-trade R) | 6.182 (reconciled) |

Net R > 0 under realistic fills (both 45bps fail-closed and 12bps 1x), so G4/G5
were escalated to per the pre-registered rule.

The control exposes where the profit actually comes from: running the SAME
strategy with the OI filter REMOVED (plain "close > SMA20 → long") gives
2,284 trades, net@45bps +60.803 bps, PF 1.177. The OI filter's marginal
contribution is +1.14 bps — essentially zero.

→ The H2 "edge" is entirely the SMA20 trend filter riding a ~3y bull market
(beta/drift), NOT the OI kernel. The coach's OI signal adds nothing on top of a
bare trend filter.

---

## 4. G4 (CPCV) + G5 (DSR/PBO) — escalation result

| gate | criterion | actual | verdict |
|---|---|---|---|
| G4 | CPCV 10th-pct split PF ≥ 1.0 | 0.805 | FAIL |
| G5 | DSR ≥ 0.95 | 0.741 | FAIL |
| G5 | PBO ≤ 0.30 | 0.4545 | FAIL |

- CPCV (N=12, k=2): 66 splits, 11 paths, agg_sharpe 0.0495; split PF
  median 1.144, 10th-pct 0.805, min 0.690. The 10th-pct fold PF < 1.0 — in a
  non-trivial share of chronologically-held-out blocks the strategy LOSES after
  cost, so there is no robust net edge.
- DSR 0.741 (deflated by N=121 prior trials in the ledger), PBO 0.455 — both
  outside the kill thresholds (DSR ≥ 0.95, PBO ≤ 0.30).

H2 KILL RULE TRIGGERED: G4 10th-pct PF < 1.0 AND G5 PBO > 0.30 / DSR < 0.95 →
no directional alpha. The SMA20 trend filter contributes nothing robust either.

---

## 5. Honest overall verdict vs the negative prior

The coach's kernel — "high OI → ripe for a big move" — fails on BOTH axes now
that real OI is finally testable:

1. Expansion (H1): high OI does not predict larger subsequent moves (same-window
   ratio 1.002, p=0.46; formally null).
2. Direction (H2): the extreme-OI + trend entry posts a nominal +62 bps net, but
   this is attributable to the SMA20 trend filter's long bias in a 2023-26 bull
   market — the OI filter adds only +1.1 bps (zero) — and it fails CPCV 10th-pct
   PF (0.805), DSR (0.741) and PBO (0.455).

This is consistent with, and now directly confirms, the negative prior: HYP-17's
funding-crowding proxy (H1 ratio 1.01 null, H2 net −40 bps) was not an artifact
of proxying. The underlying "crowded positioning → bigger move" mechanism is not
supported by the positioning data itself.

Caveat (honest): this is a ~3.2y window that is disproportionately a bull regime
(matching HYP-17's stated limitation). A distinct bear-regime test would need
more data than exists; nothing here suggests the OI kernel would resurrect there,
and the CPCV/PBO failure indicates the trend component is itself not robust.

Conclusion: the coach's "high OI → big move" kernel has NO real support. It
should not inform any live or paper decision. HYP-16 is now TESTED and REJECTED,
not just gated.