---
id: STR-20260816-vix-vrp-contango-breakout
type: strategy
status: watch
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: low_vol_contango
core_idea: breakout
confidence: medium
publish_enabled: false
publish_channel: stocks
evidence_links:
  - CAND-20260816-vix-contango-persistence
last_reviewed: 2026-08-16
created: 2026-08-16
updated: 2026-08-16
origin: HermesForge Autonomous Strategy Pipeline (cron)
tags: [strategy, breakout, vix, vrp, term-structure, contango, regime-filter, autonomous-pipeline]
topic: strategies
has_quotes: false
source: HermesForge Autonomous Pipeline
scanner_module: scanner_vix_vrp_contango
scanner_alias: scan_vixc
strategy_id: STR-VIXC-vix-contango-breakout
---

# VIX Term-Structure Contango Breakout (Long-Only) v1.0

## Origin

Autonomously coded, backtested, and walk-forward validated by the HermesForge
Autonomous Strategy Pipeline (cron job, 2026-08-16) from staged edge candidate
`CAND-20260816-vix-contango-persistence`. No human in the loop for this run;
deployment to paper trading is at WATCH-level risk pending live-paper review.

## Thesis

Persistent contango in the VIX term structure (VIX spot / VIX3M ≤ ~0.92 with
spot VIX calm ≤ ~20) indicates the market is systematically overpricing
near-term volatility — a structural, well-documented volatility-risk-premium
(VRP) regime. In this regime, equity upside breakouts are more likely to
follow through: VRP compression coincides with VIX drifting lower, which fuels
equity momentum. The "persistence" requirement (contango has been the *norm*
recently, not a flash) filters out transient spikes.

The core wager: 20-day breakouts taken during a *persistent* low-vol contango
regime carry a small but statistically robust positive expectancy, net of
transaction costs, that does not exist unconditionally.

## Signal Rules

Regime gate (computed once from cached ^VIX and ^VIX3M daily series):
- `IVTS = VIX_spot / VIX3M`
- `contango_day = (IVTS <= IVTS_MAX) AND (VIX_spot <= VIX_MAX)`
- `contango_active = contango_day AND (rolling-mean(contango_day, PERSIST_WINDOW) >= MIN_PERSIST_FRAC)`
- A rolling **fraction** (not a strict all-N-days streak) is used because VIX
  spikes would otherwise break the streak and kill the regime even when
  contango is the dominant state.

Per-ticker entry (all required, signal day i):
- `close[i] > max(prior 20 closes)` (20-day breakout, excl. today)
- `volume[i] > 1.2 × 20-day avg volume` (volume expansion)
- `close[i] > 50-SMA` (intermediate trend agreement)
- `ATR% of price <= 8%` (liquidity/volatility filter)

Risk/reward & exit (forward-scan, max 12 bars):
- `entry = close[i]`
- `stop  = min(low[i], 50-SMA[i]) - 0.5 × ATR(i)`  (below 50-SMA)
- `target = entry + 2.0 × risk`
- exit `target` / `stop` / `time`

## Default Parameters

| Param | Default | Walk-forward grid |
|---|---|---|
| `IVTS_MAX` | 0.92 | 0.90, 0.92, 0.95 |
| `VIX_MAX` | 20.0 | 18, 20 |
| `PERSIST_WINDOW` | 90 | (fixed) |
| `MIN_PERSIST_FRAC` | 0.6 | 0.5, 0.6 |
| `MIN_RR` | 2.0 | 2.0, 3.0 |
| `BREAKOUT_LOOKBACK` | 20 | (fixed) |
| `MAX_BARS_HELD` | 12 | (fixed) |

## Backtest & Validation Results

**Phase 1A (frictionless, 529-stock universe, 2019-04 → 2026-08):**
| Metric | Value |
|---|---|
| Total signals | 15,518 |
| Signals/year | 2,360.7 |
| Mean R | **+0.093** |
| Median R | +0.077 |
| Win rate | 55.6% |
| Sub-periods positive | 3/3 |
| p-value (t-test, H0: mean R=0) | **0.0** |
| ADR-004 classification | ❌ KILL (avg R < 0.2; **friction flag**) |

