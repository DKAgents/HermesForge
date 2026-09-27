---
type: moc
topic: risk
created: 2026-07-30
updated: 2026-07-30
tags: [moc, risk, navigation]
confidence: high
has_quotes: false
source: HermesForge Risk Framework
---
# Risk MOC

Navigation hub for all risk management artifacts.

## Risk Documents

```dataview
TABLE type, status
FROM "07-Risk"
WHERE type != "moc"
SORT file.name ASC
```

## Guardian Decisions

```dataview
TABLE date, decision, rationale
FROM "07-Risk"
WHERE type = "guardian-decisions" OR type = "risk-escalation" OR type = "incident-log"
SORT file.name DESC
```

## Related
- [[RISK_RULES]]
- [[ADR-005-Stage-Based-Model-Floors-and-Red-Team]]
- [[STRATEGIES-MOC]]
