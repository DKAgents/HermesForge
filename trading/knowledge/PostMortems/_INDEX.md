---
type: moc
topic: postmortem
created: 2026-11-02
updated: 2026-11-02
tags: [moc, postmortem, feedback, generation]
source: postmortem
---

# Post-Mortem Index (US-216)

One-paragraph post-mortem per failed strategy/class. Each note records the
gate it died at, the root reason, and what would have to be true for a variant
to pass. Generation crons (US-215) and `signal_class.py` (US-191) treat these
as the canonical failure record for their mechanism classes.

| Strategy / Class | Gate | Signal class | Note |
|---|---|---|---|
| STR-Q liquidity-sweep | G3 (execution realism) | ict-smc | [[STR-Q-liquidity-sweep]] |
| Chart-pattern class (16) | G0 (cost) | chart-pattern | [[STR-chart-pattern-class]] |
| Funding carry (directional) | G3 (execution realism) | systematic | [[STR-funding-carry-directional]] |
| Cross-sectional momentum (raw) | G4 (CPCV) | systematic | [[STR-xsmom-cross-sectional]] |
| STR-A ma-pullback-fibonacci | G0 (intake) | retail-ta | [[STR-A-ma-pullback-fibonacci]] |
| STR-B macd-histogram-divergence | G3 (execution realism) | retail-ta | [[STR-B-macd-histogram-divergence]] |

## Query

```dataview
TABLE gate, signal_class, status
FROM "trading/knowledge/PostMortems"
WHERE type = "postmortem"
SORT file.name ASC
```