Phase 1A mean R is positive and highly significant but *thin* (0.093), below
the ADR-004 PASS band — the friction flag was raised. This is why walk-forward
(with transaction costs) was the deciding step.

**Walk-Forward (2-year train / 1-year test, rolling; quick grid; net of
spread+commission+gap costs):**
| Window | OOS mean R | OOS n | Verdict |
|---|---|---|---|
| 2022 (bear) | **−0.336** | 420 | NO EDGE |
| 2023 | +0.147 | 3,543 | ROBUST EDGE |
| 2024 | +0.158 | 3,639 | ROBUST EDGE |
| 2025 | +0.007 | 2,072 | NO EDGE |
| 2026 | +0.112 | 2,924 | ROBUST EDGE |
| **OOS pooled** | **+0.103** | 12,598 | **ROBUST EDGE** (p=0.0, CI [0.088, 0.118]) |
| In-sample | +0.089 | 15,518 | ROBUST EDGE |

**Decision:** OOS pooled mean R = +0.103 > 0 AND OOS p-value = 0.0 < 0.10 →
**PROMISING → deployed to paper trading** at WATCH-level (reduced) risk.

## Key Risks & Caveats

- **Regime fragility:** The edge concentrates in calm/risk-on periods. The 2022
  bear-market OOS window is sharply negative (−0.336). The strategy is
  **suppressed in `risk_off` regimes** via the regime strategy selector
  (`regime_avoid: ["risk_off"]`). Do NOT run it into a VIX spike / equity
  downtrend — the contango gate itself mostly prevents this, but the selector
  is a second line of defense.
- **Thin edge:** Mean R ~0.10 net of costs is real but small. Slippage
  assumptions matter; live-paper must confirm the spread/commission model.
  2025 OOS was flat (+0.007) — the edge is not present every year.
- **Signal volume:** ~2,400 signals/year is high; the paper-trading engine must
  enforce portfolio heat/concurrency caps to avoid over-concentration in
  correlated low-vol breakouts.
- **Survivorship bias (ADR-004):** universe is current S&P constituents; the
  result could be mildly flattered. Acceptable for Phase 1A/walk-forward
  reality-check; live-paper is the real test.
- **Data dependency:** requires ^VIX and ^VIX3M daily history cached at
  `~/.hermes/market_data/VIXINDEX.parquet` and `VIX3M.parquet` (refreshed by
  `scripts/validation/cache_vix_term_structure.py`). VIX3M lags ~1 month; the
  scanner forward-fills, acceptable for a regime gate.

## Deployment

- **Scanner:** `scripts/validation/scanners/scanner_vix_vrp_contango.py`
- **Paper trading:** `scripts/paper_trading/capture_signals.py` →
  `STR-VIXC-vix-contango-breakout` (id `STR-VIXC`)
- **Position sizing:** `scripts/paper_trading/position_sizing.py` →
  `size_strategy_vixc` = **0.5% base risk** (WATCH, below the 1% single-idea ceiling)
- **Regime selector:** `scripts/research/regime_strategy_selector.py` →
  `STR-VIXC` status WATCH, `regime_best` [risk_on, neutral, complacent],
  `regime_avoid` [risk_off]
- **Walk-forward registry:** `scripts/validation/walk_forward.py` → key `VIXC`

## What Would Change My View

- Live-paper showing mean R ≤ 0 over 100+ signals → demote to KILLED.
- A return to sustained VIX backwardation (IVTS > 1.0) collapses the regime and
  the signal count; this is expected, not a failure of the strategy.
- Evidence that the 2022-bear failure generalizes to any >20 VIX / vol-spike
  regime → tighten `VIX_MAX` or add a hard VIX-slope filter.

## Related

- Edge candidate: [[CAND-20260816-vix-contango-persistence]]
- Related (existing): the engine's VRP-extreme scanner; this strategy adds the
  **term-structure persistence** angle the point-in-time VRP scan lacks.