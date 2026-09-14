---
id: PROP-001
title: Hermes Strategy Gauntlet
type: proposal
status: draft
asset_class: crypto
venue: hyperliquid
trade_style: [intraday_5m, swing]
timeframe: [5m, 1h, 6h]
confidence: medium
last_reviewed: 2026-09-14
---

# Hermes Strategy Gauntlet

A pipeline for generating strategy candidates, killing the bad ones cheaply, and hardening what survives — built on the test infrastructure Hermes already has, with the crypto-perp pieces it doesn't.

| | |
|---|---|
| Venue | Hyperliquid perps |
| Round trip, taker | 9.0 bps |
| Funding settlement | Hourly |
| Signal timeframes | 5m / 1h / 6h |
| Validation gates | G0 → G7 |

---

## 00 · Start from the cost floor, not the chart

Every decision downstream is set by one number. Hyperliquid's base perp tier is **0.045% taker / 0.015% maker**, so a taker-in / taker-out round trip costs 9.0 bps before slippage. Add realistic slippage on majors and a funding accrual if the position crosses an hourly settlement, and a 5-minute trade is carrying roughly **11–13 bps** of drag.

| Component | Cost |
|---|---|
| Entry, taker | 4.5 bps |
| Exit, taker | 4.5 bps |
| Slippage, majors at modest clip | 1.5–3.0 bps |
| Funding, 1 settlement near baseline | 0.1–0.6 bps |
| **All-in per round trip** | **10.6–12.6 bps** |
| Gross capture needed at 4× cost | **≥ 45 bps** |

> **What this eliminates before any code is written**
>
> A 5-minute strategy whose average gross capture is 20–30 bps cannot be profitable at base fees. Screening for this first is the single cheapest filter available, and it should run *before* Phase 1a.

The **4× multiplier** sets the point where cost consumes a quarter of gross edge. Tighten to 5–6× for unconditionally-taker entries; relax toward 3× only for strategies that G3 shows genuinely fill passive.

---

## 01 · Finding candidates: search conditions, not strategies

Fix a small set of **entry primitives** and search the space of **conditions** under which each has positive expectancy:

```
6 primitives × 4 regimes × 3 funding states × 4 OI quadrants
= 288 cells — every one of them a ledgered trial
```

### Discovery tiers, ranked by yield per unit of cost

| Tier | Method | Cost |
|---|---|---|
| **T0** | **Transfer audit** — re-run STR-X, STR-AA, STR-AF, STR-B against 5m/6h crypto parquet. | Days |
| **T1** | **Vault-to-hypothesis** — convert edge conditions into pre-registered, falsifiable hypotheses. | Days |
| **T2** | **Conditional-edge mining** — the 288-cell grid. | 2–3 weeks |
| **T3** | **Event-study factory** — forward returns from monitoring-detected events, block-bootstrap bands. | 2 weeks |
| **T4** | **Factor / ML discovery** — defer until T0–T3 exhausted and trials ledger in place. | Defer |

### Prerequisite: trials ledger

Append-only ledger (`hypothesis_id`, `param_hash`, universe, period, timestamp, result) that every backtest writes to exactly once. Backfill from existing 115 CSVs.

### Seed pool: ten candidates

| ID | Style | Hypothesis | Tier | Likeliest killer |
|---|---|---|---|---|
| HYP-01 | Swing 4–48h | **Funding-extreme unwind.** Fade crowded positioning when funding >95th %ile + OI still rising. | T3 | G6 regime |
| HYP-02 | Intraday 5m | **OI-confirmed breakout.** Range breakouts only in price↑/OI↑ quadrant (new money). | T2 | G3 execution |
| HYP-03 | Intraday 5m | **Cascade exhaustion.** After liquidation cascade, first retrace tradeable opposite direction. | T3 | **G2 look-ahead** |
| HYP-04 | Intraday 5m | **Settlement-hour drift.** Directional drift around hourly funding settlement boundary. | T3 | **G0 cost** |
| HYP-05 | Swing 1–7d | **Cross-sectional perp momentum.** Long top-decile / short bottom-decile 7-day return with funding filter. | T1 | G6 clustering |
| HYP-06 | Intraday 5m–4h | **BTC-beta residual reversion.** Alt residual against BTC-beta-implied price, reverts when >2σ. | T2 | **G0 two-leg cost** |
| HYP-07 | Intraday 5m | **Asia-range / EU-continuation.** Asia range break, EU-confirmed, carried through US open. | T2 | G5 trials |
| HYP-08 | Intraday 5m | **Oracle-mark dislocation.** Mark vs CEX-weighted-median oracle divergence snap-back. | T3 | **G0 capacity** |
| HYP-09 | Swing 1–5d | **Volatility compression expansion.** ATR-percentile <20th into directional expansion on structural break. | T1 | G4 stability |
| HYP-10 | Swing 1–14d | **New-listing drift.** Newly listed perps, persistent funding skew + directional drift. | T1 | **G5 sample** |

---

## 02 · Eight validation gates, cheapest first

### G0 · Cost & capacity pre-screen
Measure median |move| over intended horizon vs all-in round-trip cost. Size clip against L2 top-5 depth.

