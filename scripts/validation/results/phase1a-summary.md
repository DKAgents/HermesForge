# Phase 1A Results Summary
Generated: 2026-07-19 21:40

## Classification Criteria (ADR-004)
- **Kill**: < 12 signals/year OR avg R < 0.2 (frictionless)
- **Watch**: between kill and pass thresholds
- **Pass**: >= 25 signals/year AND avg R >= 0.6 AND positive in >= 2 of 3 sub-periods
- **Friction flag**: avg R < 0.5 — check after adding costs in Phase 1B

## Results

| Strategy | Sig/Yr | Avg R | Median R | Win Rate | Sub-Periods+ | Friction | Status |
|---|---|---|---|---|---|---|---|
| STR-A-ma-pullback-fibonacci | 41.1 | 26.04 | 9.123 | 100.0% | 3/3 | ✓ | ✅ PASS |
| STR-B-macd-histogram-divergence | 0.0 | 0.0 | 0.0 | 0.0% | 0/3 | ✓ | ❌ KILL |
| STR-C-breakout-volume | 330.5 | 0.092 | -0.518 | 43.8% | 0/3 | ⚠️ | ❌ KILL |
| STR-D-sr-role-reversal | 63.3 | 0.227 | 0.016 | 50.3% | 0/3 | ⚠️ | ⚠️  WATCH |

## Decisions

### STR-A-ma-pullback-fibonacci
**Decision:** ✅ PASS
- Sufficient frequency and edge. Advance to Phase 1B for perturbation testing.

### STR-B-macd-histogram-divergence
**Decision:** ❌ KILL
- Signals too rare or edge too weak. Drop or major revision before Phase 1B.

### STR-C-breakout-volume
**Decision:** ❌ KILL
- Signals too rare or edge too weak. Drop or major revision before Phase 1B.
- ⚠️ Friction flag: avg R below 0.5 — verify edge survives commission + slippage in Phase 1B.

### STR-D-sr-role-reversal
**Decision:** ⚠️  WATCH
- Marginal results. Advance to Phase 1B with caution flag. Review operationalization.
- ⚠️ Friction flag: avg R below 0.5 — verify edge survives commission + slippage in Phase 1B.
