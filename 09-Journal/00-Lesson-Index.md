---
type: index
updated: 2026-07-19
tags: [lessons, feedback-loop, index]
---

# Lesson Index

All lessons extracted from backtest results, paper trades, and analysis sessions.
Maintained automatically by Dataview.

---

## All Lessons (by date, newest first)

```dataview
TABLE
  source AS "Source",
  outcome AS "Outcome",
  confidence AS "Confidence",
  related_strategy AS "Strategy",
  date AS "Date"
FROM "09-Journal/Lessons"
WHERE type = "lesson"
SORT date DESC
```

---

## Filter by Outcome

### Confirms ✅

```dataview
TABLE
  source AS "Source",
  related_strategy AS "Strategy",
  date AS "Date"
FROM "09-Journal/Lessons"
WHERE type = "lesson" AND outcome = "confirms"
SORT date DESC
```

### Contradicts ❌

```dataview
TABLE
  source AS "Source",
  related_strategy AS "Strategy",
  date AS "Date"
FROM "09-Journal/Lessons"
WHERE type = "lesson" AND outcome = "contradicts"
SORT date DESC
```

### Refines 🔧

```dataview
TABLE
  source AS "Source",
  related_strategy AS "Strategy",
  date AS "Date"
FROM "09-Journal/Lessons"
WHERE type = "lesson" AND outcome = "refines"
SORT date DESC
```

### New Findings 💡

```dataview
TABLE
  source AS "Source",
  date AS "Date"
FROM "09-Journal/Lessons"
WHERE type = "lesson" AND outcome = "new-finding"
SORT date DESC
```

---

## Notes with High Confirmation Count

```dataview
TABLE
  confirmation_count AS "Confirmations",
  confidence AS "Confidence"
FROM "08-Knowledge"
WHERE confirmation_count >= 2
SORT confirmation_count DESC
LIMIT 20
```

---

## Lesson Count by Month

```dataview
TABLE rows.file.name AS "Lessons", length(rows) AS "Count"
FROM "09-Journal/Lessons"
WHERE type = "lesson"
GROUP BY dateformat(date(date), "yyyy-MM")
SORT rows.date DESC
```
