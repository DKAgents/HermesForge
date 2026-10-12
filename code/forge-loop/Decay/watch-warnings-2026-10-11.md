# Jev-Powered Decay Watch — 2026-10-11

- run: jev_decay_check.py
- date: 2026-10-11
- type: decay-watch

## Summary

3 active strategies checked. 1 flagged for attention.

## Flagged Strategies

| Strategy | Decay Prob | Rec | Trades | Avg R | Win Rate | PF |
|---|---|---|---|---|---|---|
| 🟡 STR-A-ma-pullback-fibonacci | 80% | watch | 10 | -0.096 | 10% | 0.68 |

**Note**: At 80% decay probability — above watch threshold (>45%) but below demotion threshold (>70% decay + >60% breakdown). Jev did NOT classify as structural breakdown this cycle, so remains on watch.

## Healthy Strategies

| Strategy | Decay Prob | Rec | Trades |
|---|---|---|---|
| ✅ STR-VIXC-vix-contango-breakout | 39% | healthy | 16 |
| ⏭ STR-OIL-SHOCK | 0% | no_data | 0 (new strategy, no closed trades yet) |

## Escalation Path

- **STR-A-ma-pullback-fibonacci**: Watch. If next cycle shows decay >70% AND breakdown >60%, escalate to demotion.
- **STR-OIL-SHOCK**: No data — normal for a new strategy with 0 closed trades.
- **STR-VIXC-vix-contango-breakout**: Healthy (39% well below watch threshold).