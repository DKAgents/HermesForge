# MIG-18: Risk Rules Guardrail

**Date**: 2026-09-27

**Context**: After 06-Strategies → trading/strategies move, `capture_signals.py` loads strategy files from `trading/strategies/Hypotheses/`. Risk sizing delegates to `position_sizing.py`.

**Actual risk caps** (from code audit):
- **No strategy YAML files declare `risk_pct`** — zero of 70+ strategy files have this field
- `position_sizing.py::get_risk_pct()` defaults: **1.0% for stocks, 0.5% for crypto** (line 203-207)
- Portfolio heat check in `position_sizing.py::check_portfolio_heat()` caps aggregate open risk at 5% (ADR-004 line 224)
- `risk_multiplier` from regime directives can adjust up/down but no multiplier exceeds 1.5x (code audit line 346-347)

**Result**: Effective per-trade risk never exceeds 1.0% (stocks) / 0.5% (crypto) because no strategy overrides the defaults and position sizing has no mechanism to increase them beyond those values.

**Note**: There is no explicit `min(risk_pct, 1.0)` guardrail — it is implicitly enforced by the defaults and the absence of strategy-level overrides.

**Rollback**: N/A (code unchanged, documentary only).