> **Pass** — median |move| ≥ 4× all-in cost · clip ≤ 4% top-5 depth · expected gross capture ≥ 45 bps (taker)

### G1 · Signal scan on liquidity-filtered universe
Phase 1a on Hyperliquid perps with liquidity screen. Universe fixed and versioned.

> **Pass** — ≥ 200 signals across ≥ 15 symbols · 30d median 5m notional ≥ $250k · top-5 depth ≥ $50k within 10 bps · universe hash recorded

### G2 · Leakage audit, crypto-extended
L1–L3 invariance suite + perp-specific leaks (funding lag, OI/depth lag, 24/7 calendar, delay-one-bar stress test).

> **Pass** — L1–L3 green · funding/OI accessed only with realistic lag · delay-one-bar edge decay < 50%

### G3 · Execution realism
Replay fills against L2: optimistic (mid) / realistic (queue-aware) / pessimistic (always taker + adverse selection). Accrue funding hourly.

> **Pass** — realistic ≥ 60% of optimistic avg R · pessimistic PF > 1.0 · slippage monotonic in clip size

### G4 · Combinatorial purged cross-validation
CPCV: N=12 groups, k=2 test groups → C(12,2)=66 splits, 11 reconstructed paths. Purge by holding horizon, embargo after. Stationary block bootstrap.

> **Pass** — median split PF ≥ 1.3 · 10th-%ile split PF ≥ 1.0 · worst path max-DD within budget · block-bootstrap p < 0.05

### G5 · Multiple-testing correction
Deflated Sharpe Ratio from ledger N. PBO from split-level rank distribution.

> **Pass** — DSR > 0.95 · PBO < 0.30 · values + N written to strategy note

### G6 · Robustness partitioning
P&L by regime, beta cluster, session, funding state. Edge must appear in >1 beta cluster.

> **Pass** — non-negative in ≥ 3 of 4 regimes · present in ≥ 2 of 3 beta clusters · no symbol > 35% P&L · no single month > 40%

### G7 · Forward validation
Paper-trade signals, log modelled vs realised slippage, promote Hypotheses → Active on passing.

> **Pass** — ≥ 100 trades or 30 sessions · realised slippage ≤ 1.5× modelled · live avg R ≥ 50% CPCV median

### Illustrative attrition

```
Candidates     ████████████████████████████████████████  100
G0 cost        ██████████████████                         45
G1 scan        ██████████████                             34
G2 leakage     ██████████                                 24
G3 execution   █████                                      12
G4 CPCV        ███                                         7
G5 DSR / PBO   ██                                          4
G6 partition   █                                           3
G7 forward     █                                           2
```

### Retirement (pre-registered kill rules)

- Trailing-100-trade PF < 1.15, **or**
- Trailing-20-trade avg R < 0 for two consecutive non-overlapping windows, **or**
- Realised slippage > 2× modelled for 20 consecutive trades

→ auto-demotes Active → Hypotheses, opens review note.

---

## 03 · What to build

### New signal modules

| Module | Purpose | Emits |
|---|---|---|
| `funding_state.py` | Hyperliquid funding formula: hourly=⅛ of 8h rate, interest 0.01%/8h, clamp ±0.05%, cap 4%/hr. 90-day z-score, funding/basis divergence, cumulative funding per position. | `funding_z`, `crowding_flag`, `carry_bps_per_hour`, `settlement_countdown` |
| `oi_delta.py` | Classifies ΔOI vs Δprice into new-longs/short-covering/new-shorts/long-liquidation. | `oi_quadrant`, `oi_delta_z`, `participation_score` |
| `liquidation_pressure.py` | Estimated liquidation clusters, distance in ATR, cascade-exhaustion flag. | `dist_to_cluster_atr`, `cascade_active`, `exhaustion_flag` |
| `book_imbalance.py` | Top-N depth imbalance + depth-weighted mid with persistence sampling. | `imbalance_ratio`, `depth_usd_5lvl`, `slippage_curve` |
| `crypto_regime.py` | BTC realised-vol percentile, multi-TF trend alignment, cross-sectional funding dispersion, aggregate OI trend, stablecoin net flow. | `regime`, `confidence`, `risk_multiplier` *(interface-compatible)* |
| `session_clock.py` | Asia/EU/US session boundaries, CME gap windows, weekend flag, funding settlement clock. | `session`, `liquidity_tier`, `minutes_to_settlement` |
| `correlation_state.py` | Rolling BTC beta and correlation per symbol, clustered. | `btc_beta`, `corr_cluster_id`, `portfolio_concentration` |
| `execution_sim.py` | Three-mode fill simulator (optimistic/realistic/pessimistic), queue-position, size-dependent slippage, hourly funding, margin headroom. | `fills`, `fees`, `funding_paid`, `realised_slippage_bps` |

### Revisions to existing modules

