---
strategy_id: STR-BTC-DOM
date: 2026-09-21
action: demote
decay_probability: 0.86
breakdown_probability: ">0.60"
reason: "Jev classification: edge decayed beyond recovery. Both decay (86%) and breakdown probabilities exceed demotion thresholds. Strategy no longer meets active criteria."
status: csv_only
note: "No .md file exists in 06-Strategies/Active/ — strategy tracked via CSV only (scripts/validation/results/STR-BTC-DOM-phase1a.csv). Remove from active tracking."
---
# Demotion: STR-BTC-DOM

**Date:** 2026-09-21
**Decay probability:** 86%
**Action:** Demoted from active paper trading

Jev determined with high confidence that this strategy's edge has decayed. Both the decay probability (86%) and breakdown probability exceeded the demotion thresholds (70%/60%).

The strategy was CSV-tracked only — no corresponding .md file in Active. Flag for removal from the active validation roster.