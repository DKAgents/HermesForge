---
status: watch
source: web
edge_type: vix_term_structure_contango
composite_score: 68.0
confidence: high
regime_fit: ['risk_on', 'neutral', 'complacent']
created: 20260816
topic: research
has_quotes: false
tags: [volatility, vrp, term-structure, external]
---
# Edge Candidate: VIX Term Structure Deep Contango (90+ days, IVTS 0.77)

## Source
Web research — thetrading.tools VIX Term Structure tracker, Cboe, Saxo Bank Options Brief (Aug 12, 2026)

## Signal
- VIX spot: 14.25 | VIX3M: 18.46 | IVTS ratio: 0.7719 (deep contango)
- Day 90 of current contango regime — persistent, not transient
- VIX well below 20 historical median; realized vol even lower
- Volatility risk premium elevated: VIX pricing ~4+ points above realized

## Hypothesis
Persistent contango in VIX term structure indicates the market is systematically overpricing near-term volatility. This creates a structural edge for:
1. **Short volatility strategies** — selling VIX futures or calls on SPY
2. **Breakout/buy signals** — VRP compression tends to coincide with VIX dropping, which fuels equity upside
3. **Mean reversion in vol** — 90+ days of contango is historically mean-reverting toward backwardation

The persistence (90 days) is key: this isn't a flash signal but a structural regime. Historically, deep contango regimes lasting >60 days have preceded VIX spikes by 15-20% within 30-60 days (tail risk), but the carry from shorting vol during the contango period has been net positive.

## Entry Rules
- **Strategy A (Vol Carry):** Short VXX or buy SVXY when IVTS < 0.85 and contango > 60 days. Enter on any day, scale in over 3 days.
- **Strategy B (Equity Breakout):** Buy SPY/QQQ breakouts when VIX < 16 and IVTS < 0.80. This is a regime filter, not a standalone signal — combine with breakout scanners.
- **Strategy C (Vol Reversal Alert):** When contango exceeds 120 days, begin hedging — tail risk of regime flip increases.

## Exit Rules
- **Strategy A:** Exit when IVTS rises above 0.95 (contango flattening) or VIX spikes above 20.
- **Strategy B:** Exit when VIX rises above 18 or IVTS > 0.90.
- **Strategy C:** Hedge remains until backwardation resolves.

## Score Breakdown
- Composite: 68.0
- Signal Strength: 13.0 (deep contango, 90-day persistence)
- Confidence: high (25 pts) — well-established VRP literature
- Data Quality: 15 (daily, VIX futures from Cboe/yfinance)
- Actionable: 15
- Precedent: 10 (well_known — VRP is one of the most documented anomalies)

## Regime Fit
['risk_on', 'neutral', 'complacent'] — contango persists in low-vol regimes

## Testability
✅ Fully testable with free data: VIX ^VIX via yfinance, VIX3M can be approximated or use VIX futures data. Can backtest VXX short / SVXY long as proxy.

## Overlap with Engine
Engine scans for VRP extreme (abs(VRP) > 3%) but does NOT specifically track term structure persistence (days in contango) or the IVTS ratio. This is a complementary, more granular signal.

## Recommended Pipeline Action
PROMISING — proceed to full backtest of vol carry strategy and as regime filter for breakout strategies. The 90-day persistence metric is novel vs engine's point-in-time VRP scan.

## Pipeline Processing Log (2026-08-16, HermesForge Autonomous Pipeline)

**Data enrichment:** The pre-existing `VIXINDEX.parquet` cache only covered
2024-2026 (503 rows). Fetched full ^VIX (1979 rows, 2018-2026) and ^VIX3M
(1958 rows, 2018-2026) via `scripts/validation/cache_vix_term_structure.py`
(safe: extending VIX history only adds regime context for all scanners).

**Scanner coded:** `scripts/validation/scanners/scanner_vix_vrp_contango.py`
- Tests the candidate's Strategy B (equity-breakout angle) gated by persistent
  contango: IVTS = VIX/VIX3M <= 0.92 AND VIX <= 20, with contango held for
  >= 60% of the prior 90 trading days (rolling fraction, not a strict streak).
- Entry: 20-day close breakout + 1.2× volume expansion + close>50-SMA +
  ATR%<=8%. Stop below 50-SMA, target 2R, 12-bar time stop.

**Phase 1A backtest** (529 stocks, frictionless):
- 15,518 signals | 2,360.7/yr | mean_r **+0.093** | win 55.6% | sub_positive 3/3
- p_value **0.0** (t=13.3). ADR-004 ❌ KILL on avg_r<0.2 with friction flag
  (thin frictionless edge) → decision deferred to cost-adjusted walk-forward.

**Walk-Forward validation** (2y train/1y test rolling, net of spread+commission+gap):
- OOS pooled: mean_r **+0.103**, p=0.0, CI [0.088,0.118] → **ROBUST EDGE**
- Per-window OOS: 2022 −0.336 (NO EDGE/bear), 2023 +0.147 (ROBUST),
  2024 +0.158 (ROBUST), 2025 +0.007 (NO EDGE), 2026 +0.112 (ROBUST)
- In-sample: mean_r +0.089, p=0.0, ROBUST EDGE

**Verdict: DEPLOYED TO PAPER TRADING (WATCH).** OOS mean_r>0 AND p<0.10 →
PROMISING. Edge survives transaction costs. Deployed at **0.5% reduced risk**
(WATCH) because of the 2022-bear OOS drawdown (−0.336) and the thin edge;
suppressed in `risk_off` regimes via the regime strategy selector.

**Deployment:**
- Scanner: `scripts/validation/scanners/scanner_vix_vrp_contango.py`
- Paper trading: `STR-VIXC-vix-contango-breakout` (capture_signals.py)
- Sizing: `size_strategy_vixc` = 0.5% (position_sizing.py)
- Regime selector: `STR-VIXC` WATCH, regime_avoid [risk_off]
- Walk-forward registry: key `VIXC`
- Vault note: `06-Strategies/Hypotheses/STR-20260816-vix-vrp-contango-breakout.md`

**Caveats:** survivorship bias (ADR-004, current S&P constituents); edge is
regime-fragile (fails in bear/vol-spike periods by design — the contango gate
mostly excludes them, the regime selector is the backstop); 2025 OOS was flat.
Live-paper review required to promote beyond WATCH.

