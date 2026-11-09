---
hypothesis_id: HYP-35
backtester: hermes-forge (backtester)
status: MECHANISM-UNKNOWN (first gate failed — not promoted)
date: 2026-11-09
param_hash: 960dc46ff4b1fbfc   (diagnostic run only — no trial logged to ledger)
venue: hyperliquid (xyz HIP-3 index-perp basket)
instruments: xyz:NVDA, xyz:GOOGL, xyz:TSLA, xyz:AMD, xyz:META, xyz:BRENTOIL, xyz:CL, xyz:SKHX, xyz:XYZ100
data: live probe of api.hyperliquid.xyz/info (candleSnapshot 15m/1h + fundingHistory + l2Book). No fabrication.
---

# HYP-35 — Short the xyz index-perp in the 13–15 UTC window: MECHANISM-UNKNOWN verdict

VERDICT: MECHANISM-UNKNOWN — the blocking gate failed. No structural calendar /
funding / rebalance mechanism behind the 13–15 UTC window could be identified,
and the follow-on diagnostic (run to characterize the artifact, NOT as a gated
backtest) shows the supposed "75.6% win / 5.2:1" does not reproduce. It is a
fat-tailed short-beta artifact on high-vol US equity index-perps, not a portable
edge. Consistent with the prior. NOT promoted; no trial logged.

---

## 1. The exact market (identified)

The `xyz:` namespace is Hyperliquid's index/marketcap perpetuals (HIP-3 builder
markets): equities (`xyz:NVDA`, `xyz:GOOGL`, `xyz:TSLA`, `xyz:AMD`, `xyz:META`),
commodities (`xyz:BRENTOIL`, `xyz:CL`), and marketcap indices (`xyz:SKHX`,
`xyz:XYZ100`). They are NOT in the standard `meta` universe (235 native perps);
they live in a separate namespace but are fully queryable via
`{"type":"candleSnapshot","coin":"xyz:..."}` and `fundingHistory`. The trader
0x024294c53a's "basket" is this class of names.

## 2. Mechanism investigation (the blocking gate)

I tested the three candidate mechanisms directly. None is the driver.

(a) Funding settlement — RULED OUT. `fundingHistory` for `xyz:NVDA` returns 24
    entries/day (hourly, continuous), premium-keyed (funding ~ premium), of
    magnitude ~0.05–0.13 bps/hr. There is no daily settlement event, and no
    funding discontinuity at 13–15 UTC. Funding is negligible either way.

(b) Index rebalance — NO EVIDENCE. A daily composition/mark reweight would show a
    sawtooth discontinuity in premium or mark at a fixed hour. The day-level
    premium profiles are continuous and noisy with no fixed-hour reset.

(c) Mark-vs-oracle divergence — PRESENT BUT NOT AN EDGE. `xyz:NVDA` trades at a
    persistent POSITIVE premium (perp > oracle), mean ~+1.9 bps, with an apparent
    peak at 15 UTC (~+3.6 bps). But this is (i) tiny (~2 bps), (ii) present all
    day (not localized to 13–15), and (iii) outlier-driven — the "15 UTC peak" is
    a handful of volatile days (e.g. one day shows +19.9 bps at 15:00, another
    −2.7 bps), not a stable daily pattern. A ~2 bps premium reversion cannot
    explain a 5.2:1 / 75.6% / $1.05M result, and is swamped by ~10.7 bps of cost.

(d) The honest residual explanation — DIRECTIONAL SHORT-BETA. The 13–15 UTC window
    is 8–10 AM ET (US pre-market + equity open). Shorting a basket of high-vol
    US-equity index-perps on a fixed schedule has positive expectancy only when
    the underlying falls hard on enough days (fat right tail on the short). That
    is beta with a time habit, not a mechanical calendar edge.

## 3. Diagnostic backtest (characterization only — gate already failed)

Rule as pre-registered (NOT tuned): short each of 13:00 / 14:00 / 15:00 UTC,
cover 2.6h later.

xyz:NVDA, 15m candles, recent ~53 days, 158 trades:
- win rate 46.8% (claimed: 75.6%), median return −1.44 bps, R:R 2.20 (claimed 5.2).
- mean +18.69 bps is entirely a few large wins (max +571 bps); the median trade
  LOSES. This is the overfit signature the prior predicted.

Full-history control (1h, ~208 days, 624 trades/coin), basket:
  coin         gross mean   win%
  xyz:AMD        −12.08    45.4
  xyz:BRENTOIL    −7.76    47.1
  xyz:CL          −9.88    48.9
  xyz:GOOGL       −2.86    47.1
  xyz:META        −2.28    50.3
  xyz:SKHX        −8.21    44.7
  xyz:TSLA        −8.94    48.7
  xyz:XYZ100      −0.74    43.8
  (every non-NVDA name is net NEGATIVE; the claimed edge does not generalize)

Hour-of-day control (xyz:NVDA, full history): a consistent 2.6h-short is not
special to 13–15 UTC — hour 18 (+8.09 bps) and hour 12 (+5.59) outrank hour 13
(+6.27) by mean, and hours 14/15 are +2.55 / +0.53 bps (noise). There is no
preferential 13–15 UTC calendar effect.

## 4. Cost (xyz HIP-3 market — flagged wider than native)

Round-trip ≈ 10.7 bps: taker 4.5 bps × 2 + crossing the ~1.7 bps xyz spread
(measured via `l2Book`: native perps run ~0.1–0.5 bps, so this is materially
wider) + ~0.1 bps funding (a small credit to the short, negligible). Net of cost:
the basket average is ≈ −17 bps/trade; NVDA's fat-tail mean also turns negative
on a per-trade basis (median −12 bps net). Nothing survives cost.

## 5. Honest verdict

NOT a real calendar/funding window edge. MECHANISM-UNKNOWN at the gate, and the
diagnostic confirms it is an already-priced artifact / too-thin-sample / short-beta
on high-vol names — exactly the prior's expectation. The high win rate was an
artifact of one trader's captured fills (the fill truncation noted in the
reverse-engineering report), not a reproducible rule.

Disposition: NOT PROMOTED. No trial written to data/gauntlet/trials.jsonl
(gate-failed result; a bare "short at 13:00" trial would itself be the data-mined
artifact the gate forbids). G4 (robustness) fails on the cross-coin control;
G5 (no-tuning) held — nothing was tuned, live is OFF.