| Module | Change |
|---|---|
| `market_structure.py` | Stop cap/floor in bps not price; remove session-gap assumptions; adjust target for funding on settlement-crossing holds. |
| `regime_filter.py` | Add `asset_class` parameter → `crypto_regime`; extend `as_of` + degradation tests for crypto path. |
| `validate_strategy.py` | New frontmatter: `venue`, `fee_tier_assumed`, `funding_model`, `max_holding_hours`, `execution_mode`, `trials_count`, `capacity_usd`, `decay_rule`, `gates_passed`. Gate-vs-folder consistency check. |
| Backtester profile | Add G0, G3, G5 to mandatory bias-flag checklist; trials-ledger write; cite DSR and PBO. |
| `_test_sample_signals.py` | Promote to fixtured CI with golden-output comparison. |

### New agent skills

| Skill | Gate served |
|---|---|
| `hypothesis-register` | G5 — pre-register hypothesis + falsification criteria before backtest; increments ledger. |
| `event-study` | T3/G1 — forward-return curves by horizon/regime with block-bootstrap bands. |
| `execution-audit` | G3 — run candidate through all three fill modes; report edge decay. |
| `overfit-audit` | G4/G5 — CPCV splits, PBO, DSR from ledger; formal go/no-go. |
| `regime-attribution` | G6 — P&L decomposition by regime, beta cluster, session, funding state. |
| `capacity-model` | G0/G7 — size against live L2 depth; max notional at stated slippage budget. |
| `decay-watch` | Post-G7 — scheduled recomputation of rolling stats; applies pre-registered kill rules. |

### New test suites

| Suite | Coverage |
|---|---|
| `test_execution_sim.py` | E1–E12: touch-vs-trade-through, queue position, fee tiers, funding accrual, slippage monotonicity, mode ordering invariant. |
| `test_funding_math.py` | Golden vectors: hourly=⅛ of 8h, interest 0.01%/8h, clamp ±0.05%, cap 4%/hr, premium from 5-second samples. |
| `test_oi_classification.py` | Four quadrants, boundary cases, NaN/stale-snapshot handling. |
| `test_crypto_regime.py` | Mirrors 11 areas of `test_regime_filter.py` against crypto inputs. |
| `test_trials_ledger.py` | Increment integrity, concurrent-write safety, DSR reads same N, tamper detection. |
| `test_cpcv_splits.py` | Purge/embargo correctness, C(12,2)=66 distinct splits, 11 complete paths. |

---

## 04 · Position management

| Rule | Mechanism |
|---|---|
| **Cluster exposure cap** | Net exposure per BTC-beta cluster capped as fraction of equity. |
| **Liquidation headroom floor** | Portfolio distance-to-liquidation in ATR units (not %). |
| **Conflict resolution** | Explicit precedence when 5m signal opposes open swing on same symbol. |
| **Drawdown circuit breaker** | Tiered: −X% halve size, −Y% close discretionary, −Z% flat + alert. Thresholds from G4 worst-path max-DD. |

Equal-weight allocation to start; move off only when live sample justifies it.

| Module | Purpose |
|---|---|
| `position_manager.py` | Single authority over size. Every strategy proposes; this disposes. Logs gap between intended and actual. |
| `test_position_manager.py` | R1–R14: cap enforcement, headroom recomputation, conflict matrix, circuit-breaker tiers, synthetic correlated crash. **Invariant:** no approved order reduces headroom below floor. |

---

## 05 · Sequencing

**Weeks 1–2 · Instrument** — trials ledger + backfill, execution_sim + book_imbalance + tests, G0 script, T0 transfer audit

**Weeks 3–5 · Perceive** — funding_state, oi_delta, liquidation_pressure, session_clock, correlation_state, crypto_regime, hypothesis-register, event-study, T3 event-study factory

**Weeks 6–9 · Search** — T2 conditional-edge grid, CPCV harness, overfit-audit, G4/G5, validate_strategy.py extension

**Weeks 10–14 · Forward** — position_manager + adversarial suite, paper-trade logging, testnet order placement, realised-vs-modelled slippage, decay-watch

> **If you only do one thing:** Build the execution simulator and the trials ledger first. Every strategy number is conditional on fill assumptions never modelled and a trials count never recorded.

---

## 06 · Where this proposal could be wrong

- DSR/PBO designed for institutional programs with thousands of trials; at modest size, a G5-failing but G3/G4/G6-passing strategy might still be worth paper-trading.
- CPCV assumes enough independent observations; for long-holding strategies, drop to walk-forward with wider embargo.
- Portfolio layer at weeks 10–14 could be moved earlier since its constraints change which strategies are worth validating.
- Fee tiers improve with volume; G0 threshold should read current tier, not a constant.
- Candle history is capped; parquet store is the system of record — any gap is silent survivorship bias.
- Module names and integration points are proposals to reconcile against the actual codebase.

---

> Everything above is research methodology, not investment advice. Every strategy in the seed pool is an untested hypothesis. I'm not a financial advisor, and leveraged perpetual futures can lose more than the position's margin.

## Sources

- [Funding — Hyperliquid Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding)
- [Info endpoint — Hyperliquid Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)
- [Hyperliquid Fees 2026](https://hyperliquidguide.com/guides/fees)
- [The Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- [Backtest overfitting in the machine learning era](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)
- [Combinatorial Purged Cross-Validation](https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross)