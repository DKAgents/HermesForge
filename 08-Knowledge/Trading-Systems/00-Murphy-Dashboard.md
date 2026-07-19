---
type: dashboard
source_book: "Technical Analysis of the Financial Markets"
source_author: "John J. Murphy"
book_slug: technical-analysis-financial-markets-murphy
created: 2026-07-19
tags: [dashboard, trading-system, technical-analysis-of-the-financial-markets]
---

# Murphy — Technical Analysis Dashboard

> **1,257 atomic notes** extracted from *Technical Analysis of the Financial Markets* by John J. Murphy.
> Use the queries below to navigate by concept type, topic, confidence, or page range.

---

## 📊 Coverage Summary

```dataview
TABLE length(rows) AS "Notes"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE type = "atomic-note"
GROUP BY concept_type
SORT length(rows) DESC
```

---

## 📋 All Trading Rules (high confidence)

```dataview
TABLE source_page_range AS "Page", topic AS "Topic"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/rules"
WHERE concept_type = "rule" AND confidence = "high"
SORT source_page_range ASC
```

---

## ✅ Entry Criteria Checklist

```dataview
TABLE source_page_range AS "Page", topic AS "Topic"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/rules"
WHERE concept_type = "entry-criteria"
SORT file.name ASC
```

---

## 🚪 Exit Criteria

```dataview
TABLE source_page_range AS "Page", topic AS "Topic"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/rules"
WHERE concept_type = "exit-criteria"
SORT file.name ASC
```

---

## 🛡️ Risk Guidelines

```dataview
TABLE source_page_range AS "Page", confidence
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/risk-guidelines"
SORT file.name ASC
```

---

## ⚠️ Edge Conditions (when rules break down)

```dataview
TABLE source_page_range AS "Page", topic AS "Topic"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy/edge-conditions"
SORT file.name ASC
```

---

## 🔍 Browse by Topic

### Trend & Trendlines
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "trend") AND type = "atomic-note"
SORT concept_type ASC, file.name ASC
```

### Support & Resistance
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "support-resistance")
SORT concept_type ASC
```

### Chart Patterns
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "chart-patterns")
SORT concept_type ASC, file.name ASC
```

### Oscillators & Momentum
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "oscillators")
SORT concept_type ASC, file.name ASC
```

### Moving Averages
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "moving-averages")
SORT concept_type ASC, file.name ASC
```

### Volume & Open Interest
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "volume")
SORT concept_type ASC, file.name ASC
```

### Risk Management
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "risk-management")
SORT concept_type ASC, file.name ASC
```

### Elliott Wave
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "elliott-wave")
SORT concept_type ASC
```

### Intermarket Analysis
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE contains(topic, "intermarket")
SORT concept_type ASC
```

---

## 🔬 Quality Filters

### Low Confidence Notes (needs review)
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page", topic AS "Topic"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE confidence = "low"
SORT concept_type ASC
```

### Highest Evidence Density (most quotes)
```dataview
TABLE concept_type AS "Type", source_page_range AS "Page"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE type = "atomic-note"
SORT file.size DESC
LIMIT 25
```

---

## 🗺️ Topic Coverage Map

```dataview
TABLE length(rows) AS "Notes", rows.concept_type AS "Types"
FROM "08-Knowledge/Trading-Systems/technical-analysis-financial-markets-murphy"
WHERE type = "atomic-note"
GROUP BY topic
SORT length(rows) DESC
```

---

_Dashboard auto-generated by HermesForge vault-query pipeline — 2026-07-19_
_Queries powered by Obsidian Dataview plugin_
