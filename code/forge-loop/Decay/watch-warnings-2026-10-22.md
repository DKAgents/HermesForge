# Jev-Powered Decay Watch — 2026-10-22

- tool: jev_decay
- source: jev_decay_check.py
- type: decay-watch
- run: 2026-10-22T14:00 UTC

## Active Strategies Checked (3)

| Strategy | Decay Prob | Rec | Trades | Avg R | Win Rate | PF |
|----------|-----------|-----|--------|-------|----------|----|
| STR-A-ma-pullback-fibonacci | **79%** | **watch** 🔴 | 10 | -0.096 | 10% | 0.68 |
| STR-OIL-SHOCK | 0% | no_data | 0 | — | — | — |
| STR-VIXC-vix-contango-breakout | **39%** | healthy ✅ | 16 | +0.062 | 6% | 2.0 |

## Jev Decision Request (decay > 50%)

**STR-A-ma-pullback-fibonacci** — choice query on action (run 2026-10-22):
- **demote**: 0.70
- kill: 0.26
- watch_data: 0.03
- watch_tune: 0.01
- Confidence: 0.60

## Summary

1. **STR-A-ma-pullback-fibonacci (79%)** — Above the 50% intervention threshold. 10 trades, negative avg R (-0.096), 10% win rate, PF 0.68, 2-trade current losing streak. Jev classified as watch (decay 79%; breakdown probability below the 60% demotion leg). Independent Jev decision request recommends **demote (70%, conf 0.60)**. Escalating: **5th consecutive cycle** at high decay (69% → 80% → 79% → 80% → 79%). Needs human review for demotion — no action taken autonomously.

2. **STR-OIL-SHOCK** — 0 closed trades. No data to evaluate yet (new strategy, no closed trades since Sep 1 deployment).

3. **STR-VIXC-vix-contango-breakout (39%)** — Healthy. 16 trades, PF 2.0. No intervention needed.

## Action

- **STR-A-ma-pullback-fibonacci**: FLAG for intervention — Jev decision recommends demote (5th consecutive high-decay cycle). Awaiting human approval (strategy lifecycle changes require user trigger).
- All other strategies: no intervention needed