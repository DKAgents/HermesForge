---
strategy_id: scanner_overnight_drift
date: 2026-09-21
action: demote
decay_probability: 0.82
breakdown_probability: ">0.60"
reason: "Jev classification: scanner strategy edge eroded. Both decay (82%) and breakdown exceed demotion thresholds."
status: csv_only
note: "No .md file in 06-Strategies/Active/. CSV: scripts/validation/results/scanner_overnight_drift-phase1a.csv"
---
# Demotion: scanner_overnight_drift

**Date:** 2026-09-21
**Decay probability:** 82%
**Action:** Demoted from active paper trading

Scanner-based overnight drift strategy shows significant edge erosion. Jev confirms structural decay beyond normal drawdown variance.

CSV-tracked only. Flag for removal from active validation roster.