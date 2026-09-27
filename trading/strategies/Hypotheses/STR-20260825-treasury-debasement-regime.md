---
id: STR-20260825-treasury-debasement-regime
type: strategy
status: watch
asset_class: crypto
trade_style: swing
timeframe: daily
market_regime: risk_on
core_idea: regime_trade
confidence: low
publish_enabled: false
publish_channel: crypto
evidence_links:
  - CAND-20260825-treasury-buyback-debasement-regime
last_reviewed: 2026-08-25
created: 2026-08-25
updated: 2026-08-25
origin: HermesForge Autonomous Strategy Pipeline (cron)
tags: [strategy, macro, crypto, btc, debasement, treasury, regime-trade, autonomous-pipeline]
topic: strategies
has_quotes: false
source: HermesForge Autonomous Pipeline
scanner_module: scanner_treasury_debasement
scanner_alias: scan_debase
strategy_id: STR-DEBASEMENT-treasury-buyback
scan_mode: batch
---

# Treasury Buyback / Dollar Debasement Regime Trade v1.0

## Origin

Autonomously coded, backtested, and walk-forward validated by the HermesForge
Autonomous Strategy Pipeline (cron job, 2026-08-25) from staged edge candidate
`CAND-20260825-treasury-buyback-debasement-regime`. No human in the loop.

## Thesis

The US Treasury's explicit yield-management intervention (doubling bond buybacks
from $2B to $4B on Aug 19, 2026) has activated a structural dollar debasement
regime. When a G7 Treasury engages in yield suppression without addressing
fiscal fundamentals, the FX market reprices debasement risk into hard assets.

The cross-asset pattern: DXY weakening + Gold rallying + BTC in structural
uptrend. When these three conditions align, the signal is a macro regime change
favoring BTC as a hard asset / debasement hedge. Entry on pullbacks to the
20-day moving average during the active regime.

**This is a regime trade — it fires infrequently (~11 signals/year) but aims for
high R-multiple when it does (avg R ≈ +0.30 before costs).**

## Signal Rules

**Regime gate (macro conditions, checked daily):**
1. DXY below 50-day SMA (dollar weakening)
2. GLD above 20-day SMA (gold uptrend — hard asset bid)
3. BTC above 50-day SMA (structural bull trend)

**Entry trigger (per BTC bar within regime):**
1. Regime gate active (all conditions met)
2. Two entry types:
   a) **Regime entry:** First bar where regime activates after a period of inactivity
   b) **Pullback entry:** BTC price within 10% of its 20-day SMA
3. Entry at close, stop at 1.5× ATR below entry
4. Target at 2× risk

**Exit:**
- Stop loss (1.5× ATR)
- Target profit (2× risk)
- Max hold: 20 bars (~4 weeks)

## Default Parameters

| Param | Default | Walk-forward grid |
|---|---|---|
| `ATR_STOP_MULT` | 1.5 | 1.0, 1.5, 2.0 |
| `PULLBACK_PCT` | 0.10 | 0.05, 0.10, 0.15 |
| `MIN_RR` | 2.0 | 1.5, 2.0, 2.5 |
| `DXY_SMA_SLOW` | 50 | (fixed) |
| `GLD_SMA` | 20 | (fixed) |
| `BTC_MA_TREND` | 50 | (fixed) |
| `MAX_BARS_HELD` | 20 | (fixed) |

## Backtest & Validation Results

### Phase 1A (frictionless, crypto universe, 2020-08 → 2026-08)
| Metric | Value |
|---|---|
| Total signals | 65 |
| Signals/year | 11.1 |
| Mean R | **+0.302** |
| Median R | −0.110 |
| Win rate | 47.7% |
| Sub-periods positive | 2/2 (2020-2023 bear, 2024-2026 current) |
| p-value (t-test, H0: mean R=0) | **0.157** |
| Pipeline classification | SPECULATIVE (mean R > 0, p < 0.20) |

### Walk-Forward (2-year train / 1-year test, rolling; quick grid; net of costs)
| Window | OOS mean R | OOS n | Win Rate | Verdict |
|---|---|---|---|---|
| 2022 (bear) | **−0.624** | 4 | 25% | NO EDGE |
| 2023 | **+0.620** | 16 | 62% | FRAGILE EDGE (p=0.088) |
| 2024 | **−0.684** | 10 | 20% | NO EDGE |
| 2025 | **+0.027** | 16 | 44% | NO EDGE |
| 2026 | **+0.849** | 7 | 57% | NO EDGE |
| **OOS pooled** | **+0.131** | 53 | — | **NO EDGE** (p=0.553) |
| In-sample | +0.292 | 65 | — | POSSIBLE EDGE (low confidence) |

**Decision:** OOS mean R = +0.131 > 0 but p-value = 0.553 > 0.10 →
**WATCH, deployed to paper trading with reduced risk.** The edge is inconsistent
across windows — positive in 2023/2026, negative in 2022/2024. The strategy
trades the debasement regime which is a low-frequency, high-conviction macro
setup. The Aug 2026 Treasury buyback catalyst is a specific event not captured
in the walk-forward (data only through Aug 14).

## Key Risks & Caveats

- **Low signal count:** ~11 signals/year means statistical significance is
  hard to achieve. The edge may be noise.
- **Regime dependency:** The strategy only fires when all macro conditions align.
  In prolonged dollar-strength or gold-weakness periods (like most of 2022-2024),
  it produces few signals with poor performance.
- **2026 catalyst recency:** The Aug 19 Treasury buyback that motivated this
  candidate is not in the backtest data (DXY cache ends Aug 14). The 2026 OOS
  window shows positive performance (+0.849) but only 7 signals.
- **Transaction costs matter:** With BTC at $80K+, a 2bp spread costs ~$16 per
  trade. The walk-forward already models this (5bp round-trip) but slippage
  in volatile conditions could degrade the edge.
- **BTC-specific:** Strategy only trades BTC. Single-ticker concentration risk
  means it should never exceed 1.0% portfolio risk.

## Deployment

- **Scanner:** `scripts/validation/scanners/scanner_treasury_debasement.py`
- **Paper trading:** `scripts/paper_trading/capture_signals.py` →
  `STR-DEBASEMENT-treasury-buyback` (id `STR-DEBASE`)
- **Position sizing:** `scripts/paper_trading/position_sizing.py` →
  `size_strategy_debase` = **0.5% base risk** (WATCH, reduced)
- **Regime selector:** `scripts/research/regime_strategy_selector.py` →
  `STR-DEBASE` status WATCH, `regime_best` [risk_on, neutral, complacent],
  `regime_avoid` [risk_off]
- **Walk-forward registry:** `scripts/validation/walk_forward.py` → key `DEBASE`

## What Would Change My View

- If live-paper shows mean R ≤ 0 over 20+ signals → demote to KILLED.
- If the Treasury ends buyback operations (policy reversal) → the regime catalyst
  is removed, demote to KILLED unless DXY/Gold conditions persist independently.
- If BTC drops below $72K (20% from Aug 25 $80K+) without recovery → technical
  exit per the candidate's own rules.

## Related

- Edge candidate: [[CAND-20260825-treasury-buyback-debasement-regime]]
- Complementary: CAND-20260825-oil-equity-vol-divergence (deflationary
  resolution path supports BTC/Gold same as debasement trade)
- Related regime: CAND-20260823-bofa-sellside-extreme (extreme bullish
  sentiment → risk-management overlay — debasement BTC longs should be
  reduced if BofA indicator triggers)