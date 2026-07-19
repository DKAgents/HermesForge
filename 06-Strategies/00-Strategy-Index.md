---
type: index
updated: 2026-07-19
tags: [strategy, index]
---

# Strategy Index

All active, hypothesis, and deprecated strategies. Maintained automatically by Dataview.

---

## Active Strategies

```dataview
TABLE
  core_idea AS "Idea",
  market_regime AS "Regime",
  trade_style AS "Style",
  asset_class AS "Asset",
  timeframe AS "TF",
  confidence AS "Confidence",
  last_reviewed AS "Last Reviewed"
FROM "06-Strategies/Active"
WHERE type = "strategy"
SORT last_reviewed DESC
```

---

## Hypotheses (Under Development)

```dataview
TABLE
  core_idea AS "Idea",
  market_regime AS "Regime",
  trade_style AS "Style",
  asset_class AS "Asset",
  timeframe AS "TF",
  confidence AS "Confidence",
  last_reviewed AS "Last Reviewed"
FROM "06-Strategies/Hypotheses"
WHERE type = "strategy"
SORT last_reviewed DESC
```

---

## Pending Updates

```dataview
TABLE
  file.mtime AS "Modified"
FROM "06-Strategies/Pending-Updates"
SORT file.mtime DESC
```

---

## Deprecated Strategies

```dataview
TABLE
  trade_style AS "Style",
  last_reviewed AS "Deprecated On"
FROM "06-Strategies/Deprecated"
WHERE type = "strategy"
SORT last_reviewed DESC
```

---

## Strategy Count by Status

```dataview
TABLE rows.file.name AS "Strategies"
FROM "06-Strategies"
WHERE type = "strategy"
GROUP BY status
```

---

## Validation Quick-Check

Run `python3 scripts/validate_strategy.py` to verify all strategies have passing evidence links and required sections.
